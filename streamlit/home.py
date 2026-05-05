"""首页 — 系统总览与状态一览"""
from __future__ import annotations

import streamlit as st

from streamlit.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def render() -> None:
    st.title("🍔 RAbot 投研助手")

    try:
        from backend.services.overview_service import build_overview
        overview = build_overview()
    except Exception as exc:
        st.error(f"无法加载总览数据：{exc}")
        return

    # ── 指标卡片 ──
    cols = st.columns(5)
    cols[0].metric("市场状态", overview.market_status)
    cols[1].metric("指数数量", str(overview.market.count) if overview.market else "-")
    cols[2].metric("新闻数量", str(overview.news.count) if overview.news else "-")
    cols[3].metric("宏观指标", str(overview.macro.count) if overview.macro else "-")
    cols[4].metric("报告数量", str(overview.reports.count) if overview.reports else "-")

    if overview.last_update:
        st.caption(f"最后更新：{overview.last_update}")

    if overview.warnings:
        for w in overview.warnings:
            st.warning(w)

    # ── 市场概览 ──
    st.subheader("📊 市场")
    st.markdown(overview.market_summary or "_暂无市场摘要_")
    if overview.market:
        for h in overview.market.highlights:
            st.success(h)
        for w in overview.market.warnings:
            st.warning(w)

    # ── 新闻概览 ──
    st.subheader("📰 新闻")
    st.markdown(overview.news_summary or "_暂无新闻摘要_")
    if overview.news:
        for h in overview.news.highlights:
            st.success(h)

    # ── 宏观概览 ──
    st.subheader("🌍 宏观")
    st.markdown(overview.macro_summary or "_暂无宏观摘要_")
    if overview.macro:
        for h in overview.macro.highlights:
            st.success(h)

    # ── 报告概览 ──
    st.subheader("📚 报告")
    st.markdown(overview.report_summary or "_暂无报告摘要_")
    if overview.reports and overview.reports.latest_title:
        st.info(f"最新报告：{overview.reports.latest_title}")
