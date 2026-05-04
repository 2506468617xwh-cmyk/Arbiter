from __future__ import annotations

import os
from datetime import datetime, timedelta

import requests

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


def _to_finnhub_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".US", "")


class FinnhubNewsProvider(BaseNewsProvider):
    provider_name = "finnhub"

    def _key(self) -> str:
        return (os.getenv("FINNHUB_API_KEY") or os.getenv("FINNHUB_TOKEN") or "").strip()

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        key = self._key()
        if not key:
            self.warnings.append("Finnhub 未配置 FINNHUB_API_KEY，可选海外新闻源已跳过。")
            return []
        try:
            response = requests.get(
                "https://finnhub.io/api/v1/news",
                params={"category": "general", "token": key},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            self.warnings.append(f"Finnhub market news 抓取失败：{type(exc).__name__}: {exc}")
            return []
        return [self._from_record(row, ["US", "GLOBAL"]) for row in data[:limit] if row.get("headline")]

    def fetch_by_symbol(self, symbol: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        key = self._key()
        if not key:
            self.warnings.append("Finnhub 未配置 FINNHUB_API_KEY，可选海外新闻源已跳过。")
            return []
        end = datetime.now().date()
        start = end - timedelta(days=7)
        ticker = _to_finnhub_symbol(symbol)
        try:
            response = requests.get(
                "https://finnhub.io/api/v1/company-news",
                params={"symbol": ticker, "from": start.isoformat(), "to": end.isoformat(), "token": key},
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
        except Exception as exc:
            self.warnings.append(f"Finnhub company news {ticker} 抓取失败：{type(exc).__name__}: {exc}")
            return []
        return [self._from_record(row, ["US"], [symbol.upper()]) for row in data[:limit] if row.get("headline")]

    def _from_record(self, row: dict, markets: list[str], symbols: list[str] | None = None) -> NewsItem:
        published = None
        if row.get("datetime"):
            try:
                published = datetime.fromtimestamp(int(row["datetime"])).isoformat()
            except Exception:
                published = row.get("datetime")
        return NewsItem.create(
            title=row.get("headline", ""),
            summary=row.get("summary"),
            provider=self.provider_name,
            source=row.get("source") or "Finnhub",
            url=row.get("url"),
            published_at=published,
            symbols=symbols or [],
            markets=markets,
            topics=["market"],
            language="en-US",
            raw=row,
        )
