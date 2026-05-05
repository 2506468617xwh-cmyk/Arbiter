"""宏观研究 — 全球宏观指标分析"""
from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from streamlit.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def render() -> None:
    st.title("🌍 宏观研究")

    try:
        from backend.services.macro_service import get_macro_snapshot, get_macro_series
    except Exception as exc:
        st.error(f"无法加载宏观模块：{exc}")
        return

    # ── 筛选器 ──
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            region = st.selectbox("地区", ["", "US", "CN", "EU", "JP", "GLOBAL"], format_func=lambda r: {"": "全部", "US": "美国", "CN": "中国", "EU": "欧洲", "JP": "日本", "GLOBAL": "全球"}.get(r, r))
        with c2:
            category = st.selectbox("类别", ["", "GDP", "Inflation", "Employment", "Interest Rate", "Money Supply", "Trade", "Housing", "Consumer", "Business", "Other"], format_func=lambda c: c if c else "全部")

    # ── 数据加载 ──
    with st.spinner("加载宏观数据..."):
        try:
            snapshot = get_macro_snapshot(region=region or None, category=category or None)
        except Exception as exc:
            st.error(f"加载失败：{exc}")
            return

    if not snapshot.items:
        st.info("暂无宏观数据，请先运行数据更新脚本。")
        return

    # ── 指标列表 → 可多选绘图 ──
    st.subheader("指标速览")
    df = pd.DataFrame([{
        "指标名称": item.name or item.indicator,
        "代码": item.indicator,
        "地区": item.region or "-",
        "最新日期": item.latest_date or "-",
        "最新值": f"{item.latest_value:.2f}" if item.latest_value is not None else "-",
        "趋势": item.trend_label or "-",
        "风险": item.risk_label or "-",
    } for item in snapshot.items])

    st.dataframe(df, use_container_width=True, height=300, hide_index=True)

    # ── 时序图表 ──
    st.subheader("📈 指标走势对比（可多选，最多 6 个）")
    indicator_options = {f"{item.name or item.indicator} ({item.indicator})": item.indicator for item in snapshot.items}
    selected_labels = st.multiselect("选择指标", list(indicator_options.keys()), max_selections=6)

    if selected_labels:
        selected_symbols = [indicator_options[label] for label in selected_labels]
        with st.spinner("加载时序数据..."):
            try:
                series = get_macro_series(selected_symbols, limit_per_symbol=240)
            except Exception as exc:
                st.error(f"加载时序失败：{exc}")
                series = None

        if series and series.items:
            fig = go.Figure()
            colors = ["#f59e0b", "#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"]
            for i, sym in enumerate(selected_symbols):
                sym_points = [p for p in series.items if p.symbol == sym]
                if not sym_points:
                    continue
                sdf = pd.DataFrame(sym_points)
                sdf["date"] = pd.to_datetime(sdf["date"])
                sdf = sdf.sort_values("date")
                vals = sdf["value"].dropna()
                if len(vals) == 0:
                    continue
                first_val = vals.iloc[0]
                norm = [v / first_val * 100 if first_val != 0 else None for v in sdf["value"]]
                name = next((l.split("(")[0].strip() for l in selected_labels if indicator_options[l] == sym), sym)
                fig.add_trace(go.Scatter(
                    x=sdf["date"], y=norm, mode="lines", name=name,
                    line=dict(color=colors[i % len(colors)], width=1.8),
                ))

            fig.update_layout(
                title="宏观指标归一化对比", template="plotly_white",
                hovermode="x unified", height=420,
                margin=dict(l=0, r=0, t=40, b=0),
                legend=dict(orientation="h", y=-0.18),
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── AI 宏观分析 ──
    st.subheader("🤖 AI 宏观分析")
    question = st.text_input("输入你的宏观问题", placeholder="例如：当前美国通胀趋势如何影响全球资产配置？")
    if st.button("分析", type="primary", disabled=not question.strip()):
        use_llm = st.session_state.get("use_llm", True)
        if not use_llm:
            st.warning("请在侧边栏启用 AI 模型")
        else:
            with st.spinner("AI 分析中..."):
                try:
                    from backend.services.macro_service import analyze_macro_with_llm
                    from backend.schemas.macro import MacroAnalysisRequest
                    result = analyze_macro_with_llm(MacroAnalysisRequest(
                        question=question.strip(),
                        symbols=selected_symbols if selected_labels else [],
                        use_llm=True,
                    ))
                    if result.ok:
                        st.success(result.text)
                    else:
                        st.warning(result.text)
                except Exception as exc:
                    st.error(f"AI 分析失败：{exc}")
