from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import pandas as pd


def normalize_datetime(value: Any) -> str | None:
    if value is None or value == "":
        return None
    try:
        dt = pd.to_datetime(value, errors="coerce", utc=False)
        if pd.isna(dt):
            return str(value)
        if isinstance(dt, pd.Timestamp):
            return dt.isoformat()
    except Exception:
        return str(value)
    return str(value)


def build_news_id(provider: str, title: str, url: str | None = None, published_at: str | None = None) -> str:
    base = "|".join([provider or "unknown", url or "", title or "", published_at or ""])
    return hashlib.sha256(base.encode("utf-8", errors="ignore")).hexdigest()[:32]


@dataclass
class NewsItem:
    id: str
    title: str
    summary: str | None = None
    content: str | None = None
    source: str = "unknown"
    provider: str = "unknown"
    url: str | None = None
    published_at: str | None = None
    symbols: list[str] = field(default_factory=list)
    markets: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    language: str = "unknown"
    importance_score: float | None = None
    quality_score: float | None = None
    sentiment_score: float | None = None
    risk_tags: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        *,
        title: str,
        provider: str,
        source: str | None = None,
        summary: str | None = None,
        content: str | None = None,
        url: str | None = None,
        published_at: Any = None,
        symbols: list[str] | None = None,
        markets: list[str] | None = None,
        topics: list[str] | None = None,
        language: str = "unknown",
        importance_score: float | None = None,
        quality_score: float | None = None,
        sentiment_score: float | None = None,
        risk_tags: list[str] | None = None,
        raw: dict[str, Any] | None = None,
    ) -> "NewsItem":
        normalized_time = normalize_datetime(published_at)
        item_id = build_news_id(provider=provider, title=title, url=url, published_at=normalized_time)
        return cls(
            id=item_id,
            title=str(title or "").strip(),
            summary=summary,
            content=content,
            source=source or provider,
            provider=provider,
            url=url,
            published_at=normalized_time,
            symbols=symbols or [],
            markets=markets or [],
            topics=topics or [],
            language=language,
            importance_score=importance_score,
            quality_score=quality_score,
            sentiment_score=sentiment_score,
            risk_tags=risk_tags or [],
            raw=raw or {},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "source": self.source,
            "provider": self.provider,
            "url": self.url,
            "published_at": self.published_at,
            "symbols": self.symbols,
            "markets": self.markets,
            "topics": self.topics,
            "language": self.language,
            "importance_score": self.importance_score,
            "quality_score": self.quality_score,
            "sentiment_score": self.sentiment_score,
            "risk_tags": self.risk_tags,
            "raw": self.raw,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
