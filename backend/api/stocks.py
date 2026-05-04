from fastapi import APIRouter, Query

from backend.schemas.stock import (
    StockAnalysisResponse,
    StockHistoryResponse,
    StockQuoteResponse,
    StockSearchResponse,
)
from backend.services.stock_service import get_stock_analysis, get_stock_history, get_stock_quote, search_stocks


router = APIRouter(tags=["stocks"])


@router.get("/stocks/quote", response_model=StockQuoteResponse)
def read_stock_quote(symbol: str = Query(...)) -> StockQuoteResponse:
    return get_stock_quote(symbol)


@router.get("/stocks/history", response_model=StockHistoryResponse)
def read_stock_history(
    symbol: str = Query(...),
    period: str = Query(default="day"),
    count: int = Query(default=250),
) -> StockHistoryResponse:
    return get_stock_history(symbol=symbol, period=period, count=count)


@router.get("/stocks/analyze", response_model=StockAnalysisResponse)
def read_stock_analysis(
    symbol: str = Query(...),
    use_llm: bool = Query(default=True),
    count: int = Query(default=250),
) -> StockAnalysisResponse:
    return get_stock_analysis(symbol=symbol, use_llm=use_llm, count=count)


@router.get("/stocks/search", response_model=StockSearchResponse)
def read_stock_search(keyword: str = Query(default="")) -> StockSearchResponse:
    return search_stocks(keyword)
