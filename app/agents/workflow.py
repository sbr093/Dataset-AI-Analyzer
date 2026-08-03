import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.agents.tools import analyze_dataset_tool
from app.agents.tools import summarize_dataset_tool, generate_chart_tool, detect_anomalies_tool, save_report_tool
from app.agents.validation import validate_chart, validate_dataset_summary, validate_anomalies

# 1. Initialize the LLM
# We use a standard temperature of 0 for deterministic, analytical answers.
# Initialize the local Ollama model
llm = ChatOllama(model="llama3.1", temperature=0)

# Bind the tool to the LLM so it knows it can execute the Pandas logic
tools = [analyze_dataset_tool, summarize_dataset_tool, generate_chart_tool, detect_anomalies_tool, save_report_tool]
llm_with_tools = llm.bind_tools(tools)

# Provide the LLM a compact schema description for expected tool outputs to reduce hallucination
TOOL_SCHEMA = """
Tool outputs follow these JSON shapes (examples):
- dataset_summary: {"type":"dataset_summary","rows":1234,"columns":12,"missing_values":10,"anomaly_count":2}
- anomalies: {"type":"anomalies","count":3,"items":[{"column":"sales","row_index":123,"value":450.0,"reason":"zscore"}]}
- chart: {"type":"chart","x":"region","y":"sales","chart_data":[{"region":"APAC","value":123.4,"count":10}],"insights":{}}
- save_report: {"type":"save_report","id":42,"status":"ok"}
"""

# 2. Define the System Prompt (Intent Guardrails & Persona)
SYSTEM_PROMPT = """You are a Senior Data Analysis AI Assistant.
You are working with CSV datasets and may use the available tools to answer user questions.
Always follow this process:
1. Identify whether the user is asking about dataset content, quality, anomalies, or charts.
2. If the user asks about data details, prefer using tools first.
3. When using a tool, invoke the best one for the job and keep output structured.
4. Use `state.dataset_summary` and `state.tool_history` to avoid repeating work.
5. If the user asks something outside data analysis, politely decline and stay on task.
Do not hallucinate data."""

# 3. Define the Core Agent Node
def agent_node(state: AgentState):
    messages = state.get("messages", [])
    file_path = state.get("current_file_path", "")
    tool_history = state.get("tool_history", [])
    
    # Dynamically inform the LLM of the active dataset path and past tool actions
    dynamic_system_prompt = SYSTEM_PROMPT + "\n\n" + TOOL_SCHEMA
    if file_path:
        dynamic_system_prompt += (
            f"\n\nActive Dataset File Path: '{file_path}'\n"
            f"When invoking dataset analysis tools, always pass '{file_path}' as the file path parameter."
        )

    if tool_history:
        dynamic_system_prompt += "\n\nPrevious tool outputs are available in state.tool_history. Use them to reason before calling a new tool."
        for entry in tool_history[-3:]:
            dynamic_system_prompt += f"\n- {entry.get('type', 'tool_output')}: {entry}"
        dynamic_system_prompt += "\n"
        
    # Ensure the dynamic system message is at the beginning of the context
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=dynamic_system_prompt)] + messages
    else:
        messages[0] = SystemMessage(content=dynamic_system_prompt)
        
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# 4. Define Routing Logic
def should_continue(state: AgentState) -> str:
    messages = state.get("messages", [])
    last_message = messages[-1]
    
    # If the LLM decided it needs to call a tool, route to the ToolNode
    if last_message.tool_calls:
        return "continue"

    # If a tool was just executed, allow one more agent interpretation pass
    if state.get("last_tool_executed"):
        return "end"

    return "end"

# 5. Build the LangGraph State Machine
workflow = StateGraph(AgentState)

# Add our nodes
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

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

# After a tool runs, it must always go back to the agent to interpret the result
workflow.add_edge("tools", "agent")

# Compile the graph into a runnable application
app_workflow = workflow.compile()

