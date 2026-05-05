"""RAbot 投研助手 — Streamlit 版"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ── Path setup ───────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st

st.set_page_config(page_title="RAbot 投研助手", page_icon="🍔", layout="wide")

# ── Secrets → environ ────────────────────────────────────────────────
try:
    for k, v in st.secrets.items():
        if k not in os.environ and isinstance(v, str):
            os.environ[k] = v
except Exception:
    pass

os.environ.setdefault("RABOT_AUTO_UPDATE_ON_START", "false")
os.environ.setdefault("RABOT_NEWS_AUTO_REFRESH_MINUTES", "0")
os.environ.setdefault("RABOT_DATA_DIR", str(ROOT / "data"))

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .rabot-card {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        background: #fff;
        box-shadow: 0 1px 3px rgba(0,0,0,.04);
    }
    .rabot-metric-label { font-size: .78rem; color: #6b7280; }
    .rabot-metric-value { font-size: 1.25rem; font-weight: 700; }
    .rabot-positive { color: #059669; }
    .rabot-negative { color: #dc2626; }
    .rabot-warn { color: #d97706; }
    .rabot-tag {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: .72rem;
        background: #f3f4f6;
        margin: 2px;
    }
    .rabot-divider { margin: 0.5rem 0 1rem; border-top: 1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 首页
# ══════════════════════════════════════════════════════════════════════
def page_home():
    st.title("🍔 RAbot 投研助手")
    try:
        from backend.services.overview_service import build_overview
        ov = build_overview()
    except Exception as e:
        st.error(f"加载总览失败：{e}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("市场", ov.market_status)
    c2.metric("指数", ov.market.count if ov.market else 0)
    c3.metric("新闻", ov.news.count if ov.news else 0)
    c4.metric("宏观", ov.macro.count if ov.macro else 0)
    c5.metric("报告", ov.reports.count if ov.reports else 0)
    st.caption(f"更新于 {ov.last_update}")

    for w in ov.warnings:
        st.warning(w)

    st.markdown("---")
    st.subheader("📊 市场")
    st.markdown(ov.market_summary or "_暂无摘要_")
    if ov.market:
        for h in ov.market.highlights:
            st.success(h)

    st.subheader("📰 新闻")
    st.markdown(ov.news_summary or "_暂无摘要_")

    st.subheader("🌍 宏观")
    st.markdown(ov.macro_summary or "_暂无摘要_")

    st.subheader("📚 报告")
    st.markdown(ov.report_summary or "_暂无摘要_")
    if ov.reports and ov.reports.latest_title:
        st.info(f"最新报告：{ov.reports.latest_title}")


# ══════════════════════════════════════════════════════════════════════
#  Page: 市场热力榜
# ══════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.title("📊 市场热力榜")

    try:
        from backend.services.market_service import get_market_dashboard, get_market_performance
        dash = get_market_dashboard()
        perf = get_market_performance()
    except Exception as e:
        st.error(f"加载市场数据失败：{e}")
        st.info("请先运行数据更新脚本：`python scripts/update_data.py`")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("市场状态", dash.market_status)
    c2.metric("覆盖资产", dash.asset_count)
    c3.metric("最新日期", dash.latest_date or "-")

    if dash.summary:
        st.info(dash.summary)
    for w in dash.warnings:
        st.warning(w)

    tab1, tab2, tab3 = st.tabs(["🔥 强势", "❄️ 弱势", "📋 全览"])

    def _style_df(df, cols):
        def _color(v):
            if v is None: return ""
            try:
                f = float(v)
                if f > 0: return "color: #059669"
                if f < 0: return "color: #dc2626"
            except Exception:
                pass
            return ""
        return df.style.map(_color, subset=cols).format(precision=2, na_rep="-")

    with tab1:
        if dash.strong_assets:
            rows = [{"代码": a.symbol, "名称": a.name or "", "1W%": a.return_1w, "1M%": a.return_1m, "YTD%": a.return_ytd, "波动%": a.volatility_20d, "趋势": a.trend_signal or ""} for a in dash.strong_assets]
            import pandas as pd
            st.dataframe(_style_df(pd.DataFrame(rows), ["1W%", "1M%", "YTD%", "波动%"]), use_container_width=True, hide_index=True)
        else:
            st.info("暂无强势资产")

    with tab2:
        if dash.weak_assets:
            rows = [{"代码": a.symbol, "名称": a.name or "", "1W%": a.return_1w, "1M%": a.return_1m, "YTD%": a.return_ytd, "回撤%": a.drawdown, "风险": a.risk_level or ""} for a in dash.weak_assets]
            import pandas as pd
            st.dataframe(_style_df(pd.DataFrame(rows), ["1W%", "1M%", "YTD%", "回撤%"]), use_container_width=True, hide_index=True)
        else:
            st.info("暂无弱势资产")

    with tab3:
        if perf.items:
            rows = [{"代码": a.symbol, "名称": a.name or "", "1W%": a.return_1w, "1M%": a.return_1m, "3M%": a.return_3m, "YTD%": a.return_ytd, "波动%": a.volatility_20d, "趋势": a.trend_signal or ""} for a in perf.items]
            import pandas as pd
            st.dataframe(_style_df(pd.DataFrame(rows), ["1W%", "1M%", "3M%", "YTD%", "波动%"]), use_container_width=True, hide_index=True, height=500)
        else:
            st.info("暂无资产数据")


# ══════════════════════════════════════════════════════════════════════
#  Page: 个股分析
# ══════════════════════════════════════════════════════════════════════
def page_stock():
    st.title("📈 个股分析")
    symbol = st.text_input("股票代码", placeholder="TSLA.US  600519.SH  00700.HK", key="stock_input").strip().upper()

    if not symbol:
        st.info("输入代码后按回车分析")
        return

    with st.spinner(f"分析 {symbol}..."):
        try:
            from backend.services.stock_service import get_stock_analysis
            r = get_stock_analysis(symbol, use_llm=st.session_state.get("use_llm", True))
        except Exception as e:
            st.error(f"分析失败：{e}")
            return

    for w in r.warnings:
        st.warning(w)

    if r.quote:
        q = r.quote
        c1, c2, c3, c4, c5 = st.columns(5)
        change = q.last_price - q.prev_close if q.last_price and q.prev_close else None
        pct = change / q.prev_close * 100 if change is not None and q.prev_close else None
        c1.metric("最新价", f"{q.last_price:.2f}" if q.last_price else "-", f"{pct:+.2f}%" if pct else None)
        c2.metric("最高", f"{q.high:.2f}" if q.high else "-")
        c3.metric("最低", f"{q.low:.2f}" if q.low else "-")
        c4.metric("开盘", f"{q.open:.2f}" if q.open else "-")
        c5.metric("成交", f"{q.volume:,.0f}" if q.volume else "-")

    if r.bars:
        import pandas as pd
        import plotly.graph_objects as go
        df = pd.DataFrame(r.bars)
        df["date"] = pd.to_datetime(df["date"])
        fig = go.Figure()
        fc = df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
        fig.add_trace(go.Scatter(x=df["date"], y=df["close"]/fc*100, mode="lines", name=r.name or symbol, line=dict(color="#f59e0b", width=2)))
        if "ma20" in df.columns and df["ma20"].notna().any():
            fm = df["ma20"].dropna().iloc[0]
            fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"]/fm*100, mode="lines", name="MA20", line=dict(color="#3b82f6", dash="dot")))
        if "ma60" in df.columns and df["ma60"].notna().any():
            fm2 = df["ma60"].dropna().iloc[0]
            fig.add_trace(go.Scatter(x=df["date"], y=df["ma60"]/fm2*100, mode="lines", name="MA60", line=dict(color="#10b981", dash="dot")))
        fig.update_layout(template="plotly_white", hovermode="x unified", height=400, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=-0.15))
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**趋势：** {r.trend_summary or '_暂无_'}")
    with c2:
        st.markdown(f"**风险：** {r.risk_summary or '_暂无_'}")
    if r.research_summary:
        st.info(r.research_summary)


# ══════════════════════════════════════════════════════════════════════
#  Page: 基金 ETF
# ══════════════════════════════════════════════════════════════════════
def page_fund():
    st.title("💰 基金 ETF")
    symbol = st.text_input("基金代码", placeholder="QQQ.US  510300.SH  2800.HK", key="fund_input").strip().upper()
    if not symbol:
        st.info("输入代码后按回车分析")
        return

    with st.spinner(f"分析 {symbol}..."):
        try:
            from backend.services.fund_service import get_fund_analysis
            r = get_fund_analysis(symbol, use_llm=st.session_state.get("use_llm", True))
        except Exception as e:
            st.error(f"分析失败：{e}")
            return

    for w in r.warnings:
        st.warning(w)

    if r.quote:
        q = r.quote
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("最新价", f"{q.last_price:.2f}" if q.last_price else "-")
        c2.metric("NAV", f"{q.nav:.4f}" if q.nav else "-")
        c3.metric("溢价率", f"{q.premium_discount:.2f}%" if q.premium_discount is not None else "-")
        c4.metric("类型", r.fund_type or "-")

    if r.info:
        info = r.info
        with st.expander("基金详情"):
            c1, c2, c3, c4 = st.columns(4)
            c1.caption(f"公司：{info.fund_company or '-'}")
            c2.caption(f"类别：{info.asset_class or '-'}")
            c3.caption(f"成立：{info.inception_date or '-'}")
            c4.caption(f"费率：{info.expense_ratio:.2%}" if info.expense_ratio else "费率：-")

    if r.bars:
        import pandas as pd
        import plotly.graph_objects as go
        df = pd.DataFrame(r.bars)
        df["date"] = pd.to_datetime(df["date"])
        col = "nav" if "nav" in df.columns and df["nav"].notna().any() else "close"
        fig = go.Figure()
        fv = df[col].dropna().iloc[0] if len(df[col].dropna()) else 1
        fig.add_trace(go.Scatter(x=df["date"], y=df[col]/fv*100, mode="lines", name=r.name or symbol, line=dict(color="#f59e0b", width=2)))
        if r.benchmark_bars:
            bm = pd.DataFrame(r.benchmark_bars)
            bm["date"] = pd.to_datetime(bm["date"])
            if "close" in bm.columns and len(bm["close"].dropna()):
                fbm = bm["close"].dropna().iloc[0]
                fig.add_trace(go.Scatter(x=bm["date"], y=bm["close"]/fbm*100, mode="lines", name="基准", line=dict(color="#8b5cf6", dash="dash")))
        fig.update_layout(template="plotly_white", hovermode="x unified", height=380, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**业绩：** {r.performance_summary or '_暂无_'}")
        st.markdown(f"**风险：** {r.risk_summary or '_暂无_'}")
    with c2:
        st.markdown(f"**配置：** {r.allocation_summary or '_暂无_'}")
        st.markdown(f"**定投：** {r.dca_summary or '_暂无_'}")
    if r.research_summary:
        st.info(r.research_summary)


# ══════════════════════════════════════════════════════════════════════
#  Page: 宏观研究
# ══════════════════════════════════════════════════════════════════════
def page_macro():
    st.title("🌍 宏观研究")
    try:
        from backend.services.macro_service import get_macro_snapshot, get_macro_series
    except Exception as e:
        st.error(f"加载宏观模块失败：{e}")
        return

    c1, c2 = st.columns(2)
    with c1:
        region = st.selectbox("地区", ["", "US", "CN", "EU", "JP", "GLOBAL"],
                              format_func=lambda x: {"": "全部", "US": "美国", "CN": "中国", "EU": "欧洲", "JP": "日本", "GLOBAL": "全球"}[x])
    with c2:
        category = st.selectbox("类别", ["", "GDP", "Inflation", "Employment", "Interest Rate", "Money Supply", "Trade", "Housing", "Consumer", "Business", "Other"],
                                format_func=lambda x: x or "全部")

    try:
        snap = get_macro_snapshot(region=region or None, category=category or None)
    except Exception as e:
        st.error(f"加载宏观数据失败：{e}")
        st.info("请先运行 `python scripts/update_macro.py` 更新宏观数据")
        return

    if not snap.items:
        st.info("暂无宏观数据。请运行 `python scripts/update_macro.py`")
        return

    import pandas as pd
    df = pd.DataFrame([{"指标": i.name or i.indicator, "代码": i.indicator, "地区": i.region or "", "最新日期": i.latest_date or "", "最新值": f"{i.latest_value:.2f}" if i.latest_value else "-", "趋势": i.trend_label or ""} for i in snap.items])
    st.dataframe(df, use_container_width=True, hide_index=True, height=300)

    # Chart
    opts = {f"{i.name or i.indicator} ({i.indicator})": i.indicator for i in snap.items}
    sel = st.multiselect("选择指标对比（最多6个）", list(opts.keys()), max_selections=6)
    if sel:
        syms = [opts[l] for l in sel]
        try:
            series = get_macro_series(syms, limit_per_symbol=240)
        except Exception as e:
            st.error(f"加载时序失败：{e}")
            series = None
        if series and series.items:
            import plotly.graph_objects as go
            fig = go.Figure()
            colors = ["#f59e0b", "#3b82f6", "#10b981", "#ef4444", "#8b5cf6", "#ec4899"]
            for i, sym in enumerate(syms):
                pts = [p for p in series.items if p.symbol == sym]
                if not pts: continue
                sdf = pd.DataFrame(pts)
                sdf["date"] = pd.to_datetime(sdf["date"])
                sdf = sdf.sort_values("date")
                vals = sdf["value"].dropna()
                if len(vals) == 0: continue
                fv = vals.iloc[0]
                name = sel[i].split("(")[0].strip()
                fig.add_trace(go.Scatter(x=sdf["date"], y=sdf["value"]/fv*100, mode="lines", name=name, line=dict(color=colors[i%6], width=1.8)))
            fig.update_layout(template="plotly_white", hovermode="x unified", height=400, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.18))
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 新闻雷达
# ══════════════════════════════════════════════════════════════════════
def page_news():
    st.title("📰 新闻雷达")
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        market = st.selectbox("市场", ["ALL", "CN", "US", "HK", "GLOBAL"], key="news_market")
    with c2:
        limit = st.slider("条数", 10, 100, 50)
    with c3:
        kw = st.text_input("搜索", placeholder="关键词...", key="news_kw")

    @st.cache_data(ttl=300, show_spinner=False)
    def _load_news(_market, _limit, _kw):
        from backend.services.news_service import get_latest_news, search_news
        if _kw.strip():
            return search_news(_kw.strip(), limit=_limit)
        return get_latest_news(limit=_limit, market=_market if _market != "ALL" else None)

    with st.spinner("加载新闻..."):
        try:
            result = _load_news(market, limit, kw)
        except Exception as e:
            st.error(f"加载失败：{e}")
            return

    if not result or not result.items:
        st.info("暂无新闻数据")
        if st.button("📡 尝试采集新闻", use_container_width=True):
            with st.spinner("采集中..."):
                from backend.services.news_service import collect_news
                from backend.schemas.news import NewsCollectRequest
                try:
                    r2 = collect_news(NewsCollectRequest(limit_per_source=5, markets=["CN", "US", "HK", "GLOBAL"], symbols=[], keywords=[]))
                    st.success(f"采集完成，保存 {r2.saved_count} 条")
                    st.rerun()
                except Exception as exc:
                    st.error(f"采集失败：{exc}")
        return

    st.caption(f"共 {result.count} 条 · {result.last_update}")
    for item in result.items[:limit]:
        with st.container():
            title = item.title or "(无标题)"
            url = item.url
            if url:
                st.markdown(f"**[{title}]({url})**")
            else:
                st.markdown(f"**{title}**")
            meta = []
            if item.source: meta.append(f"📡 {item.source}")
            if item.published_at: meta.append(f"🕐 {item.published_at}")
            st.caption(" · ".join(meta))
            tags = (item.risk_tags or []) + (item.topics or [])[:3]
            if tags:
                st.caption(" ".join(f"`{t}`" for t in tags[:8]))
            if item.summary:
                with st.expander("摘要"):
                    st.markdown(item.summary)
            st.divider()


# ══════════════════════════════════════════════════════════════════════
#  Page: AI 研究
# ══════════════════════════════════════════════════════════════════════
def page_ai():
    st.title("🤖 AI 研究对话")
    use_llm = st.session_state.get("use_llm", True)
    scope = st.radio("范围", ["market", "single_asset", "multi_asset"], horizontal=True,
                     format_func=lambda s: {"market": "全市场", "single_asset": "单资产", "multi_asset": "多资产"}[s])

    asset = None
    syms = []
    if scope == "single_asset":
        asset = st.text_input("资产代码", "000300.SH").strip().upper() or None
    elif scope == "multi_asset":
        inp = st.text_input("资产代码（逗号分隔）", "000300.SH, QQQ.US").strip()
        syms = [s.strip().upper() for s in inp.split(",") if s.strip()]

    if st.button("⚡ 生成市场摘要", disabled=not use_llm):
        if not use_llm:
            st.warning("请启用 AI 模型")
        else:
            with st.spinner("AI 思考中..."):
                from backend.services.llm_service import generate_quick_summary
                from backend.schemas.llm import LLMQuickSummaryRequest
                r = generate_quick_summary(LLMQuickSummaryRequest(scope=scope, asset_symbol=asset, symbols=syms, use_llm=True))
                if r.ok: st.success(r.text)
                else: st.info(r.text)

    st.markdown("---")
    q = st.text_area("💬 你的问题", placeholder="当前市场最大的风险是什么？", height=100, key="ai_q")
    if st.button("提问", disabled=not q.strip() or not use_llm, type="primary"):
        with st.spinner("AI 思考中..."):
            from backend.services.llm_service import answer_research_question
            from backend.schemas.llm import LLMChatRequest
            r = answer_research_question(LLMChatRequest(question=q.strip(), scope=scope, asset_symbol=asset, symbols=syms, use_llm=True))
            if r.ok: st.success(r.text)
            else: st.info(r.text)
            for w in r.warnings:
                st.warning(w)


# ══════════════════════════════════════════════════════════════════════
#  Page: 报告库
# ══════════════════════════════════════════════════════════════════════
def page_reports():
    st.title("📚 报告库")
    try:
        from backend.services.report_service import list_reports, get_report, get_latest_report
        rl = list_reports()
    except Exception as e:
        st.error(f"加载失败：{e}")
        return

    if not rl.reports:
        st.info("报告库为空")
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        idx = st.radio("选择报告", options=list(range(len(rl.reports))),
                       format_func=lambda i: rl.reports[i].title or rl.reports[i].filename)
        sel = rl.reports[idx]
        st.caption(f"📅 {sel.updated_at} · 📦 {sel.size_bytes/1024:.1f} KB")

    with c2:
        try:
            r = get_report(sel.filename)
            st.subheader(r.title or r.filename)
            st.markdown(r.content)
        except Exception as e:
            st.error(f"读取失败：{e}")


# ══════════════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════════════
PAGES = {
    "🏠 首页": page_home,
    "📊 市场热力榜": page_dashboard,
    "📈 个股分析": page_stock,
    "💰 基金 ETF": page_fund,
    "🌍 宏观研究": page_macro,
    "📰 新闻雷达": page_news,
    "🤖 AI 研究": page_ai,
    "📚 报告库": page_reports,
}

with st.sidebar:
    logo = ROOT / "frontend" / "public" / "hanbao.png"
    if logo.exists():
        st.image(str(logo), width=80)
    st.markdown("## 汉堡投研助手")
    page = st.radio("导航", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.session_state.use_llm = st.toggle("🤖 AI 模型", value=st.session_state.get("use_llm", True))
    st.caption("RAbot v0.1 · Streamlit")

PAGES[page]()
