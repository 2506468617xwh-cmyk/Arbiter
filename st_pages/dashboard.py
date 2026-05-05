"""市场热力�?�?全资产表现排名与热力�?""
from __future__ import annotations

import streamlit as st
import pandas as pd

from st_pages.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def _color_returns(val: float | None) -> str:
    if val is None:
        return ""
    if val > 0:
        intensity = min(255, int(50 + val * 800))
        return f"background-color: rgba(0,{intensity},0,0.18)"
    if val < 0:
        intensity = min(255, int(50 + abs(val) * 800))
        return f"background-color: rgba({intensity},0,0,0.18)"
    return ""


def render() -> None:
    st.title("📊 市场热力�?)

    try:
        from backend.services.market_service import get_market_dashboard, get_market_performance
        dashboard = get_market_dashboard()
        perf = get_market_performance()
    except Exception as exc:
        st.error(f"无法加载市场数据：{exc}")
        return

    # ── 顶部指标 ──
    cols = st.columns(4)
    cols[0].metric("市场状�?, dashboard.market_status)
    cols[1].metric("覆盖资产", str(dashboard.asset_count))
    cols[2].metric("最新日�?, dashboard.latest_date or "-")
    cols[3].metric("最后更�?, dashboard.last_update or "-")

    if dashboard.warnings:
        for w in dashboard.warnings:
            st.warning(w)

    st.markdown(dashboard.summary or "")

    # ── 热力分布 ──
    tab1, tab2, tab3 = st.tabs(["强势资产", "弱势资产", "完整排行"])

    with tab1:
        if dashboard.strong_assets:
            strong_df = pd.DataFrame([{
                "代码": a.symbol, "名称": a.name,
                "1W%": a.return_1w, "1M%": a.return_1m, "YTD%": a.return_ytd,
                "波动�?: a.volatility_20d, "趋势": a.trend_signal,
            } for a in dashboard.strong_assets])
            st.dataframe(strong_df.style.format(precision=2).applymap(_color_returns, subset=["1W%", "1M%", "YTD%"]), use_container_width=True)
        else:
            st.info("暂无强势资产数据")

    with tab2:
        if dashboard.weak_assets:
            weak_df = pd.DataFrame([{
                "代码": a.symbol, "名称": a.name,
                "1W%": a.return_1w, "1M%": a.return_1m, "YTD%": a.return_ytd,
                "回撤": a.drawdown, "风险": a.risk_level,
            } for a in dashboard.weak_assets])
            st.dataframe(weak_df.style.format(precision=2).applymap(_color_returns, subset=["1W%", "1M%", "YTD%"]), use_container_width=True)
        else:
            st.info("暂无弱势资产数据")

    with tab3:
        if perf.items:
            df = pd.DataFrame([{
                "代码": a.symbol, "名称": a.name,
                "收盘": a.close, "1W%": a.return_1w, "1M%": a.return_1m,
                "3M%": a.return_3m, "YTD%": a.return_ytd, "1Y%": a.return_1y,
                "波动�?: a.volatility_20d, "回撤": a.drawdown,
                "趋势": a.trend_signal, "风险": a.risk_level,
            } for a in perf.items])
            st.dataframe(
                df.style.format(precision=2).applymap(_color_returns, subset=["1W%", "1M%", "3M%", "YTD%", "1Y%"]),
                use_container_width=True, height=500,
            )
        else:
            st.info("暂无资产数据")
