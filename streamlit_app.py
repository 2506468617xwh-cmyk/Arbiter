"""RAbot — Streamlit 版本  |  国内免 VPN 访问"""
from __future__ import annotations

import os
import streamlit as st

# ── 将 st.secrets 注入 os.environ，兼容所有 os.getenv() 调用 ──────────
try:
    for key, value in st.secrets.items():
        if key not in os.environ and isinstance(value, str):
            os.environ[key] = value
except Exception:
    pass

# ── Streamlit Cloud 上禁用自动采集，避免免费 API 限流轰炸 ──────────
os.environ.setdefault("RABOT_AUTO_UPDATE_ON_START", "false")
os.environ.setdefault("RABOT_NEWS_AUTO_REFRESH_MINUTES", "0")

st.set_page_config(
    page_title="RAbot 投研助手",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded",
)

from st_pages.utils import init_state, PAGE_KEYS, PAGE_LABELS, PAGE_ICONS
from st_pages import home, dashboard, stock, fund, macro, news, ai_research, reports

init_state()

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.image("frontend/public/hanbao.png", width=80)
    st.markdown("## 汉堡投研助手")

    page = st.radio(
        "导航",
        options=PAGE_KEYS,
        format_func=lambda k: f"{PAGE_ICONS[k]}  {PAGE_LABELS[k]}",
        label_visibility="collapsed",
    )

    st.divider()

    st.session_state.use_llm = st.toggle("🤖 启用 AI 模型", value=st.session_state.use_llm)
    lang_label = "English" if st.session_state.language == "zh" else "中文"
    if st.button(f"🌐 {lang_label}", use_container_width=True):
        st.session_state.language = "en" if st.session_state.language == "zh" else "zh"

    st.caption("RAbot v0.1.0 · Streamlit Edition")

# ── Page Router ──────────────────────────────────────────────────────
pages = {
    "home": home.render,
    "dashboard": dashboard.render,
    "stock": stock.render,
    "fund": fund.render,
    "macro": macro.render,
    "news": news.render,
    "ai_research": ai_research.render,
    "reports": reports.render,
}

pages[page]()
