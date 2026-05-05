"""AI 研究 �?大模型对话式投研分析"""
from __future__ import annotations

import streamlit as st

from st_pages.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def render() -> None:
    st.title("🤖 AI 研究")

    use_llm = st.session_state.get("use_llm", True)

    # ── 范围选择 ──
    scope = st.radio("研究范围", ["market", "single_asset", "multi_asset"], horizontal=True,
                     format_func=lambda s: {"market": "全市�?, "single_asset": "单资�?, "multi_asset": "多资�?}.get(s, s))

    asset_symbol = None
    symbols = []

    if scope == "single_asset":
        asset_symbol = st.text_input("资产代码", placeholder="例如: 000300.SH, QQQ.US").strip().upper() or None
        if not asset_symbol:
            st.info("请输入资产代�?)
    elif scope == "multi_asset":
        symbol_input = st.text_input("资产代码（逗号分隔�?, placeholder="例如: 000300.SH, QQQ.US, 510300.SH")
        if symbol_input.strip():
            symbols = [s.strip().upper() for s in symbol_input.split(",") if s.strip()]

    # ── 快速摘�?──
    st.subheader("�?一键摘�?)
    if st.button("生成摘要", type="primary", disabled=not use_llm):
        if not use_llm:
            st.warning("请在侧边栏启�?AI 模型")
        else:
            with st.spinner("AI 正在生成摘要..."):
                try:
                    from backend.services.llm_service import generate_quick_summary
                    from backend.schemas.llm import LLMQuickSummaryRequest
                    result = generate_quick_summary(LLMQuickSummaryRequest(
                        scope=scope,
                        asset_symbol=asset_symbol,
                        symbols=symbols,
                        use_llm=True,
                    ))
                    if result.ok:
                        st.success(result.text)
                        st.caption(f"模型：{result.model or '规则�?}")
                    else:
                        st.info(result.text)
                    for w in result.warnings:
                        st.warning(w)
                except Exception as exc:
                    st.error(f"生成失败：{exc}")

    st.divider()

    # ── 自由对话 ──
    st.subheader("💬 AI 研究对话")

    question = st.text_area("输入你的问题", placeholder="例如：当前A股和美股的风险收益比如何�?, height=100)

    if st.button("提问", type="primary", disabled=not question.strip() or not use_llm):
        if not use_llm:
            st.warning("请在侧边栏启�?AI 模型")
        else:
            with st.spinner("AI 思考中..."):
                try:
                    from backend.services.llm_service import answer_research_question
                    from backend.schemas.llm import LLMChatRequest
                    result = answer_research_question(LLMChatRequest(
                        question=question.strip(),
                        scope=scope,
                        asset_symbol=asset_symbol,
                        symbols=symbols,
                        use_llm=True,
                    ))
                    if result.ok:
                        st.success(result.text)
                        st.caption(f"模型：{result.model or '规则�?}")
                    else:
                        st.info(result.text)
                    for w in result.warnings:
                        st.warning(w)
                except Exception as exc:
                    st.error(f"提问失败：{exc}")
