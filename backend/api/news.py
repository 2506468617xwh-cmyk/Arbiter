from fastapi import APIRouter, Query

from backend.schemas.news import NewsCollectRequest, NewsCollectResponse, NewsDetailResponse, NewsLatestResponse
from backend.services.news_service import collect_news, get_latest_news, get_news_by_symbol, get_news_detail, search_news


router = APIRouter(tags=["news"])


@router.get("/news/latest", response_model=NewsLatestResponse)
def read_latest_news(
    limit: int = Query(default=50, ge=1, le=200),
    market: str | None = None,
    topic: str | None = None,
    symbol: str | None = None,
) -> NewsLatestResponse:
    return get_latest_news(limit=limit, market=market, topic=topic, symbol=symbol)


@router.get("/news/search", response_model=NewsLatestResponse)
def read_news_search(keyword: str, limit: int = Query(default=100, ge=1, le=200)) -> NewsLatestResponse:
    return search_news(keyword=keyword, limit=limit)


@router.get("/news/by-symbol", response_model=NewsLatestResponse)
def read_news_by_symbol(symbol: str, limit: int = Query(default=100, ge=1, le=200)) -> NewsLatestResponse:
    return get_news_by_symbol(symbol=symbol, limit=limit)


@router.post("/news/collect", response_model=NewsCollectResponse)
def collect_news_endpoint(request: NewsCollectRequest) -> NewsCollectResponse:
    return collect_news(request)


@router.get("/news/{news_id}", response_model=NewsDetailResponse)
def read_news_detail(news_id: str) -> NewsDetailResponse:
    return get_news_detail(news_id)
