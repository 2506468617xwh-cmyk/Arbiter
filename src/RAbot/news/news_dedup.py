from __future__ import annotations

import hashlib
import re
import string
from difflib import SequenceMatcher

from RAbot.news.news_models import NewsItem


NOISE_PREFIXES = [
    "快讯",
    "财联社",
    "东方财富",
    "金十数据",
    "证券时报",
    "每经",
    "央视新闻",
    "breaking",
    "update",
]

STOP_WORDS = {
    "the", "a", "an", "to", "of", "in", "on", "for", "and", "as", "with",
    "after", "before", "amid", "over", "from", "by", "at",
}


def normalize_title(title: str | None) -> str:
    """统一的新闻标题归一化：去前缀、去来源尾巴、去标点、去英文停用词。"""
    text = (title or "").lower().strip()
    for prefix in NOISE_PREFIXES:
        text = re.sub(rf"^\s*{re.escape(prefix.lower())}\s*[:：丨|,\-]*\s*", "", text)
    text = re.sub(r"\s[-|—]\s.*$", "", text)
    punctuation = string.punctuation + "，。！？；：“”‘’、（）【】《》…—"
    text = text.translate(str.maketrans("", "", punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    tokens = [x for x in text.split(" ") if x and x not in STOP_WORDS]
    return " ".join(tokens)


def title_hash(title: str | None) -> str:
    return hashlib.md5(normalize_title(title).encode("utf-8")).hexdigest()


def news_fingerprint(item: NewsItem) -> str:
    if item.url:
        return hashlib.sha256(item.url.strip().lower().encode("utf-8")).hexdigest()
    normalized = normalize_title(item.title)
    date = (item.published_at or "")[:10]
    base = "|".join([item.provider, item.source, date, normalized])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _quality_rank(item: NewsItem) -> tuple[float, float, int]:
    return (
        float(item.quality_score or 0),
        float(item.importance_score or 0),
        1 if item.url else 0,
    )


def deduplicate_news(items: list[NewsItem]) -> list[NewsItem]:
    ordered = sorted(items, key=_quality_rank, reverse=True)
    kept: list[NewsItem] = []
    seen_urls: set[str] = set()
    seen_titles: set[str] = set()
    seen_fingerprints: set[str] = set()

    for item in ordered:
        normalized = normalize_title(item.title)
        url_key = (item.url or "").strip().lower()
        fingerprint = news_fingerprint(item)
        if url_key and url_key in seen_urls:
            continue
        if normalized and normalized in seen_titles:
            continue
        if fingerprint in seen_fingerprints:
            continue
        duplicate = False
        for old in kept:
            old_title = normalize_title(old.title)
            if normalized and old_title and SequenceMatcher(None, normalized, old_title).ratio() >= 0.90:
                duplicate = True
                break
        if duplicate:
            continue
        kept.append(item)
        if url_key:
            seen_urls.add(url_key)
        if normalized:
            seen_titles.add(normalized)
        seen_fingerprints.add(fingerprint)

    return kept
