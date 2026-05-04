from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StockQuoteResponse(BaseModel):
    symbol: str
    name: str | None = None
    market: str
    currency: str | None = None
    last_price: float | None = None
    prev_close: float | None = None
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None
    turnover: float | None = None
    trade_status: str | None = None
    quote_time: str | None = None
    source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class StockBarResponse(BaseModel):
    symbol: str
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    turnover: float | None = None
    source: str | None = None


class StockHistoryResponse(BaseModel):
    symbol: str
    market: str
    period: str
    count: int
    items: list[StockBarResponse] = Field(default_factory=list)
    source: str | None = None
    warnings: list[str] = Field(default_factory=list)


class StockAnalysisResponse(BaseModel):
    symbol: str
    name: str | None = None
    market: str
    currency: str | None = None
    quote: StockQuoteResponse | None = None
    bars: list[StockBarResponse] = Field(default_factory=list)
    benchmark_symbol: str | None = None
    benchmark_name: str | None = None
    benchmark_bars: list[StockBarResponse] = Field(default_factory=list)
    indicators: dict[str, Any] = Field(default_factory=dict)
    trend_summary: str
    risk_summary: str
    research_summary: str
    warnings: list[str] = Field(default_factory=list)
    source: str | None = None


class StockSearchResponse(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
