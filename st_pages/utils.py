"""Shared utilities and session state for RAbot Streamlit app."""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def init_state() -> None:
    defaults = {
        "use_llm": True,
        "language": "zh",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


PAGE_KEYS = [
    "home", "dashboard", "stock", "fund", "macro", "news",
    "ai_research", "reports",
]

PAGE_LABELS = {
    "home": "首页 Home",
    "dashboard": "市场热力�?Heatmap",
    "stock": "个股分析 Stocks",
    "fund": "基金 ETF Funds",
    "macro": "宏观研究 Macro",
    "news": "新闻雷达 News",
    "ai_research": "AI 研究 AI Research",
    "reports": "报告�?Reports",
}

PAGE_ICONS = {
    "home": "🏠",
    "dashboard": "📊",
    "stock": "📈",
    "fund": "💰",
    "macro": "🌍",
    "news": "📰",
    "ai_research": "🤖",
    "reports": "📚",
}
