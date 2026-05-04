from fastapi import APIRouter, Query

from backend.schemas.fund import (
    FundAnalysisResponse,
    FundChatRequest,
    FundChatResponse,
    FundHistoryResponse,
    FundInfoResponse,
    FundQuoteResponse,
    FundSearchResponse,
)
from backend.services.fund_service import (
    answer_fund_question,
    get_fund_analysis,
    get_fund_history,
    get_fund_info,
    get_fund_quote,
    search_funds,
)


router = APIRouter(tags=["funds"])


@router.get("/funds/info", response_model=FundInfoResponse)
def read_fund_info(symbol: str = Query(...)) -> FundInfoResponse:
    return get_fund_info(symbol)


@router.get("/funds/quote", response_model=FundQuoteResponse)
def read_fund_quote(symbol: str = Query(...)) -> FundQuoteResponse:
    return get_fund_quote(symbol)


@router.get("/funds/history", response_model=FundHistoryResponse)
def read_fund_history(
    symbol: str = Query(...),
    period: str = Query(default="day"),
    count: int = Query(default=500),
) -> FundHistoryResponse:
    return get_fund_history(symbol=symbol, period=period, count=count)


@router.get("/funds/analyze", response_model=FundAnalysisResponse)
def read_fund_analysis(
    symbol: str = Query(...),
    use_llm: bool = Query(default=True),
    count: int = Query(default=500),
) -> FundAnalysisResponse:
    return get_fund_analysis(symbol=symbol, use_llm=use_llm, count=count)


@router.get("/funds/search", response_model=FundSearchResponse)
def read_fund_search(keyword: str = Query(default="")) -> FundSearchResponse:
    return search_funds(keyword)


@router.post("/funds/chat", response_model=FundChatResponse)
def create_fund_chat(request: FundChatRequest) -> FundChatResponse:
    return answer_fund_question(symbol=request.symbol, question=request.question, use_llm=request.use_llm)
