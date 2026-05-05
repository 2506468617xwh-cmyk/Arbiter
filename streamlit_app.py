"""RAbot 投研助手 — Streamlit 版"""
from __future__ import annotations
import os, sys, math
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path: sys.path.insert(0, str(ROOT / "src"))
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

import streamlit as st
st.set_page_config(page_title="RAbot 投研助手", page_icon="🍔", layout="wide")

# ── secrets → environ ────────────────────────────────────────────────
try:
    for k, v in st.secrets.items():
        if k not in os.environ and isinstance(v, str):
            os.environ[k] = v
except: pass
os.environ.setdefault("RABOT_AUTO_UPDATE_ON_START", "false")
os.environ.setdefault("RABOT_NEWS_AUTO_REFRESH_MINUTES", "0")
os.environ.setdefault("RABOT_DATA_DIR", str(ROOT / "data"))

# ── session init ─────────────────────────────────────────────────────
if "use_llm" not in st.session_state: st.session_state.use_llm = True

# ── CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] { gap: 4px; padding-top: 0.5rem; }
    .stTabs [data-baseweb="tab"] { padding: 8px 16px; font-size: .88rem; }
    .rabot-card { border:1px solid #e5e7eb; border-radius:14px; padding:1.2rem 1.4rem; background:#fff; box-shadow:0 1px 4px rgba(0,0,0,.04); margin-bottom:.6rem; }
    .rabot-metric-label { font-size:.76rem; color:#6b7280; text-transform:uppercase; letter-spacing:.5px; }
    .rabot-metric-value { font-size:1.4rem; font-weight:700; }
    .rabot-up { color:#059669; } .rabot-down { color:#dc2626; } .rabot-muted { color:#6b7280; }
    .rabot-tag { display:inline-block; padding:1px 10px; border-radius:999px; font-size:.7rem; background:#f3f4f6; margin:2px; }
    .rabot-tag-green { background:#d1fae5; color:#065f46; }
    .rabot-tag-red { background:#fee2e2; color:#991b1b; }
    .rabot-tag-amber { background:#fef3c7; color:#92400e; }
    .rabot-section-title { font-size:.82rem; font-weight:600; color:#374151; text-transform:uppercase; letter-spacing:.6px; margin-bottom:.6rem; }
    hr.rabot-hr { margin:.6rem 0; border-color:#e5e7eb; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=120, show_spinner=False)
def _fetch_performance():
    from backend.services.market_service import get_market_performance
    return get_market_performance()

def _fmt_pct(v):
    if v is None: return "-"
    return f"{v:+.2f}%"

def _color_pct(v):
    if v is None: return ""
    return "color:#059669" if v >= 0 else "color:#dc2626"

def _metric_card(label, value, delta=None, cols=None):
    """Draw a metric card in a column or standalone."""
    html = f'<div class="rabot-card"><div class="rabot-metric-label">{label}</div>'
    html += f'<div class="rabot-metric-value">{value}</div>'
    if delta:
        cls = "rabot-up" if (delta.startswith("+") or (delta and delta[0] not in "- +")) else "rabot-down"
        html += f'<div class="{cls}" style="font-size:.82rem;margin-top:2px;">{delta}</div>'
    html += '</div>'
    if cols is not None:
        cols.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 首页
# ══════════════════════════════════════════════════════════════════════
def page_home():
    st.markdown("## 🍔 RAbot 投研总览")
    try:
        from backend.services.overview_service import build_overview
        ov = build_overview()
    except Exception as e:
        st.error(f"{e}"); return

    c1,c2,c3,c4,c5 = st.columns(5)
    _metric_card("市场状态", ov.market_status, delta=None, cols=c1)
    _metric_card("指数数量", str(ov.market.count if ov.market else 0), delta=None, cols=c2)
    _metric_card("新闻数量", str(ov.news.count if ov.news else 0), delta=None, cols=c3)
    _metric_card("宏观指标", str(ov.macro.count if ov.macro else 0), delta=None, cols=c4)
    _metric_card("报告数量", str(ov.reports.count if ov.reports else 0), delta=None, cols=c5)
    st.caption(f"更新于 {ov.last_update}")

    c1,c2 = st.columns(2)
    with c1:
        st.markdown('<div class="rabot-section-title">📊 市场</div>', unsafe_allow_html=True)
        st.markdown(ov.market_summary or "_暂无_")
        if ov.market:
            for h in ov.market.highlights: st.success(h)
    with c2:
        st.markdown('<div class="rabot-section-title">🌍 宏观 · 📰 新闻</div>', unsafe_allow_html=True)
        st.markdown(ov.macro_summary or "_暂无宏观摘要_")
        st.markdown(ov.news_summary or "_暂无新闻摘要_")
    st.markdown('<div class="rabot-section-title">📚 报告</div>', unsafe_allow_html=True)
    st.markdown(ov.report_summary or "_暂无_")
    if ov.reports and ov.reports.latest_title:
        st.info(f"最新：{ov.reports.latest_title}")


# ══════════════════════════════════════════════════════════════════════
#  Page: 市场热力榜
# ══════════════════════════════════════════════════════════════════════
def page_dashboard():
    st.markdown("## 📊 市场热力榜")
    try:
        from backend.services.market_service import get_market_dashboard
        dash = get_market_dashboard()
    except Exception as e:
        st.error(f"{e}"); return

    c1,c2,c3,c4 = st.columns(4)
    _metric_card("市场状态", dash.market_status, delta=None, cols=c1)
    _metric_card("覆盖资产", str(dash.asset_count), delta=None, cols=c2)
    _metric_card("最新日期", dash.latest_date or "-", delta=None, cols=c3)
    _metric_card("趋势总结", dash.summary[:40]+"…" if dash.summary and len(dash.summary)>40 else (dash.summary or "-"), delta=None, cols=c4)

    import pandas as pd
    tab1, tab2, tab3 = st.tabs(["🔥 强势资产", "❄️ 弱势资产", "📋 完整排行"])

    def _df(items, cols, extra_cols=None):
        base = {"代码": "symbol", "名称": "name", "1W%": "return_1w", "1M%": "return_1m", "3M%": "return_3m", "YTD%": "return_ytd", "波动%": "volatility_20d", "回撤%": "drawdown"}
        rows = []
        for a in items:
            row = {k: getattr(a, v, None) for k, v in base.items()}
            if extra_cols:
                for k, v in extra_cols.items():
                    row[k] = getattr(a, v, None)
            rows.append(row)
        return pd.DataFrame(rows)

    def _style(df):
        num_cols = [c for c in df.columns if "%" in c]
        return df.style.format(precision=2, na_rep="-").map(lambda v: _color_pct(v) if isinstance(v, (int, float)) else "", subset=num_cols)

    with tab1:
        if dash.strong_assets:
            st.dataframe(_style(_df(dash.strong_assets, ["trend_signal"]).drop(columns=["代码"]).set_index("名称")), use_container_width=True)
        else: st.info("暂无")
    with tab2:
        if dash.weak_assets:
            st.dataframe(_style(_df(dash.weak_assets, {"风险": "risk_level"}).drop(columns=["代码"]).set_index("名称")), use_container_width=True)
        else: st.info("暂无")
    with tab3:
        perf = _fetch_performance()
        if perf.items:
            df = _df(perf.items, {"趋势": "trend_signal", "风险": "risk_level"})
            st.dataframe(_style(df.drop(columns=["代码"]).set_index("名称")), use_container_width=True, height=520)


# ══════════════════════════════════════════════════════════════════════
#  Page: 走势图
# ══════════════════════════════════════════════════════════════════════
def page_charts():
    st.markdown("## 📈 多资产走势对比")
    from backend.services.market_service import get_available_symbols
    symbols = get_available_symbols()
    if not symbols:
        st.info("暂无资产数据"); return

    c1,c2 = st.columns([3,1])
    with c1:
        sel = st.multiselect("选择资产（可多选）", symbols, default=symbols[:4] if len(symbols)>=4 else symbols)
    with c2:
        mode = st.radio("Y轴", ["归一化", "收盘价", "回撤"], horizontal=True)

    if not sel: sel = symbols[:4]

    import pandas as pd
    import plotly.graph_objects as go

    from backend.services.market_service import get_market_timeseries
    ts = get_market_timeseries(sel, normalize=(mode == "归一化"))

    if ts.items:
        rows = [it.model_dump() for it in ts.items]
        df = pd.DataFrame(rows)
        if "date" not in df.columns:
            st.warning("走势图数据格式异常，缺少日期列")
        else:
            df["date"] = pd.to_datetime(df["date"])
            fig = go.Figure()
            colors = ["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899","#f97316","#06b6d4"]
            for i, sym in enumerate(sel):
                sdf = df[df["symbol"]==sym].sort_values("date")
                if sdf.empty: continue
                if mode == "归一化":
                    y, label = sdf["normalized"], "归一化"
                elif mode == "回撤":
                    y, label = sdf["drawdown"], "回撤%"
                else:
                    y, label = sdf["close"], "收盘价"
                name = sdf["name"].dropna().iloc[0] if len(sdf["name"].dropna()) else sym
                fig.add_trace(go.Scatter(x=sdf["date"], y=y, mode="lines", name=name, line=dict(color=colors[i%8], width=2)))
            fig.update_layout(template="plotly_white", hovermode="x unified", height=460, margin=dict(l=0,r=0,t=8,b=0), legend=dict(orientation="h", y=-.15))
            st.plotly_chart(fig, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 单资产研究
# ══════════════════════════════════════════════════════════════════════
def page_asset():
    st.markdown("## 🔍 单资产深度研究")
    from backend.services.market_service import get_available_symbols
    symbols = get_available_symbols()
    if not symbols:
        st.info("暂无资产"); return

    symbol = st.selectbox("选择资产", symbols, key="asset_sel")

    if st.button("🔍 开始研究", type="primary"):
        with st.spinner(f"分析 {symbol}..."):
            from backend.services.research_view_service import get_asset_research
            r = get_asset_research(symbol)

        for w in r.warnings: st.warning(w)

        # Cards
        score = r.technical.get("score") if isinstance(r.technical, dict) else None
        grade = r.technical.get("grade") if isinstance(r.technical, dict) else None
        c1,c2,c3,c4 = st.columns(4)
        _metric_card("资产", r.name or symbol, delta=None, cols=c1)
        _metric_card("评分", f"{score:.0f}" if score else "-", delta=grade, cols=c2)
        _metric_card("趋势", (r.market.trend_signal if r.market else None) or "-", delta=None, cols=c3)
        _metric_card("最新日期", r.latest_date or "-", delta=None, cols=c4)

        # Chart
        if r.series:
            import pandas as pd
            import plotly.graph_objects as go
            rows = [it.model_dump() for it in r.series]
            df = pd.DataFrame(rows)
            if "date" not in df.columns: st.warning("数据异常")
            else:
                df["date"] = pd.to_datetime(df["date"])
            fig = go.Figure()
            if "close" in df.columns:
                fc = df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
                fig.add_trace(go.Scatter(x=df["date"], y=df["close"]/fc*100, mode="lines", name=r.name or symbol, line=dict(color="#f59e0b", width=2)))
            fig.update_layout(template="plotly_white", hovermode="x unified", height=380, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

        # Technical detail
        if isinstance(r.technical, dict) and r.technical:
            with st.expander("📊 技术面详情"):
                import pandas as pd
                items = {k: f"{v:.2f}" if isinstance(v, float) else str(v) for k, v in r.technical.items() if k not in ("series",)}
                st.json(items)

        # Related news
        if r.related_news:
            st.markdown('<div class="rabot-section-title">📰 关联新闻</div>', unsafe_allow_html=True)
            for n in r.related_news[:5]:
                title = n.title or "(无标题)"
                url = getattr(n, "url", None)
                if url: st.markdown(f"- [{title}]({url})")
                else: st.markdown(f"- {title}")


# ══════════════════════════════════════════════════════════════════════
#  Page: 个股
# ══════════════════════════════════════════════════════════════════════
def page_stock():
    st.markdown("## 📈 个股分析")
    symbol = st.text_input("股票代码", placeholder="TSLA.US  600519.SH  00700.HK", key="stk_inp").strip().upper()
    if not symbol: st.info("输入代码后按回车"); return

    with st.spinner(f"分析 {symbol}..."):
        try:
            from backend.services.stock_service import get_stock_analysis
            r = get_stock_analysis(symbol, use_llm=st.session_state.use_llm)
        except Exception as e:
            st.error(f"{e}"); return

    for w in r.warnings: st.warning(w)

    if r.quote:
        q = r.quote
        chg = q.last_price - q.prev_close if q.last_price and q.prev_close else None
        pct = chg/q.prev_close*100 if chg is not None and q.prev_close else None
        c1,c2,c3,c4,c5 = st.columns(5)
        _metric_card("最新价", f"{q.last_price:.2f}" if q.last_price else "-", delta=_fmt_pct(pct), cols=c1)
        _metric_card("最高", f"{q.high:.2f}" if q.high else "-", delta=None, cols=c2)
        _metric_card("最低", f"{q.low:.2f}" if q.low else "-", delta=None, cols=c3)
        _metric_card("开盘", f"{q.open:.2f}" if q.open else "-", delta=None, cols=c4)
        _metric_card("成交量", f"{q.volume:,.0f}" if q.volume else "-", delta=None, cols=c5)

    if r.bars:
        import pandas as pd
        import plotly.graph_objects as go
        rows=[it.model_dump() for it in r.bars]; df=pd.DataFrame(rows)
        if "date" not in df.columns: st.warning("K线数据异常")
        else:
            df["date"]=pd.to_datetime(df["date"])
            fig = go.Figure()
            fc = df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
            fig.add_trace(go.Scatter(x=df["date"], y=df["close"]/fc*100, mode="lines", name=r.name or symbol, line=dict(color="#f59e0b", width=2)))
            if "ma20" in df.columns and df["ma20"].notna().any():
                fm=df["ma20"].dropna().iloc[0]; fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"]/fm*100, mode="lines", name="MA20", line=dict(color="#3b82f6", dash="dot")))
            if "ma60" in df.columns and df["ma60"].notna().any():
                fm2=df["ma60"].dropna().iloc[0]; fig.add_trace(go.Scatter(x=df["date"], y=df["ma60"]/fm2*100, mode="lines", name="MA60", line=dict(color="#10b981", dash="dot")))
            if r.benchmark_bars:
                bm_rows=[it.model_dump() for it in r.benchmark_bars]; bm=pd.DataFrame(bm_rows)
                if "date" in bm.columns:
                    bm["date"]=pd.to_datetime(bm["date"])
                    if "close" in bm.columns and len(bm["close"].dropna()):
                        fbm=bm["close"].dropna().iloc[0]
                        fig.add_trace(go.Scatter(x=bm["date"], y=bm["close"]/fbm*100, mode="lines", name=r.benchmark_name or "基准", line=dict(color="#8b5cf6", dash="dash")))
            fig.update_layout(template="plotly_white", hovermode="x unified", height=400, margin=dict(l=0,r=0,t=0,b=0), legend=dict(orientation="h", y=-.15))
            st.plotly_chart(fig, use_container_width=True)

    c1,c2=st.columns(2)
    with c1: st.markdown(f"**趋势：** {r.trend_summary or '_暂无_'}")
    with c2: st.markdown(f"**风险：** {r.risk_summary or '_暂无_'}")
    if r.research_summary: st.info(r.research_summary)


# ══════════════════════════════════════════════════════════════════════
#  Page: 基金 ETF
# ══════════════════════════════════════════════════════════════════════
def page_fund():
    st.markdown("## 💰 基金 ETF 分析")
    symbol = st.text_input("基金代码", placeholder="QQQ.US  510300.SH  2800.HK", key="fnd_inp").strip().upper()
    if not symbol: st.info("输入代码后按回车"); return

    with st.spinner(f"分析 {symbol}..."):
        try:
            from backend.services.fund_service import get_fund_analysis
            r = get_fund_analysis(symbol, use_llm=st.session_state.use_llm)
        except Exception as e:
            st.error(f"{e}"); return

    for w in r.warnings: st.warning(w)

    if r.quote:
        q=r.quote
        c1,c2,c3,c4=st.columns(4)
        _metric_card("最新价", f"{q.last_price:.2f}" if q.last_price else "-", delta=None, cols=c1)
        _metric_card("NAV", f"{q.nav:.4f}" if q.nav else "-", delta=None, cols=c2)
        _metric_card("溢价率", f"{q.premium_discount:.2f}%" if q.premium_discount is not None else "-", delta=None, cols=c3)
        _metric_card("类型", r.fund_type or "-", delta=None, cols=c4)

    if r.info:
        with st.expander("📋 基金详情"):
            i=r.info; c1,c2,c3,c4=st.columns(4)
            c1.caption(f"公司：{i.fund_company or '-'}")
            c2.caption(f"类别：{i.asset_class or '-'}")
            c3.caption(f"成立：{i.inception_date or '-'}")
            c4.caption(f"费率：{i.expense_ratio:.2%}" if i.expense_ratio else "-")

    if r.bars:
        import pandas as pd; import plotly.graph_objects as go
        rows=[it.model_dump() for it in r.bars]; df=pd.DataFrame(rows)
        if "date" not in df.columns: st.warning("数据异常")
        else:
            df["date"]=pd.to_datetime(df["date"])
            col="nav" if "nav" in df.columns and df["nav"].notna().any() else "close"
            fig=go.Figure()
            fv=df[col].dropna().iloc[0] if len(df[col].dropna()) else 1
            fig.add_trace(go.Scatter(x=df["date"], y=df[col]/fv*100, mode="lines", name=r.name or symbol, line=dict(color="#f59e0b", width=2)))
            if r.benchmark_bars:
                bm_rows=[it.model_dump() for it in r.benchmark_bars]; bm=pd.DataFrame(bm_rows)
                if "date" in bm.columns:
                    bm["date"]=pd.to_datetime(bm["date"])
                    if "close" in bm.columns and len(bm["close"].dropna()):
                        fbm=bm["close"].dropna().iloc[0]
                        fig.add_trace(go.Scatter(x=bm["date"], y=bm["close"]/fbm*100, mode="lines", name="基准", line=dict(color="#8b5cf6", dash="dash")))
            fig.update_layout(template="plotly_white", hovermode="x unified", height=380, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig, use_container_width=True)

    c1,c2=st.columns(2)
    with c1: st.markdown(f"**业绩：** {r.performance_summary or '_暂无_'}"); st.markdown(f"**风险：** {r.risk_summary or '_暂无_'}")
    with c2: st.markdown(f"**配置：** {r.allocation_summary or '_暂无_'}"); st.markdown(f"**定投：** {r.dca_summary or '_暂无_'}")
    if r.research_summary: st.info(r.research_summary)


# ══════════════════════════════════════════════════════════════════════
#  Page: 多资产对比
# ══════════════════════════════════════════════════════════════════════
def page_multi():
    st.markdown("## 🔗 多资产对比 & 相关性")
    from backend.services.market_service import get_available_symbols
    symbols = get_available_symbols()
    if not symbols: st.info("暂无资产"); return

    sel = st.multiselect("选择资产", symbols, default=symbols[:5] if len(symbols)>=5 else symbols)
    if not sel: sel=symbols[:4]

    if st.button("🔍 对比分析", type="primary"):
        with st.spinner("计算中..."):
            from backend.services.research_view_service import get_multi_asset_research
            from backend.schemas.research_view import MultiAssetRequest
            r = get_multi_asset_research(MultiAssetRequest(symbols=sel))

        for w in r.warnings: st.warning(w)

        # Chart
        if r.normalized_series:
            import pandas as pd; import plotly.graph_objects as go
            rows=[it.model_dump() for it in r.normalized_series]; df=pd.DataFrame(rows)
            if "date" in df.columns:
                df["date"]=pd.to_datetime(df["date"])
                fig=go.Figure()
                colors=["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899","#f97316","#06b6d4"]
                for i,sym in enumerate(sel):
                    sdf=df[df["symbol"]==sym].sort_values("date")
                    if sdf.empty: continue
                    fig.add_trace(go.Scatter(x=sdf["date"], y=sdf["normalized"], mode="lines", name=sym, line=dict(color=colors[i%8], width=2)))
                fig.update_layout(template="plotly_white", hovermode="x unified", height=400, margin=dict(l=0,r=0,t=0,b=0), legend=dict(orientation="h", y=-.15))
                st.plotly_chart(fig, use_container_width=True)

        # Performance table
        if r.performance:
            st.markdown('<div class="rabot-section-title">📊 表现对比</div>', unsafe_allow_html=True)
            import pandas as pd
            pdf=pd.DataFrame([{"资产":p.symbol, "名称":p.name or "", "1M%":_fmt_pct(p.return_1m), "3M%":_fmt_pct(p.return_3m), "波动%":f"{p.volatility_20d:.2f}" if p.volatility_20d else "-", "回撤%":f"{p.drawdown:.2f}" if p.drawdown else "-"} for p in r.performance])
            st.dataframe(pdf, use_container_width=True, hide_index=True)

        # Correlation
        if r.correlation:
            st.markdown('<div class="rabot-section-title">🔗 相关性矩阵</div>', unsafe_allow_html=True)
            st.dataframe(r.correlation, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 宏观
# ══════════════════════════════════════════════════════════════════════
def page_macro():
    st.markdown("## 🌍 宏观研究")
    try:
        from backend.services.macro_service import get_macro_snapshot, get_macro_series
    except Exception as e:
        st.error(f"{e}"); return

    c1,c2=st.columns(2)
    with c1: region=st.selectbox("地区",["","US","CN","EU","JP","GLOBAL"],format_func=lambda x:{"":"全部","US":"美国","CN":"中国","EU":"欧洲","JP":"日本","GLOBAL":"全球"}[x])
    with c2: category=st.selectbox("类别",["","GDP","Inflation","Employment","Interest Rate","Money Supply","Trade","Housing","Consumer","Business","Other"],format_func=lambda x:x or "全部")

    try:
        snap=get_macro_snapshot(region=region or None,category=category or None)
    except Exception as e:
        st.error(f"{e}"); return

    if not snap.items:
        st.info("暂无宏观数据"); return

    import pandas as pd
    st.dataframe(pd.DataFrame([{"指标":i.name or i.symbol,"地区":i.region or "","最新值":f"{i.latest_value:.2f}" if i.latest_value else "-","3M变化":_fmt_pct(i.change_3m),"趋势":i.trend_label or ""} for i in snap.items]), use_container_width=True, hide_index=True, height=320)

    opts={f"{i.name or i.symbol} ({i.symbol})":i.symbol for i in snap.items}
    sel=st.multiselect("对比走势（最多6个）",list(opts.keys()),max_selections=6)
    if sel:
        syms=[opts[l] for l in sel]
        try: series=get_macro_series(syms,limit_per_symbol=240)
        except: series=None
        if series and series.items:
            import plotly.graph_objects as go
            rows=[it.model_dump() for it in series.items]; df=pd.DataFrame(rows)
            if "date" in df.columns:
                df["date"]=pd.to_datetime(df["date"])
                fig=go.Figure()
                colors=["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899"]
                for i,sym in enumerate(syms):
                    sdf=df[df["symbol"]==sym].sort_values("date"); vals=sdf["value"].dropna()
                    if len(vals)==0: continue
                    fv=vals.iloc[0]
                    fig.add_trace(go.Scatter(x=sdf["date"],y=sdf["value"]/fv*100,mode="lines",name=sel[i].split("(")[0].strip(),line=dict(color=colors[i%6],width=1.8)))
                fig.update_layout(template="plotly_white",hovermode="x unified",height=400,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",y=-.18))
                st.plotly_chart(fig,use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
#  Page: 新闻
# ══════════════════════════════════════════════════════════════════════
def page_news():
    st.markdown("## 📰 新闻雷达")
    c1,c2,c3=st.columns([1,1,1])
    with c1: market=st.selectbox("市场",["ALL","CN","US","HK","GLOBAL"],key="n_m")
    with c2: limit=st.slider("条数",10,100,50)
    with c3: kw=st.text_input("关键词",placeholder="搜索...",key="n_kw")

    @st.cache_data(ttl=300,show_spinner=False)
    def _load(_m,_l,_kw):
        from backend.services.news_service import get_latest_news, search_news
        if _kw.strip(): return search_news(_kw.strip(),limit=_l)
        return get_latest_news(limit=_l,market=_m if _m!="ALL" else None)

    with st.spinner("加载中..."):
        try: result=_load(market,limit,kw)
        except Exception as e: st.error(f"{e}"); return

    if not result or not result.items:
        st.info("暂无新闻")
        if st.button("📡 尝试采集",use_container_width=True):
            from backend.services.news_service import collect_news
            from backend.schemas.news import NewsCollectRequest
            try:
                r2=collect_news(NewsCollectRequest(limit_per_source=5,markets=["CN","US","HK","GLOBAL"],symbols=[],keywords=[]))
                st.success(f"保存 {r2.saved_count} 条"); st.rerun()
            except Exception as exc: st.error(f"{exc}")
        return

    st.caption(f"{result.count} 条 · {result.last_update}")
    for item in result.items[:limit]:
        title=item.title or "(无标题)"
        url=getattr(item,"url",None)
        if url: st.markdown(f"**[{title}]({url})**")
        else: st.markdown(f"**{title}**")
        meta=[]
        if item.source: meta.append(f"📡 {item.source}")
        if item.published_at: meta.append(f"🕐 {item.published_at}")
        st.caption(" · ".join(meta))
        tags=(item.risk_tags or [])+(item.topics or [])[:3]
        if tags: st.caption(" ".join(f"`{t}`" for t in tags[:8]))
        if item.summary:
            with st.expander("摘要"): st.markdown(item.summary)
        st.divider()


# ══════════════════════════════════════════════════════════════════════
#  Page: AI
# ══════════════════════════════════════════════════════════════════════
def page_ai():
    st.markdown("## 🤖 AI 研究对话")
    use=st.session_state.use_llm
    scope=st.radio("范围",["market","single_asset","multi_asset"],horizontal=True,
                   format_func=lambda s:{"market":"全市场","single_asset":"单资产","multi_asset":"多资产"}[s])
    asset=None; syms=[]
    if scope=="single_asset": asset=st.text_input("资产代码","000300.SH").strip().upper() or None
    elif scope=="multi_asset":
        inp=st.text_input("代码（逗号分隔）","000300.SH, QQQ.US").strip()
        syms=[s.strip().upper() for s in inp.split(",") if s.strip()]

    if st.button("⚡ 生成摘要",disabled=not use):
        with st.spinner("AI 分析中..."):
            from backend.services.llm_service import generate_quick_summary
            from backend.schemas.llm import LLMQuickSummaryRequest
            r=generate_quick_summary(LLMQuickSummaryRequest(scope=scope,asset_symbol=asset,symbols=syms,use_llm=True))
            if r.ok: st.success(r.text)
            else: st.info(r.text)

    q=st.text_area("💬 你的问题",placeholder="当前市场最大的风险是什么？",height=100,key="ai_q")
    if st.button("提问",disabled=not q.strip() or not use,type="primary"):
        with st.spinner("AI 分析中..."):
            from backend.services.llm_service import answer_research_question
            from backend.schemas.llm import LLMChatRequest
            r=answer_research_question(LLMChatRequest(question=q.strip(),scope=scope,asset_symbol=asset,symbols=syms,use_llm=True))
            if r.ok: st.success(r.text)
            else: st.info(r.text)


# ══════════════════════════════════════════════════════════════════════
#  Page: 报告
# ══════════════════════════════════════════════════════════════════════
def page_reports():
    st.markdown("## 📚 报告库")
    try:
        from backend.services.report_service import list_reports, get_report, get_latest_report
        rl=list_reports()
    except Exception as e:
        st.error(f"{e}"); return

    if not rl.reports: st.info("报告库为空"); return

    c1,c2=st.columns([1,2])
    with c1:
        idx=st.radio("选择",list(range(len(rl.reports))),format_func=lambda i:rl.reports[i].title or rl.reports[i].filename)
        sel=rl.reports[idx]; st.caption(f"{sel.updated_at} · {sel.size_bytes/1024:.1f} KB")
    with c2:
        try:
            r=get_report(sel.filename)
            st.subheader(r.title or r.filename); st.markdown(r.content)
        except Exception as e: st.error(f"{e}")


# ══════════════════════════════════════════════════════════════════════
#  MAIN — 顶部导航
# ══════════════════════════════════════════════════════════════════════
TABS = {
    "🏠 首页": page_home,
    "📊 热力榜": page_dashboard,
    "📈 走势图": page_charts,
    "🔍 单资产": page_asset,
    "💹 个股": page_stock,
    "💰 基金": page_fund,
    "🔗 多资产": page_multi,
    "🌍 宏观": page_macro,
    "📰 新闻": page_news,
    "🤖 AI": page_ai,
    "📚 报告": page_reports,
}

# Top bar
with st.container():
    tc1, tc2 = st.columns([8, 1])
    with tc2:
        st.session_state.use_llm = st.toggle("🤖 AI", value=st.session_state.use_llm)

tabs = st.tabs(list(TABS.keys()))
for tab, (name, func) in zip(tabs, TABS.items()):
    with tab:
        func()
