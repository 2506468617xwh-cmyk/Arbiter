from typing import Optional

from pydantic import BaseModel, Field


class MarketIndexItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    date: Optional[str] = None
    close: Optional[float] = None
    pct_change: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    trend_signal: Optional[str] = None
    risk_level: Optional[str] = None
    summary: str


class MarketIndexResponse(BaseModel):
    items: list[MarketIndexItem] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MarketPerformanceItem(BaseModel):
    symbol: str
    name: Optional[str] = None
    latest_date: Optional[str] = None
    close: Optional[float] = None
    return_1w: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_ytd: Optional[float] = None
    return_1y: Optional[float] = None
    volatility_20d: Optional[float] = None
    drawdown: Optional[float] = None
    trend_signal: Optional[str] = None
    risk_level: Optional[str] = None


class MarketPerformanceResponse(BaseModel):
    items: list[MarketPerformanceItem] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MarketDashboardResponse(BaseModel):
    market_status: str
    asset_count: int = 0
    latest_date: Optional[str] = None
    strong_assets: list[MarketPerformanceItem] = Field(default_factory=list)
    weak_assets: list[MarketPerformanceItem] = Field(default_factory=list)
    high_volatility_assets: list[MarketPerformanceItem] = Field(default_factory=list)
    high_drawdown_assets: list[MarketPerformanceItem] = Field(default_factory=list)
    all_items: list[MarketPerformanceItem] = Field(default_factory=list)
    summary: str
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MarketSeriesPoint(BaseModel):
    symbol: str
    name: Optional[str] = None
    date: str
    close: Optional[float] = None
    pct_change: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    drawdown: Optional[float] = None
    volume: Optional[float] = None
    normalized: Optional[float] = None


class MarketTimeseriesResponse(BaseModel):
    items: list[MarketSeriesPoint] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)
