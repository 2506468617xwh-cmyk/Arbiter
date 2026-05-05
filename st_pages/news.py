"""新闻雷达 �?新闻检索、筛选与详情"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from st_pages.utils import ROOT
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def _sentiment_color(score: float | None) -> str:
    if score is None:
        return "#888"
    if score > 0.3:
        return "#10b981"
    if score < -0.3:
        return "#ef4444"
    return "#f59e0b"


def render() -> None:
    st.title("📰 新闻雷达")

    # ── 筛选栏 ──
    with st.container():
        c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
        with c1:
            market = st.selectbox("市场", ["ALL", "CN", "US", "HK", "GLOBAL"])
        with c2:
            topic = st.text_input("主题", placeholder="可�?)
        with c3:
            symbol = st.text_input("股票代码", placeholder="可�?)
        with c4:
            limit = st.slider("条数", 10, 100, 50)

    # ── 加载新闻 ──
    with st.spinner("加载新闻..."):
        try:
            from backend.services.news_service import get_latest_news, search_news
            if topic.strip():
                result = search_news(topic.strip(), limit=limit)
            else:
                kw = st.session_state.get("_news_keyword", "")
                if kw:
                    result = search_news(kw, limit=limit)
                else:
                    result = get_latest_news(
                        limit=limit,
                        market=market if market != "ALL" else None,
                        topic=topic.strip() or None,
                        symbol=symbol.strip() or None,
                    )
        except Exception as exc:
            st.error(f"加载新闻失败：{exc}")
            return

    # ── 搜索�?──
    keyword = st.text_input("🔍 关键词搜�?, key="_news_keyword", placeholder="输入关键词后按回�?)
    if keyword.strip():
        with st.spinner("搜索�?.."):
            try:
                result = search_news(keyword.strip(), limit=limit)
            except Exception as exc:
                st.error(f"搜索失败：{exc}")
                result = None

    if not result or not result.items:
        st.info("暂无新闻数据")
        return

    st.caption(f"�?{result.count} �? |  最后更新：{result.last_update}")

    # ── 新闻列表 ──
    for item in result.items:
        with st.container():
            c1, c2 = st.columns([5, 1])
            with c1:
                title = item.title or "(无标�?"
                if item.url:
                    st.markdown(f"**[{title}]({item.url})**")
                else:
                    st.markdown(f"**{title}**")
                meta_parts = []
                if item.source:
                    meta_parts.append(f"📡 {item.source}")
                if item.published_at:
                    meta_parts.append(f"🕐 {item.published_at}")
                st.caption("  |  ".join(meta_parts))
            with c2:
                if item.sentiment_score is not None:
                    color = _sentiment_color(item.sentiment_score)
                    st.markdown(f"<span style='color:{color};font-weight:bold'>{item.sentiment_score:+.2f}</span>", unsafe_allow_html=True)

            # 风险标签 & 主题
            tags = []
            if item.risk_tags:
                tags.extend(item.risk_tags)
            if item.topics:
                tags.extend(item.topics[:3])
            if tags:
                st.caption("  ".join(f"`{t}`" for t in tags[:8]))

            # 摘要
            if item.summary:
                with st.expander("摘要"):
                    st.markdown(item.summary)

            st.divider()
