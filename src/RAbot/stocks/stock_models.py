from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class StockQuote:
    symbol: str
    name: str | None = None
    market: str = "UNKNOWN"
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
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StockBar:
    symbol: str
    date: str
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    volume: float | None = None
    turnover: float | None = None
    source: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StockAnalysisResult:
    symbol: str
    name: str | None
    market: str
    currency: str | None
    quote: StockQuote | None
    bars: list[StockBar]
    indicators: dict[str, Any]
    trend_summary: str
    risk_summary: str
    research_summary: str
    warnings: list[str] = field(default_factory=list)
    source: str | None = None
    benchmark_symbol: str | None = None
    benchmark_name: str | None = None
    benchmark_bars: list[StockBar] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return data
