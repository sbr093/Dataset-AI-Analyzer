import os
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.agents.tools import analyze_dataset_tool

# 1. Initialize the LLM
# We use a standard temperature of 0 for deterministic, analytical answers.
# Initialize the local Ollama model
llm = ChatOllama(model="llama3.1", temperature=0)

# Bind the tool to the LLM so it knows it can execute the Pandas logic
tools = [analyze_dataset_tool]
llm_with_tools = llm.bind_tools(tools)

# 2. Define the System Prompt (Intent Guardrails & Persona)
SYSTEM_PROMPT = """You are a Senior Data Analysis AI Assistant. 
You have access to a tool that can analyze CSV datasets. 
If the user asks about data, use the tool or refer to the dataset_summary in your state.
If the user asks an irrelevant or out-of-domain query (like writing a joke, code, or a recipe), politely decline and state your purpose as a data analyst.
Do not hallucinate data."""

# 3. Define the Core Agent Node
def agent_node(state: AgentState):
    messages = state.get("messages", [])
    file_path = state.get("current_file_path", "")
    
    # Dynamically inform the LLM of the active dataset path
    dynamic_system_prompt = SYSTEM_PROMPT
    if file_path:
        dynamic_system_prompt += (
            f"\n\nActive Dataset File Path: '{file_path}'\n"
            f"When invoking dataset analysis tools, always pass '{file_path}' as the file path parameter."
        )
        
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
    # Otherwise, the LLM has finished its thought process
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