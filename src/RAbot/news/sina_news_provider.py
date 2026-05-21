from __future__ import annotations

import time
from datetime import datetime

import requests

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider

SINA_LIDS = {
    "财经要闻": "2509",
    "宏观": "2510",
    "A股": "2512",
    "港股": "2514",
    "科技": "2507",
}

SINA_API = "https://feed.mix.sina.com.cn/api/roll/get"


class SinaFinanceNewsProvider(BaseNewsProvider):
    provider_name = "sina_finance"

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        items: list[NewsItem] = []
        per_lid = max(5, limit // max(1, len(SINA_LIDS)))

        for category, lid in SINA_LIDS.items():
            try:
                batch = self._fetch_lid(lid, category, per_lid)
                items.extend(batch)
            except Exception as exc:
                self.warnings.append(f"新浪财经 {category} 抓取失败：{type(exc).__name__}: {exc}")

        return items

    def _fetch_lid(self, lid: str, category: str, limit: int) -> list[NewsItem]:
        params = {"pageid": "153", "lid": lid, "num": min(limit, 50), "page": "1"}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.sina.com.cn/",
        }
        resp = requests.get(SINA_API, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        entries = data.get("result", {}).get("data", []) or []

        items: list[NewsItem] = []
        for entry in entries:
            title = (entry.get("title") or "").strip()
            if not title:
                continue
            summary = entry.get("summary") or ""
            ctime = entry.get("ctime", "")
            published_at = None
            if ctime:
                try:
                    published_at = datetime.fromtimestamp(int(ctime)).isoformat()
                except (ValueError, OSError):
                    pass

            keywords = entry.get("keywords", "")
            topics_map = {
                "财经要闻": ["macro", "policy"],
                "宏观": ["macro", "policy"],
                "A股": ["a_share", "market"],
                "港股": ["hk_stock", "market"],
                "科技": ["tech", "ai"],
            }
            topics = topics_map.get(category, ["general"])

            url = entry.get("url") or ""
            items.append(
                NewsItem.create(
                    title=title,
                    summary=summary,
                    provider=self.provider_name,
                    source=f"新浪{category}",
                    url=url,
                    published_at=published_at,
                    markets=["CN"],
                    topics=topics,
                    language="zh-CN",
                    raw=dict(entry),
                )
            )
        return items

    def fetch_by_keyword(self, keyword: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        all_items = self.fetch_latest(limit=limit * 2)
        kw = keyword.lower()
        matched = [
            item for item in all_items
            if kw in item.title.lower() or (item.summary and kw in item.summary.lower())
        ]
        return matched[:limit]
