"""基金 ETF 分析 — 基金深度研究"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from st_pages.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def render() -> None:
    st.title("💰 基金 ETF 分析")

    c1, c2 = st.columns([3, 1])
    with c1:
        symbol = st.text_input("输入基金代码", placeholder="例如: QQQ.US, 510300.SH, 2800.HK")
    with c2:
        count = st.selectbox("数据条数", [120, 250, 500], index=1)

    if not symbol.strip():
        st.info("👆 请在输入基金代码开始分析")
        return

    symbol = symbol.strip().upper()

    with st.spinner(f"正在分析 {symbol} ..."):
        try:
            from backend.services.fund_service import get_fund_analysis
            use_llm = st.session_state.get("use_llm", True)
            result = get_fund_analysis(symbol, use_llm=use_llm, count=count)
        except Exception as exc:
            st.error(f"分析失败：{exc}")
            return

    if result.warnings:
        for w in result.warnings:
            st.warning(w)

    # ── 报价卡片 ──
    if result.quote:
        q = result.quote
        cols = st.columns(6)
        cols[0].metric("最新价", f"{q.last_price:.2f}" if q.last_price else "-")
        cols[1].metric("净值 NAV", f"{q.nav:.4f}" if q.nav else "-")
        premium = q.premium_discount
        cols[2].metric("溢价率", f"{premium:.2f}%" if premium is not None else "-")
        cols[3].metric("成交量", f"{q.volume:,.0f}" if q.volume else "-")
        cols[4].metric("成交额", f"{q.turnover:,.0f}" if q.turnover else "-")
        cols[5].metric("类型", result.fund_type or "-")

    # ── 基金信息 ──
    if result.info:
        info = result.info
        with st.expander("基金信息", expanded=False):
            cols = st.columns(4)
            cols[0].metric("基金公司", info.fund_company or "-")
            cols[1].metric("资产类别", info.asset_class or "-")
            cols[2].metric("成立日期", info.inception_date or "-")
            cols[3].metric("费用率", f"{info.expense_ratio:.4f}%" if info.expense_ratio else "-")
            cols[0].metric("管理规模", f"{info.aum:,.0f}" if info.aum else "-")
            cols[1].metric("基准", info.benchmark or "-")

    # ── NAV 走势图 ──
    if result.bars:
        import plotly.graph_objects as go
        df = pd.DataFrame(result.bars)
        df["date"] = pd.to_datetime(df["date"])

        fig = go.Figure()
        close_col = "nav" if "nav" in df.columns and df["nav"].notna().any() else "close"
        first_val = df[close_col].dropna().iloc[0] if len(df[close_col].dropna()) else 1
        fig.add_trace(go.Scatter(
            x=df["date"], y=df[close_col] / first_val * 100,
            mode="lines", name=f"{result.name or symbol} 归一化",
            line=dict(color="#f59e0b", width=2),
        ))

        if result.benchmark_bars:
            bm_df = pd.DataFrame(result.benchmark_bars)
            bm_df["date"] = pd.to_datetime(bm_df["date"])
            if "close" in bm_df.columns and len(bm_df["close"].dropna()):
                first_bm = bm_df["close"].dropna().iloc[0]
                fig.add_trace(go.Scatter(
                    x=bm_df["date"], y=bm_df["close"] / first_bm * 100,
                    mode="lines", name=f"{result.benchmark_name or '基准'}",
                    line=dict(color="#8b5cf6", width=1, dash="dash"),
                ))

        fig.update_layout(title=f"{result.name or symbol} 走势图（归一化）", template="plotly_white", hovermode="x unified", height=400, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)

    # ── 分析面板 ──
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("业绩 & 风险")
        st.markdown(f"**业绩总结**\n{result.performance_summary or '_暂无_'}")
        st.markdown(f"**风险总结**\n{result.risk_summary or '_暂无_'}")

    with c2:
        st.subheader("配置 & 定投")
        st.markdown(f"**配置分析**\n{result.allocation_summary or '_暂无_'}")
        st.markdown(f"**流动性**\n{result.liquidity_summary or '_暂无_'}")
        st.markdown(f"**定投建议**\n{result.dca_summary or '_暂无_'}")

    if result.research_summary:
        st.subheader("🤖 AI 研究摘要")
        st.info(result.research_summary)
