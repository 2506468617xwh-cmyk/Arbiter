# src/RAbot/analysis/macro_research.py

from __future__ import annotations

import math

import numpy as np
import pandas as pd


ASSET_MACRO_PROFILE: dict[str, dict] = {
    "NASDAQ": {
        "name": "纳斯达克综合指数",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "liquidity", "risk_appetite", "employment"],
        "style": "growth_equity_us",
    },
    "NASDAQ100": {
        "name": "纳斯达克100",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "liquidity", "risk_appetite", "employment"],
        "style": "growth_equity_us",
    },
    "SP500": {
        "name": "标普500",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "liquidity", "risk_appetite", "employment"],
        "style": "broad_equity_us",
    },
    "DOW": {
        "name": "道琼斯指数",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "employment", "growth", "risk_appetite"],
        "style": "value_equity_us",
    },
    "RUSSELL2000": {
        "name": "罗素2000",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "liquidity", "employment", "risk_appetite"],
        "style": "smallcap_equity_us",
    },
    "CSI300": {
        "name": "沪深300",
        "primary_regions": ["CN"],
        "important_categories": ["growth", "inflation", "liquidity", "policy_rate", "risk_appetite"],
        "style": "broad_equity_cn",
    },
    "SSE": {
        "name": "上证指数",
        "primary_regions": ["CN"],
        "important_categories": ["growth", "inflation", "liquidity", "policy_rate", "risk_appetite"],
        "style": "broad_equity_cn",
    },
    "CSI500": {
        "name": "中证500",
        "primary_regions": ["CN"],
        "important_categories": ["growth", "inflation", "liquidity", "policy_rate", "risk_appetite"],
        "style": "midcap_equity_cn",
    },
    "CSI1000": {
        "name": "中证1000",
        "primary_regions": ["CN"],
        "important_categories": ["growth", "liquidity", "policy_rate", "risk_appetite"],
        "style": "smallcap_equity_cn",
    },
    "CHINEXT": {
        "name": "创业板指",
        "primary_regions": ["CN", "US"],
        "important_categories": ["growth", "liquidity", "policy_rate", "rates", "risk_appetite"],
        "style": "growth_equity_cn",
    },
    "STAR50": {
        "name": "科创50",
        "primary_regions": ["CN", "US"],
        "important_categories": ["growth", "liquidity", "policy_rate", "rates", "risk_appetite"],
        "style": "growth_equity_cn",
    },
    "HSI": {
        "name": "恒生指数",
        "primary_regions": ["CN", "US"],
        "important_categories": ["growth", "liquidity", "rates", "policy_rate", "risk_appetite", "inflation"],
        "style": "hongkong_equity",
    },
    "GOLD": {
        "name": "黄金",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "risk_appetite", "liquidity"],
        "style": "gold",
    },
    "DXY": {
        "name": "美元指数",
        "primary_regions": ["US"],
        "important_categories": ["rates", "policy_rate", "inflation", "employment", "risk_appetite"],
        "style": "usd",
    },
    "VIX": {
        "name": "VIX",
        "primary_regions": ["US"],
        "important_categories": ["risk_appetite", "rates", "inflation", "employment"],
        "style": "volatility",
    },
    "WTI": {
        "name": "WTI原油",
        "primary_regions": ["US", "CN"],
        "important_categories": ["growth", "inflation", "risk_appetite"],
        "style": "oil",
    },
}


def build_macro_indicator_snapshot(series_df: pd.DataFrame) -> pd.DataFrame:
    if series_df is None or series_df.empty:
        return pd.DataFrame()

    rows = []

    for symbol, g in series_df.groupby("symbol"):
        g = g.copy()
        g["date"] = pd.to_datetime(g["date"], errors="coerce")
        g["value"] = pd.to_numeric(g["value"], errors="coerce")
        g = g.dropna(subset=["date", "value"]).sort_values("date")

        if g.empty:
            continue

        latest = g.iloc[-1]
        latest_date = latest["date"]
        latest_value = float(latest["value"])

        change_1m = _change_since(g, latest_date, days=31)
        change_3m = _change_since(g, latest_date, days=93)
        change_6m = _change_since(g, latest_date, days=186)
        change_1y = _change_since(g, latest_date, days=366)

        category = str(latest.get("category", ""))
        region = str(latest.get("region", ""))

        trend_label = classify_macro_trend(
            category=category,
            latest_value=latest_value,
            change_1m=change_1m,
            change_3m=change_3m,
        )

        risk_label, interpretation = interpret_macro_indicator(
            name=str(latest.get("name", symbol)),
            region=region,
            category=category,
            latest_value=latest_value,
            change_1m=change_1m,
            change_3m=change_3m,
            unit=str(latest.get("unit", "")),
        )

        rows.append(
            {
                "symbol": symbol,
                "name": latest.get("name", symbol),
                "region": region,
                "category": category,
                "source": latest.get("source", ""),
                "unit": latest.get("unit", ""),
                "latest_date": latest_date,
                "latest_value": latest_value,
                "change_1m": change_1m,
                "change_3m": change_3m,
                "change_6m": change_6m,
                "change_1y": change_1y,
                "trend_label": trend_label,
                "risk_label": risk_label,
                "interpretation": interpretation,
                "direction_note": latest.get("direction_note", ""),
                "related_assets": latest.get("related_assets", ""),
            }
        )

    out = pd.DataFrame(rows)

    if not out.empty:
        out = out.sort_values(["region", "category", "symbol"]).reset_index(drop=True)

    return out


def build_asset_macro_research(
    macro_df: pd.DataFrame,
    asset_symbol: str,
    technical_score: float | None = None,
) -> dict:
    asset = str(asset_symbol).upper().strip()

    if macro_df is None or macro_df.empty:
        return {
            "summary": "暂无可用宏观数据。请先在侧边栏更新宏观数据，或运行 python scripts/update_macro.py。",
            "support_points": [],
            "risk_points": [],
            "neutral_points": [],
            "top_indicators": pd.DataFrame(),
            "macro_bias": "数据不足",
            "macro_score": None,
            "alignment_label": "无法判断",
        }

    snapshot = build_macro_indicator_snapshot(macro_df)

    if snapshot.empty:
        return {
            "summary": "宏观数据已存在，但暂时无法生成有效快照。",
            "support_points": [],
            "risk_points": [],
            "neutral_points": [],
            "top_indicators": pd.DataFrame(),
            "macro_bias": "数据不足",
            "macro_score": None,
            "alignment_label": "无法判断",
        }

    profile = ASSET_MACRO_PROFILE.get(
        asset,
        {
            "name": asset,
            "primary_regions": [],
            "important_categories": [],
            "style": "generic",
        },
    )

    related = _select_asset_related_indicators(snapshot, asset, profile)

    if related.empty:
        related = snapshot.copy()

    related = related.copy()
    related["asset_effect_score"] = related.apply(
        lambda row: score_macro_effect_for_asset(row, asset, profile),
        axis=1,
    )
    related["importance_weight"] = related.apply(
        lambda row: _indicator_importance_weight(row, asset, profile),
        axis=1,
    )
    related["weighted_score"] = related["asset_effect_score"] * related["importance_weight"]

    valid = related.dropna(subset=["asset_effect_score", "importance_weight"]).copy()

    if valid.empty:
        macro_score = None
    else:
        denominator = valid["importance_weight"].abs().sum()
        if denominator <= 0:
            macro_score = None
        else:
            raw_score = valid["weighted_score"].sum() / denominator
            macro_score = int(max(0, min(100, round(50 + raw_score * 10))))

    risk_points: list[str] = []
    support_points: list[str] = []
    neutral_points: list[str] = []

    related_for_points = related.sort_values(
        by=["importance_weight", "latest_date"],
        ascending=[False, False],
    )

    for _, row in related_for_points.iterrows():
        text = _build_asset_macro_point(row, asset, profile)
        if not text:
            continue

        effect = _safe_float(row.get("asset_effect_score"))

        if effect is None:
            neutral_points.append(text)
        elif effect >= 0.8:
            support_points.append(text)
        elif effect <= -0.8:
            risk_points.append(text)
        else:
            neutral_points.append(text)

    support_points = support_points[:5]
    risk_points = risk_points[:5]
    neutral_points = neutral_points[:4]

    macro_bias = _macro_score_to_bias(macro_score)
    alignment_label = _build_alignment_label(technical_score, macro_score)

    summary = _build_asset_macro_summary(
        asset=asset,
        profile=profile,
        macro_bias=macro_bias,
        macro_score=macro_score,
        technical_score=technical_score,
        support_count=len(support_points),
        risk_count=len(risk_points),
    )

    top_indicators = related.sort_values(
        by=["importance_weight", "latest_date"],
        ascending=[False, False],
    ).head(12)

    return {
        "summary": summary,
        "support_points": support_points,
        "risk_points": risk_points,
        "neutral_points": neutral_points,
        "top_indicators": top_indicators,
        "macro_bias": macro_bias,
        "macro_score": macro_score,
        "alignment_label": alignment_label,
    }


def classify_macro_trend(
    category: str,
    latest_value: float,
    change_1m: float | None,
    change_3m: float | None,
) -> str:
    c1 = _safe_float(change_1m)
    c3 = _safe_float(change_3m)

    if c1 is None and c3 is None:
        return "趋势不足"

    ref = c3 if c3 is not None else c1

    if ref is None:
        return "趋势不足"

    if abs(ref) < 1e-9:
        return "基本持平"

    if category in {"rates", "policy_rate", "inflation"}:
        return "上行" if ref > 0 else "下行"

    if category in {"growth", "liquidity", "employment"}:
        return "改善" if ref > 0 else "走弱"

    if category == "risk_appetite":
        return "风险偏好降温" if ref > 0 else "风险偏好修复"

    return "上行" if ref > 0 else "下行"


def interpret_macro_indicator(
    name: str,
    region: str,
    category: str,
    latest_value: float,
    change_1m: float | None,
    change_3m: float | None,
    unit: str = "",
) -> tuple[str, str]:
    c1 = _safe_float(change_1m)
    c3 = _safe_float(change_3m)
    ref = c3 if c3 is not None else c1

    latest_text = _fmt_value(latest_value, unit)
    change_text = _fmt_change(ref, unit)

    if ref is None:
        return "数据不足", f"{name} 最新值为 {latest_text}，历史变化数据不足，暂不做方向判断。"

    if category in {"rates", "policy_rate"}:
        if ref > 0:
            return "利率压力", f"{name} 最新值为 {latest_text}，近阶段上行 {change_text}，通常意味着贴现率或融资成本压力上升。"
        return "利率支撑", f"{name} 最新值为 {latest_text}，近阶段下行 {change_text}，通常有助于缓解估值和融资成本压力。"

    if category == "inflation":
        if ref > 0:
            return "通胀压力", f"{name} 最新值为 {latest_text}，近阶段上行 {change_text}，需要观察通胀粘性及政策预期变化。"
        return "通胀降温", f"{name} 最新值为 {latest_text}，近阶段下行 {change_text}，通胀压力有所缓和。"

    if category == "growth":
        if "PMI" in name.upper() or "PMI" in name:
            if latest_value >= 50:
                return "增长改善", f"{name} 最新值为 {latest_text}，位于扩张区间，显示经济活动有修复迹象。"
            return "增长压力", f"{name} 最新值为 {latest_text}，位于收缩区间，说明经济活动仍偏弱。"

        if ref > 0:
            return "增长改善", f"{name} 最新值为 {latest_text}，近阶段改善 {change_text}，对风险资产预期相对友好。"
        return "增长压力", f"{name} 最新值为 {latest_text}，近阶段走弱 {change_text}，说明增长动能仍需观察。"

    if category == "liquidity":
        if ref > 0:
            return "流动性支撑", f"{name} 最新值为 {latest_text}，近阶段扩张 {change_text}，流动性环境边际改善。"
        return "流动性偏紧", f"{name} 最新值为 {latest_text}，近阶段收缩 {change_text}，流动性支持力度减弱。"

    if category == "employment":
        if "失业率" in name:
            if ref > 0:
                return "就业降温", f"{name} 最新值为 {latest_text}，近阶段上行 {change_text}，显示就业市场降温。"
            return "就业韧性", f"{name} 最新值为 {latest_text}，近阶段下行 {change_text}，就业市场仍有韧性。"

        if ref > 0:
            return "就业韧性", f"{name} 最新值为 {latest_text}，近阶段改善 {change_text}，增长韧性较强。"
        return "就业降温", f"{name} 最新值为 {latest_text}，近阶段走弱 {change_text}，增长动能存在降温迹象。"

    if category == "risk_appetite":
        if ref > 0:
            return "风险偏好压力", f"{name} 最新值为 {latest_text}，近阶段上行 {change_text}，市场避险情绪升温。"
        return "风险偏好修复", f"{name} 最新值为 {latest_text}，近阶段下行 {change_text}，市场风险偏好有所修复。"

    if ref > 0:
        return "边际上行", f"{name} 最新值为 {latest_text}，近阶段上行 {change_text}。"

    return "边际下行", f"{name} 最新值为 {latest_text}，近阶段下行 {change_text}。"


def score_macro_effect_for_asset(row: pd.Series, asset: str, profile: dict) -> float:
    category = str(row.get("category", ""))
    name = str(row.get("name", ""))
    symbol = str(row.get("symbol", ""))
    style = str(profile.get("style", "generic"))

    change_1m = _safe_float(row.get("change_1m"))
    change_3m = _safe_float(row.get("change_3m"))
    latest_value = _safe_float(row.get("latest_value"))

    ref = change_3m if change_3m is not None else change_1m
    if ref is None:
        return 0.0

    magnitude = _scaled_magnitude(ref)

    if style in {"growth_equity_us", "broad_equity_us", "smallcap_equity_us"}:
        return _score_us_equity(category, name, symbol, ref, latest_value, magnitude, style)

    if style in {"broad_equity_cn", "midcap_equity_cn", "smallcap_equity_cn", "growth_equity_cn"}:
        return _score_cn_equity(category, name, symbol, ref, latest_value, magnitude, style)

    if style == "hongkong_equity":
        return _score_hk_equity(category, name, symbol, ref, latest_value, magnitude)

    if style == "gold":
        return _score_gold(category, name, symbol, ref, latest_value, magnitude)

    if style == "usd":
        return _score_usd(category, name, symbol, ref, latest_value, magnitude)

    if style == "volatility":
        return _score_volatility(category, name, symbol, ref, latest_value, magnitude)

    if style == "oil":
        return _score_oil(category, name, symbol, ref, latest_value, magnitude)

    return _score_generic_risk_asset(category, name, symbol, ref, latest_value, magnitude)


def _score_us_equity(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
    style: str,
) -> float:
    growth_multiplier = 1.25 if style == "growth_equity_us" else 1.0
    smallcap_multiplier = 1.2 if style == "smallcap_equity_us" else 1.0

    if category in {"rates", "policy_rate"}:
        return -np.sign(ref) * magnitude * growth_multiplier * smallcap_multiplier

    if category == "inflation":
        return -np.sign(ref) * magnitude * 0.9

    if category == "liquidity":
        return np.sign(ref) * magnitude * 0.9

    if category == "risk_appetite":
        return -np.sign(ref) * magnitude * 1.15

    if category == "employment":
        if "失业率" in name or symbol == "UNRATE":
            return -np.sign(ref) * magnitude * 0.6
        return np.sign(ref) * magnitude * 0.5

    if category == "growth":
        return np.sign(ref) * magnitude * 0.6

    return 0.0


def _score_cn_equity(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
    style: str,
) -> float:
    growth_multiplier = 1.15 if style in {"growth_equity_cn", "smallcap_equity_cn"} else 1.0

    if category == "growth":
        if "PMI" in name.upper() or "PMI" in name:
            if latest_value is not None and latest_value >= 50:
                return 1.0 * growth_multiplier
            return -1.0 * growth_multiplier
        return np.sign(ref) * magnitude * growth_multiplier

    if category == "liquidity":
        return np.sign(ref) * magnitude * 1.05

    if category == "policy_rate":
        return -np.sign(ref) * magnitude * 0.85

    if category == "rates":
        return -np.sign(ref) * magnitude * 0.7

    if category == "inflation":
        if "PPI" in name.upper() or "PPI" in name:
            return np.sign(ref) * magnitude * 0.8
        if latest_value is not None and latest_value < 0:
            return -0.8
        if ref > 0 and latest_value is not None and latest_value < 3:
            return 0.4
        return -np.sign(ref) * magnitude * 0.4

    if category == "risk_appetite":
        return -np.sign(ref) * magnitude * 0.9

    return 0.0


def _score_hk_equity(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category in {"rates", "policy_rate"}:
        return -np.sign(ref) * magnitude * 1.05

    if category == "growth":
        if "PMI" in name.upper() or "PMI" in name:
            if latest_value is not None and latest_value >= 50:
                return 0.9
            return -0.9
        return np.sign(ref) * magnitude * 0.9

    if category == "liquidity":
        return np.sign(ref) * magnitude

    if category == "inflation":
        return -np.sign(ref) * magnitude * 0.5

    if category == "risk_appetite":
        return -np.sign(ref) * magnitude

    return 0.0


def _score_gold(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category in {"rates", "policy_rate"}:
        return -np.sign(ref) * magnitude * 1.15

    if category == "inflation":
        return np.sign(ref) * magnitude * 0.45

    if category == "risk_appetite":
        return np.sign(ref) * magnitude * 0.8

    if category == "liquidity":
        return np.sign(ref) * magnitude * 0.5

    if category == "employment":
        if "失业率" in name or symbol == "UNRATE":
            return np.sign(ref) * magnitude * 0.35
        return -np.sign(ref) * magnitude * 0.25

    return 0.0


def _score_usd(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category in {"rates", "policy_rate"}:
        return np.sign(ref) * magnitude * 1.1

    if category == "inflation":
        return np.sign(ref) * magnitude * 0.7

    if category == "employment":
        if "失业率" in name or symbol == "UNRATE":
            return -np.sign(ref) * magnitude * 0.5
        return np.sign(ref) * magnitude * 0.5

    if category == "risk_appetite":
        return np.sign(ref) * magnitude * 0.5

    if category == "liquidity":
        return -np.sign(ref) * magnitude * 0.4

    return 0.0


def _score_volatility(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category == "risk_appetite":
        return np.sign(ref) * magnitude

    if category in {"rates", "policy_rate", "inflation"}:
        return np.sign(ref) * magnitude * 0.5

    if category == "liquidity":
        return -np.sign(ref) * magnitude * 0.4

    return 0.0


def _score_oil(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category == "growth":
        return np.sign(ref) * magnitude

    if category == "inflation":
        return np.sign(ref) * magnitude * 0.5

    if category == "risk_appetite":
        return -np.sign(ref) * magnitude * 0.5

    if category == "liquidity":
        return np.sign(ref) * magnitude * 0.4

    return 0.0


def _score_generic_risk_asset(
    category: str,
    name: str,
    symbol: str,
    ref: float,
    latest_value: float | None,
    magnitude: float,
) -> float:
    if category in {"rates", "policy_rate", "inflation", "risk_appetite"}:
        return -np.sign(ref) * magnitude

    if category in {"growth", "liquidity", "employment"}:
        return np.sign(ref) * magnitude

    return 0.0


def _select_asset_related_indicators(snapshot: pd.DataFrame, asset: str, profile: dict) -> pd.DataFrame:
    related_assets_mask = snapshot["related_assets"].fillna("").str.upper().str.contains(asset, regex=False)

    primary_regions = set(profile.get("primary_regions", []) or [])
    important_categories = set(profile.get("important_categories", []) or [])

    region_mask = snapshot["region"].isin(primary_regions) if primary_regions else pd.Series(False, index=snapshot.index)
    category_mask = (
        snapshot["category"].isin(important_categories)
        if important_categories
        else pd.Series(False, index=snapshot.index)
    )

    selected = snapshot[related_assets_mask | (region_mask & category_mask)].copy()

    return selected


def _indicator_importance_weight(row: pd.Series, asset: str, profile: dict) -> float:
    weight = 1.0

    related_assets = str(row.get("related_assets", "")).upper()
    if asset in related_assets:
        weight += 0.75

    primary_regions = set(profile.get("primary_regions", []) or [])
    important_categories = set(profile.get("important_categories", []) or [])

    if row.get("region") in primary_regions:
        weight += 0.35

    if row.get("category") in important_categories:
        weight += 0.35

    symbol = str(row.get("symbol", ""))
    category = str(row.get("category", ""))

    high_importance_symbols = {
        "DGS10",
        "DGS2",
        "T10Y2Y",
        "FEDFUNDS",
        "CPIAUCSL",
        "CPILFESL",
        "PCEPI",
        "PCEPILFE",
        "UNRATE",
        "PAYEMS",
        "VIXCLS",
        "CN_CPI",
        "CN_PPI",
        "CN_PMI",
        "CN_M2",
        "CN_SOCIAL_FINANCING",
    }

    if symbol in high_importance_symbols:
        weight += 0.25

    if category in {"rates", "policy_rate", "inflation", "growth", "liquidity", "risk_appetite"}:
        weight += 0.15

    return weight


def _build_asset_macro_point(row: pd.Series, asset: str, profile: dict) -> str:
    name = str(row.get("name", row.get("symbol", "")))
    category = str(row.get("category", ""))
    latest_value = _safe_float(row.get("latest_value"))
    change_3m = _safe_float(row.get("change_3m"))
    change_1m = _safe_float(row.get("change_1m"))
    unit = str(row.get("unit", ""))
    effect = _safe_float(row.get("asset_effect_score"))

    ref = change_3m if change_3m is not None else change_1m

    latest_text = _fmt_value(latest_value, unit)
    change_text = _fmt_change(ref, unit)

    if effect is None:
        effect_text = "影响方向暂不明确"
    elif effect >= 0.8:
        effect_text = "对该资产偏支撑"
    elif effect <= -0.8:
        effect_text = "对该资产偏压力"
    else:
        effect_text = "影响偏中性"

    category_text = {
        "rates": "利率",
        "policy_rate": "政策利率",
        "inflation": "通胀",
        "employment": "就业",
        "growth": "增长",
        "liquidity": "流动性",
        "risk_appetite": "风险偏好",
    }.get(category, category or "宏观")

    if ref is None:
        return f"{name} 最新值为 {latest_text}，属于{category_text}变量，目前变化信息不足，{effect_text}。"

    if ref > 0:
        direction = f"近阶段上行 {change_text}"
    elif ref < 0:
        direction = f"近阶段下行 {change_text}"
    else:
        direction = "近阶段基本持平"

    return f"{name} 最新值为 {latest_text}，{direction}，属于{category_text}变量，{effect_text}。"


def _build_asset_macro_summary(
    asset: str,
    profile: dict,
    macro_bias: str,
    macro_score: int | None,
    technical_score: float | None,
    support_count: int,
    risk_count: int,
) -> str:
    asset_name = profile.get("name", asset)
    style = profile.get("style", "generic")

    score_text = "暂无宏观评分" if macro_score is None else f"宏观评分约为 {macro_score}/100"

    tech_text = ""
    if technical_score is not None and not pd.isna(technical_score):
        tech_text = f"当前技术评分约为 {float(technical_score):.0f}/100，"

    if macro_bias == "偏利多":
        core = f"{tech_text}{asset_name} 的宏观环境整体偏支撑，{score_text}。"
    elif macro_bias == "偏利空":
        core = f"{tech_text}{asset_name} 的宏观环境整体偏压力，{score_text}。"
    elif macro_bias == "中性混合":
        core = f"{tech_text}{asset_name} 的宏观环境多空交织，{score_text}。"
    else:
        core = f"{tech_text}{asset_name} 的宏观环境暂时数据不足，无法形成稳定判断。"

    style_hint = _style_specific_summary_hint(style)

    if support_count > risk_count:
        balance = "当前支撑因素多于压力因素，后续可观察这些支撑能否与技术趋势、新闻事件形成共振。"
    elif risk_count > support_count:
        balance = "当前压力因素多于支撑因素，即使价格趋势阶段性较强，也需要警惕宏观变量反向扰动。"
    elif support_count == 0 and risk_count == 0:
        balance = "当前宏观变量方向不够清晰，建议更多结合价格趋势和新闻面变化。"
    else:
        balance = "当前支撑与压力大致均衡，资产判断更依赖后续关键宏观数据的边际变化。"

    return core + style_hint + balance


def _style_specific_summary_hint(style: str) -> str:
    if style == "growth_equity_us":
        return " 对美股成长资产而言，美债利率、核心通胀和风险偏好是最关键的观察变量。"

    if style == "broad_equity_us":
        return " 对美股宽基资产而言，需要同时观察盈利预期、利率环境、就业韧性和风险偏好。"

    if style == "smallcap_equity_us":
        return " 对美股小盘资产而言，融资成本、流动性和经济韧性会更加重要。"

    if style in {"broad_equity_cn", "midcap_equity_cn", "smallcap_equity_cn", "growth_equity_cn"}:
        return " 对A股资产而言，中国增长动能、社融/M2、PPI修复和政策利率环境更值得重点跟踪。"

    if style == "hongkong_equity":
        return " 对港股而言，中国基本面和美国流动性会共同影响估值修复空间。"

    if style == "gold":
        return " 对黄金而言，实际利率、美元方向、通胀预期和避险情绪是核心变量。"

    if style == "usd":
        return " 对美元而言，美国利率优势、通胀粘性、就业韧性和全球避险情绪是核心变量。"

    if style == "oil":
        return " 对原油而言，全球增长预期、供需冲击和通胀环境更关键。"

    return " "


def _build_alignment_label(technical_score: float | None, macro_score: int | None) -> str:
    if technical_score is None or pd.isna(technical_score) or macro_score is None:
        return "无法判断"

    tech = float(technical_score)

    if tech >= 68 and macro_score >= 60:
        return "技术面与宏观面共振偏强"

    if tech >= 68 and macro_score <= 45:
        return "技术面较强但宏观面有压力"

    if tech <= 45 and macro_score >= 60:
        return "技术面偏弱但宏观面有修复支撑"

    if tech <= 45 and macro_score <= 45:
        return "技术面与宏观面共振偏弱"

    return "技术面与宏观面暂时中性"


def _macro_score_to_bias(score: int | None) -> str:
    if score is None:
        return "数据不足"

    if score >= 62:
        return "偏利多"

    if score <= 45:
        return "偏利空"

    return "中性混合"


def _change_since(g: pd.DataFrame, latest_date: pd.Timestamp, days: int) -> float | None:
    target_date = latest_date - pd.Timedelta(days=days)
    hist = g[g["date"] <= target_date]

    if hist.empty:
        return None

    base = float(hist.iloc[-1]["value"])
    latest = float(g.iloc[-1]["value"])

    if math.isnan(base) or math.isnan(latest):
        return None

    return latest - base


def _safe_float(value) -> float | None:
    if value is None:
        return None

    try:
        x = float(value)
    except Exception:
        return None

    if np.isnan(x) or np.isinf(x):
        return None

    return x


def _scaled_magnitude(value: float) -> float:
    abs_v = abs(value)

    if abs_v >= 5:
        return 2.0

    if abs_v >= 2:
        return 1.5

    if abs_v >= 1:
        return 1.15

    if abs_v >= 0.3:
        return 0.85

    if abs_v >= 0.1:
        return 0.55

    return 0.25


def _fmt_value(value: float | None, unit: str = "") -> str:
    if value is None or pd.isna(value):
        return "NA"

    suffix = unit or ""

    if abs(value) >= 1000:
        return f"{value:,.2f}{suffix}"

    return f"{value:.2f}{suffix}"


def _fmt_change(value: float | None, unit: str = "") -> str:
    if value is None or pd.isna(value):
        return "NA"

    suffix = unit or ""
    sign = "+" if value > 0 else ""

    if abs(value) >= 1000:
        return f"{sign}{value:,.2f}{suffix}"

    return f"{sign}{value:.2f}{suffix}"