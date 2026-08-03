from typing import TypedDict, List, Dict, Any, Annotated
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # Tracks the chat history between the user and the AI
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Stores the filepath of the currently active dataset
    current_file_path: str
    
    # Stores the statistical summary so the AI can answer questions about it
    dataset_summary: Dict[str, Any]

    # Stores previous tool outputs for more agentic multi-step reasoning
    tool_history: List[Dict[str, Any]]