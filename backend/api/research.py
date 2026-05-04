from fastapi import APIRouter, Query

from backend.schemas.research import ResearchGenerateRequest, ResearchGenerateResponse
from backend.schemas.research_view import AssetResearchResponse, MultiAssetRequest, MultiAssetResponse
from backend.services.research_task_service import create_research_report_task
from backend.services.research_view_service import get_asset_research, get_multi_asset_research


router = APIRouter(tags=["research"])


@router.post("/research/generate", response_model=ResearchGenerateResponse)
def generate_research_report(request: ResearchGenerateRequest) -> ResearchGenerateResponse:
    return create_research_report_task(request)


@router.get("/research/asset/{symbol}", response_model=AssetResearchResponse)
def read_asset_research(
    symbol: str,
    start: str | None = Query(default=None),
    end: str | None = Query(default=None),
) -> AssetResearchResponse:
    return get_asset_research(symbol, start=start, end=end)


@router.post("/research/multi-asset", response_model=MultiAssetResponse)
def read_multi_asset_research(request: MultiAssetRequest) -> MultiAssetResponse:
    return get_multi_asset_research(request)
