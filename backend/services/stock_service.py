from __future__ import annotations

from dataclasses import asdict

from fastapi import HTTPException

from backend.schemas.stock import (
    StockAnalysisResponse,
    StockHistoryResponse,
    StockQuoteResponse,
    StockSearchResponse,
)
from RAbot.stocks.longbridge_stock_provider import LongbridgeStockProvider
from RAbot.stocks.stock_analysis import analyze_stock
from RAbot.stocks.symbols import detect_market, normalize_symbol
from RAbot.stocks.tushare_stock_provider import TushareStockProvider
from RAbot.stocks.yfinance_stock_provider import YFinanceStockProvider


def _validate_symbol(symbol: str) -> tuple[str, str]:
    normalized = normalize_symbol(symbol)
    market = detect_market(normalized)
    if market == "UNKNOWN":
        raise HTTPException(status_code=400, detail="无法识别股票代码，请使用 600519.SH / TSLA.US / 700.HK 这种格式。")
    return normalized, market


def _provider_for_quote(symbol: str, market: str):
    if market == "CN":
        return TushareStockProvider()
    return LongbridgeStockProvider()


def get_stock_quote(symbol: str) -> StockQuoteResponse:
    normalized, market = _validate_symbol(symbol)
    provider = _provider_for_quote(normalized, market)
    quote = provider.get_quote(normalized)
    if market in {"US", "HK"} and quote.last_price is None:
        fallback = YFinanceStockProvider()
        fallback_quote = fallback.get_quote(normalized)
        fallback_quote.warnings = quote.warnings + ["Longbridge 行情不可用，已尝试 yfinance fallback。"] + fallback_quote.warnings
        quote = fallback_quote
    return StockQuoteResponse(**asdict(quote))


def get_stock_history(symbol: str, period: str = "day", count: int = 250) -> StockHistoryResponse:
    normalized, market = _validate_symbol(symbol)
    count = max(20, min(int(count or 250), 600))
    provider = _provider_for_quote(normalized, market)
    bars = provider.get_history(normalized, period=period, count=count)
    warnings = []
    source = provider.source
    if market in {"US", "HK"} and not bars:
        fallback = YFinanceStockProvider()
        bars = fallback.get_history(normalized, period=period, count=count)
        source = fallback.source if bars else source
        warnings.append("Longbridge 历史 K 线不可用，已尝试 yfinance fallback。")
    if market == "CN" and not bars:
        warnings.append("Tushare 未返回历史 K 线，请检查 TUSHARE_TOKEN 或数据权限。")
    return StockHistoryResponse(
        symbol=normalized,
        market=market,
        period=period,
        count=len(bars),
        items=[asdict(bar) for bar in bars],
        source=source,
        warnings=warnings,
    )


def get_stock_analysis(symbol: str, use_llm: bool = True, count: int = 250) -> StockAnalysisResponse:
    normalized, _ = _validate_symbol(symbol)
    try:
        result = analyze_stock(normalized, use_llm=use_llm, count=count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return StockAnalysisResponse(**result.to_dict())


def search_stocks(keyword: str) -> StockSearchResponse:
    keyword = str(keyword or "").strip()
    warnings = []
    items = []
    try:
        items.extend(TushareStockProvider().search_symbol(keyword))
    except Exception as exc:
        warnings.append(f"Tushare 搜索不可用：{type(exc).__name__}: {exc}")
    try:
        items.extend(LongbridgeStockProvider().search_symbol(keyword))
    except Exception as exc:
        warnings.append(f"Longbridge 搜索不可用：{type(exc).__name__}: {exc}")
    if not items:
        items.extend(YFinanceStockProvider().search_symbol(keyword))
    seen = set()
    unique = []
    for item in items:
        symbol = item.get("symbol")
        if symbol and symbol not in seen:
            seen.add(symbol)
            unique.append(item)
    return StockSearchResponse(items=unique[:30], warnings=warnings)
