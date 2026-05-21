from __future__ import annotations

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider


class EastmoneyNewsProvider(BaseNewsProvider):
    provider_name = "eastmoney"

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        try:
            import akshare as ak
        except Exception:
            return []

        if not hasattr(ak, "stock_info_global_em"):
            self.warnings.append("akshare 没有 stock_info_global_em，东方财富源已跳过。")
            return []

        try:
            df = ak.stock_info_global_em()
        except Exception as exc:
            self.warnings.append(f"东方财富新闻抓取失败：{type(exc).__name__}: {exc}")
            return []

        if df is None or df.empty:
            return []

        items: list[NewsItem] = []
        for row in df.head(limit).to_dict(orient="records"):
            title = str(row.get("标题") or row.get("title") or "").strip()
            if not title:
                continue
            summary = row.get("摘要") or row.get("summary") or ""
            published_at = row.get("发布时间") or row.get("publish_time") or row.get("datetime") or None
            url = row.get("链接") or row.get("url") or ""

            items.append(
                NewsItem.create(
                    title=title,
                    summary=summary,
                    provider=self.provider_name,
                    source="东方财富",
                    url=url,
                    published_at=published_at,
                    markets=["CN"],
                    topics=["market", "a_share"],
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
            if kw in item.title.lower() or (item.summary and kw in item.summary.lower())
        ]
        return matched[:limit]
