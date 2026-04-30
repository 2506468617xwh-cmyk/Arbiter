from __future__ import annotations

import re

import pandas as pd


BULLISH_WORDS = [
    "rally", "rebounds", "rebound", "surges", "jumps", "gains", "beats", "strong",
    "optimism", "stimulus", "easing", "cut", "cuts", "dovish", "growth",
    "record high", "soft landing",
    "降息", "刺激", "反弹", "上涨", "增长", "利好", "回暖", "改善", "超预期"
]

BEARISH_WORDS = [
    "falls", "fall", "drops", "drop", "selloff", "sell-off", "slumps", "weak",
    "misses", "inflation", "higher yields", "yields rise", "hawkish", "recession",
    "risk", "warning", "crackdown", "tariff", "sanctions",
    "下跌", "回落", "通胀", "衰退", "风险", "利空", "制裁", "关税", "低迷", "不及预期"
]

IMPORTANT_WORDS = [
    "fed", "federal reserve", "fomc", "powell", "cpi", "inflation", "jobs",
    "payrolls", "treasury", "yields", "earnings", "nvidia", "microsoft", "apple",
    "ai", "china", "stimulus", "pmi", "oil", "gold", "dollar", "recession",
    "geopolitical",
    "美联储", "鲍威尔", "通胀", "非农", "美债", "收益率", "英伟达", "微软",
    "苹果", "人工智能", "中国", "政策", "刺激", "PMI", "原油", "黄金", "美元",
    "人民币", "地产", "A股", "沪深300", "上证指数", "港股", "恒生"
]

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


def infer_sentiment(title: str, summary: str | None = None) -> str:
    text = _normalize_text(f"{title} {summary or ''}")

    bullish = sum(1 for word in BULLISH_WORDS if word.lower() in text)
    bearish = sum(1 for word in BEARISH_WORDS if word.lower() in text)

    if bullish > bearish:
        return "偏利多"

    if bearish > bullish:
        return "偏利空"

    return "中性"


def infer_related_assets(title: str, summary: str | None = None, default_assets: list[str] | None = None) -> list[str]:
    text = _normalize_text(f"{title} {summary or ''}")

    assets = set(default_assets or [])

    for asset, keywords in ASSET_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                assets.add(asset)

    return sorted(assets)


def calculate_importance_score(title: str, summary: str | None = None, related_assets: list[str] | None = None) -> int:
    text = _normalize_text(f"{title} {summary or ''}")

    score = 20

    for word in IMPORTANT_WORDS:
        if word.lower() in text:
            score += 8

    if related_assets:
        score += min(25, len(related_assets) * 5)

    if re.search(
        r"\b(cpi|fomc|fed|powell|nvidia|earnings|stimulus|treasury|yields|inflation|pmi)\b",
        text,
    ):
        score += 15

    for zh_key in ["美联储", "通胀", "非农", "美债", "收益率", "政策", "刺激", "地产", "人民币", "A股", "港股"]:
        if zh_key.lower() in text:
            score += 10

    return max(0, min(100, score))


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

    if sentiment_label == "偏利多":
        impact = "这条新闻可能对相关资产形成一定利多，主要通过风险偏好、盈利预期、政策预期或流动性预期传导。"
    elif sentiment_label == "偏利空":
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