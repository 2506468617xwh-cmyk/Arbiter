from __future__ import annotations

from typing import Any

import pandas as pd

from backend.schemas.research_view import AssetResearchResponse, MultiAssetRequest, MultiAssetResponse
from backend.services.macro_service import get_macro_overview, read_macro_series_frame
from backend.services.market_service import (
    _read_index_daily,
    get_market_performance,
    get_market_timeseries,
)
from backend.services.news_service import get_latest_news


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return [_json_safe(row) for row in value.to_dict(orient="records")]
    if isinstance(value, pd.Series):
        return _json_safe(value.to_dict())
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def get_asset_research(symbol: str, start: str | None = None, end: str | None = None) -> AssetResearchResponse:
    symbol = symbol.upper().strip()
    warnings: list[str] = []
    df, market_warnings = _read_index_daily(symbols=[symbol], start=start, end=end)
    warnings.extend(market_warnings)

    performance = get_market_performance()
    market_item = next((item for item in performance.items if item.symbol == symbol), None)

    technical: dict[str, Any] = {}
    if df.empty:
        warnings.append(f"未找到 {symbol} 的行情数据。")
    else:
        try:
            from RAbot.analysis.research_engine import build_single_asset_research

            technical = _json_safe(build_single_asset_research(df))
        except Exception as exc:
            warnings.append(f"单资产规则研究生成失败：{type(exc).__name__}: {exc}")

    news_result = get_latest_news(limit=120)
    related_news = [
        item
        for item in news_result.items
        if symbol in f"{item.title or ''} {item.summary or ''}".upper()
        or (item.summary and symbol in item.summary.upper())
    ][:12]
    warnings.extend(news_result.warnings)

    macro_result = get_macro_overview(limit=80)
    warnings.extend(macro_result.warnings)
    related_macro = macro_result.items[:12]

    news_research: dict[str, Any] = {}
    macro_research: dict[str, Any] = {}
    try:
        from RAbot.analysis.news_research import build_asset_news_research

        news_df = pd.DataFrame([item.model_dump() for item in news_result.items])
        if not news_df.empty:
            news_df = news_df.rename(columns={"source": "source_name", "url": "link"})
        news_research = _json_safe(build_asset_news_research(news_df, asset_symbol=symbol, technical_score=technical.get("score")))
    except Exception as exc:
        warnings.append(f"新闻面研究生成失败：{type(exc).__name__}: {exc}")

    try:
        from RAbot.analysis.macro_research import build_asset_macro_research

        macro_df, macro_series_warnings = read_macro_series_frame()
        warnings.extend(macro_series_warnings)
        macro_research = _json_safe(build_asset_macro_research(macro_df, asset_symbol=symbol, technical_score=technical.get("score")))
    except Exception as exc:
        warnings.append(f"宏观面研究生成失败：{type(exc).__name__}: {exc}")

    series = get_market_timeseries([symbol], start=start, end=end).items[-260:]
    latest_date = market_item.latest_date if market_item else None
    name = market_item.name if market_item else symbol
    return AssetResearchResponse(
        symbol=symbol,
        name=name,
        latest_date=latest_date,
        technical=technical,
        market=market_item,
        news=news_research,
        macro=macro_research,
        series=series,
        related_news=related_news,
        related_macro=related_macro,
        warnings=warnings,
    )


def get_multi_asset_research(request: MultiAssetRequest) -> MultiAssetResponse:
    symbols = [symbol.upper().strip() for symbol in request.symbols if symbol.strip()]
    warnings: list[str] = []
    if not symbols:
        warnings.append("请至少选择一个资产。")
        return MultiAssetResponse(warnings=warnings)

    normalized = get_market_timeseries(symbols, start=request.start, end=request.end, normalize=True)
    warnings.extend(normalized.warnings)

    perf = get_market_performance()
    performance = [item for item in perf.items if item.symbol in symbols]

    df, df_warnings = _read_index_daily(symbols=symbols, start=request.start, end=request.end)
    warnings.extend(df_warnings)
    correlation: list[dict[str, Any]] = []
    if not df.empty:
        pivot = df.pivot_table(index="date", columns="symbol", values="close").sort_index()
        returns = pivot.pct_change().dropna(how="all")
        if not returns.empty:
            corr = returns.corr()
            for row_symbol in corr.index:
                row = {"symbol": row_symbol}
                for col_symbol in corr.columns:
                    value = corr.loc[row_symbol, col_symbol]
                    row[str(col_symbol)] = None if pd.isna(value) else float(value)
                correlation.append(row)

    return MultiAssetResponse(
        symbols=symbols,
        normalized_series=normalized.items,
        performance=performance,
        correlation=correlation,
        warnings=warnings,
    )
