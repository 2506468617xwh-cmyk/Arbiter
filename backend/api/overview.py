from fastapi import APIRouter

from backend.schemas.overview import OverviewResponse
from backend.services.overview_service import build_overview


router = APIRouter(tags=["overview"])


@router.get("/overview", response_model=OverviewResponse)
def get_overview() -> OverviewResponse:
    return build_overview()
