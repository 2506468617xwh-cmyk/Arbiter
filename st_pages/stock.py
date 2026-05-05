"""个股分析 — 深度单股研究"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from st_pages.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def _build_kline_chart(bars, name: str, benchmark_bars, benchmark_name: str):
    """Plotly K-line chart: stock vs benchmark normalized with MAs."""
    if not bars:
        return go.Figure()

    df = pd.DataFrame(bars)
    df["date"] = pd.to_datetime(df["date"])

    fig = go.Figure()

    # Normalize stock close
    first_close = df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
    norm_close = df["close"] / first_close * 100

    fig.add_trace(go.Scatter(
        x=df["date"], y=norm_close, mode="lines",
        name=f"{name} (归一化)", line=dict(color="#f59e0b", width=2),
    ))

    # MAs
    if "ma20" in df.columns and df["ma20"].notna().any():
        first_ma20 = df["ma20"].dropna().iloc[0] if len(df["ma20"].dropna()) else 1
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["ma20"] / first_ma20 * 100,
            mode="lines", name="MA20", line=dict(color="#3b82f6", width=1, dash="dot"),
        ))
    if "ma60" in df.columns and df["ma60"].notna().any():
        first_ma60 = df["ma60"].dropna().iloc[0] if len(df["ma60"].dropna()) else 1
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["ma60"] / first_ma60 * 100,
            mode="lines", name="MA60", line=dict(color="#10b981", width=1, dash="dot"),
        ))

    # Benchmark
    if benchmark_bars:
        bm_df = pd.DataFrame(benchmark_bars)
        bm_df["date"] = pd.to_datetime(bm_df["date"])
        if "close" in bm_df.columns and len(bm_df["close"].dropna()):
            first_bm = bm_df["close"].dropna().iloc[0]
            fig.add_trace(go.Scatter(
                x=bm_df["date"], y=bm_df["close"] / first_bm * 100,
                mode="lines", name=f"{benchmark_name} (基准)",
                line=dict(color="#8b5cf6", width=1, dash="dash"),
            ))

    fig.update_layout(
        title=f"{name} 走势图（归一化）",
        template="plotly_white",
        hovermode="x unified",
        height=420,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", y=-0.15),
    )
    return fig


def render() -> None:
    st.title("📈 个股分析")

    with st.container():
        c1, c2 = st.columns([3, 1])
        with c1:
            symbol = st.text_input("输入股票代码", placeholder="例如: TSLA.US, 600519.SH, 00700.HK")
        with c2:
            count = st.selectbox("K线数量", [120, 250, 500, 1000], index=1)

    if not symbol.strip():
        st.info("👆 请在上方输入股票代码开始分析")
        return

    symbol = symbol.strip().upper()

    with st.spinner(f"正在分析 {symbol} ..."):
        try:
            from backend.services.stock_service import get_stock_analysis
            use_llm = st.session_state.get("use_llm", True)
            result = get_stock_analysis(symbol, use_llm=use_llm, count=count)
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
        change = q.last_price - q.prev_close if q.last_price and q.prev_close else None
        pct = (change / q.prev_close * 100) if change is not None and q.prev_close else None
        change_str = f"{change:+.2f}" if change is not None else "-"
        pct_str = f"{pct:+.2f}%" if pct is not None else "-"
        cols[1].metric("涨跌", change_str, pct_str)
        cols[2].metric("开盘", f"{q.open:.2f}" if q.open else "-")
        cols[3].metric("最高", f"{q.high:.2f}" if q.high else "-")
        cols[4].metric("最低", f"{q.low:.2f}" if q.low else "-")
        cols[5].metric("成交量", f"{q.volume:,.0f}" if q.volume else "-")

    # ── K线图 ──
    if result.bars:
        fig = _build_kline_chart(result.bars, result.name or symbol, result.benchmark_bars, result.benchmark_name or "基准")
        st.plotly_chart(fig, use_container_width=True)

    # ── 指标网格 & 风险面板 ──
    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("技术指标")
        if result.indicators:
            indf = pd.DataFrame(
                [{"指标": k, "数值": f"{v:.2f}" if isinstance(v, float) else str(v)} for k, v in result.indicators.items()]
            )
            st.dataframe(indf, use_container_width=True, hide_index=True)

    with c2:
        st.subheader("趋势 & 风险")
        st.markdown(f"**趋势判断**\n{result.trend_summary or '_暂无_'}")
        st.markdown(f"**风险评估**\n{result.risk_summary or '_暂无_'}")

    # ── AI 研究摘要 ──
    if result.research_summary:
        st.subheader("🤖 AI 研究摘要")
        st.info(result.research_summary)
