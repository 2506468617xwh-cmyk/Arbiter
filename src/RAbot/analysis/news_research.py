from __future__ import annotations

from datetime import datetime

import pandas as pd


MACRO_RISK_KEYWORDS = [
    "fed",
    "federal reserve",
    "fomc",
    "powell",
    "inflation",
    "cpi",
    "treasury",
    "yield",
    "yields",
    "rate",
    "rates",
    "hawkish",
    "recession",
    "美元",
    "美债",
    "通胀",
    "加息",
    "降息",
]

GROWTH_SUPPORT_KEYWORDS = [
    "ai",
    "nvidia",
    "microsoft",
    "apple",
    "earnings",
    "profit",
    "revenue",
    "beats",
    "guidance",
    "semiconductor",
    "chip",
    "人工智能",
    "财报",
    "盈利",
    "芯片",
    "科技",
]

CHINA_POLICY_KEYWORDS = [
    "china",
    "stimulus",
    "pmi",
    "property",
    "real estate",
    "policy",
    "liquidity",
    "consumption",
    "中国",
    "政策",
    "刺激",
    "地产",
    "社融",
    "流动性",
    "消费",
]

RISK_OFF_KEYWORDS = [
    "selloff",
    "sell-off",
    "risk",
    "war",
    "geopolitical",
    "sanctions",
    "tariff",
    "crisis",
    "volatility",
    "fear",
    "风险",
    "制裁",
    "关税",
    "冲突",
    "波动",
    "避险",
]


def _safe_int(value, default: int = 0) -> int:
    try:
        if value is None or pd.isna(value):
            return default
        return int(value)
    except Exception:
        return default


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _parse_related_assets(value) -> list[str]:
    if value is None or pd.isna(value):
        return []

    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]

    return [x.strip() for x in str(value).split(",") if x.strip()]


def _contains_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(keyword.lower() in text_lower for keyword in keywords)


def _format_news_line(row: pd.Series) -> str:
    title = row.get("title", "")
    sentiment = row.get("sentiment_label", "中性")
    importance = _safe_int(row.get("importance_score"), 0)
    source = row.get("source_name", "Unknown")
    published_at = row.get("published_at", "")

    if published_at:
        return f"{title}｜{source}｜{sentiment}｜重要性 {importance}/100｜{published_at}"

    return f"{title}｜{source}｜{sentiment}｜重要性 {importance}/100"


def filter_news_for_asset(
    news_df: pd.DataFrame,
    asset_symbol: str,
    days: int = 7,
) -> pd.DataFrame:
    """
    根据资产代码和时间窗口筛选相关新闻。

    注意：
    - 如果新闻没有 published_at，则保留，但排序时靠后。
    - 资产关联基于 related_assets 字段。
    """
    if news_df.empty:
        return pd.DataFrame()

    data = news_df.copy()

    if "related_assets" not in data.columns:
        return pd.DataFrame()

    data["asset_list"] = data["related_assets"].apply(_parse_related_assets)
    data = data[data["asset_list"].apply(lambda xs: asset_symbol in xs)].copy()

    if data.empty:
        return pd.DataFrame()

    if "published_at" in data.columns:
        data["published_dt"] = pd.to_datetime(data["published_at"], errors="coerce")

        valid_dates = data["published_dt"].dropna()

        if not valid_dates.empty:
            max_dt = valid_dates.max()
            start_dt = max_dt - pd.DateOffset(days=days)
            dated = data[data["published_dt"].notna()].copy()
            undated = data[data["published_dt"].isna()].copy()
            dated = dated[dated["published_dt"] >= start_dt].copy()
            data = pd.concat([dated, undated], ignore_index=True)

    if "importance_score" in data.columns:
        data["importance_score"] = pd.to_numeric(data["importance_score"], errors="coerce").fillna(0)
    else:
        data["importance_score"] = 0

    data = data.sort_values(
        by=["importance_score", "published_at"],
        ascending=[False, False],
        na_position="last",
    )

    return data


def build_asset_news_research(
    news_df: pd.DataFrame,
    asset_symbol: str,
    technical_score: int | None = None,
    days: int = 7,
) -> dict:
    """
    单资产新闻面研究。

    输出：
    - 情绪结构
    - 高重要性新闻
    - 宏观风险 / 成长支撑 / 中国政策 / 避险风险线索
    - 新闻面与技术面是否共振
    """
    related = filter_news_for_asset(news_df, asset_symbol=asset_symbol, days=days)

    if related.empty:
        return {
            "asset_symbol": asset_symbol,
            "days": days,
            "total_news": 0,
            "high_importance_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
            "avg_importance": 0,
            "news_bias": "暂无明显新闻信号",
            "alignment_label": "无法判断",
            "summary": f"过去{days}天内没有找到与 {asset_symbol} 明确关联的新闻，暂时无法判断新闻面对资产状态的影响。",
            "risk_points": [],
            "support_points": [],
            "top_news": [],
            "data": related,
        }

    total = len(related)
    high_importance = related[related["importance_score"] >= 70].copy()

    sentiment_counts = related["sentiment_label"].value_counts().to_dict()

    bullish_count = _safe_int(sentiment_counts.get("偏利多", 0))
    bearish_count = _safe_int(sentiment_counts.get("偏利空", 0))
    neutral_count = _safe_int(sentiment_counts.get("中性", 0))

    avg_importance = round(_safe_float(related["importance_score"].mean()), 1)

    if bullish_count > bearish_count * 1.3 and bullish_count >= 2:
        news_bias = "新闻面偏利多"
    elif bearish_count > bullish_count * 1.3 and bearish_count >= 2:
        news_bias = "新闻面偏利空"
    elif high_importance.empty and total <= 3:
        news_bias = "新闻信号较弱"
    else:
        news_bias = "新闻面中性偏分化"

    full_text = " ".join(
        (
            related.get("title", pd.Series(dtype=str)).fillna("").astype(str)
            + " "
            + related.get("summary", pd.Series(dtype=str)).fillna("").astype(str)
        ).tolist()
    )

    risk_points: list[str] = []
    support_points: list[str] = []

    if _contains_any(full_text, MACRO_RISK_KEYWORDS):
        risk_points.append("新闻中出现美联储、通胀、美债收益率或利率预期相关信息，可能通过估值折现率影响风险资产。")

    if _contains_any(full_text, RISK_OFF_KEYWORDS):
        risk_points.append("新闻中出现避险、波动、地缘或风险事件线索，可能压制短期风险偏好。")

    if _contains_any(full_text, GROWTH_SUPPORT_KEYWORDS):
        support_points.append("新闻中出现 AI、科技龙头、财报或盈利预期相关线索，可能支撑成长资产叙事。")

    if _contains_any(full_text, CHINA_POLICY_KEYWORDS):
        support_points.append("新闻中出现中国政策、PMI、地产或流动性线索，可能影响 A 股风险偏好与顺周期预期。")

    technical_score_value = _safe_int(technical_score, 0)

    if technical_score is None:
        alignment_label = "仅新闻面判断"
        alignment_text = "当前未提供技术面评分，因此仅从新闻角度观察。"
    elif technical_score_value >= 70 and news_bias == "新闻面偏利多":
        alignment_label = "技术面与新闻面共振偏强"
        alignment_text = "技术面评分较高，且新闻情绪偏利多，说明价格趋势与信息面形成一定共振。"
    elif technical_score_value >= 70 and news_bias == "新闻面偏利空":
        alignment_label = "技术面强但新闻面有扰动"
        alignment_text = "技术面评分较高，但新闻情绪偏利空，说明趋势较强的同时，事件或宏观因素可能带来估值扰动。"
    elif technical_score_value <= 45 and news_bias == "新闻面偏利多":
        alignment_label = "技术面弱但新闻面改善"
        alignment_text = "技术面评分偏低，但新闻情绪偏利多，可能意味着市场尚未完全反映潜在利好，需要观察价格是否修复。"
    elif technical_score_value <= 45 and news_bias == "新闻面偏利空":
        alignment_label = "技术面与新闻面共振偏弱"
        alignment_text = "技术面评分偏低，且新闻情绪偏利空，说明资产可能仍处于风险释放或信心不足阶段。"
    else:
        alignment_label = "技术面与新闻面中性分化"
        alignment_text = "技术面与新闻面没有形成明显一致方向，短期更适合观察关键价格位和后续事件。"

    if risk_points:
        risk_text = " ".join(risk_points)
    else:
        risk_text = "新闻中暂未出现特别集中的宏观或风险事件压力。"

    if support_points:
        support_text = " ".join(support_points)
    else:
        support_text = "新闻中暂未出现特别集中的正向叙事支撑。"

    summary = (
        f"过去{days}天内，RAbot 共捕捉到 {total} 条与 {asset_symbol} 相关的新闻，"
        f"其中高重要性新闻 {len(high_importance)} 条；情绪结构为：偏利多 {bullish_count} 条、"
        f"偏利空 {bearish_count} 条、中性 {neutral_count} 条，平均重要性为 {avg_importance}/100。"
        f"综合来看，当前{news_bias}。{alignment_text}"
        f"风险线索方面，{risk_text}支撑线索方面，{support_text}"
    )

    top_news_rows = high_importance.head(5)
    if top_news_rows.empty:
        top_news_rows = related.head(5)

    top_news = [_format_news_line(row) for _, row in top_news_rows.iterrows()]

    return {
        "asset_symbol": asset_symbol,
        "days": days,
        "total_news": total,
        "high_importance_count": len(high_importance),
        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,
        "avg_importance": avg_importance,
        "news_bias": news_bias,
        "alignment_label": alignment_label,
        "summary": summary,
        "risk_points": risk_points,
        "support_points": support_points,
        "top_news": top_news,
        "data": related,
    }


def build_news_market_snapshot(news_df: pd.DataFrame, days: int = 7) -> dict:
    """
    新闻中心总览：统计最近新闻中的风险/利多/利空结构。
    """
    if news_df.empty:
        return {
            "headline": "暂无新闻快照",
            "summary": "当前数据库暂无新闻数据。",
            "total_news": 0,
            "top_assets": [],
            "top_news": [],
        }

    data = news_df.copy()

    if "published_at" in data.columns:
        data["published_dt"] = pd.to_datetime(data["published_at"], errors="coerce")
        valid_dates = data["published_dt"].dropna()

        if not valid_dates.empty:
            max_dt = valid_dates.max()
            start_dt = max_dt - pd.DateOffset(days=days)
            dated = data[data["published_dt"].notna()].copy()
            undated = data[data["published_dt"].isna()].copy()
            dated = dated[dated["published_dt"] >= start_dt].copy()
            data = pd.concat([dated, undated], ignore_index=True)

    if data.empty:
        return {
            "headline": "暂无近期新闻快照",
            "summary": f"过去{days}天暂无新闻数据。",
            "total_news": 0,
            "top_assets": [],
            "top_news": [],
        }

    data["importance_score"] = pd.to_numeric(data.get("importance_score", 0), errors="coerce").fillna(0)

    total = len(data)
    sentiment_counts = data.get("sentiment_label", pd.Series(dtype=str)).value_counts().to_dict()

    bullish = _safe_int(sentiment_counts.get("偏利多", 0))
    bearish = _safe_int(sentiment_counts.get("偏利空", 0))
    neutral = _safe_int(sentiment_counts.get("中性", 0))

    asset_counter: dict[str, int] = {}

    for value in data.get("related_assets", pd.Series(dtype=str)).fillna(""):
        for asset in _parse_related_assets(value):
            asset_counter[asset] = asset_counter.get(asset, 0) + 1

    top_assets = sorted(asset_counter.items(), key=lambda x: x[1], reverse=True)[:8]

    if bearish > bullish * 1.25 and bearish >= 3:
        headline = "新闻面风险偏高"
    elif bullish > bearish * 1.25 and bullish >= 3:
        headline = "新闻面风险偏好改善"
    else:
        headline = "新闻面整体分化"

    top_asset_text = "、".join([f"{asset}（{count}条）" for asset, count in top_assets]) if top_assets else "暂无明显集中资产"

    summary = (
        f"过去{days}天新闻库共记录 {total} 条相关新闻，情绪结构为：偏利多 {bullish} 条、"
        f"偏利空 {bearish} 条、中性 {neutral} 条。新闻关注度较高的资产包括：{top_asset_text}。"
        f"整体判断为：{headline}。"
    )

    top_news_rows = data.sort_values("importance_score", ascending=False).head(5)
    top_news = [_format_news_line(row) for _, row in top_news_rows.iterrows()]

    return {
        "headline": headline,
        "summary": summary,
        "total_news": total,
        "top_assets": top_assets,
        "top_news": top_news,
    }