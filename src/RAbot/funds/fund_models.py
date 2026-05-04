from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class FundInfo:
    symbol: str
    name: str | None = None
    market: str = "UNKNOWN"
    fund_type: str = "UNKNOWN"
    asset_class: str | None = None
    currency: str | None = None
    benchmark: str | None = None
    fund_company: str | None = None
    inception_date: str | None = None
    expense_ratio: float | None = None
    aum: float | None = None
    source: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FundQuote:
    symbol: str
    name: str | None = None
    market: str = "UNKNOWN"
    fund_type: str = "UNKNOWN"
    currency: str | None = None
    last_price: float | None = None
    nav: float | None = None
    prev_close: float | None = None
    premium_discount: float | None = None
    volume: float | None = None
    turnover: float | None = None
    quote_time: str | None = None
    source: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FundBar:
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

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FundAnalysisResult:
    symbol: str
    name: str | None
    market: str
    fund_type: str
    currency: str | None
    info: FundInfo | None
    quote: FundQuote | None
    bars: list[FundBar]
    indicators: dict[str, Any]
    allocation_summary: str
    performance_summary: str
    risk_summary: str
    liquidity_summary: str
    dca_summary: str
    research_summary: str
    warnings: list[str] = field(default_factory=list)
    source: str | None = None
    benchmark_symbol: str | None = None
    benchmark_name: str | None = None
    benchmark_bars: list[FundBar] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
