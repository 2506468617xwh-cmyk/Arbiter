from __future__ import annotations

import os

import requests

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


class NewsAPIProvider(BaseNewsProvider):
    provider_name = "newsapi"
    default_keywords = ["Federal Reserve", "US inflation", "China economy", "AI chips", "semiconductor", "Hong Kong stocks"]

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        items: list[NewsItem] = []
        per_keyword = max(3, limit // len(self.default_keywords))
        for keyword in self.default_keywords:
            items.extend(self.fetch_by_keyword(keyword, limit=per_keyword))
        return items[:limit]

    def fetch_by_keyword(self, keyword: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        key = (os.getenv("NEWSAPI_KEY") or os.getenv("NEWS_API_KEY") or os.getenv("NEWSAPI_API_KEY") or "").strip()
        if not key:
            self.warnings.append("NewsAPI 未配置 NEWSAPI_KEY，可选海外主题新闻源已跳过。")
            return []
        try:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": keyword, "language": "en", "sortBy": "publishedAt", "pageSize": min(limit, 100), "apiKey": key},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            self.warnings.append(f"NewsAPI 关键词 {keyword} 抓取失败：{type(exc).__name__}: {exc}")
            return []

        items = []
        for row in data.get("articles", [])[:limit]:
            title = row.get("title") or ""
            if not title:
                continue
            source = row.get("source") or {}
            items.append(
                NewsItem.create(
                    title=title,
                    summary=row.get("description"),
                    content=row.get("content"),
                    provider=self.provider_name,
                    source=source.get("name") or "NewsAPI",
                    url=row.get("url"),
                    published_at=row.get("publishedAt"),
                    markets=["GLOBAL"],
                    topics=[keyword],
                    language="en-US",
                    raw=row,
                )
            )
        return items
