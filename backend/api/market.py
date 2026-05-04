from fastapi import APIRouter

from backend.schemas.market import (
    MarketDashboardResponse,
    MarketIndexResponse,
    MarketPerformanceResponse,
    MarketTimeseriesResponse,
)
from backend.services.market_service import (
    get_market_dashboard,
    get_market_indexes,
    get_market_performance,
    get_market_timeseries,
)


router = APIRouter(tags=["market"])


@router.get("/market/indexes", response_model=MarketIndexResponse)
def read_market_indexes() -> MarketIndexResponse:
    return get_market_indexes()


@router.get("/market/dashboard", response_model=MarketDashboardResponse)
def read_market_dashboard() -> MarketDashboardResponse:
    return get_market_dashboard()


@router.get("/market/performance", response_model=MarketPerformanceResponse)
def read_market_performance() -> MarketPerformanceResponse:
    return get_market_performance()


@router.get("/market/timeseries", response_model=MarketTimeseriesResponse)
def read_market_timeseries(
    symbols: str,
    start: str | None = None,
    end: str | None = None,
    normalize: bool = False,
) -> MarketTimeseriesResponse:
    symbol_list = [item.strip() for item in symbols.split(",") if item.strip()]
    return get_market_timeseries(symbol_list, start=start, end=end, normalize=normalize)
