from __future__ import annotations

from datetime import datetime

import pandas as pd

from RAbot.news.news_dedup import deduplicate_news as deduplicate_news_items
from RAbot.news.news_models import NewsItem
from RAbot.news.news_quality import (
    calculate_importance_score,
    infer_sentiment,
    score_news_items,
)
from RAbot.news.news_store import NewsResearchStore
from RAbot.settings import get_project_dir

ASSET_KEYWORDS = {
    "NASDAQ": ["nasdaq", "technology stocks", "tech stocks", "ai stocks", "纳斯达克", "科技股"],
    "NASDAQ100": ["nasdaq 100", "ndx", "mega-cap tech", "big tech", "纳指100", "大型科技股"],
    "SP500": ["s&p 500", "sp 500", "us stocks", "wall street", "标普500", "美股"],
    "DOW": ["dow jones", "dow", "道琼斯"],
    "RUSSELL2000": ["russell 2000", "small caps", "small-cap", "罗素2000"],
    "VIX": ["vix", "volatility", "fear gauge", "恐慌指数", "波动率"],
    "DXY": ["dollar", "us dollar", "dxy", "greenback", "美元", "美元指数"],
    "GOLD": ["gold", "bullion", "黄金"],
    "WTI": ["oil", "crude", "wti", "opec", "原油", "石油"],
    "HSI": ["hang seng", "hong kong stocks", "恒生指数", "港股", "恒生科技"],
    "CSI300": ["csi 300", "china stocks", "a-shares", "mainland stocks", "沪深300", "A股", "a股"],
    "SSE": ["shanghai composite", "shanghai stock market", "上证指数", "沪指"],
    "CSI500": ["csi 500", "中证500"],
    "CSI1000": ["csi 1000", "中证1000"],
    "CHINEXT": ["chinext", "growth enterprise market", "创业板", "创业板指"],
    "STAR50": ["star 50", "star market", "科创50", "科创板"],
}


def _normalize_text(text: str | None) -> str:
    return (text or "").lower().strip()


def infer_related_assets(title: str, summary: str | None = None, default_assets: list[str] | None = None) -> list[str]:
    text = _normalize_text(f"{title} {summary or ''}")

    assets = set(default_assets or [])

    for asset, keywords in ASSET_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                assets.add(asset)

    return sorted(assets)


def build_news_interpretation(
    title: str,
    summary: str | None,
    related_assets: list[str] | str | None,
    sentiment_label: str,
    importance_score: int,
    event_type: str | None = None,
    quality_score: int | None = None,
) -> str:
    if isinstance(related_assets, str):
        assets = [x.strip() for x in related_assets.split(",") if x.strip()]
    else:
        assets = related_assets or []

    asset_text = "、".join(assets) if assets else "相关资产"
    event_text = event_type or "未分类事件"

    if sentiment_label == "利好":
        impact = "这条新闻可能对相关资产形成一定利多，主要通过风险偏好、盈利预期、政策预期或流动性预期传导。"
    elif sentiment_label == "利空":
        impact = "这条新闻可能对相关资产形成一定利空，主要通过估值压力、利率预期、风险偏好下降或基本面担忧传导。"
    else:
        impact = "这条新闻目前更偏中性，适合作为背景信息纳入观察，但暂不宜单独作为方向判断依据。"

    if quality_score is not None and quality_score >= 75:
        level = "新闻质量分较高，建议重点跟踪后续市场反应。"
    elif importance_score >= 70:
        level = "重要性较高，建议重点观察。"
    elif importance_score >= 50:
        level = "重要性中等，可以结合价格走势和波动率变化继续观察。"
    else:
        level = "重要性较低，更多作为信息补充。"

    return f"事件类型：{event_text}。关联资产：{asset_text}。{impact}{level}"


def enrich_news_dataframe(df: pd.DataFrame, default_assets: list[str] | None = None) -> pd.DataFrame:
    if df.empty:
        return df

    data = df.copy()

    related_assets_list = []
    sentiment_list = []
    importance_list = []

    for _, row in data.iterrows():
        title = row.get("title", "")
        summary = row.get("summary", "")

        related_assets = infer_related_assets(title, summary, default_assets=default_assets)
        sentiment = infer_sentiment(title, summary)
        importance = calculate_importance_score(title, summary, related_assets)

        related_assets_list.append(",".join(related_assets))
        sentiment_list.append(sentiment)
        importance_list.append(importance)

    data["related_assets"] = related_assets_list
    data["sentiment_label"] = sentiment_list
    data["importance_score"] = importance_list

    return data


def _init_multi_source_providers():
    from RAbot.news.akshare_news_provider import AKShareNewsProvider
    from RAbot.news.alphavantage_news_provider import AlphaVantageNewsProvider
    from RAbot.news.eastmoney_news_provider import EastmoneyNewsProvider
    from RAbot.news.finnhub_news_provider import FinnhubNewsProvider
    from RAbot.news.futu_news_provider import FutuNewsProvider
    from RAbot.news.newsapi_provider import NewsAPIProvider
    from RAbot.news.rsshub_news_provider import RSSHubNewsProvider
    from RAbot.news.sina_news_provider import SinaFinanceNewsProvider

    return [
        SinaFinanceNewsProvider(),
        EastmoneyNewsProvider(),
        FutuNewsProvider(),
        AKShareNewsProvider(),
        RSSHubNewsProvider(),
        FinnhubNewsProvider(),
        NewsAPIProvider(),
        AlphaVantageNewsProvider(),
    ]


def collect_all_news(
    limit_per_source: int = 50,
    markets: list[str] | None = None,
    symbols: list[str] | None = None,
    keywords: list[str] | None = None,
) -> dict:
    try:
        from dotenv import load_dotenv

        load_dotenv(get_project_dir() / ".env", override=False)
    except Exception:
        pass

    warnings: list[str] = []
    provider_stats: dict[str, dict] = {}
    all_items: list[NewsItem] = []
    requested_markets = {market.upper() for market in markets or [] if market}
    requested_symbols = [symbol.strip().upper() for symbol in symbols or [] if symbol.strip()]
    requested_keywords = [keyword.strip() for keyword in keywords or [] if keyword.strip()]

    for provider in _init_multi_source_providers():
        provider_items: list[NewsItem] = []
        provider_warnings_before = len(provider.warnings)
        try:
            provider_items.extend(provider.fetch_latest(limit=limit_per_source, markets=markets))
            for symbol in requested_symbols:
                provider_items.extend(provider.fetch_by_symbol(symbol, limit=max(5, limit_per_source // 2)))
            for keyword in requested_keywords:
                provider_items.extend(provider.fetch_by_keyword(keyword, limit=max(5, limit_per_source // 2)))
        except Exception as exc:
            provider.warnings.append(f"{provider.provider_name} 采集失败：{type(exc).__name__}: {exc}")

        if requested_markets:
            filtered = []
            for item in provider_items:
                item_markets = {market.upper() for market in item.markets}
                if not item_markets or item_markets & requested_markets or "GLOBAL" in item_markets:
                    filtered.append(item)
            provider_items = filtered

        scored = score_news_items(provider_items, focus_symbols=requested_symbols)
        all_items.extend(scored)
        provider_warnings = provider.warnings[provider_warnings_before:]
        warnings.extend(provider_warnings)
        provider_stats[provider.provider_name] = {
            "fetched": len(provider_items),
            "warnings": provider_warnings,
        }

    deduped = deduplicate_news_items(all_items)
    store = NewsResearchStore()
    saved_count = store.save_news_items(deduped)

    for name in list(provider_stats):
        provider_stats[name]["saved"] = len([item for item in deduped if item.provider == name])

    return {
        "items": deduped,
        "saved_count": saved_count,
        "provider_stats": provider_stats,
        "warnings": warnings,
        "last_update": datetime.now().astimezone().isoformat(timespec="seconds"),
    }
