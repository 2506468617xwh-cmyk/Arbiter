from __future__ import annotations

from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml

from RAbot.news.news_models import NewsItem
from RAbot.news.news_provider import BaseNewsProvider, clean_html, parse_published
from RAbot.settings import get_project_dir


class RSSHubNewsProvider(BaseNewsProvider):
    provider_name = "rsshub"

    def _load_routes(self) -> tuple[list[str], list[dict]]:
        path = Path(get_project_dir()) / "config" / "news_sources.yaml"
        if not path.exists():
            self.warnings.append("未找到 config/news_sources.yaml，RSSHub 源已跳过。")
            return [], []
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cfg = raw.get("rsshub", {}) or {}
        if not cfg.get("enabled", False):
            return [], []
        return cfg.get("base_urls", []) or ["https://rsshub.app"], cfg.get("routes", []) or []

    def fetch_latest(self, limit: int = 50, **kwargs) -> list[NewsItem]:
        try:
            import feedparser
        except Exception as exc:
            self.warnings.append(f"feedparser 未安装，RSSHub 源已跳过：{type(exc).__name__}: {exc}")
            return []

        base_urls, routes = self._load_routes()
        if not routes:
            return []

        items: list[NewsItem] = []
        per_route = max(3, limit // max(1, len(routes)))
        for route in routes:
            path = route.get("path", "")
            name = route.get("name", path)
            market = route.get("market", "GLOBAL")
            topics = route.get("topics", [])
            for base in base_urls:
                url = urljoin(base.rstrip("/") + "/", path.lstrip("/"))
                try:
                    response = requests.get(url, timeout=15, headers={"User-Agent": "RAbot/0.1 local research"})
                    if response.status_code >= 400:
                        self.warnings.append(f"RSSHub {name} 暂不可用：HTTP {response.status_code}。")
                        continue
                    text = response.text or ""
                    if "<rss" not in text[:500].lower() and "<feed" not in text[:500].lower():
                        self.warnings.append(f"RSSHub {name} 返回内容不是有效 RSS，已跳过。")
                        continue
                    feed = feedparser.parse(text)
                    for entry in feed.entries[:per_route]:
                        title = clean_html(entry.get("title", ""))
                        if not title:
                            continue
                        items.append(
                            NewsItem.create(
                                title=title,
                                summary=clean_html(entry.get("summary", "")),
                                provider=self.provider_name,
                                source=name,
                                url=entry.get("link"),
                                published_at=parse_published(entry),
                                markets=[market],
                                topics=topics,
                                language="zh-CN" if market == "CN" else "unknown",
                                raw=dict(entry),
                            )
                        )
                except Exception as exc:
                    self.warnings.append(f"RSSHub {name} 抓取失败：{type(exc).__name__}: {exc}")
        return items[:limit]
