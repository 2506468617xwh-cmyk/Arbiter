from __future__ import annotations

import os

import requests

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


def _to_av_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".US", "")


class AlphaVantageNewsProvider(BaseNewsProvider):
    provider_name = "alphavantage_news_sentiment"

    def _fetch(self, params: dict) -> list[NewsItem]:
        key = (
            os.getenv("ALPHAVANTAGE_API_KEY")
            or os.getenv("ALPHA_VANTAGE_API_KEY")
            or os.getenv("ALPHAVANTAGE_KEY")
            or ""
        ).strip()
        if not key:
            self.warnings.append("Alpha Vantage 未配置 ALPHAVANTAGE_API_KEY，可选情绪新闻源已跳过。")
            return []
        try:
            response = requests.get(
                "https://www.alphavantage.co/query",
                params={"function": "NEWS_SENTIMENT", "apikey": key, **params},
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            self.warnings.append(f"Alpha Vantage News Sentiment 抓取失败：{type(exc).__name__}: {exc}")
            return []
        if "Note" in data or "Information" in data:
            self.warnings.append(f"Alpha Vantage 返回限制提示：{data.get('Note') or data.get('Information')}")
            return []
        items = []
        for row in data.get("feed", []):
            title = row.get("title") or ""
            if not title:
                continue
            sentiment = None
            try:
                sentiment = float(row.get("overall_sentiment_score"))
            except Exception:
                sentiment = None
            symbols = []
            for ticker in row.get("ticker_sentiment", []) or []:
                if ticker.get("ticker"):
                    symbols.append(str(ticker["ticker"]).upper() + ".US")
            topics = []
            for topic in row.get("topics", []) or []:
                if isinstance(topic, dict):
                    label = topic.get("topic")
                    if label:
                        topics.append(str(label))
                elif topic:
                    topics.append(str(topic))
            items.append(
                NewsItem.create(
                    title=title,
                    summary=row.get("summary"),
                    provider=self.provider_name,
                    source=row.get("source") or "Alpha Vantage",
                    url=row.get("url"),
                    published_at=row.get("time_published"),
                    symbols=symbols,
                    markets=["US"],
                    topics=topics or ["market"],
                    language="en-US",
                    sentiment_score=sentiment,
                    raw=row,
                )
            )
        return items

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        return self._fetch({"limit": min(limit, 100)})[:limit]

    def fetch_by_symbol(self, symbol: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        return self._fetch({"tickers": _to_av_symbol(symbol), "limit": min(limit, 100)})[:limit]

    def fetch_by_keyword(self, keyword: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        return self._fetch({"topics": keyword, "limit": min(limit, 100)})[:limit]
