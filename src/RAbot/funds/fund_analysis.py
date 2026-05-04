from __future__ import annotations

from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from RAbot.funds.akshare_fund_provider import AKShareFundProvider
from RAbot.funds.fund_models import FundAnalysisResult, FundBar, FundInfo, FundQuote
from RAbot.funds.fund_store import save_analysis, save_bars, save_info, save_quote
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol
from RAbot.funds.longbridge_fund_provider import LongbridgeFundProvider
from RAbot.funds.tushare_fund_provider import TushareFundProvider
from RAbot.funds.yfinance_fund_provider import YFinanceFundProvider
from RAbot.stocks.stock_models import StockBar
from RAbot.stocks.tushare_stock_provider import TushareStockProvider
from RAbot.stocks.yfinance_stock_provider import YFinanceStockProvider


DISCLAIMER = "本分析仅用于研究和学习，不构成任何投资建议；基金/ETF 可能存在净值误差、折溢价、汇率、流动性和跟踪误差风险。"


def analyze_fund(symbol: str, use_llm: bool = True, count: int = 500) -> FundAnalysisResult:
    normalized = normalize_fund_symbol(symbol)
    market = detect_fund_market(normalized)
    fund_type = detect_fund_type(normalized)
    if market == "UNKNOWN" or fund_type == "UNKNOWN":
        raise ValueError("无法识别基金/ETF代码，请使用 510300.SH / 000001.OF / QQQ.US / 2800.HK 这种格式。")

    count = max(60, min(int(count or 500), 900))
    warnings: list[str] = []
    info: FundInfo | None = None
    quote: FundQuote | None = None
    bars: list[FundBar] = []
    source = ""

    if fund_type == "CN_ETF":
        primary = TushareFundProvider()
        fallback = AKShareFundProvider()
        info, quote, bars, source = _load_with_fallback(normalized, primary, fallback, count, warnings, "A 股 ETF 优先使用 Tushare，当前已尝试 AKShare fallback。")
    elif fund_type == "CN_MUTUAL_FUND":
        primary = AKShareFundProvider()
        fallback = TushareFundProvider()
        info, quote, bars, source = _load_with_fallback(normalized, primary, fallback, count, warnings, "公募基金净值优先使用 AKShare，当前已尝试 Tushare fallback。")
    else:
        primary = LongbridgeFundProvider()
        fallback = YFinanceFundProvider()
        info, quote, bars, source = _load_with_fallback(normalized, primary, fallback, count, warnings, "Longbridge ETF 数据不可用或不完整，已尝试 yfinance fallback。")

    if quote is None:
        quote = FundQuote(symbol=normalized, market=market, fund_type=fund_type, currency=_currency(market), source=source, warnings=[])
    if info is None:
        info = FundInfo(symbol=normalized, market=market, fund_type=fund_type, currency=quote.currency or _currency(market), source=source, warnings=[])

    name = info.name or quote.name
    indicators = _build_indicators(bars)
    benchmark_symbol, benchmark_name = _benchmark_for_fund(normalized, market, fund_type, name, info.benchmark, info.asset_class)
    benchmark_bars = _load_benchmark_bars(benchmark_symbol, market, count)
    if benchmark_symbol and not benchmark_bars:
        warnings.append(f"未读取到 {benchmark_name or benchmark_symbol} 基准走势，基金走势图暂无法叠加大盘对比。")
    if info.benchmark:
        indicators["tracking_error"] = None
        warnings.append("已识别 benchmark 字段，但暂未接入基准收益序列，tracking_error 预留为空。")
    else:
        indicators["tracking_error"] = None
        warnings.append("当前未取得可用 benchmark，tracking_error 暂为空。")

    allocation_summary = _allocation_summary(normalized, name, fund_type, info.benchmark, info.asset_class)
    performance_summary = _performance_summary(indicators, len(bars))
    risk_summary = _risk_summary(normalized, fund_type, indicators, quote, bars)
    liquidity_summary = _liquidity_summary(indicators, quote)
    dca_summary = _dca_summary(fund_type, allocation_summary, indicators, len(bars))
    research_summary = _research_summary(
        symbol=normalized,
        name=name,
        fund_type=fund_type,
        info=info,
        quote=quote,
        indicators=indicators,
        allocation_summary=allocation_summary,
        performance_summary=performance_summary,
        risk_summary=risk_summary,
        liquidity_summary=liquidity_summary,
        dca_summary=dca_summary,
        use_llm=use_llm,
        warnings=warnings,
    )

    result = FundAnalysisResult(
        symbol=normalized,
        name=name,
        market=market,
        fund_type=fund_type,
        currency=quote.currency or info.currency or _currency(market),
        info=info,
        quote=quote,
        bars=bars,
        indicators=indicators,
        allocation_summary=allocation_summary,
        performance_summary=performance_summary,
        risk_summary=risk_summary,
        liquidity_summary=liquidity_summary,
        dca_summary=dca_summary,
        research_summary=research_summary,
        warnings=_dedupe(warnings + info.warnings + quote.warnings + [DISCLAIMER]),
        source=source,
        benchmark_symbol=benchmark_symbol,
        benchmark_name=benchmark_name,
        benchmark_bars=benchmark_bars,
    )

    try:
        save_info(info)
        save_quote(quote)
        save_bars(normalized, bars)
        save_analysis(result)
    except Exception as exc:
        result.warnings.append(f"基金/ETF 缓存写入失败：{type(exc).__name__}: {exc}")
    return result


def _load_with_fallback(symbol: str, primary: Any, fallback: Any, count: int, warnings: list[str], fallback_message: str) -> tuple[FundInfo | None, FundQuote | None, list[FundBar], str]:
    info = primary.get_info(symbol)
    quote = primary.get_quote(symbol)
    bars = primary.get_history(symbol, count=count)
    warnings.extend(getattr(info, "warnings", []) or [])
    warnings.extend(getattr(quote, "warnings", []) or [])
    warnings.extend(getattr(primary, "warnings", []) or [])
    source = primary.source

    needs_fallback = not bars or quote is None or (quote.last_price is None and quote.nav is None)
    if needs_fallback:
        warnings.append(fallback_message)
        fb_info = fallback.get_info(symbol)
        fb_quote = fallback.get_quote(symbol)
        fb_bars = fallback.get_history(symbol, count=count)
        warnings.extend(getattr(fb_info, "warnings", []) or [])
        warnings.extend(getattr(fb_quote, "warnings", []) or [])
        warnings.extend(getattr(fallback, "warnings", []) or [])
        if not info or not info.name:
            info = fb_info
        if (quote is None or (quote.last_price is None and quote.nav is None)) and fb_quote:
            quote = fb_quote
            source = fallback.source
        if not bars and fb_bars:
            bars = fb_bars
            source = fallback.source
        if fb_bars or (fb_quote and (fb_quote.last_price is not None or fb_quote.nav is not None)):
            warnings.append(f"{fallback.source} 已补齐部分基金/ETF 数据。")

    return info, quote, bars, source


def _build_indicators(bars: list[FundBar]) -> dict[str, Any]:
    if not bars:
        return {}
    df = pd.DataFrame([bar.to_dict() for bar in bars]).sort_values("date")
    price_col = "close"
    if df["close"].isna().all() and "nav" in df:
        price_col = "nav"
    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    close = df[price_col].dropna()
    if close.empty:
        return {}

    returns = close.pct_change().dropna()
    latest = close.iloc[-1]
    ytd_base = _ytd_base(df, price_col)
    indicators: dict[str, Any] = {
        "latest_close": _float(latest),
        "return_1m": _period_return(close, 21),
        "return_3m": _period_return(close, 63),
        "return_6m": _period_return(close, 126),
        "return_1y": _period_return(close, 252),
        "return_ytd": _float((latest / ytd_base - 1) * 100) if ytd_base not in (None, 0) else None,
        "ma20": _float(close.rolling(20).mean().iloc[-1]) if len(close) >= 20 else None,
        "ma60": _float(close.rolling(60).mean().iloc[-1]) if len(close) >= 60 else None,
        "ma120": _float(close.rolling(120).mean().iloc[-1]) if len(close) >= 120 else None,
    }
    if len(close) >= 2:
        total_return = close.iloc[-1] / close.iloc[0] - 1
        years = max(len(close) / 252, 1 / 252)
        indicators["annualized_return"] = _float(((1 + total_return) ** (1 / years) - 1) * 100)
    else:
        indicators["annualized_return"] = None
    indicators["annualized_volatility"] = _float(returns.std() * np.sqrt(252) * 100) if len(returns) >= 20 else None
    last_1y = close.tail(252)
    indicators["max_drawdown_1y"] = _float(((last_1y / last_1y.cummax()) - 1).min() * 100) if len(last_1y) >= 2 else None
    vol = indicators.get("annualized_volatility")
    ann = indicators.get("annualized_return")
    indicators["sharpe_ratio_simple"] = _float((ann or 0) / vol) if vol not in (None, 0) and ann is not None else None

    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
        indicators["volume_avg_20d"] = _float(df["volume"].dropna().tail(20).mean()) if df["volume"].notna().any() else None
    else:
        indicators["volume_avg_20d"] = None
    if "turnover" in df.columns:
        df["turnover"] = pd.to_numeric(df["turnover"], errors="coerce")
        indicators["turnover_avg_20d"] = _float(df["turnover"].dropna().tail(20).mean()) if df["turnover"].notna().any() else None
    else:
        indicators["turnover_avg_20d"] = None
    indicators["liquidity_score"] = _liquidity_score(indicators.get("turnover_avg_20d"), indicators.get("volume_avg_20d"))
    return indicators


def _benchmark_for_fund(symbol: str, market: str, fund_type: str, name: str | None, benchmark: str | None, asset_class: str | None) -> tuple[str | None, str | None]:
    text = " ".join([symbol, name or "", benchmark or "", asset_class or ""]).upper()
    if "NASDAQ" in text or "QQQ" in text or "纳指" in text or "513100" in text:
        return "^IXIC", "纳斯达克综合指数"
    if "S&P" in text or "SPY" in text or "VOO" in text or "IVV" in text or "标普" in text:
        return "^GSPC", "标普500"
    if "HANG SENG" in text or "HSI" in text or "2800" in text or "恒生" in text:
        return "^HSI", "恒生指数"
    if "GOLD" in text or "黄金" in text or "GLD" in text or "518880" in text:
        return "GC=F", "COMEX黄金"
    if "TLT" in text or "BOND" in text or "TREASURY" in text or "债" in text:
        return "^TNX", "美国10年期国债收益率"
    if market == "CN":
        return "000300.SH", "沪深300"
    if market == "US":
        return "^GSPC", "标普500"
    if market == "HK":
        return "^HSI", "恒生指数"
    return None, None


def _load_benchmark_bars(symbol: str | None, market: str, count: int) -> list[FundBar]:
    if not symbol:
        return []
    stock_bars: list[StockBar] = []
    try:
        if market == "CN" and symbol.endswith((".SH", ".SZ")):
            stock_bars = TushareStockProvider().get_index_history(symbol, count=count)
        else:
            stock_bars = YFinanceStockProvider().get_history_by_yahoo_symbol(symbol, display_symbol=symbol, count=count)
    except Exception:
        stock_bars = []
    return [
        FundBar(
            symbol=bar.symbol,
            date=bar.date,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            turnover=bar.turnover,
            source=bar.source,
        )
        for bar in stock_bars
    ]


def _period_return(close: pd.Series, days: int) -> float | None:
    if len(close) <= days:
        return None
    base = close.iloc[-days - 1]
    if base in (None, 0):
        return None
    return _float((close.iloc[-1] / base - 1) * 100)


def _ytd_base(df: pd.DataFrame, price_col: str) -> float | None:
    try:
        current_year = datetime.now().year
        dated = df.copy()
        dated["date"] = pd.to_datetime(dated["date"], errors="coerce")
        rows = dated[dated["date"].dt.year == current_year][price_col].dropna()
        if not rows.empty:
            return _float(rows.iloc[0])
    except Exception:
        pass
    return None


def _liquidity_score(turnover_avg: float | None, volume_avg: float | None) -> float | None:
    if turnover_avg is None and volume_avg is None:
        return None
    # 优先使用成交额（更能反映真实流动性），成交额为 0 时回退到成交量
    value = turnover_avg if (turnover_avg is not None and turnover_avg > 0) else volume_avg
    if value is None:
        return None
    if value >= 100000000:
        return 95.0
    if value >= 30000000:
        return 80.0
    if value >= 5000000:
        return 60.0
    if value >= 1000000:
        return 40.0
    return 25.0


def _allocation_summary(symbol: str, name: str | None, fund_type: str, benchmark: str | None, asset_class: str | None) -> str:
    text = " ".join([symbol, name or "", benchmark or "", asset_class or ""]).upper()
    if "TQQQ" in text or "2X" in text or "3X" in text or "ULTRA" in text:
        return "杠杆 ETF，主要用于高波动指数的短周期研究，复利损耗和回撤风险需要单独评估。"
    if "NASDAQ" in text or "QQQ" in text or "纳指" in text or "513100" in text:
        return "纳指/科技成长类 ETF，资产暴露偏美股科技与成长风格。"
    if "S&P" in text or "SPY" in text or "VOO" in text or "IVV" in text or "标普" in text:
        return "标普 500 宽基 ETF，资产暴露偏美国大盘宽基。"
    if "GOLD" in text or "GLD" in text or "黄金" in text or "518880" in text:
        return "黄金或贵金属 ETF，更多反映避险、实际利率和美元因素。"
    if "TLT" in text or "BOND" in text or "TREASURY" in text or "债" in text:
        return "债券 ETF，主要受利率预期、久期和信用环境影响。"
    if "300" in text or "500" in text or "2800" in text or "宽基" in text:
        return "宽基指数型基金/ETF，适合放在资产配置框架中观察。"
    if fund_type == "CN_MUTUAL_FUND":
        return "中国公募基金，需结合基金经理、持仓、风格漂移和净值序列进一步研究。"
    return "当前只能基于代码、名称和基准做初步资产类别判断，持仓与行业分布仍待补充。"


def _performance_summary(indicators: dict[str, Any], bar_count: int) -> str:
    if not indicators:
        return "历史行情或净值数据不足，暂不能形成收益表现判断。"
    return (
        f"样本包含 {bar_count} 个交易/净值点；近1月 { _pct(indicators.get('return_1m')) }，"
        f"近3月 { _pct(indicators.get('return_3m')) }，近6月 { _pct(indicators.get('return_6m')) }，"
        f"近1年 { _pct(indicators.get('return_1y')) }，YTD { _pct(indicators.get('return_ytd')) }。"
    )


def _risk_summary(symbol: str, fund_type: str, indicators: dict[str, Any], quote: FundQuote | None, bars: list[FundBar]) -> str:
    risks: list[str] = []
    if len(bars) < 120:
        risks.append("历史样本不足 120 个点，波动率、回撤和均线判断置信度有限")
    vol = indicators.get("annualized_volatility")
    drawdown = indicators.get("max_drawdown_1y")
    if vol is not None and vol >= 35:
        risks.append("年化波动率较高")
    if drawdown is not None and drawdown <= -25:
        risks.append("近一年最大回撤较深")
    if symbol.startswith("TQQQ") or "LEVERAGED" in (quote.name or "").upper() if quote else False:
        risks.append("杠杆 ETF 存在日内复位、复利损耗和极端回撤风险，不适合简单长期持有分析")
    if fund_type == "CN_ETF" and symbol.startswith(("513", "159", "520")):
        risks.append("跨境 ETF 可能受到汇率、额度、时区差异和折溢价影响")
    if quote and quote.premium_discount is not None and abs(quote.premium_discount) >= 2:
        risks.append(f"当前折溢价约 {quote.premium_discount:.2f}%，需关注二级市场价格偏离净值")
    liquidity = indicators.get("liquidity_score")
    if liquidity is not None and liquidity < 50:
        risks.append("流动性评分偏低，成交冲击成本可能较高")
    if not risks:
        risks.append("当前未识别到极端波动、深度回撤或显著流动性压力，但仍需结合持仓和宏观事件验证")
    return "；".join(risks) + "。"


def _liquidity_summary(indicators: dict[str, Any], quote: FundQuote | None) -> str:
    score = indicators.get("liquidity_score")
    turnover = indicators.get("turnover_avg_20d") or (quote.turnover if quote else None)
    volume = indicators.get("volume_avg_20d") or (quote.volume if quote else None)
    if score is None:
        return "当前缺少成交量/成交额数据，无法可靠判断流动性。"
    label = "较好" if score >= 80 else "中等" if score >= 50 else "偏弱"
    return f"20日平均成交量约 {_num(volume, 0)}，20日平均成交额约 {_num(turnover, 0)}，流动性评分 {score:.0f}/100，整体为{label}。"


def _dca_summary(fund_type: str, allocation: str, indicators: dict[str, Any], bar_count: int) -> str:
    if bar_count < 180:
        return "定投适配度：观察中。历史样本偏短，暂不宜仅凭当前序列判断长期定投特征。"
    vol = indicators.get("annualized_volatility")
    drawdown = indicators.get("max_drawdown_1y")
    if "杠杆" in allocation:
        return "定投适配度：偏低。杠杆 ETF 的路径依赖和复利损耗明显，需要单独风险框架研究。"
    if vol is not None and vol > 40:
        return "定投适配度：中低。波动较高，适合先做回撤承受能力和资金节奏压力测试。"
    if drawdown is not None and drawdown < -30:
        return "定投适配度：中等偏谨慎。回撤较深，适合长期观察但需重视风险预算。"
    if fund_type in {"CN_ETF", "US_ETF", "HK_ETF"} and ("宽基" in allocation or "标普" in allocation or "纳指" in allocation):
        return "定投适配度：可观察。宽基或核心指数属性较明确，但仍需关注估值、汇率、跟踪误差和流动性。"
    return "定投适配度：观察中。需要结合持仓、费率、风格稳定性和更长净值序列继续研究。"


def _research_summary(**kwargs: Any) -> str:
    fallback = (
        f"{kwargs['symbol']} 研究摘要：{kwargs['allocation_summary']}"
        f"{kwargs['performance_summary']} 风险侧看，{kwargs['risk_summary']}"
        f"{kwargs['dca_summary']} {DISCLAIMER}"
    )
    if not kwargs["use_llm"]:
        return fallback
    try:
        from RAbot.llm.llm_client import RAbotLLMClient

        client = RAbotLLMClient(max_tokens=800, temperature=0.25)
        if not client.is_available():
            kwargs["warnings"].append("未检测到 DEEPSEEK_API_KEY，基金/ETF 摘要使用规则型输出。")
            return fallback
        result = client.generate(
            system_prompt="你是 RAbot 基金与 ETF 研究分析师。只基于给定事实分析，不给买卖建议，不编造数据。",
            user_prompt=(
                f"基金/ETF：{kwargs['symbol']} {kwargs.get('name') or ''}\n"
                f"类型：{kwargs['fund_type']}\n"
                f"基础信息：{kwargs['info'].to_dict() if kwargs.get('info') else {}}\n"
                f"行情：{kwargs['quote'].to_dict() if kwargs.get('quote') else {}}\n"
                f"指标：{kwargs['indicators']}\n"
                f"资产类别：{kwargs['allocation_summary']}\n"
                f"表现：{kwargs['performance_summary']}\n"
                f"风险：{kwargs['risk_summary']}\n"
                f"流动性：{kwargs['liquidity_summary']}\n"
                f"定投观察：{kwargs['dca_summary']}\n"
                "请用中文输出 180-320 字研究摘要，包含核心观察、数据缺口和免责声明，不输出买入/卖出建议。"
            ),
        )
        if result.ok and result.text.strip():
            return result.text.strip()
        kwargs["warnings"].append(f"LLM 基金/ETF 摘要生成失败：{result.error or result.text}")
    except Exception as exc:
        kwargs["warnings"].append(f"LLM 基金/ETF 摘要调用失败：{type(exc).__name__}: {exc}")
    return fallback


def _currency(market: str) -> str | None:
    return "CNY" if market == "CN" else "USD" if market == "US" else "HKD" if market == "HK" else None


def _float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _pct(value: Any) -> str:
    value = _float(value)
    return "暂无" if value is None else f"{value:.2f}%"


def _num(value: Any, digits: int = 2) -> str:
    value = _float(value)
    if value is None:
        return "暂无"
    return f"{value:,.{digits}f}"


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
