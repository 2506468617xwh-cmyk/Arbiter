from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import HTTPException

from backend.schemas.fund import (
    FundAnalysisResponse,
    FundChatResponse,
    FundHistoryResponse,
    FundInfoResponse,
    FundQuoteResponse,
    FundSearchResponse,
)
from RAbot.funds.akshare_fund_provider import AKShareFundProvider
from RAbot.funds.fund_analysis import analyze_fund
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol
from RAbot.funds.longbridge_fund_provider import LongbridgeFundProvider
from RAbot.funds.tushare_fund_provider import TushareFundProvider
from RAbot.funds.yfinance_fund_provider import YFinanceFundProvider


FORMAT_HINT = "无法识别基金/ETF代码，请使用 510300.SH / 000001.OF / QQQ.US / 2800.HK 这种格式。"


def _validate_symbol(symbol: str) -> tuple[str, str, str]:
    normalized = normalize_fund_symbol(symbol)
    market = detect_fund_market(normalized)
    fund_type = detect_fund_type(normalized)
    if market == "UNKNOWN" or fund_type == "UNKNOWN":
        raise HTTPException(status_code=400, detail=FORMAT_HINT)
    return normalized, market, fund_type


def _providers_for(fund_type: str) -> list[Any]:
    if fund_type == "CN_ETF":
        return [TushareFundProvider(), AKShareFundProvider()]
    if fund_type == "CN_MUTUAL_FUND":
        return [AKShareFundProvider(), TushareFundProvider()]
    return [LongbridgeFundProvider(), YFinanceFundProvider()]


def get_fund_info(symbol: str) -> FundInfoResponse:
    normalized, _, fund_type = _validate_symbol(symbol)
    warnings: list[str] = []
    selected = None
    for provider in _providers_for(fund_type):
        info = provider.get_info(normalized)
        warnings.extend(getattr(info, "warnings", []) or [])
        warnings.extend(getattr(provider, "warnings", []) or [])
        if selected is None or info.name:
            selected = info
        if info.name:
            break
    if selected is None:
        selected = _providers_for(fund_type)[0].get_info(normalized)
    data = asdict(selected)
    data["warnings"] = _dedupe(warnings)
    return FundInfoResponse(**data)


def get_fund_quote(symbol: str) -> FundQuoteResponse:
    normalized, _, fund_type = _validate_symbol(symbol)
    warnings: list[str] = []
    selected = None
    for index, provider in enumerate(_providers_for(fund_type)):
        quote = provider.get_quote(normalized)
        warnings.extend(getattr(quote, "warnings", []) or [])
        warnings.extend(getattr(provider, "warnings", []) or [])
        selected = quote if selected is None else selected
        if quote.last_price is not None or quote.nav is not None:
            selected = quote
            if index > 0:
                warnings.append(f"{provider.source} 已作为 fallback 返回行情/净值。")
            break
    data = asdict(selected)
    data["warnings"] = _dedupe(warnings)
    return FundQuoteResponse(**data)


def get_fund_history(symbol: str, period: str = "day", count: int = 500) -> FundHistoryResponse:
    normalized, market, fund_type = _validate_symbol(symbol)
    count = max(20, min(int(count or 500), 900))
    warnings: list[str] = []
    bars = []
    source = None
    for index, provider in enumerate(_providers_for(fund_type)):
        bars = provider.get_history(normalized, period=period, count=count)
        warnings.extend(getattr(provider, "warnings", []) or [])
        if bars:
            source = provider.source
            if index > 0:
                warnings.append(f"{provider.source} 已作为 fallback 返回历史行情/净值。")
            break
    if not bars:
        warnings.append("当前数据源未返回可用历史行情或净值序列。")
    return FundHistoryResponse(
        symbol=normalized,
        market=market,
        fund_type=fund_type,
        period=period,
        count=len(bars),
        items=[asdict(bar) for bar in bars],
        source=source,
        warnings=_dedupe(warnings),
    )


def get_fund_analysis(symbol: str, use_llm: bool = True, count: int = 500) -> FundAnalysisResponse:
    normalized, _, _ = _validate_symbol(symbol)
    try:
        result = analyze_fund(normalized, use_llm=use_llm, count=count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FundAnalysisResponse(**result.to_dict())


def search_funds(keyword: str) -> FundSearchResponse:
    keyword = str(keyword or "").strip()
    warnings: list[str] = []
    items: list[dict[str, Any]] = []
    for provider in [TushareFundProvider(), AKShareFundProvider(), LongbridgeFundProvider(), YFinanceFundProvider()]:
        try:
            items.extend(provider.search_fund(keyword))
            warnings.extend(getattr(provider, "warnings", []) or [])
        except Exception as exc:
            warnings.append(f"{provider.source} 搜索不可用：{type(exc).__name__}: {exc}")
    if not items:
        items.extend(YFinanceFundProvider().search_fund(keyword))
    seen = set()
    unique = []
    for item in items:
        symbol = item.get("symbol")
        if symbol and symbol not in seen:
            seen.add(symbol)
            unique.append(item)
    return FundSearchResponse(items=unique[:40], warnings=_dedupe(warnings))


def answer_fund_question(symbol: str, question: str, use_llm: bool = True) -> FundChatResponse:
    normalized, _, _ = _validate_symbol(symbol)
    question = str(question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="请先输入基金/ETF研究问题。")
    result = analyze_fund(normalized, use_llm=False, count=500)
    fallback = (
        f"{result.symbol} 当前基金/ETF研究观察：{result.allocation_summary}"
        f"{result.performance_summary} 风险侧看，{result.risk_summary}"
        f"{result.dca_summary} 本回答仅用于研究和学习，不构成投资建议。"
    )
    warnings = list(result.warnings or [])
    if not use_llm:
        warnings.append("本次请求未调用大模型，返回规则型基金/ETF研究回答。")
        return FundChatResponse(ok=False, text=fallback, model=None, scope="fund", asset_symbol=result.symbol, symbols=[], context=result.to_dict(), warnings=_dedupe(warnings))
    try:
        from RAbot.llm.llm_client import RAbotLLMClient

        client = RAbotLLMClient(max_tokens=900, temperature=0.25)
        if not client.is_available():
            warnings.append("未检测到 DEEPSEEK_API_KEY，返回规则型基金/ETF研究回答。")
            return FundChatResponse(ok=False, text=fallback, model=None, scope="fund", asset_symbol=result.symbol, symbols=[], context=result.to_dict(), warnings=_dedupe(warnings))
        llm_result = client.generate(
            system_prompt="你是 RAbot 基金与 ETF 研究助手。只基于给定上下文回答，不给买卖建议，不编造数据，必须提示关键风险。",
            user_prompt=(
                f"用户问题：{question}\n"
                f"基金/ETF分析上下文：{result.to_dict()}\n"
                "请用中文回答，重点给研究观察、证据、数据缺口和风险提示。不要输出买入/卖出建议。"
            ),
        )
        if llm_result.ok and llm_result.text.strip():
            return FundChatResponse(ok=True, text=llm_result.text.strip(), model=llm_result.model, scope="fund", asset_symbol=result.symbol, symbols=[], context=result.to_dict(), warnings=_dedupe(warnings))
        warnings.append(f"LLM 基金/ETF问答失败：{llm_result.error or llm_result.text}")
    except Exception as exc:
        warnings.append(f"LLM 基金/ETF问答调用失败：{type(exc).__name__}: {exc}")
    return FundChatResponse(ok=False, text=fallback, model=None, scope="fund", asset_symbol=result.symbol, symbols=[], context=result.to_dict(), warnings=_dedupe(warnings))


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result
