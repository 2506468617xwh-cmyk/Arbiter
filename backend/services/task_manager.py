from __future__ import annotations

import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any, Callable

from fastapi import HTTPException

from backend.schemas.task import TaskListResponse, TaskResponse, TaskResultResponse


_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="RAbotResearchTask")
_LOCK = threading.RLock()
_TASKS: dict[str, dict[str, Any]] = {}


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _copy_task(task: dict[str, Any]) -> dict[str, Any]:
    copied = dict(task)
    copied["result"] = dict(task["result"]) if isinstance(task.get("result"), dict) else task.get("result")
    return copied


def _to_response(task: dict[str, Any]) -> TaskResponse:
    return TaskResponse(**_copy_task(task))


def create_task(task_type: str, message: str = "任务已创建") -> TaskResponse:
    task_id = uuid.uuid4().hex
    task = {
        "task_id": task_id,
        "task_type": task_type,
        "status": "pending",
        "progress": 0,
        "current_step": "等待后台执行",
        "message": message,
        "created_at": _now_iso(),
        "started_at": None,
        "finished_at": None,
        "result": None,
        "error": None,
    }
    with _LOCK:
        _TASKS[task_id] = task
    return _to_response(task)


def get_task(task_id: str) -> TaskResponse:
    with _LOCK:
        task = _TASKS.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found.")
        return _to_response(task)


def list_tasks(limit: int = 50) -> TaskListResponse:
    with _LOCK:
        tasks = sorted(_TASKS.values(), key=lambda item: item["created_at"], reverse=True)[:limit]
        responses = [_to_response(task) for task in tasks]
    return TaskListResponse(tasks=responses, count=len(responses))


def update_task(
    task_id: str,
    *,
    status: str | None = None,
    progress: int | None = None,
    current_step: str | None = None,
    message: str | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
    mark_started: bool = False,
    mark_finished: bool = False,
) -> TaskResponse:
    with _LOCK:
        task = _TASKS.get(task_id)
        if task is None:
            raise HTTPException(status_code=404, detail="Task not found.")

        if status is not None:
            task["status"] = status
        if progress is not None:
            task["progress"] = max(0, min(100, int(progress)))
        if current_step is not None:
            task["current_step"] = current_step
        if message is not None:
            task["message"] = message
        if result is not None:
            task["result"] = result
        if error is not None:
            task["error"] = error
        if mark_started and task.get("started_at") is None:
            task["started_at"] = _now_iso()
        if mark_finished:
            task["finished_at"] = _now_iso()

        return _to_response(task)


def _run_wrapper(task_id: str, func: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> None:
    try:
        update_task(
            task_id,
            status="running",
            progress=1,
            current_step="正在初始化研究任务",
            message="后台任务已启动",
            mark_started=True,
        )
        result = func(task_id, *args, **kwargs)
        update_task(
            task_id,
            status="success",
            progress=100,
            current_step="报告生成完成",
            message="研究报告已生成",
            result=result,
            mark_finished=True,
        )
    except Exception as exc:
        error_text = f"{type(exc).__name__}: {exc}"
        detail = traceback.format_exc()
        update_task(
            task_id,
            status="failed",
            progress=100,
            current_step="报告生成失败",
            message="后台任务执行失败",
            error=f"{error_text}\n{detail}",
            mark_finished=True,
        )


def run_task_in_background(
    task_id: str,
    func: Callable[..., dict[str, Any]],
    *args: Any,
    **kwargs: Any,
) -> None:
    _EXECUTOR.submit(_run_wrapper, task_id, func, *args, **kwargs)


def get_task_result(task_id: str) -> TaskResultResponse:
    task = get_task(task_id)
    return TaskResultResponse(
        task_id=task.task_id,
        status=task.status,
        progress=task.progress,
        current_step=task.current_step,
        message=task.message,
        result=task.result if task.status == "success" else None,
        error=task.error if task.status == "failed" else None,
    )
