from fastapi import APIRouter

from backend.schemas.task import TaskListResponse, TaskResponse, TaskResultResponse
from backend.services.task_manager import get_task, get_task_result, list_tasks


router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=TaskListResponse)
def read_tasks() -> TaskListResponse:
    return list_tasks(limit=50)


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def read_task(task_id: str) -> TaskResponse:
    return get_task(task_id)


@router.get("/tasks/{task_id}/result", response_model=TaskResultResponse)
def read_task_result(task_id: str) -> TaskResultResponse:
    return get_task_result(task_id)
