"""API routes for the AI Institute (Five-layer Multi-Agent Debate System)."""
from __future__ import annotations

from pydantic import BaseModel
from fastapi import APIRouter

from backend.schemas.task import TaskResponse, TaskResultResponse
from backend.services.institute_service import create_institute_task
from backend.services import task_manager

router = APIRouter(tags=["institute"])


class InstituteAnalyzeRequest(BaseModel):
    symbol: str | None = None


@router.post("/institute/analyze", response_model=TaskResponse)
def start_institute_analysis(body: InstituteAnalyzeRequest) -> TaskResponse:
    """Start a five-layer AI Institute analysis. Returns a task_id for progress tracking."""
    return create_institute_task(body.symbol)


@router.get("/institute/result/{task_id}", response_model=TaskResultResponse)
def get_institute_result(task_id: str) -> TaskResultResponse:
    """Get the full five-layer analysis result by task_id."""
    return task_manager.get_task_result(task_id)
