from langchain_core.messages import HumanMessage, ToolMessage

from app.agents.workflow import capture_tool_results_node


def test_collect_tool_results_appends_tool_messages_to_history():
    state = {
        "messages": [
            HumanMessage(content="Please summarize this dataset."),
            ToolMessage(
                content='{"type": "dataset_summary", "rows": 12, "columns": 4, "missing_values": 2, "anomaly_count": 1}',
                tool_call_id="call-123",
                name="summarize_dataset_tool",
            ),
        ],
        "tool_history": [],
    }

    result = capture_tool_results_node(state)

    assert "tool_history" in result
    assert result["last_tool_executed"] is True
    assert result["tool_history"][0]["type"] == "dataset_summary"
    assert result["tool_history"][0]["tool_name"] == "summarize_dataset_tool"


def test_capture_tool_results_ignores_invalid_payloads():
    state = {
        "messages": [
            HumanMessage(content="Please summarize this dataset."),
            ToolMessage(
                content='{"type": "dataset_summary", "rows": "bad", "columns": 4, "missing_values": 2, "anomaly_count": 1}',
                tool_call_id="call-456",
                name="summarize_dataset_tool",
            ),
        ],
        "tool_history": [],
    }

    result = capture_tool_results_node(state)

    assert result["last_tool_executed"] is False
    assert result["tool_history"] == []
