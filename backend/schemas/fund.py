from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from backend.schemas.llm import LLMResponse


class FundInfoResponse(BaseModel):
    symbol: str
    name: str | None = None
    market: str
    fund_type: str
    asset_class: str | None = None
    currency: str | None = None
    benchmark: str | None = None
    fund_company: str | None = None
    inception_date: str | None = None
    expense_ratio: float | None = None
    aum: float | None = None
    source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class FundQuoteResponse(BaseModel):
    symbol: str
    name: str | None = None
    market: str
    fund_type: str
    currency: str | None = None
    last_price: float | None = None
    nav: float | None = None
    prev_close: float | None = None
    premium_discount: float | None = None
    volume: float | None = None
    turnover: float | None = None
    quote_time: str | None = None
    source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class FundBarResponse(BaseModel):
    symbol: str
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    nav: float | None = None
    volume: float | None = None
    turnover: float | None = None
    source: str | None = None


class FundHistoryResponse(BaseModel):
    symbol: str
    market: str
    fund_type: str
    period: str
    count: int
    items: list[FundBarResponse] = Field(default_factory=list)
    source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class FundAnalysisResponse(BaseModel):
    symbol: str
    name: str | None = None
    market: str
    fund_type: str
    currency: str | None = None
    info: FundInfoResponse | None = None
    quote: FundQuoteResponse | None = None
    bars: list[FundBarResponse] = Field(default_factory=list)
    indicators: dict[str, Any] = Field(default_factory=dict)
    allocation_summary: str
    performance_summary: str
    risk_summary: str
    liquidity_summary: str
    dca_summary: str
    research_summary: str
    warnings: list[str] = Field(default_factory=list)
    source: str | None = None
    benchmark_symbol: str | None = None
    benchmark_name: str | None = None
    benchmark_bars: list[FundBarResponse] = Field(default_factory=list)


class FundSearchResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FundChatRequest(BaseModel):
    symbol: str
    question: str
    use_llm: bool = True


class FundChatResponse(LLMResponse):
    pass
