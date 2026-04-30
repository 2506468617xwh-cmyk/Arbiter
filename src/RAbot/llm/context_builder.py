# src/RAbot/llm/context_builder.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from RAbot.analysis.indicators import (
    add_technical_indicators,
    build_asset_performance_table,
)
from RAbot.analysis.macro_research import build_asset_macro_research
from RAbot.analysis.news_research import (
    build_asset_news_research,
    build_news_market_snapshot,
)
from RAbot.analysis.research_engine import (
    build_market_overview,
    build_single_asset_research,
)
from RAbot.macro.macro_store import MacroStore
from RAbot.news.news_store import NewsStore
from RAbot.settings import get_db_path
from RAbot.storage.sqlite_store import SQLiteStore


@dataclass
class ContextBuildResult:
    ok: bool
    context: dict[str, Any]
    message: str = ""


DEFAULT_CONTEXT_NEWS_LIMIT = 500


def _safe_call(func, default):
    try:
        return func()
    except Exception:
        return default


def _to_jsonable(value: Any) -> Any:
    """
    尽量把 pandas / numpy / Timestamp 类型转成 LLM prompt 里稳定可读的对象。
    """
    if isinstance(value, pd.Timestamp):
        if pd.isna(value):
            return None
        return value.strftime("%Y-%m-%d")

    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")

    if isinstance(value, pd.Series):
        return value.to_dict()

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass

    if isinstance(value, dict):
        return {str(k): _to_jsonable(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_to_jsonable(x) for x in value]

    if pd.isna(value) if not isinstance(value, (list, dict, tuple, set)) else False:
        return None

    return value


def _fmt_float(value: Any, digits: int = 2) -> str:
    if value is None:
        return "N/A"

    try:
        if pd.isna(value):
            return "N/A"
    except Exception:
        pass

    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return str(value)


def _load_all_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    store = SQLiteStore(get_db_path())
    news_store = NewsStore(get_db_path())
    macro_store = MacroStore(get_db_path())

    all_data = _safe_call(lambda: store.read_index_daily(), pd.DataFrame())
    all_news = _safe_call(lambda: news_store.read_news(limit=DEFAULT_CONTEXT_NEWS_LIMIT), pd.DataFrame())
    all_macro = _safe_call(lambda: macro_store.read_macro_series(), pd.DataFrame())

    return all_data, all_news, all_macro


def _latest_asset_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {}

    try:
        data = add_technical_indicators(df.copy())
        data = data.sort_values("date")
        latest = data.iloc[-1]

        result = {
            "date": str(latest.get("date", "")),
            "close": _fmt_float(latest.get("close")),
            "pct_change": _fmt_float(latest.get("pct_change")),
            "ma20": _fmt_float(latest.get("ma20")),
            "ma60": _fmt_float(latest.get("ma60")),
            "ma120": _fmt_float(latest.get("ma120")),
            "drawdown": _fmt_float(latest.get("drawdown")),
            "volatility_20d": _fmt_float(latest.get("volatility_20d")),
        }

        return result
    except Exception:
        return {}


def _asset_recent_performance(perf_df: pd.DataFrame, symbol: str) -> dict[str, Any]:
    if perf_df is None or perf_df.empty or "symbol" not in perf_df.columns:
        return {}

    row = perf_df[perf_df["symbol"].astype(str) == str(symbol)]

    if row.empty:
        return {}

    wanted_cols = [
        "symbol",
        "name",
        "近1周收益率%",
        "近1月收益率%",
        "近3月收益率%",
        "近6月收益率%",
        "YTD收益率%",
        "近1年收益率%",
        "20日年化波动率%",
        "当前回撤%",
        "区间最大回撤%",
    ]

    data = row.iloc[0].to_dict()
    return {
        col: _to_jsonable(data.get(col))
        for col in wanted_cols
        if col in data
    }


def _compact_news_context(asset_news: dict[str, Any]) -> dict[str, Any]:
    if not asset_news:
        return {}

    result = {
        "total_news": asset_news.get("total_news", 0),
        "high_importance_count": asset_news.get("high_importance_count", 0),
        "bullish_count": asset_news.get("bullish_count", 0),
        "bearish_count": asset_news.get("bearish_count", 0),
        "avg_importance": asset_news.get("avg_importance", 0),
        "alignment_label": asset_news.get("alignment_label", "无法判断"),
        "summary": asset_news.get("summary", ""),
        "top_news": asset_news.get("top_news", [])[:6],
    }

    return _to_jsonable(result)


def _compact_macro_context(asset_macro: dict[str, Any]) -> dict[str, Any]:
    if not asset_macro:
        return {}

    result = {
        "macro_score": asset_macro.get("macro_score"),
        "macro_bias": asset_macro.get("macro_bias", "数据不足"),
        "alignment_label": asset_macro.get("alignment_label", "无法判断"),
        "summary": asset_macro.get("summary", ""),
        "support_points": asset_macro.get("support_points", [])[:5],
        "risk_points": asset_macro.get("risk_points", [])[:5],
        "neutral_points": asset_macro.get("neutral_points", [])[:4],
    }

    top_indicators = asset_macro.get("top_indicators")

    if isinstance(top_indicators, pd.DataFrame) and not top_indicators.empty:
        show_cols = [
            "name",
            "region",
            "category",
            "latest_date",
            "latest_value",
            "change_1m",
            "change_3m",
            "trend_label",
            "risk_label",
            "asset_effect_score",
            "interpretation",
        ]
        show = top_indicators[[col for col in show_cols if col in top_indicators.columns]].head(8).copy()
        result["top_indicators"] = _to_jsonable(show)

    return _to_jsonable(result)


def build_asset_context(asset_symbol: str) -> ContextBuildResult:
    """
    构造单一资产的事实包。

    只放摘要，不塞大表，避免 prompt 过长。
    """
    asset_symbol = str(asset_symbol).strip()

    if not asset_symbol:
        return ContextBuildResult(False, {}, "未指定资产代码。")

    all_data, all_news, all_macro = _load_all_data()

    if all_data.empty:
        return ContextBuildResult(False, {}, "本地行情数据库为空，请先更新行情数据。")

    if "symbol" not in all_data.columns:
        return ContextBuildResult(False, {}, "行情数据缺少 symbol 字段。")

    df = all_data[all_data["symbol"].astype(str) == asset_symbol].copy()

    if df.empty:
        return ContextBuildResult(False, {}, f"未找到资产 {asset_symbol} 的行情数据。")

    df = df.sort_values("date")

    perf_df = _safe_call(lambda: build_asset_performance_table(all_data), pd.DataFrame())
    research = _safe_call(lambda: build_single_asset_research(df), {})
    asset_news = _safe_call(
        lambda: build_asset_news_research(
            all_news,
            asset_symbol=asset_symbol,
            technical_score=research.get("score"),
            days=7,
        ),
        {},
    )
    asset_macro = _safe_call(
        lambda: build_asset_macro_research(
            all_macro,
            asset_symbol=asset_symbol,
            technical_score=research.get("score"),
        ),
        {},
    )

    name = asset_symbol
    if "name" in df.columns:
        names = df["name"].dropna().astype(str)
        if not names.empty:
            name = names.iloc[-1]

    context = {
        "scope": "single_asset",
        "asset": {
            "symbol": asset_symbol,
            "name": name,
        },
        "latest_snapshot": _latest_asset_snapshot(df),
        "performance": _asset_recent_performance(perf_df, asset_symbol),
        "technical_research": _to_jsonable(
            {
                "score": research.get("score"),
                "grade": research.get("grade"),
                "trend_label": research.get("trend_label"),
                "risk_label": research.get("risk_label"),
                "volatility_label": research.get("volatility_label"),
                "momentum_label": research.get("momentum_label"),
                "summary": research.get("summary"),
                "action_hint": research.get("action_hint"),
                "watch_points": research.get("watch_points", [])[:6],
            }
        ),
        "news_research": _compact_news_context(asset_news),
        "macro_research": _compact_macro_context(asset_macro),
        "data_note": "以上事实包来自 RAbot 本地行情数据库、新闻数据库、宏观数据库与规则层研究模块。LLM 回答必须基于这些事实，不得编造实时数据。",
    }

    return ContextBuildResult(True, context, "")


def build_market_context() -> ContextBuildResult:
    """
    构造全市场事实包。
    """
    all_data, all_news, all_macro = _load_all_data()

    if all_data.empty:
        return ContextBuildResult(False, {}, "本地行情数据库为空，请先更新行情数据。")

    perf_df = _safe_call(lambda: build_asset_performance_table(all_data), pd.DataFrame())
    market_overview = _safe_call(lambda: build_market_overview(perf_df), {})
    news_snapshot = _safe_call(lambda: build_news_market_snapshot(all_news, days=7), {})

    top_assets = []
    weak_assets = []
    high_vol_assets = []

    if not perf_df.empty:
        if "近1月收益率%" in perf_df.columns:
            top_assets = (
                perf_df.dropna(subset=["近1月收益率%"])
                .sort_values("近1月收益率%", ascending=False)
                .head(8)
                .to_dict(orient="records")
            )
            weak_assets = (
                perf_df.dropna(subset=["近1月收益率%"])
                .sort_values("近1月收益率%", ascending=True)
                .head(8)
                .to_dict(orient="records")
            )

        if "20日年化波动率%" in perf_df.columns:
            high_vol_assets = (
                perf_df.dropna(subset=["20日年化波动率%"])
                .sort_values("20日年化波动率%", ascending=False)
                .head(8)
                .to_dict(orient="records")
            )

    context = {
        "scope": "market",
        "market_overview": _to_jsonable(market_overview),
        "news_snapshot": _to_jsonable(
            {
                "headline": news_snapshot.get("headline"),
                "summary": news_snapshot.get("summary"),
                "top_news": news_snapshot.get("top_news", [])[:8],
            }
        ),
        "top_assets_1m": _to_jsonable(top_assets),
        "weak_assets_1m": _to_jsonable(weak_assets),
        "high_vol_assets": _to_jsonable(high_vol_assets),
        "data_note": "以上事实包来自 RAbot 本地行情数据库、新闻数据库、宏观数据库与规则层研究模块。LLM 回答必须基于这些事实，不得编造实时数据。",
    }

    return ContextBuildResult(True, context, "")


def build_multi_asset_context(symbols: list[str]) -> ContextBuildResult:
    """
    构造多资产组合事实包。
    """
    symbols = [str(x).strip() for x in symbols if str(x).strip()]

    if not symbols:
        return ContextBuildResult(False, {}, "未选择资产。")

    all_data, all_news, all_macro = _load_all_data()

    if all_data.empty:
        return ContextBuildResult(False, {}, "本地行情数据库为空，请先更新行情数据。")

    perf_df = _safe_call(lambda: build_asset_performance_table(all_data), pd.DataFrame())

    assets_context: list[dict[str, Any]] = []

    for symbol in symbols:
        df = all_data[all_data["symbol"].astype(str) == symbol].copy()

        if df.empty:
            assets_context.append(
                {
                    "symbol": symbol,
                    "error": "本地数据库中未找到该资产行情数据。",
                }
            )
            continue

        df = df.sort_values("date")
        research = _safe_call(lambda df=df: build_single_asset_research(df), {})
        asset_news = _safe_call(
            lambda symbol=symbol, research=research: build_asset_news_research(
                all_news,
                asset_symbol=symbol,
                technical_score=research.get("score"),
                days=7,
            ),
            {},
        )
        asset_macro = _safe_call(
            lambda symbol=symbol, research=research: build_asset_macro_research(
                all_macro,
                asset_symbol=symbol,
                technical_score=research.get("score"),
            ),
            {},
        )

        name = symbol
        if "name" in df.columns:
            names = df["name"].dropna().astype(str)
            if not names.empty:
                name = names.iloc[-1]

        assets_context.append(
            {
                "symbol": symbol,
                "name": name,
                "latest_snapshot": _latest_asset_snapshot(df),
                "performance": _asset_recent_performance(perf_df, symbol),
                "technical_research": _to_jsonable(
                    {
                        "score": research.get("score"),
                        "grade": research.get("grade"),
                        "trend_label": research.get("trend_label"),
                        "risk_label": research.get("risk_label"),
                        "volatility_label": research.get("volatility_label"),
                        "momentum_label": research.get("momentum_label"),
                        "summary": research.get("summary"),
                        "action_hint": research.get("action_hint"),
                        "watch_points": research.get("watch_points", [])[:4],
                    }
                ),
                "news_research": _compact_news_context(asset_news),
                "macro_research": _compact_macro_context(asset_macro),
            }
        )

    context = {
        "scope": "multi_asset",
        "symbols": symbols,
        "assets": _to_jsonable(assets_context),
        "data_note": "以上事实包来自 RAbot 本地行情数据库、新闻数据库、宏观数据库与规则层研究模块。LLM 回答必须基于这些事实，不得编造实时数据。",
    }

    return ContextBuildResult(True, context, "")