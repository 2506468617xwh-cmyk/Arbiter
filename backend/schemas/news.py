from typing import Any, Optional

from pydantic import BaseModel, Field


class NewsItem(BaseModel):
    id: str | int | None = None
    title: str
    source: Optional[str] = None
    provider: Optional[str] = None
    published_at: Optional[str] = None
    url: Optional[str] = None
    quality_score: Optional[float] = None
    importance_score: Optional[float] = None
    sentiment_score: Optional[float] = None
    risk_tag: Optional[str] = None
    risk_tags: list[str] = Field(default_factory=list)
    markets: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    summary: Optional[str] = None


class NewsDetailResponse(NewsItem):
    source_id: Optional[str] = None
    query: Optional[str] = None
    related_assets: Optional[str] = None
    sentiment_label: Optional[str] = None
    event_type: Optional[str] = None
    source_score: Optional[float] = None
    source_tier: Optional[str] = None
    freshness_score: Optional[float] = None
    interpretation: Optional[str] = None
    content: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class NewsLatestResponse(BaseModel):
    items: list[NewsItem] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class NewsCollectRequest(BaseModel):
    limit_per_source: int = 50
    markets: list[str] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class NewsCollectResponse(BaseModel):
    items: list[NewsItem] = Field(default_factory=list)
    saved_count: int = 0
    provider_stats: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    last_update: str
