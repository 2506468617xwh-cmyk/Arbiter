from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

import feedparser
import pandas as pd
import yaml
from bs4 import BeautifulSoup

from RAbot.news.news_engine import build_news_interpretation, enrich_news_dataframe
from RAbot.news.news_quality import deduplicate_news, enrich_news_quality
from RAbot.settings import get_project_dir


@dataclass
class NewsSourceConfig:
    id: str
    name: str
    query: str
    language: str
    region: str
    assets: list[str]
    max_items: int = 20


def get_news_config_path() -> Path:
    return get_project_dir() / "config" / "news_sources.yaml"


def load_news_sources() -> list[NewsSourceConfig]:
    path = get_news_config_path()

    if not path.exists():
        return []

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    sources = raw.get("sources", [])
    configs: list[NewsSourceConfig] = []

    for item in sources:
        configs.append(
            NewsSourceConfig(
                id=item["id"],
                name=item["name"],
                query=item["query"],
                language=item.get("language", "en-US"),
                region=item.get("region", "US"),
                assets=item.get("assets", []),
                max_items=int(item.get("max_items", 20)),
            )
        )

    return configs


def clean_html(text: str | None) -> str:
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text(" ", strip=True)


def parse_published(entry) -> str:
    if getattr(entry, "published_parsed", None):
        try:
            dt = datetime(*entry.published_parsed[:6])
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    published = entry.get("published", "")

    if published:
        try:
            dt = pd.to_datetime(published)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return ""

    return ""


class GoogleNewsRSSProvider:
    def build_url(self, source: NewsSourceConfig) -> str:
        query = quote_plus(source.query)
        language = source.language
        region = source.region

        # Google News RSS 的 ceid 通常使用 CN:zh-Hans / US:en 这类形式。
        # 这里做一个兼容，保证中英文源都能拉。
        if language.lower().startswith("zh"):
            ceid = f"{region}:zh-Hans"
        else:
            ceid = f"{region}:en"

        return f"https://news.google.com/rss/search?q={query}&hl={language}&gl={region}&ceid={ceid}"

    def fetch_source(self, source: NewsSourceConfig) -> pd.DataFrame:
        url = self.build_url(source)
        feed = feedparser.parse(url)

        records = []

        for entry in feed.entries[: source.max_items]:
            title = clean_html(entry.get("title", ""))
            summary = clean_html(entry.get("summary", ""))
            link = entry.get("link", "")
            published_at = parse_published(entry)

            source_name = source.name

            if hasattr(entry, "source"):
                try:
                    source_name = entry.source.get("title", source.name)
                except Exception:
                    source_name = source.name

            records.append(
                {
                    "source_id": source.id,
                    "source_name": source_name,
                    "query": source.query,
                    "title": title,
                    "summary": summary,
                    "link": link,
                    "published_at": published_at,
                }
            )

        df = pd.DataFrame(records)

        if df.empty:
            return df

        df = enrich_news_dataframe(df, default_assets=source.assets)
        df = enrich_news_quality(df)

        interpretations = []
        for _, row in df.iterrows():
            interpretations.append(
                build_news_interpretation(
                    title=row.get("title", ""),
                    summary=row.get("summary", ""),
                    related_assets=row.get("related_assets", ""),
                    sentiment_label=row.get("sentiment_label", "中性"),
                    importance_score=int(row.get("importance_score", 0) or 0),
                    event_type=row.get("event_type", "其他"),
                    quality_score=int(row.get("quality_score", 0) or 0),
                )
            )

        df["interpretation"] = interpretations

        return df


def fetch_all_news() -> pd.DataFrame:
    sources = load_news_sources()

    if not sources:
        return pd.DataFrame()

    provider = GoogleNewsRSSProvider()
    frames = []

    for source in sources:
        try:
            df = provider.fetch_source(source)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            frames.append(
                pd.DataFrame(
                    [
                        {
                            "source_id": source.id,
                            "source_name": source.name,
                            "query": source.query,
                            "title": f"{source.name} 更新失败",
                            "summary": str(e),
                            "link": "",
                            "published_at": "",
                            "related_assets": ",".join(source.assets),
                            "sentiment_label": "中性",
                            "importance_score": 0,
                            "event_type": "其他",
                            "source_score": 0,
                            "source_tier": "D",
                            "freshness_score": 0,
                            "quality_score": 0,
                            "normalized_title": "",
                            "title_hash": "",
                            "interpretation": "该新闻源更新失败，请稍后重试。",
                        }
                    ]
                )
            )

    if not frames:
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    result = enrich_news_quality(result)
    result = deduplicate_news(result)

    return result