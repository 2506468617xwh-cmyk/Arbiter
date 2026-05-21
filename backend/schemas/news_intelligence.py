"""Schemas for the AI Market Intelligence (Narrative Engine)."""
from __future__ import annotations

from pydantic import BaseModel, Field


class MarketTheme(BaseModel):
    name: str = ""
    heat: int = 0  # 0-100
    sentiment: str = "中性"  # 利好 | 利空 | 中性
    summary: str = ""
    related_assets: list[str] = Field(default_factory=list)
    affected_sectors: list[str] = Field(default_factory=list)
    news_count: int = 0


class MarketNarrative(BaseModel):
    headline: str = ""
    body: str = ""
    key_themes: list[str] = Field(default_factory=list)
    risk_level: str = "中"  # 低 | 中 | 高 | 极高


class SentimentGauge(BaseModel):
    # 0-100 scale: 0 = extreme fear, 100 = extreme greed
    overall: int = 50
    ai_tech: int = 50
    semiconductors: int = 50
    macro_policy: int = 50
    geopolitics: int = 50
    risk_appetite: str = "中性"  # 风险偏好 | 中性 | 风险规避


class MarketEvent(BaseModel):
    title: str = ""
    impact: str = "中"  # 低 | 中 | 高 | 极高
    direction: str = "中性"  # 利好 | 利空 | 中性
    affected_assets: list[str] = Field(default_factory=list)
    ai_analysis: str = ""
    published_at: str = ""


class AIBriefing(BaseModel):
    title: str = ""
    summary: str = ""
    highlights: list[str] = Field(default_factory=list)
    watch_today: list[str] = Field(default_factory=list)
    key_risks: list[str] = Field(default_factory=list)


class NewsIntelligenceResponse(BaseModel):
    narrative: MarketNarrative = Field(default_factory=MarketNarrative)
    themes: list[MarketTheme] = Field(default_factory=list)
    sentiment: SentimentGauge = Field(default_factory=SentimentGauge)
    events: list[MarketEvent] = Field(default_factory=list)
    briefing: AIBriefing = Field(default_factory=AIBriefing)
    last_update: str = ""
    news_count: int = 0
    warnings: list[str] = Field(default_factory=list)
