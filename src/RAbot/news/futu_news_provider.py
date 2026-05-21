from __future__ import annotations

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


class FutuNewsProvider(BaseNewsProvider):
    provider_name = "futu"

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        try:
            import akshare as ak
        except Exception:
            return []

        if not hasattr(ak, "stock_info_global_futu"):
            self.warnings.append("akshare 没有 stock_info_global_futu，富途源已跳过。")
            return []

        try:
            df = ak.stock_info_global_futu()
        except Exception as exc:
            self.warnings.append(f"富途新闻抓取失败：{type(exc).__name__}: {exc}")
            return []

        if df is None or df.empty:
            return []

        items: list[NewsItem] = []
        for row in df.head(limit).to_dict(orient="records"):
            title = str(row.get("标题") or row.get("title") or "").strip()
            if not title:
                continue
            content = row.get("内容") or row.get("content") or row.get("摘要") or row.get("summary") or ""
            published_at = row.get("发布时间") or row.get("publish_time") or row.get("datetime") or None
            url = row.get("链接") or row.get("url") or ""

            items.append(
                NewsItem.create(
                    title=title,
                    summary=None,
                    content=content,
                    provider=self.provider_name,
                    source="富途牛牛",
                    url=url,
                    published_at=published_at,
                    markets=["GLOBAL"],
                    topics=["global", "market"],
                    language="zh-CN",
                    raw=row,
                )
            )
        return items

    def fetch_by_keyword(self, keyword: str, limit: int = 50, **kwargs) -> list[NewsItem]:
        all_items = self.fetch_latest(limit=limit * 3)
        kw = keyword.lower()
        matched = [
            item for item in all_items
            if kw in item.title.lower() or (item.content and kw in item.content.lower())
        ]
        return matched[:limit]
