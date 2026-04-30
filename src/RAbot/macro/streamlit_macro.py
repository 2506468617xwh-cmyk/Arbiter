# src/RAbot/macro/streamlit_macro.py

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from RAbot.analysis.macro_research import build_macro_indicator_snapshot
from RAbot.macro.macro_store import MacroStore


REGION_LABELS = {
    "US": "美国宏观",
    "CN": "中国宏观",
}

CATEGORY_LABELS = {
    "rates": "利率",
    "policy_rate": "政策利率",
    "inflation": "通胀",
    "employment": "就业",
    "growth": "增长",
    "liquidity": "流动性",
    "risk_appetite": "风险偏好",
}


def render_macro_center() -> None:
    st.subheader("宏观中心")

    store = MacroStore()
    macro_df = store.read_macro_series()

    if macro_df.empty:
        st.info("暂无宏观数据。请先在终端运行：python scripts/update_macro.py")
        _render_update_log(store)
        return

    snapshot = build_macro_indicator_snapshot(macro_df)

    if snapshot.empty:
        st.warning("宏观数据已存在，但暂时无法生成快照。")
        _render_update_log(store)
        return

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric("宏观指标数", f"{snapshot['symbol'].nunique():,.0f}")

    with c2:
        us_count = snapshot[snapshot["region"] == "US"]["symbol"].nunique()
        st.metric("美国指标", f"{us_count:,.0f}")

    with c3:
        cn_count = snapshot[snapshot["region"] == "CN"]["symbol"].nunique()
        st.metric("中国指标", f"{cn_count:,.0f}")

    with c4:
        latest_date = pd.to_datetime(snapshot["latest_date"], errors="coerce").max()
        st.metric("最新数据日期", latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "NA")

    st.divider()

    region_options = ["全部"] + [REGION_LABELS.get(x, x) for x in sorted(snapshot["region"].dropna().unique())]
    selected_region_label = st.selectbox("地区", region_options, index=0)

    selected_region = None
    for key, label in REGION_LABELS.items():
        if label == selected_region_label:
            selected_region = key
            break

    view_snapshot = snapshot.copy()
    view_series = macro_df.copy()

    if selected_region:
        view_snapshot = view_snapshot[view_snapshot["region"] == selected_region]
        view_series = view_series[view_series["region"] == selected_region]

    category_options = ["全部"] + [
        CATEGORY_LABELS.get(x, x) for x in sorted(view_snapshot["category"].dropna().unique())
    ]
    selected_category_label = st.selectbox("类别", category_options, index=0)

    selected_category = None
    for key, label in CATEGORY_LABELS.items():
        if label == selected_category_label:
            selected_category = key
            break

    if selected_category:
        view_snapshot = view_snapshot[view_snapshot["category"] == selected_category]
        view_series = view_series[view_series["category"] == selected_category]

    st.markdown("#### 宏观指标快照")

    display = view_snapshot.copy()
    display["latest_date"] = pd.to_datetime(display["latest_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    display["region"] = display["region"].map(lambda x: REGION_LABELS.get(x, x))
    display["category"] = display["category"].map(lambda x: CATEGORY_LABELS.get(x, x))

    show_cols = [
        "name",
        "region",
        "category",
        "latest_date",
        "latest_value",
        "change_1m",
        "change_3m",
        "trend_label",
        "risk_label",
        "interpretation",
    ]

    st.dataframe(
        display[show_cols],
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.markdown("#### 单指标走势")

    symbol_name_map = {
        f"{row['name']}（{row['symbol']}）": row["symbol"]
        for _, row in view_snapshot.iterrows()
    }

    if not symbol_name_map:
        st.info("当前筛选条件下没有指标。")
        _render_update_log(store)
        return

    selected_name = st.selectbox("选择指标", list(symbol_name_map.keys()))
    selected_symbol = symbol_name_map[selected_name]

    one = view_series[view_series["symbol"] == selected_symbol].copy()
    one = one.sort_values("date")

    if one.empty:
        st.info("该指标暂无时间序列。")
    else:
        fig = px.line(
            one,
            x="date",
            y="value",
            title=selected_name,
            markers=False,
        )
        fig.update_layout(
            height=420,
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig, use_container_width=True)

        latest_row = view_snapshot[view_snapshot["symbol"] == selected_symbol]
        if not latest_row.empty:
            latest_row = latest_row.iloc[0]
            with st.container(border=True):
                st.markdown("**规则解读**")
                st.write(latest_row.get("interpretation", ""))
                note = latest_row.get("direction_note", "")
                if isinstance(note, str) and note.strip():
                    st.caption(note)

    st.divider()
    _render_update_log(store)


def _render_update_log(store: MacroStore) -> None:
    with st.expander("宏观数据更新日志", expanded=False):
        log_df = store.read_update_log(limit=80)

        if log_df.empty:
            st.info("暂无更新日志。")
            return

        st.dataframe(log_df, use_container_width=True, hide_index=True)