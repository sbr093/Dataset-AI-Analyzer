import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.services.file_loader import load_dataframe
import json
from app.agents.tools import analyze_dataset_tool
from app.agents.tools import (
    summarize_dataset_tool, generate_chart_tool, detect_anomalies_tool,
    save_report_tool, find_extreme_row_tool, filter_count_tool, most_common_value_tool,
)
from app.agents.validation import (
    validate_chart, validate_dataset_summary, validate_anomalies,
    validate_extreme_row, validate_filter_count, validate_most_common,
)

# 1. Initialize the LLM
# We use a standard temperature of 0 for deterministic, analytical answers.
# Initialize the local Groq model
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)

# Bind the tools to the LLM so it knows it can execute the Pandas logic.
# tool_choice is left as "auto": Groq's API hard-rejects (400) any turn where
# tool_choice="any" is set but the model responds in plain text instead of
# calling a tool (e.g. "hi") - the system prompt is instructed enough for
# gpt-oss-120b to reliably call a tool on real data questions without forcing.
tools = [
    analyze_dataset_tool, summarize_dataset_tool, generate_chart_tool,
    detect_anomalies_tool, save_report_tool, find_extreme_row_tool, filter_count_tool,
    most_common_value_tool,
]
llm_with_tools = llm.bind_tools(tools)

# Plain-prose tool guide instead of raw JSON examples: embedding literal JSON
# in the prompt reliably caused the model to imitate that JSON as its answer
# text instead of issuing a real tool call.
TOOL_GUIDE = """
Tool guide:
- summarize_dataset_tool: overall stats (rows, columns, missing values, duplicates, quality score).
- generate_chart_tool: grouped averages/sums of a numeric column by a category column.
- find_extreme_row_tool: the single row with the highest or lowest value in a column. Use this for "best/worst/highest/lowest <column>" questions, not generate_chart_tool.
- filter_count_tool: count how many rows match a category value you already know. Use this for "how many <category>" questions.
- most_common_value_tool: the most frequent value(s) in a column, with counts. Use this for "most common/frequent/popular <column>" questions, not generate_chart_tool.
- detect_anomalies_tool: statistical outliers.
- save_report_tool: persist a generated summary for later lookup.
"""

# 2. Define the System Prompt (Intent Guardrails & Persona)
SYSTEM_PROMPT = """You are a Senior Data Analysis AI Assistant working with a single active dataset (CSV, TSV, Excel, or JSON).
For any question about the dataset, you must call one of the available tools to compute the real answer from the data.
Never write out a tool call as text or JSON in your answer — always use the actual tool-calling mechanism.
Never guess or hallucinate numbers; only state values a tool actually returned.
Once a tool has returned a valid result, use it to answer in clear, plain language."""

def collect_tool_results(state: AgentState) -> dict:
    messages = state.get("messages", [])
    tool_history = list(state.get("tool_history", []))

    for message in reversed(messages):
        if getattr(message, "type", "") != "tool":
            continue

        tool_name = getattr(message, "name", "unknown_tool")
        tool_content = getattr(message, "content", "")
        try:
            parsed = json.loads(tool_content)
        except Exception:
            parsed = {"raw": tool_content}

        tool_history.append({
            "type": parsed.get("type", "tool_output"),
            "tool_name": tool_name,
            "payload": parsed,
        })
        break

    return {"tool_history": tool_history}


def validate_tool_output(payload: dict) -> bool:
    if not isinstance(payload, dict):
        return False

    if payload.get("type") == "dataset_summary":
        return validate_dataset_summary(payload)
    if payload.get("type") == "chart":
        return validate_chart(payload)
    if payload.get("type") == "anomalies":
        return validate_anomalies(payload)
    if payload.get("type") == "save_report":
        return "status" in payload and "id" in payload
    if payload.get("type") == "extreme_row":
        return validate_extreme_row(payload)
    if payload.get("type") == "filter_count":
        return validate_filter_count(payload)
    if payload.get("type") == "most_common":
        return validate_most_common(payload)
    return False


def capture_tool_results_node(state: AgentState) -> dict:
    updates = collect_tool_results(state)
    history = updates.get("tool_history", [])
    valid_history = []

    for entry in history:
        payload = entry.get("payload") or {}
        if validate_tool_output(payload):
            valid_history.append(entry)

    if valid_history:
        return {"tool_history": valid_history, "last_tool_executed": True}
    return {"tool_history": list(state.get("tool_history", [])), "last_tool_executed": False}


# 3. Define the Core Agent Node
def agent_node(state: AgentState):
    messages = state.get("messages", [])
    file_path = state.get("current_file_path", "")
    tool_history = state.get("tool_history", [])
    loop_count = state.get("loop_count", 0)

    # Dynamically inform the LLM of the active dataset path and past tool actions
    dynamic_system_prompt = SYSTEM_PROMPT + "\n\n" + TOOL_GUIDE
    if file_path:
        dynamic_system_prompt += (
            f"\n\nActive Dataset File Path: '{file_path}'\n"
            f"When invoking dataset analysis tools, always pass '{file_path}' as the file path parameter."
        )
        # Ground the model in the real column names so it doesn't guess wrong
        # capitalization/spacing (e.g. "car_model" instead of "Car Model").
        if os.path.exists(file_path):
            try:
                columns = load_dataframe(file_path, nrows=0).columns.tolist()
                dynamic_system_prompt += f"\nDataset columns: {', '.join(columns)}"
            except Exception:
                pass

    if tool_history:
        dynamic_system_prompt += "\n\nPrevious tool results this turn:"
        for entry in tool_history[-3:]:
            dynamic_system_prompt += f"\n- {entry.get('type', 'tool_output')}: {entry.get('payload')}"
        dynamic_system_prompt += "\nIf these already answer the question, respond in plain language now instead of calling another tool."

    # Ensure the dynamic system message is at the beginning of the context
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=dynamic_system_prompt)] + messages
    else:
        messages[0] = SystemMessage(content=dynamic_system_prompt)

    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "loop_count": loop_count + 1}

# 4. Define Routing Logic
MAX_AGENT_LOOPS = 4

def should_continue(state: AgentState) -> str:
    messages = state.get("messages", [])
    last_message = messages[-1]

    # Hard cap so a forced tool call that keeps failing (e.g. bad params)
    # can't loop indefinitely.
    if state.get("loop_count", 0) >= MAX_AGENT_LOOPS:
        return "end"

    # If the LLM decided it needs to call a tool, route to the ToolNode
    if last_message.tool_calls:
        return "continue"

    return "end"

# 5. Build the LangGraph State Machine
workflow = StateGraph(AgentState)

# Add our nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))
workflow.add_node("capture_tool_results", capture_tool_results_node)

# Define the edges (how information flows)
workflow.set_entry_point("agent")

# Conditional edge: After the agent thinks, does it use a tool or finish?
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",
        "end": END
    }
)

# After a tool runs, capture the tool output into state and then hand back control to the agent.
workflow.add_edge("tools", "capture_tool_results")
workflow.add_edge("capture_tool_results", "agent")

# Compile the graph into a runnable application
app_workflow = workflow.compile()

