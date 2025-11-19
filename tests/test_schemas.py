import pytest
from pydantic import ValidationError
from app.models import schemas

def test_agent_input_valid():
    data = {"query": "Valid query text", "max_iterations": 3}
    obj = schemas.AgentInput(**data)
    assert obj.query == data["query"]
    assert obj.max_iterations == data["max_iterations"]

def test_agent_input_invalid_query_too_short():
    with pytest.raises(ValidationError):
        schemas.AgentInput(query="bad", max_iterations=2)

def test_agent_input_invalid_iterations_too_low():
    with pytest.raises(ValidationError):
        schemas.AgentInput(query="Valid query here", max_iterations=0)

def test_agent_output_required_fields():
    data = {
        "success": True,
        "report": "Some markdown",
        "iterations": 1,
        "findings_count": 2
    }
    obj = schemas.AgentOutput(**data)
    assert obj.success is True
    assert obj.iterations == 1

def test_task_status_progress_range():
    with pytest.raises(ValidationError):
        schemas.TaskStatus(task_id="123", status="running", progress=1.5)

def test_tool_call_result_accepts_none_result():
    obj = schemas.ToolCallResult(tool_name="web_search", success=True, result=None)
    assert obj.result == ""
