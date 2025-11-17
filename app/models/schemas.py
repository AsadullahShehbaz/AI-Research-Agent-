from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, List, Union
import hashlib

class AgentInput(BaseModel):
    """
    Input payload for an agent execution.

    Example:
        {
            "query": "What are recent advances in AI?",
            "max_iterations": 3
        }
    """
    query: str = Field(..., min_length=5, max_length=1000, description="Research query or task description")
    max_iterations: Optional[int] = Field(3, ge=1, le=10, description="Max iterations agent can perform")

class AgentOutput(BaseModel):
    """
    Output returned from an agent after processing.

    Example:
        {
            "success": true,
            "report": "Summary report markdown here...",
            "iterations": 3,
            "findings_count": 5
        }
    """
    success: bool
    report: str = Field(..., description="Generated markdown report or output text")
    iterations: int = Field(..., ge=0)
    findings_count: int = Field(..., ge=0)

class ResearchTaskRequest(BaseModel):
    """
    API request model to start a research task.

    Example:
        {
            "query": "Latest trends in renewable energy",
            "max_iterations": 5
        }
    """
    query: str = Field(..., min_length=5, max_length=1000)
    max_iterations: Optional[int] = Field(3, ge=1, le=10)

class TaskStatus(BaseModel):
    """
    Status response for an ongoing research task.

    Example:
        {
            "task_id": "abc123",
            "status": "running",
            "progress": 0.5
        }
    """
    task_id: str
    status: str = Field(..., description="Task status, e.g., running, completed, failed")
    progress: float = Field(0.0, ge=0.0, le=1.0, description="Completion fraction between 0 and 1")

class HealthResponse(BaseModel):
    """
    API health check response.

    Example:
        {
            "status": "healthy",
            "version": "1.0.0",
            "agent_status": "ready"
        }
    """
    status: str
    version: str
    agent_status: str

class ToolCallResult(BaseModel):
    """
    Result from calling an external tool (e.g. web search).

    Example:
        {
            "tool_name": "web_search",
            "success": true,
            "result": "Search results content"
        }
    """
    tool_name: str
    success: bool
    result: Union[str, dict, None]

    @field_validator("result", pre=True)
    def allow_empty_result(cls, v):
        # Allow empty strings or None
        if v is None:
            return ""
        return v
