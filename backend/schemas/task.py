from typing import Any, Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["pending", "running", "success", "failed", "cancelled"]


class TaskResponse(BaseModel):
    task_id: str
    task_type: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    current_step: str
    message: str
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse] = Field(default_factory=list)
    count: int = 0


class TaskResultResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int = Field(ge=0, le=100)
    current_step: str
    message: str
    result: dict[str, Any] | None = None
    error: str | None = None
