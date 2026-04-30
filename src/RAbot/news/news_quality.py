from __future__ import annotations

import hashlib
import re
import string
from datetime import datetime
from pathlib import Path

import pandas as pd
import yaml

from RAbot.settings import get_project_dir


EVENT_KEYWORDS = {
    "货币政策": [
        "fed", "federal reserve", "fomc", "powell", "rate decision", "interest rates",
        "央行", "美联储", "议息", "降息", "加息", "货币政策", "利率"
    ],
    "通胀数据": [
        "cpi", "ppi", "inflation", "core inflation", "pce",
        "通胀", "物价", "居民消费价格", "生产者价格", "核心通胀"
    ],
    "就业数据": [
        "jobs report", "payrolls", "unemployment", "jobless claims", "labor market",
        "非农", "失业率", "就业", "初请失业金"
    ],
    "美债利率": [
        "treasury yields", "bond yields", "10-year", "2-year", "yield curve",
        "美债", "收益率", "期限利差", "国债利率"
    ],
    "AI科技": [
        "ai", "artificial intelligence", "nvidia", "microsoft", "apple", "semiconductor",
        "chip", "big tech", "人工智能", "算力", "英伟达", "微软", "苹果", "半导体", "芯片", "科技"
    ],
    "公司财报": [
        "earnings", "revenue", "profit", "guidance", "quarterly results",
        "财报", "营收", "利润", "业绩", "指引"
    ],
    "中国政策": [
        "china stimulus", "policy support", "beijing policy", "fiscal policy",
        "稳增长", "政策", "刺激", "财政政策", "专项债", "降准", "逆回购", "一揽子政策"
    ],
    "中国宏观": [
        "china economy", "pmi", "social financing", "credit growth", "m2",
        "中国经济", "宏观", "PMI", "社融", "M2", "CPI", "PPI", "工业增加值", "固定资产投资"
    ],
    "A股市场": [
        "a-shares", "csi 300", "shanghai composite", "chinext",
        "A股", "沪深300", "上证指数", "创业板", "科创50", "北向资金", "成交额"
    ],
    "中国地产": [
        "property", "real estate", "developer", "home sales",
        "地产", "房地产", "房企", "楼市", "商品房", "土地", "保交楼"
    ],
    "人民币汇率": [
        "yuan", "renminbi", "offshore yuan", "currency fixing",
        "人民币", "离岸人民币", "中间价", "汇率", "贬值", "升值"
    ],
    "港股市场": [
        "hang seng", "hong kong stocks", "h shares",
        "港股", "恒生指数", "恒生科技", "南向资金"
    ],
    "大宗商品": [
        "oil", "crude", "opec", "gold", "commodity", "copper",
        "原油", "石油", "黄金", "大宗商品", "铜", "OPEC"
    ],
    "地缘风险": [
        "geopolitical", "war", "sanctions", "tariff", "conflict",
        "地缘", "冲突", "战争", "制裁", "关税", "贸易摩擦"
    ],
    "市场情绪": [
        "risk appetite", "selloff", "rally", "volatility", "vix",
        "风险偏好", "抛售", "反弹", "波动", "避险", "恐慌"
    ],
}


def get_news_quality_config_path() -> Path:
    return get_project_dir() / "config" / "news_quality.yaml"


def load_news_quality_config() -> dict:
    path = get_news_quality_config_path()

    if not path.exists():
        return {
            "source_quality": {},
            "default_source_score": 55,
            "event_type_weights": {},
        }

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def normalize_title(title: str | None) -> str:
    text = (title or "").lower().strip()

    # 去掉常见媒体尾巴，比如 " - Reuters"
    text = re.sub(r"\s[-|—]\s.*$", "", text)

    # 去标点
    translator = str.maketrans("", "", string.punctuation + "，。！？；：“”‘’、（）【】《》")
    text = text.translate(translator)

    # 合并空白
    text = re.sub(r"\s+", " ", text).strip()

    # 去掉非常常见的低信息词
    stop_words = {
        "the", "a", "an", "to", "of", "in", "on", "for", "and", "as", "with",
        "after", "before", "amid", "over", "from", "by", "at"
    }

    tokens = [x for x in text.split(" ") if x and x not in stop_words]
    return " ".join(tokens)


def title_hash(title: str | None) -> str:
    normalized = normalize_title(title)
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


def infer_source_score(source_name: str | None, config: dict | None = None) -> tuple[int, str]:
    cfg = config or load_news_quality_config()
    source_quality = cfg.get("source_quality", {}) or {}
    default_score = int(cfg.get("default_source_score", 55))

    source = (source_name or "").lower().strip()

    best_score = default_score
    matched_name = "未分级来源"

    for key, score in source_quality.items():
        key_lower = str(key).lower().strip()
        if key_lower and key_lower in source:
            score_int = int(score)
            if score_int > best_score:
                best_score = score_int
                matched_name = str(key)

    if best_score >= 90:
        tier = "S"
    elif best_score >= 80:
        tier = "A"
    elif best_score >= 70:
        tier = "B"
    elif best_score >= 60:
        tier = "C"
    else:
        tier = "D"

    return best_score, tier


def classify_event_type(title: str | None, summary: str | None = None) -> str:
    text = f"{title or ''} {summary or ''}".lower()

    scores: dict[str, int] = {}

    for event_type, keywords in EVENT_KEYWORDS.items():
        count = 0
        for keyword in keywords:
            if keyword.lower() in text:
                count += 1

        if count:
            scores[event_type] = count

    if not scores:
        return "其他"

    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[0][0]


def calculate_freshness_score(published_at: str | None) -> int:
    if not published_at:
        return 35

    try:
        published = pd.to_datetime(published_at, errors="coerce")
        if pd.isna(published):
            return 35

        now = pd.Timestamp.now(tz=published.tz) if published.tzinfo else pd.Timestamp.now()
        hours = max(0, (now - published).total_seconds() / 3600)

        if hours <= 6:
            return 100
        if hours <= 24:
            return 90
        if hours <= 72:
            return 75
        if hours <= 168:
            return 55
        if hours <= 336:
            return 35
        return 20

    except Exception:
        return 35


def calculate_quality_score(
    source_score: int,
    freshness_score: int,
    importance_score: int,
    event_type: str,
    related_assets: str | list[str] | None,
    config: dict | None = None,
) -> int:
    cfg = config or load_news_quality_config()
    event_weights = cfg.get("event_type_weights", {}) or {}

    event_bonus = int(event_weights.get(event_type, 0))

    if isinstance(related_assets, list):
        asset_count = len(related_assets)
    elif isinstance(related_assets, str):
        asset_count = len([x for x in related_assets.split(",") if x.strip()])
    else:
        asset_count = 0

    asset_bonus = min(8, asset_count * 2)

    score = (
        source_score * 0.30
        + freshness_score * 0.25
        + int(importance_score) * 0.30
        + event_bonus
        + asset_bonus
    )

    return max(0, min(100, int(round(score))))


def enrich_news_quality(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    config = load_news_quality_config()
    data = df.copy()

    title_hashes = []
    normalized_titles = []
    event_types = []
    source_scores = []
    source_tiers = []
    freshness_scores = []
    quality_scores = []

    for _, row in data.iterrows():
        title = row.get("title", "")
        summary = row.get("summary", "")
        source_name = row.get("source_name", "")
        published_at = row.get("published_at", "")
        importance_score = row.get("importance_score", 0)
        related_assets = row.get("related_assets", "")

        normalized = normalize_title(title)
        h = title_hash(title)

        event_type = classify_event_type(title, summary)
        source_score, source_tier = infer_source_score(source_name, config)
        freshness = calculate_freshness_score(published_at)
        quality = calculate_quality_score(
            source_score=source_score,
            freshness_score=freshness,
            importance_score=int(importance_score or 0),
            event_type=event_type,
            related_assets=related_assets,
            config=config,
        )

        normalized_titles.append(normalized)
        title_hashes.append(h)
        event_types.append(event_type)
        source_scores.append(source_score)
        source_tiers.append(source_tier)
        freshness_scores.append(freshness)
        quality_scores.append(quality)

    data["normalized_title"] = normalized_titles
    data["title_hash"] = title_hashes
    data["event_type"] = event_types
    data["source_score"] = source_scores
    data["source_tier"] = source_tiers
    data["freshness_score"] = freshness_scores
    data["quality_score"] = quality_scores

    return data


def deduplicate_news(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    data = df.copy()

    if "title_hash" not in data.columns:
        data = enrich_news_quality(data)

    for col in ["quality_score", "importance_score", "freshness_score", "source_score"]:
        if col not in data.columns:
            data[col] = 0
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    data = data.sort_values(
        ["quality_score", "importance_score", "freshness_score", "source_score"],
        ascending=[False, False, False, False],
    )

    data = data.drop_duplicates(subset=["title_hash"], keep="first")
    data = data.drop_duplicates(subset=["link"], keep="first")

    return data.reset_index(drop=True)