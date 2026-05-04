from fastapi import APIRouter, Query

from backend.schemas.macro import MacroAnalysisRequest, MacroAnalysisResponse, MacroOverviewResponse, MacroSeriesResponse, MacroSnapshotResponse
from backend.services.macro_service import analyze_macro_with_llm, get_macro_overview, get_macro_series, get_macro_snapshot


router = APIRouter(tags=["macro"])


@router.get("/macro/overview", response_model=MacroOverviewResponse)
def read_macro_overview() -> MacroOverviewResponse:
    return get_macro_overview()


@router.get("/macro/snapshot", response_model=MacroSnapshotResponse)
def read_macro_snapshot(
    region: str | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=200),
) -> MacroSnapshotResponse:
    return get_macro_snapshot(region=region, category=category, limit=limit)


@router.get("/macro/series", response_model=MacroSeriesResponse)
def read_macro_series(
    symbols: str = Query(default=""),
    limit_per_symbol: int = Query(default=240),
) -> MacroSeriesResponse:
    symbol_list = [item.strip() for item in symbols.split(",") if item.strip()]
    return get_macro_series(symbols=symbol_list, limit_per_symbol=limit_per_symbol)


@router.post("/macro/analyze", response_model=MacroAnalysisResponse)
def create_macro_analysis(request: MacroAnalysisRequest) -> MacroAnalysisResponse:
    return analyze_macro_with_llm(request)
