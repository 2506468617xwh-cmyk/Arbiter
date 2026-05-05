from __future__ import annotations

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


class AKShareNewsProvider(BaseNewsProvider):
    provider_name = "akshare_jin10"

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        try:
            import akshare as ak
        except Exception:
            return []

        if not hasattr(ak, "js_news"):
            return []

        try:
            df = ak.js_news(timestamp="")
        except TypeError:
            try:
                df = ak.js_news()
            except Exception:
                return []
        except Exception:
            return []

        if df is None or df.empty:
            return []

        items: list[NewsItem] = []
        for row in df.head(limit).to_dict(orient="records"):
            title = str(row.get("title") or row.get("内容") or row.get("content") or "").strip()
            if not title:
                continue
            items.append(
                NewsItem.create(
                    title=title,
                    summary=row.get("content") or row.get("内容"),
                    provider=self.provider_name,
                    source="金十数据",
                    published_at=row.get("datetime") or row.get("时间") or row.get("time"),
                    markets=["GLOBAL"],
                    topics=["macro", "commodity", "forex"],
                    language="zh-CN",
                    raw=row,
                )
            )
        return items
