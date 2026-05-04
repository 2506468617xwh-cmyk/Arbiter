from typing import Any, Optional

from pydantic import BaseModel, Field

from backend.schemas.macro import MacroIndicatorItem
from backend.schemas.market import MarketPerformanceItem, MarketSeriesPoint
from backend.schemas.news import NewsItem


class AssetResearchResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    latest_date: Optional[str] = None
    technical: dict[str, Any] = Field(default_factory=dict)
    market: Optional[MarketPerformanceItem] = None
    news: dict[str, Any] = Field(default_factory=dict)
    macro: dict[str, Any] = Field(default_factory=dict)
    series: list[MarketSeriesPoint] = Field(default_factory=list)
    related_news: list[NewsItem] = Field(default_factory=list)
    related_macro: list[MacroIndicatorItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class MultiAssetRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    start: Optional[str] = None
    end: Optional[str] = None


class MultiAssetResponse(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    normalized_series: list[MarketSeriesPoint] = Field(default_factory=list)
    performance: list[MarketPerformanceItem] = Field(default_factory=list)
    correlation: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
