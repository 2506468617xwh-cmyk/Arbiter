"""RAbot 投研助手 — Streamlit 版  |  国内免 VPN"""
from __future__ import annotations
import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

import streamlit as st
st.set_page_config(page_title="RAbot", page_icon="🍔", layout="wide")

# ── Secrets ──────────────────────────────────────────────────────────
try:
    for k, v in st.secrets.items():
        if k not in os.environ and isinstance(v, str):
            os.environ[k] = v
except: pass
os.environ.setdefault("RABOT_AUTO_UPDATE_ON_START", "false")
os.environ.setdefault("RABOT_NEWS_AUTO_REFRESH_MINUTES", "0")

# ── Session init ─────────────────────────────────────────────────────
if "theme" not in st.session_state: st.session_state.theme = "warm"
if "lang" not in st.session_state: st.session_state.lang = "zh"
if "use_llm" not in st.session_state: st.session_state.use_llm = True
T = st.session_state.theme
L = st.session_state.lang

# ══════════════════════════════════════════════════════════════════════
#  CSS — 5 Vercel themes
# ══════════════════════════════════════════════════════════════════════
THEMES_CSS = {
    "warm": """
        :root{--bg:#f7f1e8;--bg-soft:#fffaf2;--panel:#fffdf9;--ink:#27221f;--muted:#746b64;
        --line:#e7ded3;--brand:#d97706;--brand-hover:#b45309;--brand-soft:#fff3df;
        --nav-hover:#f0e6d9;--ctrl-border:#d9cfc1;--switch:#ddd3c6;
        --shadow:0 18px 40px rgba(69,55,38,.08);color-scheme:light}
    """,
    "white-red": """
        :root{--bg:#f8fafc;--bg-soft:#fff1f2;--panel:#ffffff;--ink:#171717;--muted:#64748b;
        --line:#e2e8f0;--brand:#dc2626;--brand-hover:#b91c1c;--brand-soft:#fee2e2;
        --nav-hover:#fee2e2;--ctrl-border:#e2e8f0;--switch:#e5e7eb;
        --shadow:0 18px 42px rgba(15,23,42,.08);color-scheme:light}
    """,
    "black-blue": """
        :root{--bg:#070b12;--bg-soft:#101827;--panel:#0f172a;--ink:#e5edf7;--muted:#94a3b8;
        --line:#263244;--brand:#38bdf8;--brand-hover:#0284c7;--brand-soft:#082f49;
        --nav-hover:#172554;--ctrl-border:#334155;--switch:#334155;
        --shadow:0 18px 44px rgba(0,0,0,.34);color-scheme:dark}
    """,
    "white-green": """
        :root{--bg:#f7fbf6;--bg-soft:#ecfdf5;--panel:#ffffff;--ink:#17231c;--muted:#5f7167;
        --line:#dbe7de;--brand:#16a34a;--brand-hover:#15803d;--brand-soft:#dcfce7;
        --nav-hover:#dcfce7;--ctrl-border:#cfe3d5;--switch:#d1e7d8;
        --shadow:0 18px 40px rgba(22,101,52,.09);color-scheme:light}
    """,
    "black-gold": """
        :root{--bg:#0d0b08;--bg-soft:#18130b;--panel:#14110c;--ink:#f6ead2;--muted:#baa987;
        --line:#382d1b;--brand:#fbbf24;--brand-hover:#d97706;--brand-soft:#2b2112;
        --nav-hover:#2b2112;--ctrl-border:#45361f;--switch:#3d301d;
        --shadow:0 18px 44px rgba(0,0,0,.38);color-scheme:dark}
    """,
}

CORE_CSS = f"""
<style>
    {THEMES_CSS[T]}
    .stApp {{ background: var(--bg) !important; }}
    .stMarkdown, .stText, p, h1, h2, h3, h4, label, .stSelectbox label, .stRadio label {{ color: var(--ink) !important; }}
    .stTabs [data-baseweb="tab-list"] {{ gap: 2px; background: var(--bg); }}
    .stTabs [data-baseweb="tab"] {{ color: var(--muted) !important; padding: 8px 16px; border-radius: 8px 8px 0 0; font-size:.88rem; }}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {{ color: var(--brand) !important; background: var(--panel) !important; }}
    .stButton>button {{ border-radius:8px; font-weight:600; }}
    .stButton>button[kind="primary"] {{ background: var(--brand) !important; border-color: var(--brand) !important; color:#fff !important; }}
    .stButton>button[kind="primary"]:hover {{ background: var(--brand-hover) !important; }}
    .stButton>button[kind="secondary"] {{ border:1px solid var(--ctrl-border) !important; background: var(--panel) !important; color: var(--ink) !important; }}
    hr {{ border-color: var(--line) !important; }}
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stMultiSelect>div>div>div {{ border-color:var(--ctrl-border)!important; color:var(--ink)!important; background:var(--panel)!important; }}
    .stSelectbox [data-baseweb="popover"] li, .stMultiSelect [data-baseweb="popover"] li {{ color:var(--ink)!important; }}
    .stSelectbox [data-baseweb="popover"] li:hover, .stMultiSelect [data-baseweb="popover"] li:hover {{ background:var(--nav-hover)!important; }}
    .stSelectbox [data-baseweb="popover"], .stMultiSelect [data-baseweb="popover"] {{ background:var(--panel)!important; border-color:var(--line)!important; }}
    div[data-baseweb="select"] svg, div[data-baseweb="select"] path {{ stroke:var(--muted)!important; }}
    input[aria-autocomplete="list"] {{ color:var(--ink)!important; }}
    .stSlider>div>div>div>div {{ background:var(--brand)!important; }}
    .stRadio>div {{ gap:4px; }}
    .stRadio label {{ color:var(--ink)!important; }}
    .stRadio [data-testid="stMarkdownContainer"] p {{ color:var(--ink)!important; }}
    .stCheckbox label {{ color:var(--ink)!important; }}
    .stExpander {{ border:1px solid var(--line)!important; border-radius:10px!important; background:var(--panel)!important; }}
    .stExpander summary {{ color:var(--ink)!important; }}
    .stExpander [data-testid="stExpanderDetails"] {{ color:var(--ink)!important; }}
    .stAlert {{ border-radius:10px!important; }}
    .stDataFrame {{ border:1px solid var(--line); border-radius:10px; }}
    .rabot-card {{ border:1px solid var(--line); border-radius:14px; padding:1rem 1.2rem; background:var(--panel); box-shadow:var(--shadow); margin-bottom:.6rem; transition:box-shadow .2s; }}
    .rabot-card:hover {{ box-shadow: 0 22px 48px rgba(0,0,0,.12); }}
    .rabot-card-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:.5rem; }}
    .rabot-card-title {{ font-weight:600; color:var(--ink); line-height:1.4; }}
    .rabot-card-meta {{ font-size:.76rem; color:var(--muted); margin-top:4px; }}
    .rabot-tag {{ display:inline-block; padding:1px 10px; border-radius:999px; font-size:.7rem; background:var(--bg-soft); color:var(--muted); margin:2px; border:1px solid var(--line); }}
    .rabot-tag-accent {{ background:var(--brand-soft); color:var(--brand); border-color:var(--brand); }}
    .rabot-metric-label {{ font-size:.74rem; color:var(--muted); text-transform:uppercase; letter-spacing:.5px; }}
    .rabot-metric-value {{ font-size:1.35rem; font-weight:700; color:var(--ink); }}
    .rabot-up {{ color:#059669 !important; }} .rabot-down {{ color:#dc2626 !important; }}
    .rabot-sidebar {{ border-left:1px solid var(--line); background:var(--panel); padding:1rem 1.2rem; border-radius:12px; box-shadow:var(--shadow); }}
    .rabot-settings-row {{ display:flex; align-items:center; justify-content:space-between; padding:.4rem 0; }}
    .rabot-settings-label {{ font-size:.84rem; font-weight:600; color:var(--ink); }}
    .rabot-summary {{ border-left:3px solid var(--brand); border-radius:8px; background:var(--brand-soft); color:var(--muted); padding:.5rem .7rem; margin-top:.4rem; font-size:.84rem; line-height:1.6; }}
    .stWarning,.stInfo,.stSuccess,.stError {{ border-radius:10px !important; }}
    @media (max-width:768px) {{ .rabot-card {{ padding:.7rem .9rem; }} }}
</style>
<script>
    const t = window.parent.document.querySelector('.stApp');
    if (t) {{
        const colors = {THEMES_CSS[T].strip()};
        for (const [k, v] of Object.entries(colors)) {{
            if (k.startsWith('--')) t.style.setProperty(k, v);
        }}
    }}
</script>
"""

st.markdown(CORE_CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════
#  i18n
# ══════════════════════════════════════════════════════════════════════
I18N = {
    "home": {"zh": "首页", "en": "Home"},
    "dashboard": {"zh": "热力榜", "en": "Heatmap"},
    "charts": {"zh": "走势图", "en": "Charts"},
    "asset": {"zh": "单资产", "en": "Asset"},
    "stock": {"zh": "个股", "en": "Stocks"},
    "fund": {"zh": "基金", "en": "Funds"},
    "multi": {"zh": "多资产", "en": "Multi"},
    "macro": {"zh": "宏观", "en": "Macro"},
    "news": {"zh": "新闻", "en": "News"},
    "ai": {"zh": "AI研究", "en": "AI"},
    "reports": {"zh": "报告库", "en": "Reports"},
    "settings": {"zh": "设置", "en": "Settings"},
    "theme_label": {"zh": "主题", "en": "Theme"},
    "lang_label": {"zh": "语言", "en": "Language"},
    "use_llm": {"zh": "AI 模型", "en": "AI Model"},
    "no_data": {"zh": "暂无数据", "en": "No data"},
    "loading": {"zh": "加载中...", "en": "Loading..."},
    "err_load": {"zh": "加载失败", "en": "Load failed"},
    "search_placeholder": {"zh": "输入代码后按回车分析", "en": "Type symbol and press Enter"},
    "summary": {"zh": "摘要", "en": "Summary"},
    "read_more": {"zh": "详情", "en": "Details"},
    "source": {"zh": "来源", "en": "Source"},
    "published": {"zh": "发布", "en": "Published"},
    "view_original": {"zh": "查看原文", "en": "View Original"},
    "stock_input": {"zh": "股票代码", "en": "Stock Symbol"},
    "fund_input": {"zh": "基金代码", "en": "Fund Symbol"},
}
def t(key): return I18N.get(key, {}).get(L, key)

THEME_LABELS = {"warm": "默认暖色", "white-red": "白+红", "black-blue": "黑+蓝", "white-green": "白+绿", "black-gold": "黑+金"}

# ══════════════════════════════════════════════════════════════════════
#  Shared
# ══════════════════════════════════════════════════════════════════════
def _fmt_pct(v): return f"{v:+.2f}%" if v is not None else "-"

TAG_CN = {
    # 科技 & AI
    "AI": "人工智能", "chips": "芯片", "semiconductor": "半导体", "NVIDIA": "英伟达",
    "Apple": "苹果", "Tesla": "特斯拉", "Microsoft": "微软", "Google": "谷歌",
    "Meta": "Meta", "Amazon": "亚马逊", "tech": "科技", "software": "软件",
    "hardware": "硬件", "cloud": "云计算", "cyber": "网络安全", "robotics": "机器人",
    "EV": "电动车", "autonomous driving": "自动驾驶", "battery": "电池",
    # 宏观
    "Federal Reserve": "美联储", "Fed": "美联储", "ECB": "欧央行", "PBOC": "央行",
    "inflation": "通胀", "CPI": "CPI", "PPI": "PPI", "deflation": "通缩",
    "interest rate": "利率", "rate cut": "降息", "rate hike": "加息",
    "monetary policy": "货币政策", "fiscal policy": "财政政策",
    "GDP": "GDP", "PMI": "PMI", "NFP": "非农", "unemployment": "失业率",
    "employment": "就业", "jobless claims": "失业金", "wages": "工资",
    "manufacturing": "制造业", "services": "服务业", "retail sales": "零售",
    "trade": "贸易", "trade war": "贸易战", "tariff": "关税", "sanction": "制裁",
    "supply chain": "供应链", "export": "出口", "import": "进口",
    "geopolitics": "地缘政治", "war": "战争", "conflict": "冲突",
    "election": "大选", "Trump": "特朗普", "Biden": "拜登",
    # 中国市场
    "China": "中国", "China economy": "中国经济", "A shares": "A股",
    "CSI 300": "沪深300", "SSE": "上交所", "SZSE": "深交所",
    "Hang Seng": "恒生", "Hong Kong stocks": "港股", "CNY": "人民币",
    "Chinese tech": "中国科技", "property market": "房市", "Evergrande": "恒大",
    # 美股
    "US stocks": "美股", "S&P 500": "标普500", "Nasdaq": "纳斯达克",
    "Dow Jones": "道琼斯", "Wall Street": "华尔街", "USD": "美元",
    # 资产
    "equity": "权益", "bond": "债券", "Treasury": "美债", "yield": "收益率",
    "yield curve": "收益率曲线", "credit": "信用债", "junk bond": "垃圾债",
    "commodity": "商品", "oil": "原油", "crude": "原油", "OPEC": "OPEC",
    "gold": "黄金", "silver": "白银", "copper": "铜", "lithium": "锂",
    "iron ore": "铁矿石", "steel": "钢铁", "natural gas": "天然气",
    "forex": "外汇", "crypto": "加密货币", "Bitcoin": "比特币", "Ethereum": "以太坊",
    # 策略
    "bullish": "看涨", "bearish": "看跌", "neutral": "中性",
    "volatility": "波动率", "VIX": "VIX恐慌", "risk": "风险", "risk-off": "避险",
    "risk-on": "风险偏好", "correction": "回调", "rallie": "反弹", "crash": "暴跌",
    "bubble": "泡沫", "recession": "衰退", "soft landing": "软着陆",
    "bull market": "牛市", "bear market": "熊市",
    # 行业
    "energy": "能源", "healthcare": "医疗", "pharma": "制药", "biotech": "生物科技",
    "finance": "金融", "bank": "银行", "insurance": "保险", "fintech": "金融科技",
    "real estate": "房地产", "housing": "房产", "REITs": "REITs",
    "consumer": "消费", "luxury": "奢侈品", "retail": "零售",
    "auto": "汽车", "aerospace": "航天", "defense": "国防", "infrastructure": "基建",
    "telecom": "电信", "media": "传媒", "entertainment": "娱乐", "gaming": "游戏",
    # 公司事件
    "earnings": "财报", "earnings report": "财报", "revenue": "营收",
    "profit": "利润", "guidance": "业绩指引", "IPO": "上市", "M&A": "并购",
    "buyback": "回购", "dividend": "分红", "split": "拆股",
    "layoff": "裁员", "restructuring": "重组", "bankruptcy": "破产",
    "investigation": "调查", "fine": "罚款", "lawsuit": "诉讼",
    "regulation": "监管", "antitrust": "反垄断", "compliance": "合规",
    # 基金/ETF
    "ETF": "ETF", "fund": "基金", "mutual fund": "共同基金",
    "hedge fund": "对冲基金", "pension": "养老金", "sovereign fund": "主权基金",
    # 其他
    "market": "市场", "economy": "经济", "global": "全球", "Asia": "亚洲",
    "Europe": "欧洲", "Japan": "日本", "emerging market": "新兴市场",
    "CN": "中国", "US": "美国", "HK": "香港", "GLOBAL": "全球",
    "JP": "日本", "EU": "欧洲", "EM": "新兴市场",
}
def _tag_cn(tag: str) -> str:
    return TAG_CN.get(tag, tag)

def _metric_card(label, value, delta=None, cols=None):
    html = f'<div class="rabot-card"><div class="rabot-metric-label">{label}</div><div class="rabot-metric-value">{value}</div>'
    if delta:
        cls = "rabot-up" if (delta.startswith("+") or (delta and delta[0] not in "-+")) else "rabot-down"
        html += f'<div class="{cls}" style="font-size:.82rem;margin-top:2px;">{delta}</div>'
    html += '</div>'
    (cols or st).markdown(html, unsafe_allow_html=True)

def _safe_items(items):
    if not items: return []
    try: return [it.model_dump() for it in items]
    except: return [dict(it) if hasattr(it,'__iter__') and not isinstance(it,str) else it for it in items]

# ══════════════════════════════════════════════════════════════════════
#  Pages
# ══════════════════════════════════════════════════════════════════════

def page_home():
    st.markdown(f"## 🍔 RAbot")
    try:
        from backend.services.overview_service import build_overview
        ov = build_overview()
    except Exception as e: st.error(str(e)); return
    c1,c2,c3,c4,c5=st.columns(5)
    _metric_card("Market", ov.market_status, cols=c1)
    _metric_card("Indexes", str(ov.market.count if ov.market else 0), cols=c2)
    _metric_card("News", str(ov.news.count if ov.news else 0), cols=c3)
    _metric_card("Macro", str(ov.macro.count if ov.macro else 0), cols=c4)
    _metric_card("Reports", str(ov.reports.count if ov.reports else 0), cols=c5)
    st.caption(f"Updated {ov.last_update}")
    c1,c2=st.columns(2)
    with c1:
        st.markdown(f'<div class="rabot-metric-label">📊 {t("home")}</div>',unsafe_allow_html=True)
        st.markdown(ov.market_summary or "_—_")
        if ov.market:
            for h in ov.market.highlights: st.success(h)
    with c2:
        st.markdown(f'<div class="rabot-metric-label">🌍 Macro</div>',unsafe_allow_html=True)
        st.markdown(ov.macro_summary or "_—_")
        st.markdown(ov.news_summary or "")
    if ov.reports and ov.reports.latest_title: st.info(ov.reports.latest_title)


def page_dashboard():
    st.markdown("## 📊 " + t("dashboard"))
    try:
        from backend.services.market_service import get_market_dashboard
        dash = get_market_dashboard()
    except Exception as e: st.error(str(e)); return
    c1,c2,c3=st.columns(3)
    _metric_card("Status", dash.market_status, cols=c1)
    _metric_card("Assets", str(dash.asset_count), cols=c2)
    _metric_card("Latest", dash.latest_date or "-", cols=c3)
    import pandas as pd
    tab1,tab2,tab3=st.tabs(["🔥 Strong","❄️ Weak","📋 All"])
    def _make_df(items, extra=None):
        rows=[]
        for a in items:
            r={"Name":a.name or a.symbol,"1W%":_fmt_pct(a.return_1w),"1M%":_fmt_pct(a.return_1m),"3M%":_fmt_pct(a.return_3m),"YTD%":_fmt_pct(a.return_ytd),"Vol%":f"{a.volatility_20d:.1f}" if a.volatility_20d else "-"}
            if extra:
                for k,v in extra.items(): r[k]=getattr(a,v,None) or ""
            rows.append(r)
        return pd.DataFrame(rows)
    with tab1:
        if dash.strong_assets: st.dataframe(_make_df(dash.strong_assets),use_container_width=True,hide_index=True)
        else: st.info(t("no_data"))
    with tab2:
        if dash.weak_assets: st.dataframe(_make_df(dash.weak_assets,{"Risk":"risk_level"}),use_container_width=True,hide_index=True)
        else: st.info(t("no_data"))
    with tab3:
        from backend.services.market_service import get_market_performance
        perf=get_market_performance()
        if perf.items: st.dataframe(_make_df(perf.items,{"Trend":"trend_signal"}),use_container_width=True,hide_index=True,height=520)
        else: st.info(t("no_data"))


def page_charts():
    st.markdown("## 📈 " + t("charts"))
    from backend.services.market_service import get_available_symbols, get_market_timeseries
    syms=get_available_symbols()
    if not syms: st.info(t("no_data")); return
    c1,c2=st.columns([3,1])
    with c1: sel=st.multiselect("Assets",syms,default=syms[:4] if len(syms)>=4 else syms)
    with c2: mode=st.radio("Y",["Normalized","Close","Drawdown"],horizontal=True)
    if not sel: sel=syms[:4]
    ts=get_market_timeseries(sel,normalize=(mode=="Normalized"))
    if ts.items:
        rows=_safe_items(ts.items); import pandas as pd; df=pd.DataFrame(rows)
        if "date" in df.columns:
            import plotly.graph_objects as go
            df["date"]=pd.to_datetime(df["date"]); fig=go.Figure()
            colors=["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899","#f97316","#06b6d4"]
            for i,sym in enumerate(sel):
                sdf=df[df["symbol"]==sym].sort_values("date")
                if sdf.empty: continue
                y_col="normalized" if mode=="Normalized" else ("drawdown" if mode=="Drawdown" else "close")
                fig.add_trace(go.Scatter(x=sdf["date"],y=sdf[y_col],mode="lines",name=sym,line=dict(color=colors[i%8],width=2)))
            fig.update_layout(template="plotly_white",hovermode="x unified",height=440,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",y=-.15))
            st.plotly_chart(fig,use_container_width=True)


def page_asset():
    st.markdown("## 🔍 " + t("asset"))
    from backend.services.market_service import get_available_symbols
    syms=get_available_symbols()
    if not syms: st.info(t("no_data")); return
    symbol=st.selectbox("Asset",syms,key="asset_sel")
    if st.button("🔍 Analyze",type="primary"):
        with st.spinner(t("loading")):
            from backend.services.research_view_service import get_asset_research
            r=get_asset_research(symbol)
        for w in r.warnings: st.warning(w)
        score=r.technical.get("score") if isinstance(r.technical,dict) else None
        grade=r.technical.get("grade") if isinstance(r.technical,dict) else None
        c1,c2,c3,c4=st.columns(4)
        _metric_card("Asset",r.name or symbol,cols=c1)
        _metric_card("Score",f"{score:.0f}" if score else "-",delta=grade,cols=c2)
        _metric_card("Trend",r.market.trend_signal if r.market else "-",cols=c3)
        _metric_card("Date",r.latest_date or "-",cols=c4)
        if r.series:
            rows=_safe_items(r.series); import pandas as pd; df=pd.DataFrame(rows)
            if "date" in df.columns:
                import plotly.graph_objects as go
                df["date"]=pd.to_datetime(df["date"]); fig=go.Figure()
                fc=df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
                fig.add_trace(go.Scatter(x=df["date"],y=df["close"]/fc*100,mode="lines",name=r.name or symbol,line=dict(color="#f59e0b",width=2)))
                fig.update_layout(template="plotly_white",hovermode="x unified",height=360,margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig,use_container_width=True)
        if r.related_news:
            st.markdown(f'<div class="rabot-metric-label">📰 Related News</div>',unsafe_allow_html=True)
            for n in r.related_news[:5]:
                title=n.title or "(untitled)"; url=getattr(n,"url",None)
                st.markdown(f"- [{title}]({url})" if url else f"- {title}")


def page_stock():
    st.markdown("## 📈 " + t("stock"))
    symbol=st.text_input(t("stock_input"),placeholder="TSLA.US  600519.SH",key="stk_inp").strip().upper()
    if not symbol: st.info(t("search_placeholder")); return
    with st.spinner(t("loading")):
        try:
            from backend.services.stock_service import get_stock_analysis
            r=get_stock_analysis(symbol,use_llm=st.session_state.use_llm)
        except Exception as e: st.error(str(e)); return
    for w in r.warnings: st.warning(w)
    if r.quote:
        q=r.quote; chg=q.last_price-q.prev_close if q.last_price and q.prev_close else None
        pct=chg/q.prev_close*100 if chg is not None and q.prev_close else None
        c1,c2,c3,c4,c5=st.columns(5)
        _metric_card("Price",f"{q.last_price:.2f}" if q.last_price else "-",_fmt_pct(pct),c1)
        _metric_card("High",f"{q.high:.2f}" if q.high else "-",cols=c2)
        _metric_card("Low",f"{q.low:.2f}" if q.low else "-",cols=c3)
        _metric_card("Open",f"{q.open:.2f}" if q.open else "-",cols=c4)
        _metric_card("Volume",f"{q.volume:,.0f}" if q.volume else "-",cols=c5)
    if r.bars:
        rows=_safe_items(r.bars); import pandas as pd; df=pd.DataFrame(rows)
        if "date" in df.columns:
            import plotly.graph_objects as go
            df["date"]=pd.to_datetime(df["date"]); fig=go.Figure()
            fc=df["close"].dropna().iloc[0] if len(df["close"].dropna()) else 1
            fig.add_trace(go.Scatter(x=df["date"],y=df["close"]/fc*100,mode="lines",name=r.name or symbol,line=dict(color="#f59e0b",width=2)))
            if "ma20" in df.columns and df["ma20"].notna().any():
                fm=df["ma20"].dropna().iloc[0]; fig.add_trace(go.Scatter(x=df["date"],y=df["ma20"]/fm*100,mode="lines",name="MA20",line=dict(color="#3b82f6",dash="dot")))
            if "ma60" in df.columns and df["ma60"].notna().any():
                fm2=df["ma60"].dropna().iloc[0]; fig.add_trace(go.Scatter(x=df["date"],y=df["ma60"]/fm2*100,mode="lines",name="MA60",line=dict(color="#10b981",dash="dot")))
            fig.update_layout(template="plotly_white",hovermode="x unified",height=400,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",y=-.15))
            st.plotly_chart(fig,use_container_width=True)
    c1,c2=st.columns(2)
    with c1: st.markdown(f"**Trend:** {r.trend_summary or '_—_'}")
    with c2: st.markdown(f"**Risk:** {r.risk_summary or '_—_'}")
    if r.research_summary: st.info(r.research_summary)


def page_fund():
    st.markdown("## 💰 " + t("fund"))
    symbol=st.text_input(t("fund_input"),placeholder="QQQ.US  510300.SH",key="fnd_inp").strip().upper()
    if not symbol: st.info(t("search_placeholder")); return
    with st.spinner(t("loading")):
        try:
            from backend.services.fund_service import get_fund_analysis
            r=get_fund_analysis(symbol,use_llm=st.session_state.use_llm)
        except Exception as e: st.error(str(e)); return
    for w in r.warnings: st.warning(w)
    if r.quote:
        q=r.quote; c1,c2,c3,c4=st.columns(4)
        _metric_card("Price",f"{q.last_price:.2f}" if q.last_price else "-",cols=c1)
        _metric_card("NAV",f"{q.nav:.4f}" if q.nav else "-",cols=c2)
        _metric_card("Prem%",f"{q.premium_discount:.2f}%" if q.premium_discount is not None else "-",cols=c3)
        _metric_card("Type",r.fund_type or "-",cols=c4)
    if r.info:
        with st.expander("Fund Info"):
            i=r.info; c1,c2,c3,c4=st.columns(4)
            c1.caption(f"Company: {i.fund_company or '-'}"); c2.caption(f"Class: {i.asset_class or '-'}")
            c3.caption(f"Inception: {i.inception_date or '-'}"); c4.caption(f"Fee: {i.expense_ratio:.2%}" if i.expense_ratio else "-")
    if r.bars:
        rows=_safe_items(r.bars); import pandas as pd; df=pd.DataFrame(rows)
        if "date" in df.columns:
            import plotly.graph_objects as go
            df["date"]=pd.to_datetime(df["date"]); col="nav" if "nav" in df.columns and df["nav"].notna().any() else "close"
            fig=go.Figure(); fv=df[col].dropna().iloc[0] if len(df[col].dropna()) else 1
            fig.add_trace(go.Scatter(x=df["date"],y=df[col]/fv*100,mode="lines",name=r.name or symbol,line=dict(color="#f59e0b",width=2)))
            fig.update_layout(template="plotly_white",hovermode="x unified",height=380,margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig,use_container_width=True)
    c1,c2=st.columns(2)
    with c1: st.markdown(f"**Perf:** {r.performance_summary or '_—_'}"); st.markdown(f"**Risk:** {r.risk_summary or '_—_'}")
    with c2: st.markdown(f"**Alloc:** {r.allocation_summary or '_—_'}"); st.markdown(f"**DCA:** {r.dca_summary or '_—_'}")
    if r.research_summary: st.info(r.research_summary)


def page_multi():
    st.markdown("## 🔗 " + t("multi"))
    from backend.services.market_service import get_available_symbols
    syms=get_available_symbols()
    if not syms: st.info(t("no_data")); return
    sel=st.multiselect("Assets",syms,default=syms[:5] if len(syms)>=5 else syms)
    if not sel: sel=syms[:4]
    if st.button("🔍 Compare",type="primary"):
        with st.spinner(t("loading")):
            from backend.services.research_view_service import get_multi_asset_research
            from backend.schemas.research_view import MultiAssetRequest
            r=get_multi_asset_research(MultiAssetRequest(symbols=sel))
        for w in r.warnings: st.warning(w)
        if r.normalized_series:
            rows=_safe_items(r.normalized_series); import pandas as pd; df=pd.DataFrame(rows)
            if "date" in df.columns:
                import plotly.graph_objects as go
                df["date"]=pd.to_datetime(df["date"]); fig=go.Figure()
                colors=["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899","#f97316","#06b6d4"]
                for i,sym in enumerate(sel):
                    sdf=df[df["symbol"]==sym].sort_values("date")
                    if sdf.empty: continue
                    fig.add_trace(go.Scatter(x=sdf["date"],y=sdf["normalized"],mode="lines",name=sym,line=dict(color=colors[i%8],width=2)))
                fig.update_layout(template="plotly_white",hovermode="x unified",height=400,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",y=-.15))
                st.plotly_chart(fig,use_container_width=True)
        if r.performance:
            import pandas as pd
            pdf=pd.DataFrame([{"Asset":p.symbol,"Name":p.name or "","1M":_fmt_pct(p.return_1m),"3M":_fmt_pct(p.return_3m),"Vol%":f"{p.volatility_20d:.1f}" if p.volatility_20d else "-","DD%":f"{p.drawdown:.1f}" if p.drawdown else "-"} for p in r.performance])
            st.dataframe(pdf,use_container_width=True,hide_index=True)
        if r.correlation:
            st.markdown(f'<div class="rabot-metric-label">🔗 Correlation</div>',unsafe_allow_html=True)
            st.dataframe(r.correlation,use_container_width=True,hide_index=True)


def page_macro():
    st.markdown("## 🌍 " + t("macro"))
    try:
        from backend.services.macro_service import get_macro_snapshot, get_macro_series
    except Exception as e: st.error(str(e)); return
    c1,c2=st.columns(2)
    with c1: region=st.selectbox("Region",["","US","CN","EU","JP","GLOBAL"],format_func=lambda x:{"":"All","US":"US","CN":"China","EU":"Europe","JP":"Japan","GLOBAL":"Global"}[x])
    with c2: category=st.selectbox("Category",["","GDP","Inflation","Employment","Interest Rate","Money Supply","Trade","Housing","Consumer","Business","Other"],format_func=lambda x:x or "All")
    try: snap=get_macro_snapshot(region=region or None,category=category or None)
    except Exception as e: st.error(str(e)); return
    if not snap.items: st.info(t("no_data")); return
    import pandas as pd
    st.dataframe(pd.DataFrame([{"Indicator":i.name or i.symbol,"Region":i.region or "","Value":f"{i.latest_value:.2f}" if i.latest_value else "-","3M%":_fmt_pct(i.change_3m),"Trend":i.trend_label or ""} for i in snap.items]),use_container_width=True,hide_index=True,height=320)
    opts={f"{i.name or i.symbol} ({i.symbol})":i.symbol for i in snap.items}
    sel=st.multiselect("Compare (max 6)",list(opts.keys()),max_selections=6)
    if sel:
        syms=[opts[l] for l in sel]
        try: series=get_macro_series(syms,limit_per_symbol=240)
        except: series=None
        if series and series.items:
            rows=_safe_items(series.items); df=pd.DataFrame(rows)
            if "date" in df.columns:
                import plotly.graph_objects as go
                df["date"]=pd.to_datetime(df["date"]); fig=go.Figure()
                colors=["#f59e0b","#3b82f6","#10b981","#ef4444","#8b5cf6","#ec4899"]
                for i,sym in enumerate(syms):
                    sdf=df[df["symbol"]==sym].sort_values("date"); vals=sdf["value"].dropna()
                    if len(vals)==0: continue
                    fv=vals.iloc[0]; fig.add_trace(go.Scatter(x=sdf["date"],y=sdf["value"]/fv*100,mode="lines",name=sel[i].split("(")[0].strip(),line=dict(color=colors[i%6],width=1.8)))
                fig.update_layout(template="plotly_white",hovermode="x unified",height=400,margin=dict(l=0,r=0,t=0,b=0),legend=dict(orientation="h",y=-.18))
                st.plotly_chart(fig,use_container_width=True)

# ══════════════════════════════════════════════════════════════════════
#  Page: 新闻 — 卡片式 + 侧边详情
# ══════════════════════════════════════════════════════════════════════
def page_news():
    st.markdown("## 📰 " + t("news"))
    c1,c2,c3=st.columns([1,1,1])
    with c1: market=st.selectbox("Market",["ALL","CN","US","HK","GLOBAL"],key="n_m")
    with c2: limit=st.slider("Count",10,100,50)
    with c3: kw=st.text_input("Search",placeholder="Keyword...",key="n_kw")

    @st.cache_data(ttl=300,show_spinner=False)
    def _load_news(_m,_l,_kw):
        from backend.services.news_service import get_latest_news, search_news
        if _kw.strip(): return search_news(_kw.strip(),limit=_l)
        return get_latest_news(limit=_l,market=_m if _m!="ALL" else None)

    with st.spinner(t("loading")):
        try: result=_load_news(market,limit,kw)
        except Exception as e: st.error(str(e)); return

    if not result or not result.items:
        st.info(t("no_data"))
        if st.button("📡 Collect",use_container_width=True):
            from backend.services.news_service import collect_news
            from backend.schemas.news import NewsCollectRequest
            try:
                r2=collect_news(NewsCollectRequest(limit_per_source=5,markets=["CN","US","HK","GLOBAL"],symbols=[],keywords=[]))
                st.success(f"Saved {r2.saved_count}")
                st.rerun()
            except Exception as exc: st.error(str(exc))
        return

    st.caption(f"{result.count} items · {result.last_update}")

    # ── News cards ──
    for idx, item in enumerate(result.items[:limit]):
        title = item.title or "(untitled)"
        url = getattr(item, "url", None)
        summary = item.summary or ""
        tags = [_tag_cn(t) for t in ((item.risk_tags or []) + (item.topics or [])[:3])]

        # Truncate summary
        short_summary = summary[:120] + ("…" if len(summary) > 120 else "")

        st.markdown(f"""
        <div class="rabot-card" id="news-{idx}">
            <div class="rabot-card-header">
                <div style="flex:1">
                    <div class="rabot-card-title">{title}</div>
                    <div class="rabot-summary">{short_summary or "_No summary_"}</div>
                </div>
            </div>
            <div style="margin-top:.5rem">
                {" ".join(f'<span class="rabot-tag rabot-tag-accent">{t}</span>' for t in tags[:6])}
            </div>
            <div class="rabot-card-meta">{item.source or "?"} · {item.published_at or "?"}</div>
        </div>
        """, unsafe_allow_html=True)

        # Detail expander
        with st.expander(f"📋 {title[:50]}…"):
            meta_parts = []
            if item.source: meta_parts.append(f"**{t('source')}:** {item.source}")
            if item.published_at: meta_parts.append(f"**{t('published')}:** {item.published_at}")
            if item.provider: meta_parts.append(f"**Provider:** {item.provider}")
            st.markdown(" · ".join(meta_parts))
            if tags:
                st.markdown(" ".join(f'<span class="rabot-tag">{t}</span>' for t in tags[:10]), unsafe_allow_html=True)
            if summary:
                st.markdown(f'<div class="rabot-summary">{summary}</div>', unsafe_allow_html=True)
            content = getattr(item, "content", None) or ""
            if content and content != summary:
                with st.expander(t("read_more")):
                    st.markdown(content[:2000])
            if url:
                st.markdown(f"[🌐 {t('view_original')}]({url})")


def page_ai():
    st.markdown("## 🤖 " + t("ai"))
    use=st.session_state.use_llm
    scope=st.radio("Scope",["market","single_asset","multi_asset"],horizontal=True,
                   format_func=lambda s:{"market":"Market","single_asset":"Single","multi_asset":"Multi"}[s])
    asset=None; syms=[]
    if scope=="single_asset": asset=st.text_input("Symbol","000300.SH").strip().upper() or None
    elif scope=="multi_asset":
        inp=st.text_input("Symbols (,)", "000300.SH, QQQ.US").strip()
        syms=[s.strip().upper() for s in inp.split(",") if s.strip()]
    if st.button("⚡ Summarize",disabled=not use):
        with st.spinner(t("loading")):
            from backend.services.llm_service import generate_quick_summary
            from backend.schemas.llm import LLMQuickSummaryRequest
            r=generate_quick_summary(LLMQuickSummaryRequest(scope=scope,asset_symbol=asset,symbols=syms,use_llm=True))
        if r.ok: st.success(r.text)
        else: st.info(r.text)
    q=st.text_area("💬 Question",placeholder="What's the biggest market risk?",height=100,key="ai_q")
    if st.button("Ask",disabled=not q.strip() or not use,type="primary"):
        with st.spinner(t("loading")):
            from backend.services.llm_service import answer_research_question
            from backend.schemas.llm import LLMChatRequest
            r=answer_research_question(LLMChatRequest(question=q.strip(),scope=scope,asset_symbol=asset,symbols=syms,use_llm=True))
        if r.ok: st.success(r.text)
        else: st.info(r.text)
        for w in r.warnings: st.warning(w)


def page_reports():
    st.markdown("## 📚 " + t("reports"))
    try:
        from backend.services.report_service import list_reports, get_report
        rl=list_reports()
    except Exception as e: st.error(str(e)); return
    if not rl.reports: st.info(t("no_data")); return
    c1,c2=st.columns([1,2])
    with c1:
        idx=st.radio("Select",list(range(len(rl.reports))),format_func=lambda i:rl.reports[i].title or rl.reports[i].filename)
        sel=rl.reports[idx]; st.caption(f"{sel.updated_at} · {sel.size_bytes/1024:.1f} KB")
    with c2:
        try: r=get_report(sel.filename); st.subheader(r.title or r.filename); st.markdown(r.content)
        except Exception as e: st.error(str(e))


# ══════════════════════════════════════════════════════════════════════
#  MAIN — Top nav + Settings sidebar
# ══════════════════════════════════════════════════════════════════════
TABS = [
    ("🏠 " + t("home"), page_home),
    ("📊 " + t("dashboard"), page_dashboard),
    ("📈 " + t("charts"), page_charts),
    ("🔍 " + t("asset"), page_asset),
    ("💹 " + t("stock"), page_stock),
    ("💰 " + t("fund"), page_fund),
    ("🔗 " + t("multi"), page_multi),
    ("🌍 " + t("macro"), page_macro),
    ("📰 " + t("news"), page_news),
    ("🤖 " + t("ai"), page_ai),
    ("📚 " + t("reports"), page_reports),
]

# Settings toggle
with st.container():
    ctop, cset = st.columns([10, 1])
    with cset:
        if "show_settings" not in st.session_state: st.session_state.show_settings = False
        if st.button("⚙️" if not st.session_state.show_settings else "✕", key="settings_toggle"):
            st.session_state.show_settings = not st.session_state.show_settings

# Settings panel
if st.session_state.show_settings:
    with st.container():
        st.markdown('<div class="rabot-sidebar">', unsafe_allow_html=True)
        st.markdown(f'<div class="rabot-metric-label">{t("settings")}</div>', unsafe_allow_html=True)
        new_theme = st.selectbox(
            t("theme_label"), list(THEME_LABELS.keys()),
            format_func=lambda x: THEME_LABELS[x],
            index=list(THEME_LABELS.keys()).index(T)
        )
        new_lang = st.radio(t("lang_label"), ["zh", "en"], horizontal=True,
                           format_func=lambda x: "中文" if x=="zh" else "English",
                           index=0 if L=="zh" else 1)
        st.session_state.use_llm = st.toggle(t("use_llm"), value=st.session_state.use_llm)
        if new_theme != T or new_lang != L:
            st.session_state.theme = new_theme
            st.session_state.lang = new_lang
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# Main content
tabs = st.tabs([name for name, _ in TABS])
for tab, (_, func) in zip(tabs, TABS):
    with tab:
        func()
