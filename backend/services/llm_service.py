from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from backend.schemas.llm import LLMChatRequest, LLMQuickSummaryRequest, LLMResponse, PetSummaryRequest
from backend.schemas.research_view import MultiAssetRequest
from backend.services.overview_service import build_overview
from backend.services.research_view_service import get_asset_research, get_multi_asset_research


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _load_env() -> None:
    try:
        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        pass


def _fallback_summary(request: LLMQuickSummaryRequest) -> LLMResponse:
    warnings = ["当前未调用大模型，返回本地规则层一句话摘要。"]
    scope = request.scope

    if scope == "single_asset" and request.asset_symbol:
        data = get_asset_research(request.asset_symbol)
        text = (
            f"{data.name or data.symbol} 当前规则层结论为："
            f"{data.technical.get('summary') if isinstance(data.technical, dict) else '本地数据不足，暂不能形成有效判断'}"
        )
        return LLMResponse(
            ok=False,
            text=text,
            model=None,
            scope=scope,
            asset_symbol=data.symbol,
            symbols=[],
            context=None,
            warnings=warnings + data.warnings,
        )

    if scope == "multi_asset" and request.symbols:
        data = get_multi_asset_research(MultiAssetRequest(symbols=request.symbols))
        text = f"多资产组合已读取 {len(data.symbols)} 个标的，当前可先对比走势、回撤和相关性，再决定是否调用大模型做综合判断。"
        return LLMResponse(
            ok=False,
            text=text,
            model=None,
            scope=scope,
            symbols=data.symbols,
            context=None,
            warnings=warnings + data.warnings,
        )

    overview = build_overview()
    text = f"{overview.market_summary} {overview.news_summary} {overview.macro_summary}"
    return LLMResponse(
        ok=False,
        text=text,
        model=None,
        scope="market",
        symbols=[],
        context=None,
        warnings=warnings + overview.warnings,
    )


def generate_quick_summary(request: LLMQuickSummaryRequest) -> LLMResponse:
    if not request.use_llm:
        return _fallback_summary(request)

    _load_env()
    try:
        from RAbot.llm.research_chat import RAbotResearchChat
    except Exception as exc:
        fallback = _fallback_summary(request)
        fallback.warnings.append(f"RAbotResearchChat 导入失败：{type(exc).__name__}: {exc}")
        return fallback

    chat = RAbotResearchChat()
    scope = request.scope

    if scope == "single_asset":
        symbol = (request.asset_symbol or "").upper().strip()
        if not symbol:
            return LLMResponse(ok=False, text="请先指定单资产代码。", scope=scope, warnings=["缺少 asset_symbol。"])
        result = chat.answer_question(
            question="请基于 RAbot 本地事实包，用一句中文概括当前这个资产最重要的研究结论，不超过 80 个字。",
            scope="single_asset",
            asset_symbol=symbol,
        )
        return _to_response(result, scope=scope, asset_symbol=symbol, symbols=[])

    if scope == "multi_asset":
        symbols = [symbol.upper().strip() for symbol in request.symbols if symbol.strip()]
        if not symbols:
            return LLMResponse(ok=False, text="请至少选择一个多资产标的。", scope=scope, warnings=["缺少 symbols。"])
        result = chat.answer_question(
            question="请基于 RAbot 本地事实包，用一句中文概括这组资产当前最重要的相对强弱或风险线索，不超过 100 个字。",
            scope="multi_asset",
            symbols=symbols,
        )
        return _to_response(result, scope=scope, asset_symbol=None, symbols=symbols)

    result = chat.answer_question(
        question="请基于 RAbot 本地事实包，用一句中文概括当前全市场最重要的研究结论，不超过 100 个字。",
        scope="market",
    )
    return _to_response(result, scope="market", asset_symbol=None, symbols=[])


def answer_research_question(request: LLMChatRequest) -> LLMResponse:
    question = request.question.strip()
    if not question:
        return LLMResponse(ok=False, text="请先输入问题。", scope=request.scope, warnings=["问题为空。"])

    if not request.use_llm:
        return LLMResponse(
            ok=False,
            text="当前已关闭大模型调用。请打开右侧模型开关后再进行 AI 研究对话。",
            scope=request.scope,
            asset_symbol=request.asset_symbol,
            symbols=request.symbols,
            warnings=["本次请求未调用大模型。"],
        )

    _load_env()
    try:
        from RAbot.llm.research_chat import RAbotResearchChat
    except Exception as exc:
        return LLMResponse(
            ok=False,
            text=f"AI 研究对话模块导入失败：{type(exc).__name__}: {exc}",
            scope=request.scope,
            asset_symbol=request.asset_symbol,
            symbols=request.symbols,
            warnings=["请检查 src/RAbot/llm/research_chat.py 和 openai 依赖。"],
        )

    chat = RAbotResearchChat()
    scope = request.scope
    result = chat.answer_question(
        question=question,
        scope=scope,
        asset_symbol=(request.asset_symbol or "").upper().strip() if request.asset_symbol else None,
        symbols=[symbol.upper().strip() for symbol in request.symbols if symbol.strip()],
    )
    return _to_response(
        result,
        scope=scope,
        asset_symbol=(request.asset_symbol or "").upper().strip() if request.asset_symbol else None,
        symbols=[symbol.upper().strip() for symbol in request.symbols if symbol.strip()],
    )


def _compact_pet_text(text: str) -> str:
    cleaned = " ".join((text or "").strip().split())
    if not cleaned:
        return ""
    for marker in ("。", "！", "？", ".", "!", "?"):
        if marker in cleaned:
            cleaned = cleaned.split(marker, 1)[0] + marker
            break
    return cleaned[:80]


def _pet_fallback(request: PetSummaryRequest, warnings: list[str] | None = None) -> LLMResponse:
    context = request.context or {}
    text = "这一页数据还不够，我建议先刷新一下。"
    if context:
        title = str(context.get("title") or context.get("page_title") or request.page_name or "当前页面")
        text = f"{title}已有可读上下文，适合先观察数据更新时间、风险提示和主要变化。"
    return LLMResponse(
        ok=False,
        text=_compact_pet_text(text),
        model=None,
        scope="pet",
        asset_symbol=None,
        symbols=[],
        context=context,
        warnings=warnings or ["汉堡未调用大模型，已返回规则型一句话。"],
    )


def generate_pet_summary(request: PetSummaryRequest) -> LLMResponse:
    if not request.use_llm:
        return _pet_fallback(request)

    _load_env()
    context = request.context or {}
    if not context:
        return _pet_fallback(request, ["这一页数据还不够，未调用大模型。"])

    try:
        from RAbot.llm.llm_client import RAbotLLMClient
    except Exception as exc:
        return _pet_fallback(request, [f"汉堡 LLM 客户端导入失败：{type(exc).__name__}: {exc}"])

    client = RAbotLLMClient(max_tokens=120, temperature=0.2)
    if not client.is_available():
        return _pet_fallback(request, ["未检测到可用的大模型配置，已返回规则型一句话。"])

    context_text = str(context)[:3000]
    if request.mode == "market":
        user_prompt = (
            "请基于以下市场数据，用中文输出一句不超过80字的市场总结。"
            "不要给投资建议，不要输出买入卖出结论，只总结市场状态、风格和风险。"
        )
    else:
        user_prompt = (
            "请基于当前页面信息，用中文输出一句不超过80字的总结。"
            "你是 RAbot 的汉堡，只用一句话告诉用户这一页最值得关注的变化。"
        )

    try:
        result = client.generate(
            system_prompt="你是 RAbot 的汉堡研究助手。只输出一句中文，最多80字，不给买卖建议，不编造缺失数据。",
            user_prompt=f"{user_prompt}\n\n页面：{request.page_name}\n\n上下文：\n{context_text}",
        )
    except Exception as exc:
        return _pet_fallback(request, [f"汉堡 LLM 调用失败：{type(exc).__name__}: {exc}"])

    if result.ok and result.text.strip():
        return LLMResponse(
            ok=True,
            text=_compact_pet_text(result.text),
            model=result.model,
            scope="pet",
            asset_symbol=None,
            symbols=[],
            context=context,
            warnings=[],
        )
    return _pet_fallback(request, [f"汉堡 LLM 未返回有效结果：{result.error or result.text}"])


def _to_response(result: Any, *, scope: str, asset_symbol: str | None, symbols: list[str]) -> LLMResponse:
    warnings: list[str] = []
    if not getattr(result, "ok", False):
        warnings.append("大模型未返回成功结果，页面展示的是模块返回的错误或提示。")
    return LLMResponse(
        ok=bool(getattr(result, "ok", False)),
        text=str(getattr(result, "text", "") or ""),
        model=getattr(result, "model", None),
        scope=scope,
        asset_symbol=asset_symbol,
        symbols=symbols,
        context=getattr(result, "context", None),
        warnings=warnings,
    )
