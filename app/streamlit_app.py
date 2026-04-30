from __future__ import annotations

import inspect
import html
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


try:
    from RAbot.analysis.indicators import (
        add_technical_indicators,
        build_asset_performance_table,
        build_correlation_matrix,
        build_normalized_price_table,
        summarize_latest_status,
    )
    from RAbot.analysis.macro_research import build_asset_macro_research
    from RAbot.analysis.news_research import (
        build_asset_news_research,
        build_news_market_snapshot,
    )
    from RAbot.analysis.research_engine import (
        build_market_overview,
        build_single_asset_research,
    )
    from RAbot.alerts.alerts_engine import AlertsEngine
    from RAbot.alerts.alerts_store import AlertsStore
    from RAbot.data.pipeline import load_index_configs, update_all_indexes
    from RAbot.macro.streamlit_macro import render_macro_center
    from RAbot.news.news_provider import fetch_all_news
    from RAbot.news.news_store import NewsStore
    from RAbot.reporting.markdown_report import generate_index_markdown_report
    from RAbot.review.view_reviewer import ViewReviewer
    from RAbot.review.view_store import ViewStore
    from RAbot.settings import get_db_path
    from RAbot.storage.sqlite_store import SQLiteStore
    from RAbot.llm.research_chat import RAbotResearchChat
except Exception as e:
    st.set_page_config(page_title="RAbot 启动错误", layout="wide")
    st.error("RAbot 前端启动失败：模块导入错误")
    st.exception(e)
    st.stop()


try:
    from RAbot.reporting.report_jobs import (
        create_job,
        get_job,
        list_jobs,
        run_job_async,
    )

    REPORT_JOB_BACKEND = "v2"
except Exception:
    try:
        from RAbot.reporting.report_jobs import (
            get_latest_report_file as legacy_get_latest_report_file,
            get_report_job as legacy_get_report_job,
            read_report_file as legacy_read_report_file,
            start_report_job as legacy_start_report_job,
        )

        REPORT_JOB_BACKEND = "legacy"
    except Exception:
        REPORT_JOB_BACKEND = "none"


try:
    from RAbot.macro.macro_provider import iter_macro_indicators
    from RAbot.macro.fred_provider import FredGraphProvider
    from RAbot.macro.china_macro_provider import ChinaTushareMacroProvider
    from RAbot.macro.macro_store import MacroStore

    MACRO_MODULE_READY = True
except Exception:
    MACRO_MODULE_READY = False


st.set_page_config(
    page_title="RAbot Index Research",
    page_icon="📈",
    layout="wide",
)


DEFAULT_WATCHLIST = [
    "NASDAQ",
    "NASDAQ100",
    "SP500",
    "CSI300",
    "SSE",
    "HSI",
    "GOLD",
    "DXY",
    "WTI",
    "VIX",
]


st.markdown(
    """
    <style>
    :root {
        --rabot-bg: #F7F0E4;
        --rabot-bg-soft: #FBF7EF;
        --rabot-card: rgba(255, 253, 248, 0.94);
        --rabot-card-solid: #FFFDF8;
        --rabot-border: rgba(91, 64, 43, 0.14);
        --rabot-text: #2B2118;
        --rabot-muted: #6F6257;
        --rabot-faint: #8A7D70;
        --rabot-accent: #D97745;
        --rabot-accent-dark: #A94F2B;
        --rabot-accent-soft: rgba(217, 119, 69, 0.12);
        --rabot-risk: #B84A3A;
        --rabot-risk-soft: rgba(184, 74, 58, 0.12);
        --rabot-support: #4F8A5B;
        --rabot-support-soft: rgba(79, 138, 91, 0.12);
        --rabot-neutral-soft: rgba(111, 98, 87, 0.10);
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(217, 119, 69, 0.08), transparent 30rem),
            linear-gradient(180deg, #F7F0E4 0%, #F6EFE3 100%);
        color: var(--rabot-text);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1320px;
        color: var(--rabot-text);
    }

    h1, h2, h3, h4, h5, h6, p, label, span, div {
        color: inherit;
    }

    h1 {
        color: var(--rabot-text);
        letter-spacing: 0;
        font-weight: 760;
    }

    h2, h3 {
        color: var(--rabot-text);
        letter-spacing: 0;
    }

    [data-testid="stSidebar"] {
        background: #EFE3D1;
        border-right: 1px solid var(--rabot-border);
    }

    [data-testid="stSidebar"] * {
        color: var(--rabot-text);
    }

    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: var(--rabot-text) !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--rabot-text) !important;
    }

    div[data-testid="stMetric"] {
        text-align: center;
    }

    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 780;
    }

    div[data-testid="stMetricDelta"] {
        justify-content: center;
    }

    .small-muted {
        color: var(--rabot-faint);
        font-size: 0.9rem;
    }

    .rabot-card,
    .rabot-section-card,
    .rabot-text-card,
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--rabot-card);
        border: 1px solid var(--rabot-border);
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(43, 33, 24, 0.06);
    }

    .rabot-card,
    .rabot-section-card,
    .rabot-text-card {
        padding: 18px 20px;
        margin: 0.35rem 0 0.85rem;
        transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
    }

    .rabot-card:hover,
    .rabot-section-card:hover,
    .rabot-text-card:hover {
        border-color: rgba(217, 119, 69, 0.28);
        box-shadow: 0 10px 28px rgba(43, 33, 24, 0.08);
    }

    .rabot-card {
        text-align: center;
        min-height: 138px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    .rabot-card-title,
    .rabot-section-title {
        color: var(--rabot-muted);
        font-size: 0.88rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.58rem;
    }

    .rabot-card-value {
        color: var(--rabot-text);
        font-size: clamp(1.35rem, 2.15vw, 2rem);
        line-height: 1.16;
        font-weight: 780;
        margin: 0.12rem 0 0.45rem;
        overflow-wrap: anywhere;
        max-width: 100%;
    }

    .rabot-card-value-compact {
        font-size: clamp(1.12rem, 1.75vw, 1.72rem);
        line-height: 1.25;
    }

    .rabot-card-value-date {
        font-size: clamp(1.05rem, 1.4vw, 1.32rem);
        line-height: 1.18;
        letter-spacing: 0;
        word-break: keep-all;
    }

    .rabot-card-subtitle {
        color: var(--rabot-faint);
        font-size: 0.82rem;
        line-height: 1.45;
        text-align: center;
    }

    .rabot-card-positive .rabot-card-value,
    .rabot-tone-positive {
        color: var(--rabot-support);
    }

    .rabot-card-negative .rabot-card-value,
    .rabot-tone-negative {
        color: var(--rabot-risk);
    }

    .rabot-card-accent .rabot-card-value,
    .rabot-tone-accent {
        color: var(--rabot-accent-dark);
    }

    .rabot-card-up .rabot-card-value,
    .rabot-tone-up {
        color: var(--rabot-risk);
    }

    .rabot-card-down .rabot-card-value,
    .rabot-tone-down {
        color: var(--rabot-support);
    }

    .rabot-tag-row {
        display: flex;
        justify-content: center;
        align-items: center;
        flex-wrap: wrap;
        gap: 7px;
        margin-top: 0.35rem;
    }

    .rabot-tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 999px;
        padding: 4px 10px;
        font-size: 12px;
        line-height: 1.25;
        font-weight: 650;
        color: var(--rabot-accent-dark);
        background: var(--rabot-accent-soft);
        border: 1px solid rgba(217, 119, 69, 0.15);
        max-width: 100%;
    }

    .rabot-tag-positive {
        color: var(--rabot-support);
        background: var(--rabot-support-soft);
        border-color: rgba(79, 138, 91, 0.16);
    }

    .rabot-tag-negative {
        color: var(--rabot-risk);
        background: var(--rabot-risk-soft);
        border-color: rgba(184, 74, 58, 0.16);
    }

    .rabot-tag-neutral {
        color: var(--rabot-muted);
        background: var(--rabot-neutral-soft);
        border-color: rgba(111, 98, 87, 0.14);
    }

    .rabot-tag-up {
        color: var(--rabot-risk);
        background: var(--rabot-risk-soft);
        border-color: rgba(184, 74, 58, 0.16);
    }

    .rabot-tag-down {
        color: var(--rabot-support);
        background: var(--rabot-support-soft);
        border-color: rgba(79, 138, 91, 0.16);
    }

    .rabot-backend-status {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 7px;
        margin: -0.15rem 0 1rem;
    }

    .rabot-action-row {
        display: flex;
        justify-content: center;
        width: 100%;
        margin: 0.55rem 0 1rem;
    }

    .rabot-action-row-spacer {
        height: 0;
    }

    .rabot-status-chip {
        display: inline-flex;
        align-items: center;
        gap: 5px;
        border-radius: 999px;
        padding: 4px 9px;
        font-size: 12px;
        font-weight: 680;
        border: 1px solid var(--rabot-border);
        background: rgba(255, 253, 248, 0.72);
        color: var(--rabot-muted);
    }

    .rabot-status-chip-ok {
        color: var(--rabot-support);
        background: var(--rabot-support-soft);
        border-color: rgba(79, 138, 91, 0.18);
    }

    .rabot-status-chip-bad {
        color: var(--rabot-risk);
        background: var(--rabot-risk-soft);
        border-color: rgba(184, 74, 58, 0.18);
    }

    .rabot-alert-card {
        background: var(--rabot-card);
        border: 1px solid var(--rabot-border);
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(43, 33, 24, 0.06);
        padding: 18px 20px;
        margin: 0.45rem 0 0.9rem;
    }

    .rabot-alert-title {
        color: var(--rabot-text);
        font-size: 1.02rem;
        font-weight: 780;
        text-align: center;
        margin-bottom: 0.55rem;
    }

    .rabot-alert-message {
        color: var(--rabot-text);
        line-height: 1.65;
        font-size: 0.95rem;
        margin: 0.5rem 0;
    }

    .rabot-gauge-card {
        min-height: 286px;
        padding: 18px 20px 16px;
        text-align: center;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        align-items: center;
    }

    .rabot-gauge-meter {
        position: relative;
        width: min(100%, 315px);
        height: 176px;
        margin: 0.05rem auto 0.05rem;
    }

    .rabot-gauge-svg {
        display: block;
        width: 100%;
        height: 100%;
        overflow: visible;
    }

    .rabot-gauge-score {
        color: var(--rabot-text);
        font-size: clamp(1.7rem, 3vw, 2.2rem);
        line-height: 1;
        font-weight: 760;
        margin: 0.25rem 0 0.2rem;
    }

    .rabot-gauge-ticks {
        display: flex;
        justify-content: space-between;
        width: min(100%, 295px);
        margin: -0.45rem auto 0.45rem;
        color: var(--rabot-muted);
        font-size: 0.78rem;
    }

    .rabot-section-card,
    .rabot-text-card {
        text-align: left;
    }

    .rabot-section-card .rabot-section-title,
    .rabot-text-card .rabot-section-title {
        text-align: center;
        color: var(--rabot-text);
        font-size: 1rem;
        margin-bottom: 0.65rem;
    }

    .rabot-text-body {
        color: var(--rabot-text);
        font-size: 0.96rem;
        line-height: 1.72;
        text-align: left;
        white-space: pre-wrap;
    }

    .rabot-bullet-list {
        margin: 0.25rem 0 0;
        padding-left: 1.1rem;
        color: var(--rabot-text);
        line-height: 1.65;
    }

    .rabot-bullet-list li {
        margin: 0.24rem 0;
    }

    .rabot-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
        gap: 14px;
        align-items: stretch;
    }

    .rabot-heat-list {
        display: flex;
        flex-direction: column;
        gap: 12px;
        margin-top: 0.45rem;
    }

    .rabot-heat-row {
        display: grid;
        grid-template-columns: minmax(74px, 0.85fr) minmax(140px, 2.2fr) auto;
        gap: 10px;
        align-items: center;
        color: var(--rabot-text);
        font-size: 0.9rem;
    }

    .rabot-heat-symbol {
        font-weight: 760;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .rabot-heat-track {
        height: 10px;
        border-radius: 999px;
        background: rgba(91, 64, 43, 0.12);
        overflow: hidden;
    }

    .rabot-heat-fill {
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #4F8A5B, #D97745, #B84A3A);
    }

    .rabot-heat-value {
        min-width: 64px;
        text-align: right;
        color: var(--rabot-muted);
        font-weight: 700;
    }

    .rabot-news-title {
        color: var(--rabot-text);
        font-size: 1.02rem;
        line-height: 1.45;
        font-weight: 760;
        text-decoration: none;
    }

    .rabot-news-title:hover {
        color: var(--rabot-accent-dark);
    }

    .rabot-chart-heading {
        margin: 1.1rem 0 0.35rem;
        text-align: center;
    }

    .rabot-chart-heading-title {
        font-size: 1.05rem;
        color: var(--rabot-text);
        font-weight: 760;
    }

    .rabot-chart-heading-subtitle {
        color: var(--rabot-faint);
        font-size: 0.86rem;
        margin-top: 0.15rem;
    }

    div[data-testid="stTabs"] button {
        color: var(--rabot-muted);
        font-weight: 650;
    }

    div[data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--rabot-accent-dark);
    }

    div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
        background-color: var(--rabot-accent);
    }

    .stButton > button,
    div[data-testid="stBaseButton-secondary"] button,
    div[data-testid="stBaseButton-secondary"],
    button[kind="secondary"] {
        background: var(--rabot-card-solid);
        color: var(--rabot-accent-dark) !important;
        border: 1px solid rgba(217, 119, 69, 0.42);
        border-radius: 12px;
        font-weight: 700;
        box-shadow: 0 2px 10px rgba(43, 33, 24, 0.04);
    }

    .stButton > button:hover,
    div[data-testid="stBaseButton-secondary"]:hover,
    button[kind="secondary"]:hover {
        color: #FFFDF8 !important;
        background: var(--rabot-accent);
        border-color: var(--rabot-accent);
    }

    .stButton > button[kind="primary"],
    div[data-testid="stBaseButton-primary"],
    button[kind="primary"] {
        background: var(--rabot-accent) !important;
        color: #FFFDF8 !important;
        border-color: var(--rabot-accent) !important;
    }

    .stButton > button[kind="primary"]:hover,
    div[data-testid="stBaseButton-primary"]:hover,
    button[kind="primary"]:hover {
        background: var(--rabot-accent-dark) !important;
        border-color: var(--rabot-accent-dark) !important;
        color: #FFFDF8 !important;
    }

    .stButton button p,
    .stButton button span,
    div[data-testid="stBaseButton-primary"] p,
    div[data-testid="stBaseButton-primary"] span {
        color: inherit !important;
        opacity: 1 !important;
    }

    [data-baseweb="input"],
    [data-baseweb="textarea"],
    [data-baseweb="select"],
    [data-baseweb="popover"] {
        background-color: var(--rabot-card-solid) !important;
        color: var(--rabot-text) !important;
        border-color: var(--rabot-border) !important;
    }

    [data-baseweb="input"] > div,
    [data-baseweb="textarea"] > div,
    [data-baseweb="select"] > div {
        background-color: var(--rabot-card-solid) !important;
        color: var(--rabot-text) !important;
        overflow: visible !important;
    }

    input, textarea {
        color: var(--rabot-text) !important;
        background-color: var(--rabot-card-solid) !important;
        caret-color: var(--rabot-accent-dark);
        -webkit-text-fill-color: var(--rabot-text) !important;
        opacity: 1 !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #5D5148 !important;
        opacity: 0.78 !important;
    }

    [data-baseweb="select"] input {
        background: transparent !important;
        -webkit-text-fill-color: var(--rabot-text) !important;
        min-width: 2px !important;
        width: auto !important;
        box-shadow: none !important;
    }

    [data-baseweb="tag"] {
        background-color: rgba(217, 119, 69, 0.18) !important;
        border: 1px solid rgba(217, 119, 69, 0.22) !important;
        color: var(--rabot-accent-dark) !important;
        border-radius: 999px !important;
        display: inline-flex !important;
        align-items: center !important;
        min-height: 30px !important;
        height: auto !important;
        margin: 4px 4px 4px 0 !important;
        padding: 3px 9px !important;
        overflow: visible !important;
        line-height: 1.25 !important;
        max-width: 245px !important;
    }

    [data-baseweb="tag"] span,
    [data-baseweb="tag"] div {
        color: var(--rabot-accent-dark) !important;
        opacity: 1 !important;
        line-height: 1.25 !important;
        overflow: visible !important;
        white-space: nowrap !important;
        background: transparent !important;
        max-width: 205px !important;
        text-overflow: ellipsis !important;
    }

    [data-baseweb="tag"] svg {
        color: var(--rabot-accent-dark) !important;
        fill: var(--rabot-accent-dark) !important;
        opacity: 1 !important;
        flex: 0 0 auto !important;
    }

    [data-baseweb="select"] [data-baseweb="tag"] span,
    [data-baseweb="select"] [data-baseweb="tag"] div {
        background: transparent !important;
    }

    [data-baseweb="select"] [role="combobox"],
    [data-baseweb="select"] [aria-haspopup="listbox"] {
        min-height: 42px !important;
        height: auto !important;
        align-items: center !important;
        padding-top: 4px !important;
        padding-bottom: 4px !important;
        overflow: visible !important;
        row-gap: 4px !important;
    }

    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="textarea"] span,
    [data-baseweb="textarea"] div {
        color: var(--rabot-text) !important;
        opacity: 1 !important;
    }

    [data-baseweb="select"] svg,
    [data-testid="stWidgetLabel"] svg {
        color: var(--rabot-accent-dark) !important;
        fill: var(--rabot-accent-dark) !important;
    }

    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] label,
    [data-testid="stWidgetLabel"] p,
    [data-testid="stWidgetLabel"] span,
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] p,
    [data-testid="stRadio"] span {
        color: var(--rabot-text) !important;
        opacity: 1 !important;
        font-weight: 650;
    }

    [data-testid="stRadio"] [role="radiogroup"] label div:first-child {
        border-color: var(--rabot-text) !important;
        background: var(--rabot-card-solid) !important;
    }

    [data-testid="stRadio"] [aria-checked="true"] div:first-child {
        border-color: var(--rabot-accent) !important;
        background: var(--rabot-accent) !important;
    }

    [data-testid="stMarkdownContainer"],
    [data-testid="stMarkdownContainer"] p,
    [data-testid="stMarkdownContainer"] span,
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: var(--rabot-text) !important;
        opacity: 1 !important;
    }

    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {
        color: var(--rabot-muted) !important;
    }

    [data-testid="stMarkdownContainer"] {
        overflow-x: auto;
    }

    [data-testid="stMarkdownContainer"] table {
        width: max-content;
        min-width: 100%;
        table-layout: auto;
        border-collapse: collapse;
        font-size: 0.9rem;
    }

    [data-testid="stMarkdownContainer"] table th,
    [data-testid="stMarkdownContainer"] table td {
        white-space: nowrap;
        word-break: keep-all;
        overflow-wrap: normal;
        padding: 0.72rem 0.9rem;
        vertical-align: middle;
        border-color: rgba(91, 64, 43, 0.14) !important;
    }

    [data-testid="stMarkdownContainer"] table th {
        color: var(--rabot-text) !important;
        font-weight: 760;
        background: rgba(255, 253, 248, 0.58);
    }

    [data-testid="stMarkdownContainer"] table td {
        color: var(--rabot-text) !important;
    }

    [data-testid="stMarkdownContainer"] table th:not(:first-child),
    [data-testid="stMarkdownContainer"] table td:not(:first-child) {
        text-align: right;
    }

    [data-testid="stMarkdownContainer"] table th:nth-child(2),
    [data-testid="stMarkdownContainer"] table td:nth-child(2) {
        text-align: left;
    }

    div[role="listbox"],
    div[role="option"] {
        background: var(--rabot-card-solid) !important;
        color: var(--rabot-text) !important;
    }

    div[role="option"]:hover {
        background: rgba(217, 119, 69, 0.12) !important;
    }

    [data-testid="stDataFrame"],
    [data-testid="stTable"] {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--rabot-border);
        background: var(--rabot-card);
    }

    div[data-testid="stAlert"] {
        border-radius: 14px;
        border: 1px solid var(--rabot-border);
    }

    hr {
        border-color: var(--rabot-border);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_store() -> SQLiteStore:
    return SQLiteStore(get_db_path())


def load_news_store() -> NewsStore:
    return NewsStore(get_db_path())


def load_view_store() -> ViewStore:
    return ViewStore(get_db_path())


def fmt_num(value, suffix: str = "", digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):,.{digits}f}{suffix}"
    except Exception:
        return str(value)


def safe_float(value) -> Optional[float]:
    if value is None or pd.isna(value):
        return None

    try:
        if isinstance(value, str):
            value = value.strip().replace("%", "").replace(",", "")
        return float(value)
    except Exception:
        return None


def fmt_delta(value) -> str | None:
    if value is None or pd.isna(value):
        return None

    value = safe_float(value)

    if value is None:
        return None

    if value > 0:
        return f"+{value:.2f}%"

    if value < 0:
        return f"{value:.2f}%"

    return "0.00%"


def html_text(value: Any, fallback: str = "") -> str:
    if value is None:
        return html.escape(fallback)

    text = str(value).strip()
    if not text:
        return html.escape(fallback)

    return html.escape(text)


def tone_class(tone: str | None, prefix: str = "rabot") -> str:
    tone = (tone or "neutral").lower()
    if tone not in {"positive", "negative", "neutral", "accent", "up", "down"}:
        tone = "neutral"
    return f"{prefix}-{tone}"


def infer_tone(value: Any, default: str = "neutral") -> str:
    number = safe_float(value)
    if number is not None:
        if number > 0:
            return "up"
        if number < 0:
            return "down"
        return default

    text = str(value or "").lower()
    up_words = ["强", "多", "改善", "支撑", "上行", "健康", "利多", "偏强", "positive", "bull", "good"]
    down_words = ["弱", "空", "下行", "利空", "偏弱", "negative", "bear", "bad"]
    risk_words = ["风险", "压力", "回撤"]

    if any(word in text for word in risk_words):
        return "negative"

    if any(word in text for word in down_words):
        return "down"

    if any(word in text for word in up_words):
        return "up"

    return default


def render_tag_row(tags, extra_class: str = "") -> None:
    if tags is None:
        return

    if isinstance(tags, (str, int, float)):
        tag_items = [(str(tags), "accent")]
    else:
        tag_items = []
        for item in tags:
            if item is None:
                continue
            if isinstance(item, dict):
                tag_items.append((item.get("label") or item.get("text") or "", item.get("tone", "neutral")))
            elif isinstance(item, (tuple, list)) and item:
                tag_items.append((item[0], item[1] if len(item) > 1 else "neutral"))
            else:
                tag_items.append((item, "neutral"))

    chips = []
    for label, tone in tag_items:
        label = str(label).strip()
        if not label:
            continue
        chips.append(f'<span class="rabot-tag {tone_class(tone, "rabot-tag")}">{html.escape(label)}</span>')

    if not chips:
        return

    class_name = "rabot-tag-row"
    if extra_class:
        class_name += f" {html.escape(extra_class)}"

    st.markdown(f'<div class="{class_name}">{"".join(chips)}</div>', unsafe_allow_html=True)


def _render_tag_html(tag: Any, tone: str = "neutral") -> str:
    if tag is None or str(tag).strip() == "":
        return ""

    return (
        '<div class="rabot-tag-row">'
        f'<span class="rabot-tag {tone_class(tone, "rabot-tag")}">{html_text(tag)}</span>'
        "</div>"
    )


def render_center_metric_card(title, value, tag=None, delta=None, tone: str = "neutral") -> None:
    tone = (tone or "neutral").lower()
    value_text = html_text(value, "N/A")
    value_text = value_text.replace("\n", "<br>")
    raw_value = str(value or "")
    value_class = "rabot-card-value"
    if "<br>" in value_text:
        value_class += " rabot-card-value-compact"
    elif re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_value.strip()):
        value_class += " rabot-card-value-date"
    tag_html = _render_tag_html(tag, tone if tone != "accent" else "accent")
    delta_html = ""

    if delta is not None and str(delta).strip():
        delta_tone = infer_tone(delta, "neutral")
        delta_html = (
            f'<div class="rabot-card-subtitle rabot-tone-{delta_tone}">'
            f"{html_text(delta)}</div>"
        )

    st.markdown(
        f"""
        <div class="rabot-card rabot-card-{tone}">
            <div class="rabot-card-title">{html_text(title)}</div>
            <div class="{value_class}">{value_text}</div>
            {tag_html}
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_status_card(title, value, tag=None, tone: str = "neutral") -> None:
    render_center_metric_card(title=title, value=value, tag=tag, delta=None, tone=tone)


def render_text_card(title, text, tag=None, tone: str = "neutral") -> None:
    body = html_text(text, "暂无数据")
    tag_html = _render_tag_html(tag, tone)
    st.markdown(
        f"""
        <div class="rabot-text-card">
            <div class="rabot-section-title">{html_text(title)}</div>
            {tag_html}
            <div class="rabot-text-body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_bullet_card(title, items, empty_text: str = "暂无数据", tone: str = "neutral") -> None:
    if items is None:
        clean_items = []
    elif isinstance(items, str):
        clean_items = [items] if items.strip() else []
    else:
        clean_items = [str(item).strip() for item in items if item is not None and str(item).strip()]

    if clean_items:
        body = "<ul class=\"rabot-bullet-list\">" + "".join(
            f"<li>{html.escape(item)}</li>" for item in clean_items
        ) + "</ul>"
    else:
        body = f'<div class="rabot-card-subtitle">{html_text(empty_text)}</div>'

    st.markdown(
        f"""
        <div class="rabot-text-card">
            <div class="rabot-section-title rabot-tone-{html.escape(tone)}">{html_text(title)}</div>
            {body}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_heat_dashboard(perf_df: pd.DataFrame) -> None:
    if perf_df.empty or "symbol" not in perf_df.columns:
        render_section_card("市场热力排行榜", "暂无可展示的热力数据。", tag="Heat", tone="accent")
        return

    score_col = None
    for candidate in ["近1月收益率%", "近3月收益率%", "YTD收益率%", "近1周收益率%"]:
        if candidate in perf_df.columns:
            score_col = candidate
            break

    if score_col is None:
        render_section_card("市场热力排行榜", "暂无收益率字段，暂时无法生成热力仪表盘。", tag="Heat", tone="accent")
        return

    data = perf_df[["symbol", score_col]].copy()
    data[score_col] = pd.to_numeric(data[score_col], errors="coerce")
    data = data.dropna(subset=[score_col]).sort_values(score_col, ascending=False).head(8)

    if data.empty:
        render_section_card("市场热力排行榜", "暂无可展示的热力数据。", tag=score_col, tone="accent")
        return

    min_value = float(data[score_col].min())
    max_value = float(data[score_col].max())
    span = max(max_value - min_value, 1e-9)

    rows = []
    for _, row in data.iterrows():
        value = float(row[score_col])
        width = 12 + ((value - min_value) / span) * 88 if span else 50
        tone = "up" if value >= 0 else "down"
        fill = "linear-gradient(90deg, #D97745, #B84A3A)" if value >= 0 else "linear-gradient(90deg, #4F8A5B, #79A985)"
        rows.append(
            '<div class="rabot-heat-row">'
            f'<div class="rabot-heat-symbol">{html_text(row.get("symbol", ""))}</div>'
            '<div class="rabot-heat-track">'
            f'<div class="rabot-heat-fill" style="width:{width:.1f}%; background:{fill};"></div>'
            "</div>"
            f'<div class="rabot-heat-value rabot-tone-{tone}">{value:+.2f}%</div>'
            "</div>"
        )

    st.markdown(
        '<div class="rabot-section-card">'
        '<div class="rabot-section-title">市场热力排行榜</div>'
        '<div class="rabot-tag-row">'
        f'<span class="rabot-tag">{html_text(score_col)}</span>'
        f'<span class="rabot-tag rabot-tag-neutral">Top {len(data)}</span>'
        "</div>"
        f'<div class="rabot-heat-list">{"".join(rows)}</div>'
        "</div>",
        unsafe_allow_html=True,
    )


def render_backend_status(status_items: list[tuple[str, bool]]) -> None:
    chips = []
    for label, ok in status_items:
        status_class = "rabot-status-chip-ok" if ok else "rabot-status-chip-bad"
        symbol = "✓" if ok else "✕"
        text = "已连接" if ok else "未连接"
        chips.append(
            f'<span class="rabot-status-chip {status_class}">'
            f"{symbol} {html_text(label)}：{text}</span>"
        )

    if not chips:
        return

    st.markdown(
        f'<div class="rabot-backend-status">{"".join(chips)}</div>',
        unsafe_allow_html=True,
    )


def get_latest_asset_price(symbol: str) -> tuple[str | None, float | None]:
    if not symbol:
        return None, None

    try:
        df = SQLiteStore(get_db_path()).read_index_daily(symbol=symbol)
        if df.empty or "date" not in df.columns or "close" not in df.columns:
            return None, None

        data = df.copy()
        data["date_dt"] = pd.to_datetime(data["date"], errors="coerce")
        data["close"] = pd.to_numeric(data["close"], errors="coerce")
        data = data.dropna(subset=["date_dt", "close"]).sort_values("date_dt")

        if data.empty:
            return None, None

        latest = data.iloc[-1]
        return latest["date_dt"].strftime("%Y-%m-%d"), float(latest["close"])
    except Exception:
        return None, None


def save_research_view(
    source: str,
    scope: str,
    symbol: str | None,
    title: str,
    view_text: str,
    horizon_days: int = 7,
) -> tuple[bool, str]:
    if not str(view_text or "").strip():
        return False, "暂无可保存的观点文本。"

    base_date = None
    base_price = None

    if scope == "single_asset" and symbol:
        base_date, base_price = get_latest_asset_price(symbol)

    if base_date is None:
        base_date = datetime.now().strftime("%Y-%m-%d")

    try:
        view_id = load_view_store().create_view(
            source=source,
            scope=scope,
            symbol=symbol or "",
            title=title,
            view_text=view_text,
            horizon_days=horizon_days,
            base_date=base_date,
            base_price=base_price,
            status="observing",
        )
    except Exception as e:
        return False, f"保存失败：{type(e).__name__}: {e}"

    if not view_id:
        return False, "保存失败，请稍后重试。"

    return True, f"已保存为观点记录 #{view_id}。"


def fmt_return(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):+.2f}%"
    except Exception:
        return str(value)


def status_label(status: str) -> str:
    return {
        "observing": "观察中",
        "validated": "已验证",
        "invalidated": "已失效",
        "archived": "已归档",
    }.get(status, status or "N/A")


def render_view_card(row: pd.Series) -> None:
    view = row.to_dict()
    view_id = int(view.get("id"))
    status = str(view.get("status") or "observing")
    title = view.get("title") or f"观点 #{view_id}"
    symbol = view.get("symbol") or "全市场"

    with st.container(border=True):
        top_cols = st.columns([2.2, 1, 1, 1])
        with top_cols[0]:
            st.markdown(f"**{title}**")
            render_tag_row(
                [
                    (view.get("source") or "unknown", "accent"),
                    (view.get("scope") or "unknown", "neutral"),
                    (symbol, "neutral"),
                    (status_label(status), "positive" if status == "validated" else "negative" if status == "invalidated" else "accent"),
                ]
            )
            st.caption(f"创建：{view.get('created_at', 'N/A')}｜基准：{view.get('base_date', 'N/A')}｜周期：{view.get('horizon_days', 7)}天")

        with top_cols[1]:
            render_center_metric_card("基准价格", fmt_num(view.get("base_price")), tag="base", tone="neutral")
        with top_cols[2]:
            render_center_metric_card("5日表现", fmt_return(view.get("forward_return_5d")), tag="forward", tone=infer_tone(view.get("forward_return_5d"), "neutral"))
        with top_cols[3]:
            render_center_metric_card("20日表现", fmt_return(view.get("forward_return_20d")), tag="forward", tone=infer_tone(view.get("forward_return_20d"), "neutral"))

        metric_cols = st.columns(3)
        with metric_cols[0]:
            st.caption(f"1日后续收益：{fmt_return(view.get('forward_return_1d'))}")
        with metric_cols[1]:
            st.caption(f"5日后续收益：{fmt_return(view.get('forward_return_5d'))}")
        with metric_cols[2]:
            st.caption(f"20日后续收益：{fmt_return(view.get('forward_return_20d'))}")

        with st.expander("查看观点正文与复盘", expanded=False):
            render_text_card("观点正文", view.get("view_text", ""), tag=view.get("source", ""), tone="accent")
            render_text_card("系统复盘", view.get("review_result", "") or "暂无复盘结果。", tag="review", tone="neutral")

        note_key = f"view_note_{view_id}"
        status_key = f"view_status_{view_id}"
        delete_key = f"view_delete_{view_id}"

        action_cols = st.columns([1.2, 2.5, 1, 1])
        with action_cols[0]:
            next_status = st.selectbox(
                "状态",
                options=["observing", "validated", "invalidated", "archived"],
                index=["observing", "validated", "invalidated", "archived"].index(status) if status in ["observing", "validated", "invalidated", "archived"] else 0,
                format_func=status_label,
                key=status_key,
            )

        with action_cols[1]:
            user_note = st.text_area(
                "备注",
                value=str(view.get("user_note") or ""),
                height=82,
                key=note_key,
            )

        with action_cols[2]:
            if st.button("保存状态", key=f"save_view_{view_id}", use_container_width=True, type="primary"):
                ok = load_view_store().update_view_status(view_id, next_status, user_note=user_note)
                if ok:
                    st.success("观点状态已保存。")
                    st.rerun()
                else:
                    st.error("保存失败。")

        with action_cols[3]:
            confirm_delete = st.checkbox("确认删除", key=delete_key)
            if st.button("删除观点", key=f"delete_view_{view_id}", use_container_width=True, disabled=not confirm_delete):
                ok = load_view_store().delete_view(view_id)
                if ok:
                    st.success("观点已删除。")
                    st.rerun()
                else:
                    st.error("删除失败。")


def render_view_review_tab(all_data: pd.DataFrame, config_map: dict) -> None:
    render_section_card(
        "RAbot 观点复盘",
        "记录 AI 快评和研究对话中的判断，并用后续行情表现做轻量复盘。结果只用于研究过程管理，不构成投资建议。",
        tag="Research Journal",
        tone="accent",
    )

    action_cols = st.columns([1.35, 1.35, 4])
    with action_cols[0]:
        if st.button("刷新观察中观点", use_container_width=True, type="primary"):
            with st.spinner("正在复盘观察中观点..."):
                result = ViewReviewer().refresh_all_observing_views()
            st.success(f"已刷新 {len(result)} 条观察中观点。")
            if not result.empty:
                st.dataframe(result, use_container_width=True, hide_index=True)

    with action_cols[1]:
        if st.button("清空筛选", use_container_width=True):
            for key in ["view_filter_status", "view_filter_symbol", "view_filter_source", "view_filter_limit"]:
                st.session_state.pop(key, None)
            st.rerun()

    available_symbols = []
    if all_data is not None and not all_data.empty and "symbol" in all_data.columns:
        available_symbols = sorted(all_data["symbol"].dropna().astype(str).unique().tolist())

    filter_cols = st.columns([1, 1, 1, 1])
    with filter_cols[0]:
        status_filter = st.selectbox(
            "状态筛选",
            options=["全部", "observing", "validated", "invalidated", "archived"],
            format_func=lambda x: "全部" if x == "全部" else status_label(x),
            key="view_filter_status",
        )
    with filter_cols[1]:
        symbol_filter = st.selectbox(
            "标的筛选",
            options=["全部"] + available_symbols,
            key="view_filter_symbol",
        )
    with filter_cols[2]:
        source_filter = st.selectbox(
            "来源筛选",
            options=["全部", "ai_quick_view", "ai_chat", "manual"],
            key="view_filter_source",
        )
    with filter_cols[3]:
        limit = st.selectbox(
            "显示条数",
            options=[20, 50, 100],
            index=0,
            key="view_filter_limit",
        )

    views = load_view_store().list_views(
        limit=int(limit),
        status=None if status_filter == "全部" else status_filter,
        symbol=None if symbol_filter == "全部" else symbol_filter,
        source=None if source_filter == "全部" else source_filter,
    )

    if views.empty:
        st.info("暂无观点记录。可以先在 AI 快评或 AI 研究对话中保存观点。")
        return

    st.caption(f"当前显示 {len(views)} 条观点记录。")
    for _, row in views.iterrows():
        render_view_card(row)


def alert_tone(level: str) -> str:
    if level in {"critical", "warning"}:
        return "negative"
    if level == "watch":
        return "accent"
    return "neutral"


def alert_level_label(level: str) -> str:
    return {
        "info": "信息",
        "watch": "观察",
        "warning": "预警",
        "critical": "严重",
    }.get(level, level or "N/A")


def render_alert_card(row: pd.Series) -> None:
    import json

    alert = row.to_dict()
    alert_id = int(alert.get("id"))
    level = str(alert.get("level") or "info")
    tone = alert_tone(level)
    symbols = str(alert.get("symbols") or "")
    evidence_text = "{}"

    try:
        evidence_text = json.dumps(json.loads(alert.get("evidence_json") or "{}"), ensure_ascii=False, indent=2)
    except Exception:
        evidence_text = str(alert.get("evidence_json") or "{}")

    st.markdown(
        '<div class="rabot-alert-card">'
        f'<div class="rabot-alert-title">{html_text(alert.get("title", "研究预警"))}</div>'
        '<div class="rabot-tag-row">'
        f'<span class="rabot-tag {tone_class(tone, "rabot-tag")}">{html_text(alert_level_label(level))}</span>'
        f'<span class="rabot-tag rabot-tag-neutral">{html_text(alert.get("alert_type", ""))}</span>'
        f'<span class="rabot-tag rabot-tag-neutral">{html_text(symbols or "全市场")}</span>'
        '</div>'
        f'<div class="rabot-alert-message">{html_text(alert.get("message", ""))}</div>'
        f'<div class="rabot-card-subtitle">创建时间：{html_text(alert.get("created_at", ""))}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    with st.expander(f"证据与备注 #{alert_id}", expanded=False):
        st.code(evidence_text, language="json")
        note = st.text_area(
            "用户备注",
            value=str(alert.get("user_note") or ""),
            key=f"alert_note_{alert_id}",
            height=90,
        )
        col1, col2, col3 = st.columns([1.2, 1.2, 4])
        with col1:
            if st.button("保存备注", key=f"save_alert_note_{alert_id}", use_container_width=True, type="primary"):
                ok = AlertsStore().update_note(alert_id, note)
                if ok:
                    st.success("备注已保存。")
                    st.rerun()
                else:
                    st.error("备注保存失败。")
        with col2:
            if st.button("归档预警", key=f"archive_alert_{alert_id}", use_container_width=True):
                ok = AlertsStore().archive_alert(alert_id)
                if ok:
                    st.success("预警已归档。")
                    st.rerun()
                else:
                    st.error("归档失败。")


def render_today_alerts_preview(watchlist_symbols: list[str]) -> None:
    st.subheader("今日研究预警")
    store = AlertsStore()
    alerts = store.list_alerts(limit=5, status="active")

    if not alerts.empty and "level" in alerts.columns:
        alerts["_priority"] = alerts["level"].map({"critical": 0, "warning": 1, "watch": 2, "info": 3}).fillna(9)
        alerts = alerts.sort_values(["_priority", "id"], ascending=[True, False]).head(5)

    if alerts.empty:
        render_section_card("今日研究预警", "暂无活跃预警。可以点击下方按钮生成今日预警。", tag="Alerts", tone="neutral")
    else:
        items = [
            f"{alert_level_label(row.level)}｜{row.title}"
            for _, row in alerts.iterrows()
        ]
        render_bullet_card("活跃预警", items, empty_text="暂无活跃预警。", tone="accent")

    if st.button("生成今日预警", key="today_generate_alerts", use_container_width=True, type="primary"):
        with st.spinner("正在生成研究预警..."):
            generated = AlertsEngine().generate_alerts(watchlist_symbols=watchlist_symbols)
            saved = AlertsStore().save_alerts(generated)
        st.success(f"生成 {len(generated)} 条预警，新增保存 {saved} 条。")
        st.rerun()


def render_alerts_tab(watchlist_symbols: list[str]) -> None:
    render_section_card(
        "RAbot 研究预警",
        "基于行情、新闻、宏观和跨资产关系生成研究提示，不构成交易建议。",
        tag="Research Alerts",
        tone="accent",
    )

    action_cols = st.columns([1.3, 1.1, 1.1, 3.5])
    with action_cols[0]:
        if st.button("生成今日预警", use_container_width=True, type="primary"):
            with st.spinner("正在生成研究预警..."):
                alerts = AlertsEngine().generate_alerts(watchlist_symbols=watchlist_symbols)
                saved = AlertsStore().save_alerts(alerts)
            st.success(f"生成 {len(alerts)} 条预警，新增保存 {saved} 条。")
            st.rerun()
    with action_cols[1]:
        if st.button("刷新列表", use_container_width=True):
            st.rerun()
    with action_cols[2]:
        if st.button("清理旧预警", use_container_width=True):
            removed = AlertsStore().clear_old_alerts(keep_latest=300)
            st.success(f"已清理 {removed} 条旧预警。")
            st.rerun()

    filter_cols = st.columns(4)
    with filter_cols[0]:
        status_filter = st.selectbox("状态", ["全部", "active", "archived"], index=1, key="alert_filter_status")
    with filter_cols[1]:
        type_filter = st.selectbox(
            "类型",
            ["全部", "trend_alert", "risk_alert", "macro_alert", "news_alert", "cross_asset_alert", "data_alert"],
            key="alert_filter_type",
        )
    with filter_cols[2]:
        level_filter = st.selectbox("等级", ["全部", "info", "watch", "warning", "critical"], key="alert_filter_level")
    with filter_cols[3]:
        limit = st.selectbox("显示条数", [20, 50, 100], key="alert_filter_limit")

    store = AlertsStore()
    alerts = store.list_alerts(
        limit=int(limit),
        status=None if status_filter == "全部" else status_filter,
        alert_type=None if type_filter == "全部" else type_filter,
        level=None if level_filter == "全部" else level_filter,
    )

    active_alerts = store.list_alerts(limit=1000, status="active")
    active_total = len(active_alerts)
    warn_total = int(active_alerts["level"].isin(["warning", "critical"]).sum()) if not active_alerts.empty and "level" in active_alerts.columns else 0
    news_total = int((active_alerts["alert_type"] == "news_alert").sum()) if not active_alerts.empty and "alert_type" in active_alerts.columns else 0
    cross_total = int((active_alerts["alert_type"] == "cross_asset_alert").sum()) if not active_alerts.empty and "alert_type" in active_alerts.columns else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_center_metric_card("活跃预警", active_total, tag="active", tone="accent")
    with m2:
        render_center_metric_card("高等级预警", warn_total, tag="warning/critical", tone="negative" if warn_total else "neutral")
    with m3:
        render_center_metric_card("新闻预警", news_total, tag="news", tone="accent")
    with m4:
        render_center_metric_card("跨资产预警", cross_total, tag="cross", tone="accent")

    if alerts.empty:
        st.info("暂无符合筛选条件的研究预警。")
        return

    st.caption(f"当前显示 {len(alerts)} 条预警。")
    for _, row in alerts.iterrows():
        render_alert_card(row)


def pick_existing_watchlist(all_data: pd.DataFrame, selected: list[str] | None = None) -> list[str]:
    if all_data is None or all_data.empty or "symbol" not in all_data.columns:
        return []

    available = set(all_data["symbol"].dropna().astype(str).unique().tolist())
    candidates = selected or DEFAULT_WATCHLIST
    picked = [symbol for symbol in candidates if symbol in available]

    if picked:
        return picked

    return [symbol for symbol in DEFAULT_WATCHLIST if symbol in available]


def _perf_value(row: pd.Series, column: str, suffix: str = "%") -> str:
    if column not in row.index:
        return "N/A"

    value = row.get(column)
    if value is None or pd.isna(value):
        return "N/A"

    try:
        return f"{float(value):.2f}{suffix}"
    except Exception:
        return str(value)


def render_watchlist_asset_card(row: pd.Series, config_map: dict) -> None:
    symbol = str(row.get("symbol", ""))
    name = str(row.get("name") or (config_map[symbol].name if symbol in config_map else symbol))
    month_value = safe_float(row.get("近1月收益率%"))
    tone = "up" if month_value is not None and month_value >= 0 else "down" if month_value is not None else "neutral"

    st.markdown(
        f"""
        <div class="rabot-card rabot-card-{tone}">
            <div class="rabot-card-title">{html_text(symbol)}</div>
            <div class="rabot-card-subtitle">{html_text(name)}</div>
            <div class="rabot-card-value">{_perf_value(row, "近1月收益率%")}</div>
            <div class="rabot-tag-row">
                <span class="rabot-tag {tone_class(tone, "rabot-tag")}">近1月</span>
                <span class="rabot-tag rabot-tag-neutral">近1周 {_perf_value(row, "近1周收益率%")}</span>
            </div>
            <div class="rabot-card-subtitle">
                波动 {_perf_value(row, "20日年化波动率%")} ｜ 回撤 {_perf_value(row, "当前回撤%")}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_temperature_card(perf_df: pd.DataFrame) -> None:
    if perf_df is None or perf_df.empty or "近1月收益率%" not in perf_df.columns:
        render_center_metric_card("市场温度", "N/A", tag="暂无数据", tone="neutral")
        return

    returns = pd.to_numeric(perf_df["近1月收益率%"], errors="coerce").dropna()
    if returns.empty:
        render_center_metric_card("市场温度", "N/A", tag="暂无数据", tone="neutral")
        return

    positive_ratio = float((returns > 0).mean())
    avg_return = float(returns.mean())
    temperature = max(0, min(100, int(round(positive_ratio * 70 + max(min(avg_return, 20), -20) / 40 * 30 + 15))))

    if temperature >= 68:
        label = "偏热"
        tone = "up"
    elif temperature <= 42:
        label = "偏冷"
        tone = "down"
    else:
        label = "中性"
        tone = "accent"

    st.markdown(
        '<div class="rabot-section-card">'
        '<div class="rabot-section-title">市场温度</div>'
        f'<div class="rabot-card-value rabot-tone-{tone}">{temperature}/100</div>'
        '<div class="rabot-heat-track" style="height:12px; margin:0.35rem 0 0.55rem;">'
        f'<div class="rabot-heat-fill" style="width:{temperature}%;"></div>'
        '</div>'
        '<div class="rabot-tag-row">'
        f'<span class="rabot-tag {tone_class(tone, "rabot-tag")}">{label}</span>'
        f'<span class="rabot-tag rabot-tag-neutral">上涨占比 {positive_ratio:.0%}</span>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


def render_today_heat_modules(perf_df: pd.DataFrame) -> None:
    heat_col1, heat_col2, heat_col3 = st.columns([1, 1.25, 1.25])

    with heat_col1:
        render_market_temperature_card(perf_df)

    with heat_col2:
        render_bullet_card(
            "今日热力榜",
            perf_bullets(perf_df, "近1月收益率%", ascending=False, value_label="近1月", limit=5),
            empty_text="暂无热力数据",
            tone="up",
        )

    with heat_col3:
        render_bullet_card(
            "风险关注榜",
            perf_bullets(perf_df, "20日年化波动率%", ascending=False, value_label="20日波动", limit=5),
            empty_text="暂无风险数据",
            tone="accent",
        )


def perf_bullets(perf_df: pd.DataFrame, column: str, ascending: bool, value_label: str, limit: int = 3) -> list[str]:
    if perf_df is None or perf_df.empty or column not in perf_df.columns or "symbol" not in perf_df.columns:
        return []

    data = perf_df.copy()
    data[column] = pd.to_numeric(data[column], errors="coerce")
    data = data.dropna(subset=[column]).sort_values(column, ascending=ascending).head(limit)

    return [f"{row.symbol}｜{value_label} {float(row[column]):.2f}%" for _, row in data.iterrows()]


def render_today_ai_entry() -> None:
    st.subheader("问 RAbot 今日市场")

    question = st.text_area(
        "今日快问",
        value=st.session_state.get("today_ai_question", ""),
        placeholder="例如：今天全球资产主线是什么？我应该重点观察哪些风险？",
        key="today_ai_question_input",
        height=110,
        label_visibility="collapsed",
    )

    col_left, col_ask, col_clear, col_right = st.columns([2.2, 1.35, 1.35, 2.2])

    with col_ask:
        ask_clicked = st.button("询问 RAbot", key="today_ai_ask_button", use_container_width=True, type="primary")

    with col_clear:
        clear_clicked = st.button("清空回答", key="today_ai_clear_button", use_container_width=True)

    if clear_clicked:
        st.session_state.pop("today_ai_answer", None)
        st.session_state.pop("today_ai_answer_meta", None)
        st.session_state.pop("today_ai_question", None)
        st.rerun()

    if ask_clicked:
        clean_question = str(question or "").strip()
        st.session_state["today_ai_question"] = clean_question

        if not clean_question:
            st.warning("请先输入一个问题。")
        else:
            try:
                with st.spinner("RAbot 正在构造今日市场事实包并调用 LLM ..."):
                    chat = RAbotResearchChat()
                    result = chat.answer_question(question=clean_question, scope="market")

                st.session_state["today_ai_answer"] = result.text
                st.session_state["today_ai_answer_meta"] = {
                    "ok": result.ok,
                    "model": result.model,
                }
            except Exception as e:
                st.session_state["today_ai_answer"] = f"{type(e).__name__}: {e}"
                st.session_state["today_ai_answer_meta"] = {
                    "ok": False,
                    "model": "N/A",
                }

    answer = st.session_state.get("today_ai_answer")
    meta = st.session_state.get("today_ai_answer_meta", {})

    if answer:
        render_text_card(
            "RAbot 今日回答",
            answer,
            tag=f"模型：{meta.get('model', 'N/A')}",
            tone="accent" if meta.get("ok") else "negative",
        )
    else:
        render_section_card(
            "今日 AI 快问入口",
            "输入一个市场问题，RAbot 会基于本地行情、新闻、宏观和规则层研究事实包回答。",
            tag="Market Scope",
            tone="accent",
        )


def render_today_overview(
    all_data: pd.DataFrame,
    all_news: pd.DataFrame,
    all_macro: pd.DataFrame,
    config_map: dict,
    watchlist_symbols: list[str],
) -> None:
    st.subheader("RAbot Research Desk")

    if all_data is None or all_data.empty:
        st.info("暂无行情数据，请先更新行情数据。")
        return

    data = all_data.copy()
    latest_date = pd.to_datetime(data["date"], errors="coerce").max() if "date" in data.columns else pd.NaT
    latest_date_text = "N/A" if pd.isna(latest_date) else latest_date.strftime("%Y-%m-%d")
    news_count = 0 if all_news is None else len(all_news)
    macro_count = 0

    if all_macro is not None and not all_macro.empty and "symbol" in all_macro.columns:
        macro_count = int(all_macro["symbol"].nunique())

    header_col1, header_col2, header_col3, header_col4 = st.columns([1.6, 1, 1, 1])

    with header_col1:
        render_section_card(
            "RAbot Research Desk",
            "今日全球资产研究总览",
            tag="Opening Screen",
            tone="accent",
        )

    with header_col2:
        render_center_metric_card("当前数据日期", latest_date_text, tag="行情覆盖", tone="accent")

    with header_col3:
        render_center_metric_card("新闻读取条数", f"{news_count} 条", tag="News", tone="neutral")

    with header_col4:
        render_center_metric_card("宏观指标数", f"{macro_count} 个", tag="Macro", tone="neutral")

    render_today_ai_entry()

    try:
        perf_df = build_asset_performance_table(data)
    except Exception as e:
        perf_df = pd.DataFrame()
        st.warning(f"市场表现表生成失败：{type(e).__name__}: {e}")

    if perf_df.empty:
        render_section_card("今日市场主线", "暂无足够数据生成市场主线。", tag="Market", tone="accent")
    else:
        try:
            market_overview = build_market_overview(perf_df)
        except Exception:
            market_overview = {}

        headline = market_overview.get("headline", "暂无足够数据生成市场主线")
        summary = market_overview.get("summary", "暂无足够数据生成市场主线。")
        render_section_card("今日市场主线", f"{headline}\n\n{summary}", tag="市场主线", tone="accent")

    st.subheader("市场仪表盘")
    render_today_heat_modules(perf_df)

    selected_watchlist = pick_existing_watchlist(data, watchlist_symbols)
    render_today_alerts_preview(watchlist_symbols=selected_watchlist)

    st.subheader("自选资产状态")

    if perf_df.empty or not selected_watchlist:
        st.info("暂无可展示的自选资产表现。")
    else:
        watch_perf = perf_df[perf_df["symbol"].astype(str).isin(selected_watchlist)].copy()
        if watch_perf.empty:
            st.info("自选资产暂无表现数据。")
        else:
            for start in range(0, len(watch_perf), 4):
                cols = st.columns(4)
                for col, (_, row) in zip(cols, watch_perf.iloc[start : start + 4].iterrows()):
                    with col:
                        render_watchlist_asset_card(row, config_map)

    st.subheader("强弱与风险雷达")
    radar_col1, radar_col2, radar_col3, radar_col4 = st.columns(4)

    with radar_col1:
        render_bullet_card(
            "强势资产",
            perf_bullets(perf_df, "近1月收益率%", ascending=False, value_label="近1月"),
            empty_text="暂无数据",
            tone="up",
        )

    with radar_col2:
        render_bullet_card(
            "弱势资产",
            perf_bullets(perf_df, "近1月收益率%", ascending=True, value_label="近1月"),
            empty_text="暂无数据",
            tone="down",
        )

    with radar_col3:
        render_bullet_card(
            "高波动资产",
            perf_bullets(perf_df, "20日年化波动率%", ascending=False, value_label="20日波动"),
            empty_text="暂无数据",
            tone="accent",
        )

    with radar_col4:
        render_bullet_card(
            "高回撤资产",
            perf_bullets(perf_df, "当前回撤%", ascending=True, value_label="当前回撤"),
            empty_text="暂无数据",
            tone="negative",
        )

    news_col, macro_col = st.columns(2)

    with news_col:
        st.subheader("新闻快照")
        if all_news is None or all_news.empty:
            render_section_card("新闻快照", "暂无新闻数据，请先更新新闻。", tag="News", tone="neutral")
        else:
            try:
                news_snapshot = build_news_market_snapshot(all_news, days=7)
            except Exception:
                news_snapshot = {}

            render_section_card(
                f"新闻快照：{news_snapshot.get('headline', '暂无新闻快照')}",
                news_snapshot.get("summary", "暂无新闻快照。"),
                tag="近7日",
                tone="accent",
            )
            render_bullet_card(
                "重点新闻",
                news_snapshot.get("top_news", [])[:5],
                empty_text="暂无重点新闻。",
                tone="accent",
            )

    with macro_col:
        st.subheader("宏观快照")
        if all_macro is None or all_macro.empty:
            render_section_card("宏观快照", "暂无宏观数据，请先更新宏观数据。", tag="Macro", tone="neutral")
        else:
            latest_macro_date = "N/A"
            if "date" in all_macro.columns:
                macro_dt = pd.to_datetime(all_macro["date"], errors="coerce").max()
                latest_macro_date = "N/A" if pd.isna(macro_dt) else macro_dt.strftime("%Y-%m-%d")
            elif "latest_date" in all_macro.columns:
                macro_dt = pd.to_datetime(all_macro["latest_date"], errors="coerce").max()
                latest_macro_date = "N/A" if pd.isna(macro_dt) else macro_dt.strftime("%Y-%m-%d")

            region_series = all_macro["region"].astype(str).str.upper() if "region" in all_macro.columns else pd.Series([], dtype=str)
            if not region_series.empty and "symbol" in all_macro.columns:
                us_count = int(all_macro.loc[region_series == "US", "symbol"].nunique())
                cn_count = int(all_macro.loc[region_series == "CN", "symbol"].nunique())
            else:
                us_count = 0
                cn_count = 0

            m1, m2, m3 = st.columns(3)
            with m1:
                render_center_metric_card("宏观指标", f"{macro_count}", tag="总数", tone="accent")
            with m2:
                render_center_metric_card("美国指标", f"{us_count}", tag="US", tone="neutral")
            with m3:
                render_center_metric_card("中国指标", f"{cn_count}", tag="CN", tone="neutral")

            render_section_card(
                "宏观说明",
                f"宏观指标包含日度、月度等不同频率。当前宏观数据最新覆盖日期：{latest_macro_date}。",
                tag="Data Coverage",
                tone="neutral",
            )

    st.subheader("最新简报入口")
    latest_report = get_latest_report_file()
    if latest_report:
        render_section_card(
            "最新简报",
            f"最新报告文件：{latest_report.name}\n可在“简报预览”tab 查看完整内容。",
            tag="Report",
            tone="accent",
        )
    else:
        render_section_card(
            "最新简报",
            "暂无可预览报告。可在“简报预览”tab 后台生成新简报。",
            tag="Report",
            tone="neutral",
        )


def render_section_card(title, body, tag=None, tone: str = "neutral") -> None:
    tag_html = _render_tag_html(tag, tone)
    st.markdown(
        f"""
        <div class="rabot-section-card">
            <div class="rabot-section-title">{html_text(title)}</div>
            {tag_html}
            <div class="rabot-text-body">{html_text(body, "暂无数据")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_macro_provider(indicator):
    if indicator.source == "fred":
        return FredGraphProvider()

    if indicator.source == "tushare":
        return ChinaTushareMacroProvider()

    raise ValueError(f"暂不支持的宏观数据源：{indicator.source}")


def update_macro_from_frontend(
    regions: list[str] | None = None,
    start_date: str = "2015-01-01",
) -> pd.DataFrame:
    if not MACRO_MODULE_READY:
        return pd.DataFrame(
            [
                {
                    "symbol": "MACRO_MODULE",
                    "name": "宏观模块",
                    "region": "",
                    "source": "",
                    "status": "failed",
                    "rows": 0,
                    "message": "宏观模块未正确导入，请检查 src/RAbot/macro 相关文件是否已创建。",
                }
            ]
        )

    store = MacroStore()
    indicators = iter_macro_indicators()

    if regions:
        wanted_regions = {x.upper() for x in regions}
        indicators = [x for x in indicators if x.region.upper() in wanted_regions]

    results = []

    for indicator in indicators:
        try:
            provider = get_macro_provider(indicator)
            df = provider.fetch_indicator(
                indicator=indicator,
                start_date=start_date,
                end_date=None,
            )

            if df is None or df.empty:
                msg = "未获取到数据，可能是接口权限、字段差异或数据源暂不可用。"
                store.log_update(
                    symbol=indicator.symbol,
                    name=indicator.name,
                    region=indicator.region,
                    source=indicator.source,
                    status="empty",
                    rows=0,
                    message=msg,
                )
                results.append(
                    {
                        "symbol": indicator.symbol,
                        "name": indicator.name,
                        "region": indicator.region,
                        "source": indicator.source,
                        "status": "empty",
                        "rows": 0,
                        "message": msg,
                    }
                )
                continue

            rows = store.upsert_macro_series(df)
            min_date = pd.to_datetime(df["date"], errors="coerce").min()
            max_date = pd.to_datetime(df["date"], errors="coerce").max()
            msg = f"更新成功：{rows} 行，区间 {min_date.date()} 至 {max_date.date()}"

            store.log_update(
                symbol=indicator.symbol,
                name=indicator.name,
                region=indicator.region,
                source=indicator.source,
                status="success",
                rows=rows,
                message=msg,
            )
            results.append(
                {
                    "symbol": indicator.symbol,
                    "name": indicator.name,
                    "region": indicator.region,
                    "source": indicator.source,
                    "status": "success",
                    "rows": rows,
                    "message": msg,
                }
            )

        except Exception as e:
            msg = f"{type(e).__name__}: {e}"
            store.log_update(
                symbol=indicator.symbol,
                name=indicator.name,
                region=indicator.region,
                source=indicator.source,
                status="failed",
                rows=0,
                message=msg,
            )
            results.append(
                {
                    "symbol": indicator.symbol,
                    "name": indicator.name,
                    "region": indicator.region,
                    "source": indicator.source,
                    "status": "failed",
                    "rows": 0,
                    "message": msg,
                }
            )

    return pd.DataFrame(results)


def auto_update_market_data_on_startup(
    configs,
    preferred_symbols: list[str] | None = None,
) -> None:
    """
    每个 Streamlit session 启动后自动刷新一次核心行情。

    只更新自选资产或 DEFAULT_WATCHLIST 中存在于配置里的资产；不改数据库结构，
    仍复用原有 update_all_indexes 管线。
    """
    if st.session_state.get("startup_market_update_done"):
        return

    config_symbols = {cfg.symbol for cfg in configs}
    preferred = preferred_symbols or st.session_state.get("watchlist_symbols") or DEFAULT_WATCHLIST
    symbols = [symbol for symbol in preferred if symbol in config_symbols]

    if not symbols:
        symbols = [cfg.symbol for cfg in configs if cfg.symbol in config_symbols]

    st.session_state["startup_market_update_done"] = True
    st.session_state["startup_market_update_symbols"] = symbols

    try:
        with st.spinner("正在自动更新最新行情数据..."):
            result = update_all_indexes(symbols=symbols, start=None, end=None)

        st.session_state["startup_market_update_result"] = result
        ok_count = int(result["success"].sum()) if not result.empty and "success" in result.columns else 0
        st.session_state["startup_market_update_message"] = f"启动自动行情更新完成：成功 {ok_count}/{len(symbols)}"

    except Exception as e:
        st.session_state["startup_market_update_result"] = pd.DataFrame()
        st.session_state["startup_market_update_message"] = f"启动自动行情更新失败：{type(e).__name__}: {e}"


def get_reports_dir() -> Path:
    reports_dir = PROJECT_DIR / "data" / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def read_report_file(path: str | Path | None) -> str:
    if not path:
        return ""

    try:
        file_path = Path(path)

        if not file_path.is_absolute():
            file_path = PROJECT_DIR / file_path

        if not file_path.exists():
            return ""

        return file_path.read_text(encoding="utf-8")

    except Exception:
        return ""


def get_latest_report_file() -> Optional[Path]:
    """
    从报告库中选择最新报告。

    规则：
    - 只扫描 data/reports；
    - 支持 .md / .markdown / .txt；
    - 按文件修改时间 mtime 选择最新；
    - 不相信 session_state、active job 或旧任务表路径。
    """
    reports_dir = get_reports_dir()

    candidates: list[Path] = []

    for pattern in ["*.md", "*.markdown", "*.txt"]:
        candidates.extend(reports_dir.glob(pattern))

    candidates = [
        p
        for p in candidates
        if p.is_file()
        and not p.name.startswith("~$")
        and p.stat().st_size > 0
    ]

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def looks_like_report_content(value: Any) -> bool:
    """
    判断字符串是 Markdown 报告正文，还是文件路径。

    之前“报告全绿”的问题就是：
    generate_index_markdown_report 返回了正文字符串，
    但前端误以为它是 output_path，于是整篇报告被塞进 st.success 绿色提示框。
    """
    if not isinstance(value, str):
        return False

    text = value.strip()

    if not text:
        return False

    if "\n" in text:
        return True

    if text.startswith("# "):
        return True

    if text.startswith("## "):
        return True

    if text.startswith("### "):
        return True

    if len(text) > 260:
        return True

    return False


def save_report_content_to_file(content: str) -> Path:
    """
    如果报告生成函数返回的是 Markdown 正文，就保存为真正的 md 文件。
    后续任务状态只存文件路径，避免 UI 变成全绿。
    """
    reports_dir = get_reports_dir()
    filename = f"rabot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = reports_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def normalize_report_path(value: Any) -> Optional[Path]:
    """
    把各种可能的返回值规范成真实报告路径。

    支持：
    - 绝对路径
    - 相对项目根目录的路径
    - 相对 data/reports 的文件名
    - Markdown 正文字符串
    """
    if value is None:
        return None

    if isinstance(value, str) and looks_like_report_content(value):
        return save_report_content_to_file(value)

    candidate = Path(str(value))
    reports_dir = get_reports_dir()

    if candidate.is_absolute():
        if candidate.exists():
            return candidate

        if str(candidate).lower().endswith((".md", ".markdown", ".txt")):
            return candidate

        return None

    project_candidate = PROJECT_DIR / candidate
    reports_candidate = reports_dir / candidate

    if project_candidate.exists():
        return project_candidate

    if reports_candidate.exists():
        return reports_candidate

    if str(candidate).lower().endswith((".md", ".markdown", ".txt")):
        return project_candidate

    return None


def call_generate_report_flexibly(enable_llm: bool = True) -> Any:
    """
    兼容不同版本的 generate_index_markdown_report 参数名。
    """
    func = generate_index_markdown_report

    try:
        signature = inspect.signature(func)
        params = signature.parameters
        kwargs: Dict[str, Any] = {}

        if "enable_llm" in params:
            kwargs["enable_llm"] = enable_llm
        elif "use_llm" in params:
            kwargs["use_llm"] = enable_llm
        elif "llm_enabled" in params:
            kwargs["llm_enabled"] = enable_llm
        elif "with_llm" in params:
            kwargs["with_llm"] = enable_llm

        return func(**kwargs)

    except TypeError:
        return func()


def generate_llm_report_background(
    enable_llm: bool = True,
    progress_callback=None,
) -> Dict[str, Any]:
    """
    后台生成报告。

    修复点：
    1. 如果 generate_index_markdown_report 返回文件路径，就使用路径；
    2. 如果返回 Markdown 正文，就保存成 data/reports/*.md；
    3. 如果没有返回可用路径，就找 reports 文件夹中新生成或修改的文件；
    4. 任务结果里永远只放路径，不放整篇正文。
    """
    if progress_callback:
        progress_callback(8, "正在准备本地行情、新闻与宏观数据。")

    reports_dir = get_reports_dir()

    before_files: Dict[str, float] = {}
    for pattern in ["*.md", "*.markdown", "*.txt"]:
        for file in reports_dir.glob(pattern):
            if file.is_file():
                before_files[str(file.resolve())] = file.stat().st_mtime

    before_latest = get_latest_report_file()

    if progress_callback:
        if enable_llm:
            progress_callback(25, "正在调用 DeepSeek 研究层生成简报。")
        else:
            progress_callback(25, "正在生成规则层 Markdown 简报。")

    result = call_generate_report_flexibly(enable_llm=enable_llm)

    if progress_callback:
        progress_callback(88, "正在确认报告文件保存结果。")

    report_path: Optional[Path] = None

    if isinstance(result, dict):
        for key in ["report_path", "output_path", "path", "file_path", "result"]:
            if result.get(key):
                report_path = normalize_report_path(result.get(key))
                if report_path:
                    break
    else:
        report_path = normalize_report_path(result)

    changed_files = []

    for pattern in ["*.md", "*.markdown", "*.txt"]:
        for file in reports_dir.glob(pattern):
            if not file.is_file():
                continue

            resolved = str(file.resolve())
            current_mtime = file.stat().st_mtime
            previous_mtime = before_files.get(resolved)

            if previous_mtime is None or current_mtime > previous_mtime:
                changed_files.append(file)

    if changed_files:
        report_path = max(changed_files, key=lambda p: p.stat().st_mtime)

    if report_path is None:
        after_latest = get_latest_report_file()

        if after_latest and after_latest != before_latest:
            report_path = after_latest
        elif after_latest:
            report_path = after_latest

    if progress_callback:
        progress_callback(96, "报告生成完成，正在写入任务结果。")

    output_path = str(report_path) if report_path else ""

    if looks_like_report_content(output_path):
        output_path = ""

    return {
        "report_path": output_path,
        "output_path": output_path,
        "enable_llm": enable_llm,
        "backend": "v2",
    }


def _v2_job_to_dict(job: Any) -> Optional[Dict[str, Any]]:
    if job is None:
        return None

    if isinstance(job, dict):
        return job

    result_json = getattr(job, "result_json", None) or {}

    output_path = (
        result_json.get("report_path")
        or result_json.get("output_path")
        or result_json.get("path")
        or result_json.get("file_path")
        or ""
    )

    if looks_like_report_content(output_path):
        output_path = ""

    return {
        "job_id": getattr(job, "job_id", ""),
        "job_type": getattr(job, "job_type", ""),
        "status": getattr(job, "status", "unknown"),
        "progress": getattr(job, "progress", 0),
        "message": getattr(job, "message", ""),
        "created_at": getattr(job, "created_at", ""),
        "updated_at": getattr(job, "updated_at", ""),
        "finished_at": getattr(job, "finished_at", None),
        "input_json": getattr(job, "input_json", {}) or {},
        "result_json": result_json,
        "output_path": output_path,
        "error": getattr(job, "error", None),
    }


def get_current_report_job() -> Optional[Dict[str, Any]]:
    job_id = st.session_state.get("active_report_job_id")

    if not job_id:
        return None

    if REPORT_JOB_BACKEND == "v2":
        job = get_job(job_id)
        return _v2_job_to_dict(job)

    if REPORT_JOB_BACKEND == "legacy":
        job = legacy_get_report_job(job_id)

        if job and isinstance(job, dict):
            output_path = job.get("output_path", "")
            if looks_like_report_content(output_path):
                job["output_path"] = ""

        return job

    return None


def start_background_report(enable_llm: bool = True) -> None:
    """
    启动后台报告任务。
    """
    st.session_state["report_job_done_toast_shown"] = False

    if REPORT_JOB_BACKEND == "v2":
        job_id = create_job(
            job_type="llm_report",
            input_data={
                "enable_llm": enable_llm,
                "source": "streamlit_app",
            },
        )

        st.session_state["active_report_job_id"] = job_id

        submitted = run_job_async(
            job_id,
            generate_llm_report_background,
            enable_llm=enable_llm,
        )

        if submitted:
            st.success("报告已进入后台生成队列。你现在可以继续使用其他功能。")
        else:
            st.warning("这个报告任务已经在运行中。")

        return

    if REPORT_JOB_BACKEND == "legacy":
        job_id = legacy_start_report_job(enable_llm=enable_llm)
        st.session_state["active_report_job_id"] = job_id
        st.success("报告已进入后台生成队列。你现在可以继续使用其他功能。")
        return

    st.error("报告后台任务模块不可用。请检查 src/RAbot/reporting/report_jobs.py。")


def render_report_job_status(compact: bool = False) -> None:
    """
    渲染当前后台报告任务状态。
    """
    job = get_current_report_job()

    if not job:
        if not compact:
            st.info("暂无后台报告任务。")
        return

    status = job.get("status", "unknown")
    progress = int(job.get("progress", 0) or 0)
    message = job.get("message", "")
    output_path = job.get("output_path", "")

    if looks_like_report_content(output_path):
        output_path = ""

    if status == "success":
        st.progress(100, text="报告生成完成")

        if output_path:
            st.success(f"报告生成完成：{output_path}")
        else:
            st.success("报告生成完成。")

        if not st.session_state.get("report_job_done_toast_shown"):
            st.toast("RAbot 报告已生成完成。", icon="✅")
            st.session_state["report_job_done_toast_shown"] = True

    elif status == "failed":
        st.progress(100, text="报告生成失败")
        st.error(job.get("error") or message or "报告生成失败。")

        if not st.session_state.get("report_job_done_toast_shown"):
            st.toast("RAbot 报告生成失败。", icon="⚠️")
            st.session_state["report_job_done_toast_shown"] = True

    else:
        safe_progress = max(0, min(100, progress))
        st.progress(safe_progress, text=message or "报告正在后台生成中。")

        if not compact:
            st.caption("后台生成不会阻塞页面。你可以切换到其他板块继续使用。")

    if not compact:
        with st.expander("查看后台任务详情", expanded=False):
            safe_job = dict(job)
            if looks_like_report_content(safe_job.get("output_path", "")):
                safe_job["output_path"] = "[已隐藏：任务历史中曾错误写入报告正文]"
            st.json(safe_job)


def render_recent_report_jobs(limit: int = 5) -> None:
    if REPORT_JOB_BACKEND != "v2":
        return

    jobs = list_jobs(job_type="llm_report", limit=limit)

    if not jobs:
        st.caption("暂无历史报告任务。")
        return

    with st.expander("最近报告任务", expanded=False):
        for raw_job in jobs:
            job = _v2_job_to_dict(raw_job)
            if not job:
                continue

            status = job.get("status", "unknown")
            progress = job.get("progress", 0)
            created_at = job.get("created_at", "")
            updated_at = job.get("updated_at", "")
            output_path = job.get("output_path", "")
            job_id = str(job.get("job_id", ""))

            if looks_like_report_content(output_path):
                output_path = ""

            if status == "success":
                label = "已完成"
            elif status == "failed":
                label = "失败"
            elif status == "running":
                label = "生成中"
            elif status == "pending":
                label = "等待中"
            else:
                label = status

            st.markdown(
                f"""
                **{label}** ｜ `{job_id[:8]}`  
                进度：{progress}%  
                创建时间：{created_at}  
                更新时间：{updated_at}
                """
            )

            if output_path:
                st.caption(f"报告路径：{output_path}")
            elif status == "success":
                st.caption("报告路径：未记录，预览区会直接读取 data/reports 中最新报告。")

            if status == "failed":
                with st.expander(f"错误详情 {job_id[:8]}", expanded=False):
                    st.code(job.get("error") or "未知错误", language="text")

            st.divider()


def load_best_report_preview() -> str:
    """
    加载简报预览文本。

    最终逻辑：
    - 永远从 data/reports 文件夹里按文件修改时间选择最新报告；
    - 不读取 session_state 中的旧路径；
    - 不读取 active job 的旧路径；
    - 不读取任务表里的旧 output_path；
    - 刷新页面后重新扫描报告库。
    """
    latest = get_latest_report_file()

    if latest:
        text = read_report_file(latest)
        if text:
            st.session_state["preview_report_path"] = str(latest)
            return text

    st.session_state["preview_report_path"] = ""
    return ""


def render_metric_cards(status: dict) -> None:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pct_change = status.get("pct_change")
        render_center_metric_card(
            "区间末收盘价",
            fmt_num(status.get("close")),
            tag="最新收盘",
            delta=fmt_delta(pct_change),
            tone=infer_tone(pct_change, "accent"),
        )

    with col2:
        status_label = status.get("status", "N/A")
        render_center_metric_card(
            "区间末状态",
            status_label,
            tag="MA20 / MA60 / MA120",
            tone=infer_tone(status_label, "accent"),
        )

    with col3:
        drawdown = status.get("drawdown")
        drawdown_value = safe_float(drawdown)
        drawdown_tone = "negative" if drawdown_value is not None and drawdown_value < -8 else "neutral"
        render_center_metric_card(
            "区间内回撤",
            fmt_num(drawdown, "%"),
            tag="相对区间高点",
            tone=drawdown_tone,
        )

    with col4:
        vol = status.get("volatility_20d")
        vol_value = safe_float(vol)
        vol_tone = "negative" if vol_value is not None and vol_value >= 30 else "neutral"
        render_center_metric_card(
            "20日年化波动率",
            fmt_num(vol, "%"),
            tag="基于日收益率",
            tone=vol_tone,
        )


def apply_plotly_paper_theme(fig: go.Figure) -> go.Figure:
    layout_kwargs: dict[str, Any] = {
        "plot_bgcolor": "rgba(0,0,0,0)",
        "paper_bgcolor": "rgba(0,0,0,0)",
        "font": dict(color="#2B2118"),
        "legend": dict(font=dict(color="#2B2118"), bgcolor="rgba(0,0,0,0)"),
    }

    if getattr(fig.layout.title, "text", None):
        layout_kwargs["title"] = dict(font=dict(color="#2B2118"))

    if "indicator" not in {getattr(trace, "type", "") for trace in fig.data}:
        layout_kwargs["xaxis"] = dict(
            gridcolor="rgba(91, 64, 43, 0.12)",
            zerolinecolor="rgba(91, 64, 43, 0.16)",
            linecolor="rgba(91, 64, 43, 0.18)",
        )
        layout_kwargs["yaxis"] = dict(
            gridcolor="rgba(91, 64, 43, 0.12)",
            zerolinecolor="rgba(91, 64, 43, 0.16)",
            linecolor="rgba(91, 64, 43, 0.18)",
        )

    fig.update_layout(**layout_kwargs)
    return fig


def plot_score_gauge(score: int, grade: str) -> go.Figure:
    score = max(0, min(100, int(score)))

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 36, "color": "#2B2118"}},
            title={"text": grade, "font": {"size": 20, "color": "#2B2118"}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#6F6257"},
                "bar": {"thickness": 0.28, "color": "#D97745"},
                "steps": [
                    {"range": [0, 36], "color": "rgba(184, 74, 58, 0.14)"},
                    {"range": [36, 52], "color": "rgba(217, 119, 69, 0.14)"},
                    {"range": [52, 68], "color": "rgba(111, 98, 87, 0.10)"},
                    {"range": [68, 82], "color": "rgba(79, 138, 91, 0.13)"},
                    {"range": [82, 100], "color": "rgba(79, 138, 91, 0.20)"},
                ],
                "threshold": {
                    "line": {"width": 4, "color": "#A94F2B"},
                    "thickness": 0.75,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        height=285,
        margin=dict(l=18, r=18, t=30, b=10),
    )

    return apply_plotly_paper_theme(fig)


def render_score_gauge_card(score: int, grade: str) -> None:
    score = max(0, min(100, int(score or 0)))
    grade_tone = infer_tone(grade, "accent")
    cx, cy = 120, 118
    arc_r = 82
    needle_r = 62
    theta = math.radians(180 - (score / 100) * 180)
    needle_x = cx + needle_r * math.cos(theta)
    needle_y = cy - needle_r * math.sin(theta)

    major_ticks = []
    minor_ticks = []

    for tick in range(0, 101, 10):
        tick_theta = math.radians(180 - tick * 1.8)
        is_major = tick % 50 == 0
        outer_r = 74
        inner_r = 60 if is_major else 66
        x1 = cx + outer_r * math.cos(tick_theta)
        y1 = cy - outer_r * math.sin(tick_theta)
        x2 = cx + inner_r * math.cos(tick_theta)
        y2 = cy - inner_r * math.sin(tick_theta)
        line = (
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="#6F6257" stroke-width="{1.8 if is_major else 1.1}" '
            f'stroke-linecap="round" opacity="{0.75 if is_major else 0.42}" />'
        )

        if is_major:
            major_ticks.append(line)
        else:
            minor_ticks.append(line)

    st.markdown(
        f"""
        <div class="rabot-section-card rabot-gauge-card">
            <div class="rabot-section-title">综合状态仪表盘</div>
            <div class="rabot-gauge-score">{score}/100</div>
            <div class="rabot-gauge-meter">
                <svg class="rabot-gauge-svg" viewBox="0 0 240 142" role="img" aria-label="score gauge">
                    <defs>
                        <linearGradient id="rabotGaugeGradient" x1="38" y1="{cy}" x2="202" y2="{cy}" gradientUnits="userSpaceOnUse">
                            <stop offset="0%" stop-color="#D97745" />
                            <stop offset="54%" stop-color="#C9894B" />
                            <stop offset="100%" stop-color="#4F8A5B" />
                        </linearGradient>
                        <filter id="rabotNeedleShadow" x="-20%" y="-20%" width="140%" height="140%">
                            <feDropShadow dx="0" dy="1" stdDeviation="1" flood-color="#2B2118" flood-opacity="0.18"/>
                        </filter>
                    </defs>
                    <path d="M 38 {cy} A {arc_r} {arc_r} 0 0 1 202 {cy}"
                          fill="none" stroke="url(#rabotGaugeGradient)"
                          stroke-width="15" stroke-linecap="round" />
                    <path d="M 49 {cy} A 71 71 0 0 1 191 {cy}"
                          fill="none" stroke="rgba(91, 64, 43, 0.10)"
                          stroke-width="1.4" stroke-linecap="round" />
                    {''.join(minor_ticks)}
                    {''.join(major_ticks)}
                    <line x1="{cx}" y1="{cy}" x2="{needle_x:.1f}" y2="{needle_y:.1f}"
                          stroke="#A94F2B" stroke-width="3.4" stroke-linecap="round"
                          filter="url(#rabotNeedleShadow)" />
                    <circle cx="{cx}" cy="{cy}" r="7" fill="#FFFDF8" stroke="#A94F2B" stroke-width="3.4" />
                    <circle cx="{cx}" cy="{cy}" r="2.5" fill="#A94F2B" />
                </svg>
            </div>
            <div class="rabot-gauge-ticks">
                <span>0</span><span>50</span><span>100</span>
            </div>
            <div class="rabot-tag-row">
                <span class="rabot-tag {tone_class(grade_tone, "rabot-tag")}">{html_text(grade)}</span>
                <span class="rabot-tag">{score}/100</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_research_cards(research: dict) -> None:
    st.subheader("RAbot 研究结论")

    score = int(research.get("score", 0))
    grade = research.get("grade", "N/A")

    gauge_col, cards_col = st.columns([1.25, 2.75])

    with gauge_col:
        render_score_gauge_card(score, grade)

    with cards_col:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            trend_label = research.get("trend_label", "N/A")
            render_status_card("趋势状态", trend_label, tag="均线结构", tone=infer_tone(trend_label, "neutral"))

        with col2:
            risk_label = research.get("risk_label", "N/A")
            render_status_card("风险状态", risk_label, tag="回撤维度", tone=infer_tone(risk_label, "neutral"))

        with col3:
            volatility_label = research.get("volatility_label", "N/A")
            render_status_card("波动状态", volatility_label, tag="20日波动率", tone=infer_tone(volatility_label, "neutral"))

        with col4:
            momentum_label = research.get("momentum_label", "N/A")
            render_status_card("动量状态", momentum_label, tag="近1月表现", tone=infer_tone(momentum_label, "neutral"))

        text_col1, text_col2 = st.columns(2)

        with text_col1:
            render_text_card("综合判断", research.get("summary", ""), tag=grade, tone=infer_tone(grade, "accent"))

        with text_col2:
            render_text_card("行动提示", research.get("action_hint", ""), tag="下一步观察", tone="accent")

        render_bullet_card("重点观察", research.get("watch_points", []), empty_text="暂无重点观察。", tone="accent")


def render_asset_news_research(asset_news: dict) -> None:
    st.subheader("相关新闻面观察")

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        render_center_metric_card("相关新闻", f"{asset_news.get('total_news', 0)} 条", tag="近7日", tone="accent")

    with col2:
        render_center_metric_card("高重要性", f"{asset_news.get('high_importance_count', 0)} 条", tag="重点跟踪", tone="accent")

    with col3:
        render_center_metric_card("偏利多", f"{asset_news.get('bullish_count', 0)} 条", tag="正向线索", tone="up")

    with col4:
        render_center_metric_card("偏利空", f"{asset_news.get('bearish_count', 0)} 条", tag="风险线索", tone="down")

    with col5:
        render_center_metric_card("平均重要性", f"{asset_news.get('avg_importance', 0)}/100", tag="综合权重", tone="neutral")

    alignment_label = asset_news.get("alignment_label", "无法判断")
    render_section_card(
        f"新闻面判断：{alignment_label}",
        asset_news.get("summary", ""),
        tag=alignment_label,
        tone=infer_tone(alignment_label, "accent"),
    )

    render_bullet_card(
        "重点新闻",
        asset_news.get("top_news", []),
        empty_text="暂无重点新闻。",
        tone="accent",
    )


def render_asset_macro_research(asset_macro: dict) -> None:
    st.subheader("宏观环境观察")

    macro_score = asset_macro.get("macro_score")
    macro_score_text = "N/A" if macro_score is None else f"{macro_score}/100"

    col1, col2, col3 = st.columns(3)

    with col1:
        render_center_metric_card("宏观评分", macro_score_text, tag="Macro", tone="accent")

    with col2:
        macro_bias = asset_macro.get("macro_bias", "数据不足")
        render_center_metric_card("宏观方向", macro_bias, tag="方向判断", tone=infer_tone(macro_bias, "neutral"))

    with col3:
        alignment = asset_macro.get("alignment_label", "无法判断")
        alignment_display = str(alignment).replace("技术面与宏观面", "技术面与宏观面\n")
        render_center_metric_card("技术-宏观关系", alignment_display, tag="一致性", tone=infer_tone(alignment, "accent"))

    render_text_card("宏观综合判断", asset_macro.get("summary", ""), tag=alignment, tone=infer_tone(alignment, "accent"))

    macro_col1, macro_col2, macro_col3 = st.columns(3)

    with macro_col1:
        render_bullet_card("宏观支撑因素", asset_macro.get("support_points", []), empty_text="暂无支撑因素。", tone="positive")

    with macro_col2:
        render_bullet_card("宏观压力因素", asset_macro.get("risk_points", []), empty_text="暂无压力因素。", tone="negative")

    with macro_col3:
        render_bullet_card("中性观察因素", asset_macro.get("neutral_points", []), empty_text="暂无中性观察。", tone="neutral")

    top_indicators = asset_macro.get("top_indicators", pd.DataFrame())

    with st.expander("查看相关宏观指标明细", expanded=False):
        if top_indicators is None or top_indicators.empty:
            st.info("暂无相关宏观指标。")
        else:
            show = top_indicators.copy()

            if "latest_date" in show.columns:
                show["latest_date"] = pd.to_datetime(
                    show["latest_date"],
                    errors="coerce",
                ).dt.strftime("%Y-%m-%d")

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
                "asset_effect_score",
                "interpretation",
            ]

            st.dataframe(
                show[[col for col in show_cols if col in show.columns]],
                use_container_width=True,
                hide_index=True,
            )


def render_asset_ai_quick_view(selected_symbol: str) -> None:
    """
    单资产研究页里的 RAbot AI 快评板块。
    """
    st.subheader("RAbot AI 快评")

    if not selected_symbol:
        st.info("请先选择一个资产。")
        return

    quick_key = f"ai_quick_view_{selected_symbol}"
    meta_key = f"ai_quick_view_meta_{selected_symbol}"

    with st.container(border=True):
        render_tag_row([("本地事实包", "accent"), (selected_symbol, "neutral")])

        st.markdown('<div class="rabot-action-row-spacer"></div>', unsafe_allow_html=True)
        col_left, col1, col2, col_right = st.columns([2.2, 1.35, 1.35, 2.2])

        with col1:
            generate_clicked = st.button(
                "生成 AI 快评",
                key=f"generate_ai_quick_view_{selected_symbol}",
                use_container_width=True,
                type="primary",
            )

        with col2:
            clear_clicked = st.button(
                "清空快评",
                key=f"clear_ai_quick_view_{selected_symbol}",
                use_container_width=True,
            )

        if clear_clicked:
            st.session_state.pop(quick_key, None)
            st.session_state.pop(meta_key, None)
            st.rerun()

        if generate_clicked:
            with st.spinner(f"RAbot 正在分析 {selected_symbol} ..."):
                chat = RAbotResearchChat()
                result = chat.generate_asset_quick_view(selected_symbol)

            st.session_state[quick_key] = result.text
            st.session_state[meta_key] = {
                "ok": result.ok,
                "model": result.model,
            }

        answer = st.session_state.get(quick_key)
        meta = st.session_state.get(meta_key, {})

        if answer:
            if meta.get("ok"):
                subtitle = f"模型：{meta.get('model', 'N/A')} / 标的：{selected_symbol}"
                render_text_card("RAbot AI 快评", answer, tag=subtitle, tone="accent")
            else:
                st.warning("AI 快评未成功生成。")
                render_text_card("RAbot AI 快评", answer, tag=f"标的：{selected_symbol}", tone="negative")

            if st.button(
                "保存为观点",
                key=f"save_ai_quick_view_{selected_symbol}",
                use_container_width=True,
                type="primary",
                disabled=not bool(answer),
            ):
                ok, message = save_research_view(
                    source="ai_quick_view",
                    scope="single_asset",
                    symbol=selected_symbol,
                    title=f"{selected_symbol} AI 快评",
                    view_text=answer,
                    horizon_days=7,
                )
                if ok:
                    st.success(message)
                else:
                    st.warning(message)
        else:
            render_section_card(
                "RAbot AI 快评",
                "点击“生成 AI 快评”，让 RAbot 给出当前标的的简短研究观点。",
                tag=f"标的：{selected_symbol}",
                tone="accent",
            )


def render_ai_research_chat_tab(
    available_symbols: list[str],
    config_map: dict,
) -> None:
    """
    AI 研究对话 tab。
    """
    st.subheader("RAbot AI 研究对话")

    st.caption(
        "这个对话不是裸聊。RAbot 会先从本地行情、新闻、宏观和规则层研究中构造事实包，"
        "再让 LLM 基于事实包回答。"
    )

    if "rabot_ai_chat_history" not in st.session_state:
        st.session_state["rabot_ai_chat_history"] = []

    scope_label = st.radio(
        "研究范围",
        options=["全市场", "单标的", "多标的组合"],
        horizontal=True,
    )

    scope = "market"
    selected_asset = None
    selected_symbols = []

    if scope_label == "单标的":
        scope = "single_asset"
        selected_asset = st.selectbox(
            "选择咨询标的",
            options=available_symbols,
            format_func=lambda x: f"{x} - {config_map[x].name if x in config_map else x}",
        )

    elif scope_label == "多标的组合":
        scope = "multi_asset"
        selected_symbols = st.multiselect(
            "选择多个咨询标的",
            options=available_symbols,
            default=[s for s in ["NASDAQ", "SP500", "CSI300", "SSE", "GOLD", "DXY"] if s in available_symbols],
            format_func=lambda x: f"{x} - {config_map[x].name if x in config_map else x}",
        )

    question = st.text_area(
        "你想问 RAbot 什么？",
        placeholder=(
            "例如：\n"
            "1. 今天全球资产主线是什么？\n"
            "2. 为什么纳指强但黄金也强？\n"
            "3. A股现在弱主要是宏观问题还是风险偏好问题？\n"
            "4. DXY 上行对纳指、黄金、港股分别意味着什么？"
        ),
        height=130,
    )

    col_left, col1, col2, col_right = st.columns([2.2, 1.35, 1.35, 2.2])

    with col1:
        ask_clicked = st.button("询问 RAbot", type="primary", use_container_width=True)

    with col2:
        clear_clicked = st.button("清空对话", use_container_width=True)

    if clear_clicked:
        st.session_state["rabot_ai_chat_history"] = []
        st.rerun()

    if ask_clicked:
        with st.spinner("RAbot 正在构造事实包并调用 LLM ..."):
            chat = RAbotResearchChat()
            result = chat.answer_question(
                question=question,
                scope=scope,
                asset_symbol=selected_asset,
                symbols=selected_symbols,
            )

        item = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scope_label": scope_label,
            "scope": scope,
            "asset_symbol": selected_asset,
            "symbols": selected_symbols,
            "question": question,
            "answer": result.text,
            "ok": result.ok,
            "model": result.model,
        }

        st.session_state["rabot_ai_chat_history"].append(item)
        st.session_state["rabot_ai_chat_history"] = st.session_state["rabot_ai_chat_history"][-10:]

    history = st.session_state.get("rabot_ai_chat_history", [])

    if not history:
        st.info("暂无对话。你可以先问一个全市场问题，例如：当前全球资产主线是什么？")
        return

    st.divider()
    st.markdown("### 最近对话")

    for idx, item in enumerate(reversed(history)):
        with st.container(border=True):
            scope_text = item.get("scope_label", "全市场")

            if item.get("asset_symbol"):
                scope_text += f"｜{item.get('asset_symbol')}"

            if item.get("symbols"):
                scope_text += "｜" + "、".join(item.get("symbols", []))

            st.caption(f"范围：{scope_text}｜模型：{item.get('model', 'N/A')}")

            st.markdown("**你问：**")
            st.write(item.get("question", ""))

            st.markdown("**RAbot 答：**")

            if item.get("ok"):
                st.markdown(item.get("answer", ""))
            else:
                st.warning(item.get("answer", ""))

            save_key = f"save_ai_chat_view_{idx}_{item.get('created_at', '')}"
            if st.button("保存为观点", key=save_key, use_container_width=True, disabled=not item.get("answer")):
                item_scope = item.get("scope") or "market"
                if item_scope == "single_asset":
                    item_symbol = item.get("asset_symbol") or ""
                elif item_scope == "multi_asset":
                    item_symbol = ",".join(item.get("symbols") or [])
                else:
                    item_symbol = ""

                question_text = str(item.get("question") or "")
                answer_text = str(item.get("answer") or "")
                ok, message = save_research_view(
                    source="ai_chat",
                    scope=item_scope,
                    symbol=item_symbol,
                    title=f"AI 对话：{question_text[:30]}",
                    view_text=f"用户问题：{question_text}\n\nRAbot回答：\n{answer_text}",
                    horizon_days=7,
                )
                if ok:
                    st.success(message)
                else:
                    st.warning(message)


def render_chart_heading(title: str, subtitle: str | None = None) -> None:
    subtitle_html = f'<div class="rabot-chart-heading-subtitle">{html_text(subtitle)}</div>' if subtitle else ""
    st.markdown(
        f"""
        <div class="rabot-chart-heading">
            <div class="rabot-chart-heading-title">{html_text(title)}</div>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def parse_manual_date(text: str) -> Optional[pd.Timestamp]:
    if text is None:
        return None

    raw = text.strip()

    if not raw:
        return None

    try:
        if re.fullmatch(r"\d{8}", raw):
            return pd.to_datetime(raw, format="%Y%m%d")

        if re.fullmatch(r"\d{2}/\d{1,2}/\d{1,2}", raw):
            return pd.to_datetime(raw, format="%y/%m/%d")

        if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", raw):
            return pd.to_datetime(raw, format="%Y/%m/%d")

        if re.fullmatch(r"\d{4}-\d{1,2}-\d{1,2}", raw):
            return pd.to_datetime(raw, format="%Y-%m-%d")

        return pd.to_datetime(raw)

    except Exception:
        return None


def get_time_range_selector(df: pd.DataFrame) -> Tuple[Optional[pd.Timestamp], Optional[pd.Timestamp], str]:
    if df.empty or "date" not in df.columns:
        return None, None, "全部数据"

    min_dt = pd.to_datetime(df["date"]).min()
    max_dt = pd.to_datetime(df["date"]).max()

    if "range_start" not in st.session_state:
        st.session_state["range_start"] = min_dt.date()

    if "range_end" not in st.session_state:
        st.session_state["range_end"] = max_dt.date()

    with st.popover("设置行情图时间区间", use_container_width=True):
        st.caption("统一时间入口：快捷区间 / 日期选择 / 手动输入。只有选择“手动输入”时才显示输入框。")

        mode = st.selectbox(
            "选择方式",
            options=[
                "全部数据",
                "近1个月",
                "近3个月",
                "近6个月",
                "近1年",
                "近3年",
                "近5年",
                "日期选择",
                "手动输入",
            ],
            index=0,
        )

        if mode == "全部数据":
            start_dt = min_dt
            end_dt = max_dt
            label = f"全部数据：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近1个月":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(months=1))
            label = f"近1个月：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近3个月":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(months=3))
            label = f"近3个月：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近6个月":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(months=6))
            label = f"近6个月：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近1年":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(years=1))
            label = f"近1年：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近3年":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(years=3))
            label = f"近3年：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "近5年":
            end_dt = max_dt
            start_dt = max(min_dt, max_dt - pd.DateOffset(years=5))
            label = f"近5年：{start_dt.date()} 至 {end_dt.date()}"

        elif mode == "日期选择":
            selected_range = st.date_input(
                "选择日期区间",
                value=(st.session_state["range_start"], st.session_state["range_end"]),
                min_value=min_dt.date(),
                max_value=max_dt.date(),
                help="直接点日历选择开始日期和结束日期。",
            )

            if isinstance(selected_range, tuple) and len(selected_range) == 2:
                start_raw, end_raw = selected_range
                st.session_state["range_start"] = start_raw
                st.session_state["range_end"] = end_raw
                start_dt = pd.to_datetime(start_raw)
                end_dt = pd.to_datetime(end_raw)
                label = f"日期选择：{start_dt.date()} 至 {end_dt.date()}"
            else:
                start_dt = min_dt
                end_dt = max_dt
                label = "日期区间未完整选择，暂用全部数据"

        else:
            st.caption("示例：`24/01/31`、`2024/01/31`、`2024-01-31`、`20240131`")

            col1, col2 = st.columns(2)

            with col1:
                start_text = st.text_input(
                    "开始日期",
                    value=st.session_state.get("manual_start_text", min_dt.strftime("%y/%m/%d")),
                    placeholder="例如：24/01/31",
                )

            with col2:
                end_text = st.text_input(
                    "结束日期",
                    value=st.session_state.get("manual_end_text", max_dt.strftime("%y/%m/%d")),
                    placeholder="例如：26/04/29",
                )

            st.session_state["manual_start_text"] = start_text
            st.session_state["manual_end_text"] = end_text

            start_dt = parse_manual_date(start_text)
            end_dt = parse_manual_date(end_text)

            if start_dt is None or end_dt is None:
                st.warning("日期格式没识别出来，暂时使用全部数据。推荐格式：24/01/31。")
                start_dt = min_dt
                end_dt = max_dt
                label = "手动输入无效，暂用全部数据"
            else:
                start_dt = max(min_dt, start_dt)
                end_dt = min(max_dt, end_dt)
                label = f"手动输入：{start_dt.date()} 至 {end_dt.date()}"

        if start_dt > end_dt:
            st.warning("开始日期晚于结束日期，已自动交换。")
            start_dt, end_dt = end_dt, start_dt

        st.info(label)

    return start_dt, end_dt, label


def filter_df_by_date(
    df: pd.DataFrame,
    start_dt: Optional[pd.Timestamp],
    end_dt: Optional[pd.Timestamp],
) -> pd.DataFrame:
    if df.empty or start_dt is None or end_dt is None:
        return df

    data = df.copy()
    data["date_dt"] = pd.to_datetime(data["date"])
    filtered = data[(data["date_dt"] >= start_dt) & (data["date_dt"] <= end_dt)].copy()
    filtered.drop(columns=["date_dt"], inplace=True, errors="ignore")

    return filtered


def filter_all_data_by_date(
    all_data: pd.DataFrame,
    start_dt: Optional[pd.Timestamp],
    end_dt: Optional[pd.Timestamp],
) -> pd.DataFrame:
    if all_data.empty or start_dt is None or end_dt is None:
        return all_data

    data = all_data.copy()
    data["date_dt"] = pd.to_datetime(data["date"])
    data = data[(data["date_dt"] >= start_dt) & (data["date_dt"] <= end_dt)].copy()
    data.drop(columns=["date_dt"], inplace=True, errors="ignore")

    return data


def plot_index_price(df: pd.DataFrame) -> go.Figure:
    data = add_technical_indicators(df)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data["close"],
            mode="lines",
            name="收盘价",
            line=dict(width=2.4),
        )
    )

    for ma in ["ma20", "ma60", "ma120"]:
        if ma in data.columns:
            fig.add_trace(
                go.Scatter(
                    x=data["date"],
                    y=data[ma],
                    mode="lines",
                    name=ma.upper(),
                    line=dict(width=1.55),
                )
            )

    fig.update_layout(
        height=500,
        margin=dict(l=18, r=18, t=18, b=82),
        xaxis_title="日期",
        yaxis_title="点位 / 价格",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
    )

    return apply_plotly_paper_theme(fig)


def plot_drawdown(df: pd.DataFrame) -> go.Figure:
    data = add_technical_indicators(df)

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["date"],
            y=data["drawdown"],
            mode="lines",
            name="回撤",
            fill="tozeroy",
            line=dict(width=1.8),
        )
    )

    fig.update_layout(
        height=330,
        margin=dict(l=18, r=18, t=18, b=62),
        xaxis_title="日期",
        yaxis_title="回撤（%）",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.22,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        ),
    )

    return apply_plotly_paper_theme(fig)


def plot_volume(df: pd.DataFrame) -> go.Figure:
    data = df.copy()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=data["date"],
            y=data["volume"],
            name="成交量",
        )
    )

    fig.update_layout(
        height=330,
        margin=dict(l=18, r=18, t=18, b=58),
        xaxis_title="日期",
        yaxis_title="成交量",
        hovermode="x unified",
        showlegend=False,
    )

    return apply_plotly_paper_theme(fig)


def plot_normalized_comparison(all_data: pd.DataFrame, selected_symbols: list[str]) -> go.Figure:
    fig = go.Figure()

    table = build_normalized_price_table(all_data, selected_symbols)

    if table.empty:
        return apply_plotly_paper_theme(fig)

    for symbol in selected_symbols:
        if symbol not in table.columns:
            continue

        fig.add_trace(
            go.Scatter(
                x=table["date_dt"],
                y=table[symbol],
                mode="lines",
                name=symbol,
                line=dict(width=2),
            )
        )

    fig.update_layout(
        height=470,
        margin=dict(l=18, r=18, t=18, b=84),
        xaxis_title="日期",
        yaxis_title="归一化点位",
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12),
        ),
    )

    return apply_plotly_paper_theme(fig)


def plot_return_bar(perf_df: pd.DataFrame, column: str, title: str) -> go.Figure:
    fig = go.Figure()

    if perf_df.empty or column not in perf_df.columns:
        return apply_plotly_paper_theme(fig)

    data = perf_df.dropna(subset=[column]).copy()
    data = data.sort_values(column, ascending=True)

    fig.add_trace(
        go.Bar(
            x=data[column],
            y=data["symbol"],
            orientation="h",
            text=data[column],
            textposition="auto",
            name=column,
        )
    )

    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", y=0.96),
        height=max(360, 28 * len(data)),
        margin=dict(l=18, r=18, t=60, b=38),
        xaxis_title=column,
        yaxis_title="资产",
        showlegend=False,
    )

    return apply_plotly_paper_theme(fig)


def plot_correlation_heatmap(corr: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    if corr.empty:
        return apply_plotly_paper_theme(fig)

    fig.add_trace(
        go.Heatmap(
            z=corr.values,
            x=corr.columns,
            y=corr.index,
            zmin=-1,
            zmax=1,
            colorbar=dict(title="相关系数"),
            text=corr.values,
            texttemplate="%{text:.2f}",
        )
    )

    fig.update_layout(
        title=dict(text="日收益率相关性矩阵", x=0.5, xanchor="center", y=0.96),
        height=560,
        margin=dict(l=18, r=18, t=60, b=38),
    )

    return apply_plotly_paper_theme(fig)


def render_news_card(row: pd.Series) -> None:
    title = row.get("title", "无标题")
    link = row.get("link", "")
    source_name = row.get("source_name", "Unknown")
    published_at = row.get("published_at", "")
    related_assets = row.get("related_assets", "")
    sentiment = row.get("sentiment_label", "中性")
    importance = row.get("importance_score", 0)
    event_type = row.get("event_type", "其他")
    source_tier = row.get("source_tier", "D")
    freshness = row.get("freshness_score", 0)
    quality = row.get("quality_score", 0)
    summary = row.get("summary", "")
    interpretation = row.get("interpretation", "")

    with st.container(border=True):
        if link:
            st.markdown(
                f'<a class="rabot-news-title" href="{html.escape(str(link), quote=True)}" target="_blank">'
                f"{html_text(title, '无标题')}</a>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(f'<div class="rabot-news-title">{html_text(title, "无标题")}</div>', unsafe_allow_html=True)

        st.caption(f"来源：{source_name}｜发布时间：{published_at or '未知'}｜关联资产：{related_assets or '暂无'}")
        render_tag_row(
            [
                (f"等级 {source_tier}", "accent"),
                (str(sentiment), infer_tone(sentiment, "neutral")),
                (str(event_type), "neutral"),
                (f"重要性 {importance}/100", "accent"),
                (f"新鲜度 {freshness}/100", "neutral"),
                (f"质量 {quality}/100", "accent"),
            ]
        )

        if summary:
            st.markdown(
                f'<div class="rabot-text-body">{html.escape(str(summary)[:700])}</div>',
                unsafe_allow_html=True,
            )

        if interpretation:
            render_text_card("RAbot 解读", interpretation, tag="interpretation", tone="accent")


try:
    st.title("RAbot Index Research")
    st.caption("独立指数研究助手：指数行情、趋势指标、新闻联动、宏观环境、状态评分与本地简报生成。")

    store = load_store()
    news_store = load_news_store()
    configs = load_index_configs()
    config_map = {cfg.symbol: cfg for cfg in configs}

    auto_update_market_data_on_startup(
        configs=configs,
        preferred_symbols=st.session_state.get("watchlist_symbols"),
    )

    if MACRO_MODULE_READY:
        macro_store = MacroStore(get_db_path())
        all_macro = macro_store.read_macro_series()
    else:
        macro_store = None
        all_macro = pd.DataFrame()

    with st.sidebar:
        st.header("数据更新")

        startup_update_message = st.session_state.get("startup_market_update_message")
        if startup_update_message:
            if "失败" in startup_update_message:
                st.warning(startup_update_message)
            else:
                st.success(startup_update_message)

        start_date = st.date_input(
            "行情开始日期",
            value=pd.to_datetime("2020-01-01"),
        )

        selected_symbols_for_update = st.multiselect(
            "选择要更新的指数/资产",
            options=[cfg.symbol for cfg in configs],
            default=[cfg.symbol for cfg in configs if cfg.symbol in ["NASDAQ", "SP500", "CSI300", "SSE"]],
            format_func=lambda x: f"{x} - {config_map[x].name}",
        )

        if st.button("更新所选行情", use_container_width=True, type="primary"):
            with st.spinner("正在更新行情数据..."):
                result = update_all_indexes(
                    symbols=selected_symbols_for_update,
                    start=start_date.strftime("%Y-%m-%d"),
                )

            st.success("行情更新完成")
            st.dataframe(result, use_container_width=True)

        if st.button("更新新闻", use_container_width=True, type="primary"):
            with st.spinner("正在抓取最新新闻，包括海外与国内市场..."):
                news_df = fetch_all_news()
                rows = news_store.upsert_news(news_df)

            st.success(f"新闻更新完成：写入/更新 {rows} 条")

        st.divider()

        st.header("宏观数据")

        macro_start_date = st.date_input(
            "宏观开始日期",
            value=pd.to_datetime("2015-01-01"),
        )

        macro_regions = st.multiselect(
            "选择宏观地区",
            options=["US", "CN"],
            default=["US", "CN"],
            format_func=lambda x: "美国宏观" if x == "US" else "中国宏观",
        )

        if st.button("更新宏观数据", use_container_width=True, type="primary"):
            with st.spinner("正在更新中美宏观数据..."):
                macro_result = update_macro_from_frontend(
                    regions=macro_regions,
                    start_date=macro_start_date.strftime("%Y-%m-%d"),
                )

            success_count = int((macro_result["status"] == "success").sum()) if not macro_result.empty else 0
            empty_count = int((macro_result["status"] == "empty").sum()) if not macro_result.empty else 0
            failed_count = int((macro_result["status"] == "failed").sum()) if not macro_result.empty else 0

            st.success(f"宏观更新完成：成功 {success_count}，空数据 {empty_count}，失败 {failed_count}")
            st.dataframe(macro_result, use_container_width=True, hide_index=True)

        st.divider()

        st.header("报告生成")

        if REPORT_JOB_BACKEND == "v2":
            st.caption("当前报告后台：新版 SQLite 任务队列")
        elif REPORT_JOB_BACKEND == "legacy":
            st.caption("当前报告后台：旧版任务队列")
        else:
            st.warning("报告后台模块未正确导入。")

        enable_llm_for_report = st.toggle(
            "启用 DeepSeek 研究层",
            value=True,
            help="关闭后只生成规则层报告，速度更快。",
        )

        if st.button("后台生成 Markdown 简报", use_container_width=True, type="primary"):
            start_background_report(enable_llm=enable_llm_for_report)

        render_report_job_status(compact=True)

        st.divider()
        st.header("自选资产")

        sidebar_data_for_watchlist = store.read_index_daily()

        if sidebar_data_for_watchlist.empty or "symbol" not in sidebar_data_for_watchlist.columns:
            st.caption("暂无行情数据，更新行情后可设置首页自选资产。")
        else:
            available_watch_symbols = sorted(sidebar_data_for_watchlist["symbol"].dropna().astype(str).unique().tolist())
            default_watch_symbols = [
                symbol for symbol in DEFAULT_WATCHLIST if symbol in set(available_watch_symbols)
            ]

            previous_watch_symbols = st.session_state.get("watchlist_symbols")
            if previous_watch_symbols:
                default_watch_symbols = [
                    symbol for symbol in previous_watch_symbols if symbol in set(available_watch_symbols)
                ] or default_watch_symbols

            selected_watch_symbols = st.multiselect(
                "今日总览自选资产",
                options=available_watch_symbols,
                default=default_watch_symbols,
                format_func=lambda x: f"{x} - {config_map[x].name if x in config_map else x}",
                key="watchlist_symbols_selector",
            )
            st.session_state["watchlist_symbols"] = selected_watch_symbols

    status_df = store.get_data_status()
    all_data = store.read_index_daily()
    all_news = news_store.read_news(limit=500)

    db_path = Path(get_db_path())
    backend_status_items = [
        ("后端", True),
        ("SQLite", db_path.exists()),
        ("行情库", not status_df.empty),
        ("新闻库", all_news is not None),
        ("宏观库", MACRO_MODULE_READY and macro_store is not None),
        ("报告后台", REPORT_JOB_BACKEND != "none"),
    ]
    render_backend_status(backend_status_items)

    watchlist_symbols = pick_existing_watchlist(
        all_data,
        st.session_state.get("watchlist_symbols") or st.session_state.get("watchlist_symbols_selector"),
    )
    st.session_state["watchlist_symbols"] = watchlist_symbols

    (
        tab_today,
        tab_single,
        tab_compare,
        tab_heat,
        tab_news,
        tab_macro,
        tab_ai_chat,
        tab_views,
        tab_alerts,
        tab_logs,
        tab_report,
    ) = st.tabs(
        ["今日总览", "单资产研究", "多资产比较", "市场热力榜", "新闻中心", "宏观中心", "AI 研究对话", "观点复盘", "研究预警", "数据状态与日志", "简报预览"]
    )

    with tab_today:
        render_today_overview(
            all_data=all_data,
            all_news=all_news,
            all_macro=all_macro,
            config_map=config_map,
            watchlist_symbols=watchlist_symbols,
        )

    with tab_single:
        if all_data.empty:
            st.info("暂无行情数据。建议先运行：python scripts/update_data.py --symbols NASDAQ SP500 --start 2020-01-01")
        else:
            available_symbols = sorted(all_data["symbol"].unique().tolist())

            selected_symbol = st.selectbox(
                "选择主图指数/资产",
                options=available_symbols,
                format_func=lambda x: f"{x} - {config_map[x].name if x in config_map else x}",
            )

            df_full = all_data[all_data["symbol"] == selected_symbol].copy()
            df_full = df_full.sort_values("date")

            start_dt, end_dt, range_label = get_time_range_selector(df_full)

            st.caption(f"当前图表区间：{range_label}")

            df = filter_df_by_date(df_full, start_dt, end_dt)

            if df.empty:
                st.warning("当前时间区间内没有数据，请重新设置时间范围。")
            else:
                status = summarize_latest_status(df)
                research = build_single_asset_research(df)

                name = df["name"].iloc[-1] if "name" in df.columns and not df.empty else selected_symbol

                render_metric_cards(status)
                render_research_cards(research)
                render_asset_ai_quick_view(selected_symbol)

                asset_news = build_asset_news_research(
                    all_news,
                    asset_symbol=selected_symbol,
                    technical_score=research.get("score"),
                    days=7,
                )
                render_asset_news_research(asset_news)

                if MACRO_MODULE_READY:
                    asset_macro = build_asset_macro_research(
                        all_macro,
                        asset_symbol=selected_symbol,
                        technical_score=research.get("score"),
                    )
                    render_asset_macro_research(asset_macro)
                else:
                    st.warning("宏观模块尚未正确导入，暂时无法展示宏观环境观察。")

                with st.expander("查看该资产相关新闻明细", expanded=False):
                    related_news_df = asset_news.get("data", pd.DataFrame())

                    if related_news_df.empty:
                        st.info("暂无相关新闻。")
                    else:
                        show_cols = [
                            "published_at",
                            "source_name",
                            "title",
                            "event_type",
                            "source_tier",
                            "quality_score",
                            "sentiment_label",
                            "importance_score",
                            "related_assets",
                        ]
                        st.dataframe(
                            related_news_df[[col for col in show_cols if col in related_news_df.columns]],
                            use_container_width=True,
                        )

                render_chart_heading(
                    f"{name}：收盘价与均线",
                    "图例位于图表底部；均线基于当前筛选区间重新计算。",
                )
                st.plotly_chart(
                    plot_index_price(df),
                    use_container_width=True,
                )

                chart_col1, chart_col2 = st.columns([2, 1])

                with chart_col1:
                    render_chart_heading(
                        f"{name}：历史回撤",
                        "回撤为相对区间内历史高点的跌幅。",
                    )
                    st.plotly_chart(
                        plot_drawdown(df),
                        use_container_width=True,
                    )

                with chart_col2:
                    if "volume" in df.columns and df["volume"].notna().sum() > 0:
                        render_chart_heading(
                            f"{name}：成交量",
                            "成交量口径取决于原始数据源。",
                        )
                        st.plotly_chart(
                            plot_volume(df),
                            use_container_width=True,
                        )
                    else:
                        st.info("当前资产暂无可用成交量数据。")

                st.subheader("最新指标")

                latest_cols = [
                    "date",
                    "close",
                    "pct_change",
                    "ma20",
                    "ma60",
                    "ma120",
                    "volatility_20d",
                    "drawdown",
                ]

                latest_table = add_technical_indicators(df).tail(20)
                latest_table = latest_table[[col for col in latest_cols if col in latest_table.columns]]

                st.dataframe(
                    latest_table.sort_values("date", ascending=False),
                    use_container_width=True,
                )

    with tab_compare:
        if all_data.empty:
            st.info("暂无可比较数据。")
        else:
            available_symbols = sorted(all_data["symbol"].unique().tolist())

            compare_symbols = st.multiselect(
                "选择用于对比的指数/资产",
                options=available_symbols,
                default=[s for s in ["NASDAQ", "SP500", "CSI300", "SSE", "GOLD", "DXY"] if s in available_symbols],
                format_func=lambda x: f"{x} - {config_map[x].name if x in config_map else x}",
            )

            if not compare_symbols:
                st.warning("请至少选择一个资产。")
            else:
                comparison_base = all_data[all_data["symbol"].isin(compare_symbols)].copy()

                min_dt = pd.to_datetime(comparison_base["date"]).min()
                max_dt = pd.to_datetime(comparison_base["date"]).max()

                col1, col2 = st.columns(2)

                with col1:
                    compare_start = st.date_input(
                        "对比开始日期",
                        value=max(min_dt, max_dt - pd.DateOffset(years=3)).date(),
                        min_value=min_dt.date(),
                        max_value=max_dt.date(),
                    )

                with col2:
                    compare_end = st.date_input(
                        "对比结束日期",
                        value=max_dt.date(),
                        min_value=min_dt.date(),
                        max_value=max_dt.date(),
                    )

                compare_data = filter_all_data_by_date(
                    comparison_base,
                    pd.to_datetime(compare_start),
                    pd.to_datetime(compare_end),
                )

                render_chart_heading(
                    "多指数归一化走势对比",
                    "所有资产以所选区间第一条有效数据为100，便于横向比较强弱。",
                )
                st.plotly_chart(
                    plot_normalized_comparison(compare_data, compare_symbols),
                    use_container_width=True,
                )

                corr = build_correlation_matrix(compare_data, compare_symbols)

                st.plotly_chart(
                    plot_correlation_heatmap(corr),
                    use_container_width=True,
                )

                st.subheader("相关性矩阵数据")
                st.dataframe(corr, use_container_width=True)

    with tab_heat:
        if all_data.empty:
            st.info("暂无市场热力榜数据。")
        else:
            perf_df = build_asset_performance_table(all_data)

            if perf_df.empty:
                st.warning("暂时无法生成表现表。")
            else:
                market_overview = build_market_overview(perf_df)
                news_snapshot = build_news_market_snapshot(all_news, days=7)

                st.subheader("RAbot 市场总览")

                overview_col1, overview_col2 = st.columns(2)

                with overview_col1:
                    render_text_card(
                        market_overview.get("headline", "市场总览"),
                        market_overview.get("summary", ""),
                        tag="市场总览",
                        tone="accent",
                    )
                    render_market_heat_dashboard(perf_df)

                with overview_col2:
                    render_text_card(
                        f"新闻面快照：{news_snapshot.get('headline', '暂无新闻快照')}",
                        news_snapshot.get("summary", ""),
                        tag="新闻快照",
                        tone="accent",
                    )
                    render_bullet_card(
                        "高重要性新闻",
                        news_snapshot.get("top_news", []),
                        empty_text="暂无高重要性新闻。",
                        tone="accent",
                    )

                st.subheader("多资产表现总览")

                st.dataframe(
                    perf_df.sort_values("近1月收益率%", ascending=False, na_position="last"),
                    use_container_width=True,
                )

                col1, col2 = st.columns(2)

                with col1:
                    return_col = st.selectbox(
                        "选择收益排行指标",
                        options=[
                            "近1周收益率%",
                            "近1月收益率%",
                            "近3月收益率%",
                            "近6月收益率%",
                            "YTD收益率%",
                            "近1年收益率%",
                        ],
                        index=1,
                    )

                    st.plotly_chart(
                        plot_return_bar(perf_df, return_col, f"{return_col}排行"),
                        use_container_width=True,
                    )

                with col2:
                    risk_col = st.selectbox(
                        "选择风险排行指标",
                        options=[
                            "20日年化波动率%",
                            "当前回撤%",
                            "区间最大回撤%",
                        ],
                        index=0,
                    )

                    st.plotly_chart(
                        plot_return_bar(perf_df, risk_col, f"{risk_col}排行"),
                        use_container_width=True,
                    )

                st.subheader("研究提示")

                top_return = perf_df.dropna(subset=[return_col]).sort_values(return_col, ascending=False).head(3)
                worst_return = perf_df.dropna(subset=[return_col]).sort_values(return_col, ascending=True).head(3)
                high_vol = perf_df.dropna(subset=["20日年化波动率%"]).sort_values(
                    "20日年化波动率%",
                    ascending=False,
                ).head(3)

                hint_col1, hint_col2, hint_col3 = st.columns(3)

                with hint_col1:
                    render_bullet_card(
                        "当前收益强势资产",
                        [f"{row.symbol}（{row[return_col]}%）" for _, row in top_return.iterrows()],
                        empty_text="暂无强势资产。",
                        tone="up",
                    )

                with hint_col2:
                    render_bullet_card(
                        "当前收益弱势资产",
                        [f"{row.symbol}（{row[return_col]}%）" for _, row in worst_return.iterrows()],
                        empty_text="暂无弱势资产。",
                        tone="down",
                    )

                with hint_col3:
                    render_bullet_card(
                        "当前波动较高资产",
                        [f"{row.symbol}（{row['20日年化波动率%']}%）" for _, row in high_vol.iterrows()],
                        empty_text="暂无高波动资产。",
                        tone="neutral",
                    )

    with tab_news:
        st.subheader("RAbot 新闻中心")

        col_update, col_note = st.columns([1, 3])

        with col_update:
            if st.button("更新最新新闻", use_container_width=True, type="primary"):
                with st.spinner("正在抓取最新新闻，包括海外与国内市场..."):
                    news_df = fetch_all_news()
                    rows = news_store.upsert_news(news_df)

                st.success(f"新闻更新完成：写入/更新 {rows} 条")

        with col_note:
            render_section_card(
                "新闻中心",
                "支持国内新闻、来源质量评分、事件类型分类、新鲜度评分与综合质量分。",
                tag="筛选与质量评估",
                tone="accent",
            )

        source_status = news_store.read_news_sources()

        if not source_status.empty:
            with st.expander("新闻源状态", expanded=False):
                st.dataframe(source_status, use_container_width=True)

        event_type_status = news_store.read_event_types()

        if not event_type_status.empty:
            with st.expander("事件类型分布", expanded=False):
                st.dataframe(event_type_status, use_container_width=True)

        news_snapshot = build_news_market_snapshot(all_news, days=7)

        render_text_card(
            f"新闻市场快照：{news_snapshot.get('headline', '暂无新闻快照')}",
            news_snapshot.get("summary", ""),
            tag="近7日",
            tone="accent",
        )

        available_assets = ["全部"] + [cfg.symbol for cfg in configs]
        sentiment_options = ["全部", "偏利多", "偏利空", "中性"]

        if not event_type_status.empty and "event_type" in event_type_status.columns:
            event_type_options = ["全部"] + event_type_status["event_type"].dropna().astype(str).tolist()
        else:
            event_type_options = ["全部"]

        filter_col1, filter_col2, filter_col3, filter_col4 = st.columns([1, 1, 1, 1])

        with filter_col1:
            news_asset = st.selectbox("关联资产", options=available_assets, index=0)

        with filter_col2:
            news_sentiment = st.selectbox("情绪标签", options=sentiment_options, index=0)

        with filter_col3:
            news_event_type = st.selectbox("事件类型", options=event_type_options, index=0)

        with filter_col4:
            news_source_tier = st.selectbox("来源等级", options=["全部", "S", "A", "B", "C", "D"], index=0)

        filter_col5, filter_col6, filter_col7 = st.columns([1, 1, 2])

        with filter_col5:
            news_limit = st.selectbox("显示条数", options=[20, 50, 100, 200], index=1)

        with filter_col6:
            min_quality = st.slider("最低质量分", min_value=0, max_value=100, value=0, step=5)

        with filter_col7:
            news_keyword = st.text_input("关键词搜索", placeholder="例如：CPI / Nvidia / 中国政策 / 人民币 / 地产")

        news_df = news_store.read_news(
            limit=int(news_limit),
            asset=news_asset,
            sentiment=news_sentiment,
            event_type=news_event_type,
            source_tier=news_source_tier,
            min_quality_score=int(min_quality),
            keyword=news_keyword.strip() if news_keyword else None,
        )

        if news_df.empty:
            st.warning("暂无新闻数据。请先点击“更新最新新闻”，或降低筛选条件。")
        else:
            st.caption(f"当前显示 {len(news_df)} 条新闻。")

            top_news = news_df.sort_values("quality_score", ascending=False).head(5)

            render_bullet_card(
                "高质量新闻观察",
                [
                    f"{row.get('title', '')} ｜{row.get('event_type', '其他')} ｜{row.get('sentiment_label', '中性')} ｜质量 {row.get('quality_score', 0)}/100 ｜来源等级 {row.get('source_tier', 'D')}"
                    for _, row in top_news.iterrows()
                ],
                empty_text="暂无高质量新闻。",
                tone="accent",
            )

            st.divider()

            for _, row in news_df.iterrows():
                render_news_card(row)

    with tab_macro:
        if not MACRO_MODULE_READY:
            st.error("宏观模块尚未正确导入。请确认 src/RAbot/macro 相关文件已经创建。")
            st.caption("需要至少包含：macro_provider.py、fred_provider.py、china_macro_provider.py、macro_store.py、streamlit_macro.py。")
        else:
            render_macro_center()

    with tab_ai_chat:
        if all_data.empty:
            st.info("暂无行情数据。请先更新行情数据后再使用 AI 研究对话。")
        else:
            available_symbols_for_ai = sorted(all_data["symbol"].dropna().astype(str).unique().tolist())
            render_ai_research_chat_tab(
                available_symbols=available_symbols_for_ai,
                config_map=config_map,
            )

    with tab_views:
        render_view_review_tab(all_data=all_data, config_map=config_map)

    with tab_alerts:
        render_alerts_tab(watchlist_symbols=watchlist_symbols)

    with tab_logs:
        st.subheader("本地行情数据状态")

        if status_df.empty:
            st.warning("当前数据库暂无行情数据。")
        else:
            st.dataframe(status_df, use_container_width=True)

        st.subheader("最近行情更新日志")
        log_df = store.read_update_log(limit=50)

        if log_df.empty:
            st.info("暂无行情更新日志。")
        else:
            st.dataframe(log_df, use_container_width=True)

        st.subheader("最近新闻更新日志")
        news_log_df = news_store.read_update_log(limit=50)

        if news_log_df.empty:
            st.info("暂无新闻更新日志。")
        else:
            st.dataframe(news_log_df, use_container_width=True)

        if MACRO_MODULE_READY:
            st.subheader("最近宏观更新日志")
            macro_log_df = MacroStore().read_update_log(limit=50)

            if macro_log_df.empty:
                st.info("暂无宏观更新日志。")
            else:
                st.dataframe(macro_log_df, use_container_width=True)

    with tab_report:
        st.subheader("自动生成的指数研究简报预览")

        col_left, col_a, col_b, col_right = st.columns([2.2, 1.35, 1.35, 2.2])

        with col_a:
            if st.button("后台生成新简报", use_container_width=True, type="primary"):
                start_background_report(enable_llm=True)

        with col_b:
            if st.button("刷新任务状态", use_container_width=True):
                st.rerun()

        with col_right:
            st.info("报告预览会直接扫描 data/reports，并展示文件修改时间最新的一份报告。")

        render_report_job_status(compact=False)
        render_recent_report_jobs(limit=5)

        st.divider()

        preview_text = load_best_report_preview()
        preview_report_path = st.session_state.get("preview_report_path", "")

        if preview_text:
            if preview_report_path:
                st.caption(f"当前预览报告：{preview_report_path}")

            st.markdown(preview_text)
        else:
            st.info("暂无可预览报告。点击“后台生成新简报”后，报告完成时会自动保存到 data/reports。")

except Exception as e:
    st.error("前端运行时出错。下面是具体报错：")
    st.exception(e)
