from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from RAbot.stocks.finnhub_stock_provider import FinnhubStockProvider
from RAbot.stocks.longbridge_stock_provider import LongbridgeStockProvider
from RAbot.stocks.stock_models import StockAnalysisResult, StockBar, StockQuote
from RAbot.stocks.stock_store import save_analysis, save_bars, save_quote
from RAbot.stocks.symbols import detect_market, normalize_symbol
from RAbot.stocks.tickflow_stock_provider import TickFlowStockProvider
from RAbot.stocks.tushare_stock_provider import TushareStockProvider
from RAbot.stocks.yfinance_stock_provider import YFinanceStockProvider


def analyze_stock(symbol: str, use_llm: bool = True, count: int = 250) -> StockAnalysisResult:
    normalized = normalize_symbol(symbol)
    market = detect_market(normalized)
    warnings: list[str] = []
    if market == "UNKNOWN":
        raise ValueError("无法识别股票代码，请使用 600519.SH / TSLA.US / 700.HK 这种格式。")

    quote: StockQuote | None = None
    bars: list[StockBar] = []
    benchmark_symbol, benchmark_name = _benchmark_for_market(market)
    benchmark_bars: list[StockBar] = []
    source = ""

    if market == "CN":
        tushare = TushareStockProvider()
        quote = tushare.get_quote(normalized)
        bars = tushare.get_history(normalized, count=count)
        source = tushare.source
        warnings.extend(quote.warnings)
        if not bars or (quote and quote.last_price is None):
            warnings.append("Tushare 个股数据不可用或不完整，尝试 TickFlow / yfinance 兜底。")
            quote, bars, source = _fallback_stock_data(
                normalized,
                market,
                quote,
                bars,
                source,
                [TickFlowStockProvider(), YFinanceStockProvider()],
                count,
                warnings,
            )
        benchmark_bars = tushare.get_index_history(benchmark_symbol, count=count) if benchmark_symbol else []
        if benchmark_symbol and not benchmark_bars:
            benchmark_bars = _load_external_benchmark(market, count=count)
        if benchmark_symbol and not benchmark_bars:
            warnings.append("未读取到沪深300基准走势，个股图暂无法和A股大盘对比。")
    else:
        longbridge = LongbridgeStockProvider()
        quote = longbridge.get_quote(normalized)
        bars = longbridge.get_history(normalized, count=count)
        warnings.extend(quote.warnings if quote else [])
        warnings.extend(longbridge.warnings)
        source = longbridge.source

        if not bars or (quote and quote.last_price is None):
            warnings.append("Longbridge 数据不可用或不完整，尝试 TickFlow / Finnhub / yfinance 兜底。")
            quote, bars, source = _fallback_stock_data(
                normalized,
                market,
                quote,
                bars,
                source,
                [TickFlowStockProvider(), FinnhubStockProvider(), YFinanceStockProvider()],
                count,
                warnings,
            )
        benchmark_bars = _load_external_benchmark(market, count=count)
        if benchmark_symbol and not benchmark_bars:
            warnings.append(f"未读取到{benchmark_name}基准走势，个股图暂无法和大盘对比。")

    indicators = _build_indicators(bars)
    benchmark_indicators = _benchmark_indicators(bars, benchmark_bars)
    indicators.update(benchmark_indicators)
    trend_summary = _trend_summary(quote, indicators, len(bars))
    risk_summary = _risk_summary(indicators, len(bars))
    research_summary = _research_summary(
        symbol=normalized,
        quote=quote,
        indicators=indicators,
        trend_summary=trend_summary,
        risk_summary=risk_summary,
        use_llm=use_llm,
        warnings=warnings,
    )

    result = StockAnalysisResult(
        symbol=normalized,
        name=quote.name if quote else None,
        market=market,
        currency=quote.currency if quote else _currency(market),
        quote=quote,
        bars=bars,
        benchmark_symbol=benchmark_symbol,
        benchmark_name=benchmark_name,
        benchmark_bars=benchmark_bars,
        indicators=indicators,
        trend_summary=trend_summary,
        risk_summary=risk_summary,
        research_summary=research_summary,
        warnings=_dedupe(warnings),
        source=source,
    )

    try:
        save_quote(quote)
        save_bars(normalized, bars)
        save_analysis(result)
    except Exception as exc:
        result.warnings.append(f"个股缓存写入失败：{type(exc).__name__}: {exc}")

    return result


def _fallback_stock_data(
    symbol: str,
    market: str,
    quote: StockQuote | None,
    bars: list[StockBar],
    source: str,
    providers: list[Any],
    count: int,
    warnings: list[str],
) -> tuple[StockQuote | None, list[StockBar], str]:
    current_quote = quote
    current_bars = bars
    current_source = source
    for provider in providers:
        provider_quote: StockQuote | None = None
        provider_bars: list[StockBar] = []
        need_quote = current_quote is None or current_quote.last_price is None
        need_bars = not current_bars
        if not need_quote and not need_bars:
            break
        if need_quote:
            provider_quote = provider.get_quote(symbol)
            warnings.extend(getattr(provider_quote, "warnings", []) or [])
            if provider_quote.last_price is not None:
                current_quote = provider_quote
                current_source = provider.source
        if need_bars:
            provider_bars = provider.get_history(symbol, count=count)
            warnings.extend(getattr(provider, "warnings", []) or [])
            if provider_bars:
                current_bars = provider_bars
                current_source = provider.source
        if provider_quote and provider_quote.last_price is not None:
            warnings.append(f"{provider.source} 已补齐最新行情。")
        if provider_bars:
            warnings.append(f"{provider.source} 已补齐历史 K 线。")

    if current_quote is None:
        current_quote = StockQuote(symbol=symbol, market=market, currency=_currency(market), source=current_source)
    return current_quote, current_bars, current_source


def _benchmark_for_market(market: str) -> tuple[str | None, str | None]:
    if market == "CN":
        return "000300.SH", "沪深300"
    if market == "US":
        return "^GSPC", "标普500"
    if market == "HK":
        return "^HSI", "恒生指数"
    return None, None


def _load_external_benchmark(market: str, count: int) -> list[StockBar]:
    symbol, _ = _benchmark_for_market(market)
    if not symbol:
        return []
    for provider in [TickFlowStockProvider(), FinnhubStockProvider(), YFinanceStockProvider()]:
        try:
            if isinstance(provider, YFinanceStockProvider):
                bars = provider.get_history_by_yahoo_symbol(symbol, display_symbol=symbol, count=count)
            else:
                bars = provider.get_history(symbol, count=count)
            if bars:
                return bars
        except Exception:
            continue
    return []


def _benchmark_indicators(stock_bars: list[StockBar], benchmark_bars: list[StockBar]) -> dict[str, Any]:
    if not stock_bars or not benchmark_bars:
        return {"benchmark_return_20d": None, "relative_return_20d": None, "benchmark_return_60d": None, "relative_return_60d": None}
    stock = pd.DataFrame([bar.to_dict() for bar in stock_bars]).sort_values("date")
    benchmark = pd.DataFrame([bar.to_dict() for bar in benchmark_bars]).sort_values("date")
    stock["close"] = pd.to_numeric(stock["close"], errors="coerce")
    benchmark["close"] = pd.to_numeric(benchmark["close"], errors="coerce")
    merged = stock[["date", "close"]].merge(benchmark[["date", "close"]], on="date", how="inner", suffixes=("_stock", "_benchmark"))
    if merged.empty:
        return {"benchmark_return_20d": None, "relative_return_20d": None, "benchmark_return_60d": None, "relative_return_60d": None}
    stock_close = merged["close_stock"].dropna()
    benchmark_close = merged["close_benchmark"].dropna()
    stock_20 = _period_return(stock_close, 20)
    benchmark_20 = _period_return(benchmark_close, 20)
    stock_60 = _period_return(stock_close, 60)
    benchmark_60 = _period_return(benchmark_close, 60)
    return {
        "benchmark_return_20d": benchmark_20,
        "relative_return_20d": _float(stock_20 - benchmark_20) if stock_20 is not None and benchmark_20 is not None else None,
        "benchmark_return_60d": benchmark_60,
        "relative_return_60d": _float(stock_60 - benchmark_60) if stock_60 is not None and benchmark_60 is not None else None,
    }


def _build_indicators(bars: list[StockBar]) -> dict[str, Any]:
    if not bars:
        return {}
    df = pd.DataFrame([bar.to_dict() for bar in bars]).sort_values("date")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    close = df["close"].dropna()
    if close.empty:
        return {}

    latest = close.iloc[-1]
    indicators: dict[str, Any] = {
        "latest_close": _float(latest),
        "ma20": _float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None,
        "ma60": _float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None,
        "ma120": _float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else None,
        "return_5d": _period_return(close, 5),
        "return_20d": _period_return(close, 20),
        "return_60d": _period_return(close, 60),
    }
    returns = close.pct_change().dropna()
    indicators["volatility_20d"] = _float(returns.tail(20).std() * np.sqrt(252) * 100) if len(returns) >= 20 else None
    last_120 = close.tail(120)
    running_max = last_120.cummax()
    drawdown = close / close.cummax() - 1
    indicators["max_drawdown_120d"] = _float(((last_120 / running_max) - 1).min() * 100) if len(last_120) >= 2 else _float(drawdown.min() * 100)

    volume = df["volume"].dropna()
    if len(volume) >= 21:
        avg = volume.iloc[-21:-1].mean()
        indicators["volume_ratio_20d"] = _float(volume.iloc[-1] / avg) if avg else None
    else:
        indicators["volume_ratio_20d"] = None

    return indicators


def _period_return(close: pd.Series, days: int) -> float | None:
    if len(close) <= days:
        return None
    base = close.iloc[-days - 1]
    if not base:
        return None
    return _float((close.iloc[-1] / base - 1) * 100)


def _trend_summary(quote: StockQuote | None, indicators: dict[str, Any], bar_count: int) -> str:
    if not indicators:
        return "当前历史行情不足，无法形成趋势判断。"
    latest = indicators.get("latest_close") or (quote.last_price if quote else None)
    above = []
    for key in ["ma20", "ma60", "ma120"]:
        value = indicators.get(key)
        if latest is not None and value is not None and latest > value:
            above.append(key.upper())
    short_return = indicators.get("return_20d")
    direction = "偏强" if short_return is not None and short_return > 3 else "偏弱" if short_return is not None and short_return < -3 else "震荡"
    return f"样本包含 {bar_count} 根日线，价格位于 {len(above)}/3 条主要均线上方，近20日表现{direction}。"


def _risk_summary(indicators: dict[str, Any], bar_count: int) -> str:
    risks = []
    if bar_count < 120:
        risks.append("历史样本不足 120 日，回撤和中期均线判断置信度有限")
    vol = indicators.get("volatility_20d")
    if vol is not None and vol > 45:
        risks.append("20日年化波动率较高")
    drawdown = indicators.get("max_drawdown_120d")
    if drawdown is not None and drawdown < -25:
        risks.append("近120日最大回撤较深")
    vr = indicators.get("volume_ratio_20d")
    if vr is not None and vr > 2:
        risks.append("最近成交量显著高于20日均量")
    return "；".join(risks) if risks else "当前未识别到极端波动、深度回撤或成交量异常，但仍需结合基本面和事件风险。"


def _research_summary(
    *,
    symbol: str,
    quote: StockQuote | None,
    indicators: dict[str, Any],
    trend_summary: str,
    risk_summary: str,
    use_llm: bool,
    warnings: list[str],
) -> str:
    fallback = (
        f"{symbol} 当前研究结论：{trend_summary} 风险侧看，{risk_summary}"
        " 本分析仅基于本地可读取行情和技术指标，不构成投资建议。"
    )
    if not use_llm:
        return fallback
    try:
        from RAbot.llm.llm_client import RAbotLLMClient

        client = RAbotLLMClient(max_tokens=700, temperature=0.25)
        if not client.is_available():
            warnings.append("未检测到 DEEPSEEK_API_KEY，个股研究摘要使用规则型输出。")
            return fallback
        result = client.generate(
            system_prompt="你是 RAbot 个股研究分析师。只基于给定事实分析，不给买卖建议，不编造数据。",
            user_prompt=(
                f"股票：{symbol}\n"
                f"行情：{quote.to_dict() if quote else {}}\n"
                f"指标：{indicators}\n"
                f"趋势摘要：{trend_summary}\n"
                f"风险摘要：{risk_summary}\n"
                "请用中文输出 180-300 字个股研究摘要，结构为核心判断、支撑因素、风险提示。"
            ),
        )
        if result.ok and result.text.strip():
            return result.text.strip()
        warnings.append(f"LLM 个股摘要生成失败：{result.error or result.text}")
    except Exception as exc:
        warnings.append(f"LLM 个股摘要调用失败：{type(exc).__name__}: {exc}")
    return fallback


def _float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _currency(market: str) -> str | None:
    return "CNY" if market == "CN" else "USD" if market == "US" else "HKD" if market == "HK" else None


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
