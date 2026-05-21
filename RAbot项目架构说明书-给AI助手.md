# RAbot - 全球市场研究助手 项目架构说明书

> **用途**: 让 AI 助手（Claude/GPT 等）快速理解本项目架构，便于探讨优化方向。
> **生成日期**: 2026-05-20

---

## 1. 项目定位

RAbot 是一个**面向个人投资者的全球市场研究与复盘工具**。核心功能包括：

- 拉取全球主要指数/股票/ETF/基金的日线行情
- 计算技术指标 (MA, 波动率, 回撤等)
- 多源新闻采集、去重、情感分析、风险标记
- 宏观指标追踪 (FRED, Tushare)
- LLM 驱动的 AI 研究报告生成 (DeepSeek)
- React 前端展示 + FastAPI 后端

**一句话**: 本地化运行的多资产市场研究工作站，具备数据采集→存储→分析→报告→展示的完整闭环。

---

## 2. 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI + Uvicorn (Python 3.11) |
| 前端框架 | React 18 + TypeScript + Vite 5 |
| CSS | Tailwind CSS 3 + Framer Motion |
| 图表 | lightweight-charts 5 + 手写 SVG |
| 数据库 | SQLite (3个库文件) |
| LLM | DeepSeek API (OpenAI 兼容) |
| 数据源 | yfinance, Tushare, AKShare, Longbridge, Finnhub, Alpha Vantage, RSSHub |
| 部署 | Vercel (前端) + Render (后端) |

---

## 3. 目录结构

```
RAbot - Mobile/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 应用入口, CORS, 路由注册, 生产模式静态文件服务
│   ├── api/                    # API 路由层 (薄层, 只做参数解析和调用 service)
│   │   ├── market.py           # 市场指数相关接口
│   │   ├── stocks.py           # 个股分析接口
│   │   ├── funds.py            # 基金/ETF 分析接口
│   │   ├── macro.py            # 宏观研究接口
│   │   ├── news.py             # 新闻雷达接口
│   │   ├── news_intelligence.py # AI 市场情报 (叙事引擎)
│   │   ├── llm.py              # LLM 对话/快评接口
│   │   ├── research.py         # 研究引擎接口 (单资产/多资产)
│   │   ├── overview.py         # 首页聚合接口
│   │   ├── reports.py          # 报告库 CRUD 接口
│   │   ├── tasks.py            # 异步任务状态查询
│   │   └── system.py           # 系统状态/手动更新
│   ├── schemas/                # Pydantic 数据模型 (请求/响应 Schema)
│   └── services/               # 业务逻辑层
│       ├── market_service.py   # 市场数据查询与仪表盘构建
│       ├── stock_service.py    # 个股分析协调
│       ├── fund_service.py     # 基金分析协调
│       ├── macro_service.py    # 宏观数据查询与 LLM 分析
│       ├── news_service.py     # 新闻查询与采集
│       ├── news_intelligence_service.py # AI 叙事引擎
│       ├── llm_service.py      # LLM 快评/对话协调
│       ├── overview_service.py # 首页数据聚合
│       ├── report_service.py   # 报告读写删
│       ├── research_task_service.py # 异步报告生成 (核心, 约950行)
│       ├── research_view_service.py # 单/多资产研究页数据
│       ├── update_service.py   # 启动时自动数据刷新
│       └── task_manager.py     # 内存中的异步任务管理器
│
├── src/RAbot/                  # Python 核心研究库 (独立于 Web 层, 可脱离 FastAPI 使用)
│   ├── settings.py             # 全局配置 (数据目录, DB路径, 环境变量)
│   ├── data/                   # 数据采集层
│   │   ├── providers.py        # YFinanceProvider, TushareProvider, ProviderFactory
│   │   └── pipeline.py         # 数据更新管道 (拉取→计算指标→写入SQLite)
│   ├── storage/
│   │   └── sqlite_store.py     # SQLite 读写封装 (index_daily 表, update_log 表)
│   ├── analysis/               # 研究分析引擎 (纯规则, 不依赖 LLM)
│   │   ├── indicators.py       # 技术指标计算 (MA, 波动率, 回撤, 相关性, 归一化)
│   │   ├── research_engine.py  # 单/多资产评分引擎 (趋势40分+回撤25+波动20+动量15)
│   │   ├── news_research.py    # 新闻→资产关联研究
│   │   └── macro_research.py   # 宏观→资产关联研究
│   ├── stocks/                 # 个股分析模块
│   │   ├── stock_models.py     # StockQuote, StockBar, StockAnalysisResult 数据类
│   │   ├── stock_provider.py   # 抽象基类
│   │   ├── tushare_stock_provider.py  # A股数据 (Tushare API)
│   │   ├── longbridge_stock_provider.py # 美股/港股 (Longbridge API)
│   │   ├── finnhub_stock_provider.py    # 美股备选
│   │   ├── tickflow_stock_provider.py   # 可配置的第三方备选
│   │   ├── yfinance_stock_provider.py   # 最后兜底
│   │   ├── stock_analysis.py   # 核心协调逻辑 (数据获取→指标→LLM摘要, ~350行)
│   │   ├── stock_store.py      # SQLite 缓存 (data/stocks/stock_research.db)
│   │   └── symbols.py          # 代码识别 (600519.SH→CN, TSLA.US→US)
│   ├── funds/                  # 基金/ETF 分析模块 (架构与 stocks/ 对等)
│   │   ├── fund_models.py, fund_provider.py
│   │   ├── tushare_fund_provider.py, akshare_fund_provider.py
│   │   ├── longbridge_fund_provider.py, yfinance_fund_provider.py
│   │   ├── fund_analysis.py    # 核心协调逻辑 (~450行)
│   │   ├── fund_store.py       # SQLite 缓存 (data/funds/fund_research.db)
│   │   └── fund_symbols.py
│   ├── news/                   # 新闻系统
│   │   ├── news_models.py      # NewsItem 数据类
│   │   ├── news_provider.py    # 抽象基类
│   │   ├── finnhub_news_provider.py, newsapi_provider.py
│   │   ├── alphavantage_news_provider.py, rsshub_news_provider.py
│   │   ├── akshare_news_provider.py, eastmoney_news_provider.py
│   │   ├── sina_news_provider.py, futu_news_provider.py
│   │   ├── news_engine.py      # 多源采集→去重→评分→入库 (核心管道)
│   │   ├── news_dedup.py       # 基于标题相似度的去重
│   │   ├── news_quality.py     # 重要性评分, 情感推断, 风险标签
│   │   └── news_store.py       # SQLite 读写 (data/news/news_research.db)
│   ├── macro/                  # 宏观指标模块
│   │   ├── macro_provider.py   # 抽象基类 + 配置加载
│   │   ├── fred_provider.py    # FRED 数据拉取
│   │   ├── china_macro_provider.py # 中国宏观 (Tushare)
│   │   └── macro_store.py      # SQLite 读写 (macro_series 表)
│   ├── llm/                    # LLM 集成层
│   │   ├── llm_client.py       # DeepSeek OpenAI-compatible 客户端
│   │   ├── context_builder.py  # 为 LLM 构造结构化事实包 (市场/单资产/多资产)
│   │   ├── research_chat.py    # 研究对话管理器 (市场问答/单资产快评/多资产组合)
│   │   ├── research_prompt.py  # Prompt 模板
│   │   └── research_writer.py  # LLM 报告撰写器
│   ├── reporting/              # 报告生成
│   │   ├── markdown_report.py  # 核心 Markdown 报告生成器 (~600行)
│   │   └── report_jobs.py      # 报告任务定义
│   ├── review/                 # 复盘视图模块
│   │   ├── view_reviewer.py
│   │   └── view_store.py
│   └── alerts/                 # 告警模块
│       ├── alerts_engine.py
│       └── alerts_store.py
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── App.tsx             # 根组件 (底部5Tab导航, 主题/语言持久化, 页面懒加载)
│   │   ├── main.tsx            # 入口
│   │   ├── styles.css          # Tailwind + CSS 变量主题系统
│   │   ├── i18n.tsx            # 中英文国际化 (React Context)
│   │   ├── i18n-dom.ts         # DOM 文本翻译
│   │   ├── api/
│   │   │   └── client.ts       # 全部 API 类型定义 + fetch 封装 (~740行)
│   │   ├── pages/              # 页面组件 (14个页面)
│   │   │   ├── HomePage.tsx        # 首页 (全球指数卡片, AI 市场脉搏, 热门板块)
│   │   │   ├── MarketsPage.tsx     # 行情页 (仪表盘/热力榜/走势图 三子页)
│   │   │   ├── StockAnalysisPage.tsx # 个股分析页
│   │   │   ├── FundAnalysisPage.tsx  # 基金/ETF 分析页
│   │   │   ├── MacroResearchPage.tsx # 宏观研究页
│   │   │   ├── NewsPage.tsx         # 新闻雷达页
│   │   │   ├── AIResearchPage.tsx   # AI 研究页 (LLM 对话/快评)
│   │   │   ├── AssetResearchPage.tsx # 单资产研究页
│   │   │   ├── MultiAssetPage.tsx   # 多资产研究页
│   │   │   ├── ResearchPage.tsx     # 研究页容器 (包装 AIResearchPage)
│   │   │   ├── WatchlistPage.tsx    # 自选页
│   │   │   ├── ChartsPage.tsx       # 走势图页
│   │   │   ├── ReportsPage.tsx      # 报告库页
│   │   │   ├── DashboardPage.tsx    # 仪表盘页
│   │   │   └── SettingsPage.tsx     # 设置页
│   │   └── components/         # 可复用组件 (~40个)
│   │       ├── BottomNav.tsx       # 底部5Tab导航
│   │       ├── MarketOverview.tsx  # 全球指数卡片网格
│   │       ├── AISummary.tsx       # AI 市场脉搏组件
│   │       ├── TickerTape.tsx      # 跑马灯行情条
│   │       ├── IndexCard.tsx       # 指数卡片
│   │       ├── LineChart.tsx       # lightweight-charts K线/走势图
│   │       ├── HeatList.tsx        # 热力榜
│   │       ├── StockQuoteCard.tsx, StockKlineChart.tsx, StockIndicatorGrid.tsx
│   │       ├── StockAnalysisReport.tsx, StockRiskPanel.tsx, StockSearchBox.tsx
│   │       ├── FundQuoteCard.tsx, FundNavChart.tsx, FundIndicatorGrid.tsx
│   │       ├── FundAnalysisReport.tsx, FundRiskPanel.tsx, FundDcaPanel.tsx
│   │       ├── FundSearchBox.tsx, FundResearchChatPanel.tsx
│   │       ├── NewsItemCard.tsx, NewsFilterBar.tsx, NewsRiskTags.tsx
│   │       ├── NewsSourcePanel.tsx, SentimentGauge.tsx
│   │       ├── MacroLineChart.tsx, MarketNarrative.tsx
│   │       ├── ResearchForm.tsx, ResearchChatPanel.tsx, TaskStatusCard.tsx
│   │       ├── ResearchPet.tsx  # AI 研究宠物动画
│   │       ├── ReportReader.tsx # Markdown 报告阅读器
│   │       ├── ModelSettingsDrawer.tsx # 模型设置侧滑面板
│   │       └── ProgressBar.tsx, MetricCard.tsx, StatusPill.tsx 等
│   ├── vite.config.ts          # Vite 配置 (开发代理 /api → 127.0.0.1:8000)
│   └── tailwind.config.js
│
├── config/                     # YAML 配置文件
│   ├── indexes.yaml            # 17个全球指数定义 (代码, 数据源, 市场)
│   ├── macro_indicators.yaml   # 美国(11个) + 中国(7个) 宏观指标定义
│   ├── news_sources.yaml       # 新闻源配置
│   └── news_quality.yaml       # 新闻质量评分规则
│
├── data/                       # 本地数据存储
│   ├── market/index_research.db    # 指数日线 + 技术指标
│   ├── stocks/stock_research.db    # 个股缓存
│   ├── funds/fund_research.db      # 基金/ETF 缓存
│   ├── news/news_research.db       # 结构化新闻库
│   ├── macro/ (macro_series 表)    # 宏观指标时间序列
│   └── reports/                    # 生成的 Markdown 研究报告
│       └── assets/                 # 报告内嵌 SVG 图表
│
├── scripts/                    # 独立运行脚本
│   ├── update_data.py          # 手动更新指数行情
│   ├── update_news.py          # 手动更新新闻
│   ├── update_macro.py         # 手动更新宏观数据
│   ├── generate_report.py      # 手动生成报告
│   └── longbridge_oauth_login.py
│
├── .env / .env.example         # 环境变量 (API Keys)
├── requirements.txt            # Python 依赖
├── start.bat / start.sh        # 一键启动脚本
├── render.yaml                 # Render 部署配置
└── DEPLOYMENT.md               # 部署文档
```

---

## 4. 架构分层

```
┌─────────────────────────────────────────────────┐
│                   Frontend                       │
│         React 18 + TypeScript + Vite             │
│   14 pages, ~40 components, Tailwind CSS         │
│   Tab: 首页/行情/自选/资讯/AI研究                 │
└──────────────────┬──────────────────────────────┘
                   │ HTTP (REST API)
                   │ /api/*  (开发时代理到 :8000)
┌──────────────────▼──────────────────────────────┐
│              Backend (FastAPI)                    │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌─────────────┐  │
│  │ API 路由  │→│ Services  │→│  RAbot Core  │  │
│  │ (薄层)    │  │ (业务逻辑) │  │ (核心库)     │  │
│  └──────────┘  └───────────┘  └─────────────┘  │
│                                                  │
│  API 层: 参数验证 + 调用 Service                  │
│  Service 层: 协调 RAbot 模块 + 数据组装           │
│  Task Manager: 后台异步报告生成                   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              RAbot Core Library                   │
│              (src/RAbot/)                         │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌─────────┐           │
│  │ data/   │ │analysis/ │ │llm/     │           │
│  │ 数据采集 │ │ 规则引擎  │ │ LLM集成 │           │
│  └────┬────┘ └────┬─────┘ └────┬────┘           │
│       │           │             │                │
│  ┌────▼───────────▼─────────────▼────┐           │
│  │        storage/ (SQLite)          │           │
│  └───────────────────────────────────┘           │
│                                                  │
│  ┌─────────┐ ┌────────┐ ┌──────────┐            │
│  │ stocks/ │ │ funds/ │ │ macro/   │            │
│  │ 个股分析 │ │ ETF分析│ │ 宏观指标 │            │
│  └─────────┘ └────────┘ └──────────┘            │
│                                                  │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐          │
│  │ news/   │ │reporting/│ │ alerts/  │          │
│  │ 新闻系统 │ │ 报告生成 │ │ 告警     │          │
│  └─────────┘ └──────────┘ └──────────┘          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│              External APIs                       │
│  yfinance | Tushare | Longbridge | AKShare       │
│  Finnhub | Alpha Vantage | NewsAPI | RSSHub      │
│  FRED | DeepSeek                                 │
└─────────────────────────────────────────────────┘
```

---

## 5. 核心数据流

### 5.1 数据更新流
```
.env (API keys)
  ↓
RAbot/settings.py (读取配置)
  ↓
scripts/update_data.py (或 startup auto-update)
  ↓
RAbot/data/pipeline.py (update_all_indexes)
  ↓
ProviderFactory → YFinanceProvider / TushareProvider (拉取数据)
  ↓
RAbot/analysis/indicators.py (计算 MA/波动率/回撤)
  ↓
SQLiteStore.upsert_index_daily() (写入 data/market/index_research.db)
```

### 5.2 API 请求流 (以获取市场仪表盘为例)
```
Browser: GET /api/market/dashboard
  ↓
backend/api/market.py: read_market_dashboard()
  ↓
backend/services/market_service.py: get_market_dashboard()
  ↓ (直接读取 SQLite, 不调用外部 API)
data/market/index_research.db → SQL 查询 → 数据组装
  ↓
MarketDashboardResponse (Pydantic model) → JSON
  ↓
React: fetchMarketDashboard() → 渲染 MarketOverview 组件
```

### 5.3 报告生成流 (异步)
```
Browser: POST /api/research/generate
  ↓
backend/api/research.py
  ↓
backend/services/research_task_service.py: create_research_report_task()
  ↓
TaskManager (内存中) → 后台线程执行:
  1. 读取市场数据 (get_market_indexes)
  2. 读取/采集新闻 (get_latest_news / collect_all_news)
  3. 读取宏观数据 (get_macro_overview)
  4. 生成 SVG 图表 (市场走势/新闻评分/宏观趋势)
  5. 调用核心报告模块 (RAbot.reporting.markdown_report)
  6. LLM 生成标题 (RAbotLLMClient)
  7. 组装完整 Markdown 报告
  8. 保存到 data/reports/
  ↓
Browser: 轮询 GET /api/tasks/{task_id} → 获取进度 → 完成后查看报告
```

---

## 6. 前端架构要点

### 6.1 页面懒加载 + Keep-Alive
- 使用 `React.lazy()` + `Suspense` 实现14个页面的代码分割
- 使用 `PageSlot` 组件 (display:none 切换) 实现页面保活，避免切换 Tab 后状态丢失和重新请求

### 6.2 底部导航 (5个Tab)
| Tab | Key | 对应页面 | 包含子面 |
|-----|-----|---------|---------|
| 首页 | home | HomePage | - |
| 行情 | markets | MarketsPage | 仪表盘/热力榜/走势图 |
| 自选 | watchlist | WatchlistPage | - |
| 资讯 | news | NewsPage | 新闻雷达/AI 市场情报 |
| AI研究 | research | ResearchPage → AIResearchPage | - |

### 6.3 主题系统
- CSS 变量 (`[data-theme]`) 实现的4套主题: bloomberg / ocean / graphite / midnight-gold / light
- 用户偏好持久化到 localStorage
- 组件使用 `var(--bg-deep)`, `var(--accent)` 等语义化 CSS 变量

### 6.4 国际化 (i18n)
- 中/英文切换 (zh-CN / en)
- React Context 提供翻译函数
- DOM 文本翻译通过 mutationObserver 实现

---

## 7. 数据源策略

### 7.1 指数数据
| 市场 | 首选数据源 | 备选 |
|------|-----------|------|
| 美股 | yfinance | - |
| A股 | Tushare | yfinance |
| 港股 | yfinance | - |
| 商品/外汇 | yfinance | - |

### 7.2 个股数据
| 市场 | 首选 | 备选1 | 备选2 | 备选3 |
|------|------|-------|-------|-------|
| A股 (600519.SH) | Tushare | TickFlow | yfinance | - |
| 美股 (TSLA.US) | Longbridge | TickFlow | Finnhub | yfinance |
| 港股 (700.HK) | Longbridge | TickFlow | Finnhub | yfinance |

### 7.3 基金/ETF 数据
| 类型 | 首选 | 备选 |
|------|------|------|
| A股 ETF (510300.SH) | Tushare | AKShare |
| 公募基金 (000001.OF) | AKShare | Tushare |
| 美股/港股 ETF | Longbridge | yfinance |

### 7.4 新闻源 (8个Provider, 按优先级)
1. SinaFinanceNewsProvider (新浪财经)
2. EastmoneyNewsProvider (东方财富)
3. FutuNewsProvider (富途)
4. AKShareNewsProvider
5. RSSHubNewsProvider
6. FinnhubNewsProvider
7. NewsAPIProvider
8. AlphaVantageNewsProvider

### 7.5 宏观数据源
- 美国: FRED (Federal Reserve Economic Data)
- 中国: Tushare

---

## 8. 数据库表结构

### 8.1 data/market/index_research.db
```sql
-- 主表: 指数日线 + 技术指标
CREATE TABLE index_daily (
    date TEXT NOT NULL,
    symbol TEXT NOT NULL,
    name TEXT, market TEXT, source TEXT, source_symbol TEXT,
    open REAL, high REAL, low REAL, close REAL,
    volume REAL, amount REAL,
    pct_change REAL,           -- 日涨跌幅%
    ma20 REAL, ma60 REAL, ma120 REAL,  -- 移动均线
    volatility_20d REAL,       -- 20日年化波动率
    drawdown REAL,             -- 当前回撤%
    updated_at TEXT,
    PRIMARY KEY (date, symbol)
);

-- 日志表
CREATE TABLE update_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT, status TEXT, message TEXT,
    rows INTEGER, updated_at TEXT
);
```

### 8.2 data/news/news_research.db
- `news_items` 表: 标题/摘要/来源/发布时间/URL/质量评分/重要性/情感/风险标签/关联资产/市场/主题/原始JSON

### 8.3 data/stocks/stock_research.db 和 data/funds/fund_research.db
- 缓存个股/ETF 的 quote, bars, analysis 结果

---

## 9. API 接口全景

### 9.1 市场数据
| 方法 | 路径 | 功能 |
|------|------|------|
| GET | /api/overview | 首页聚合数据 |
| GET | /api/market/indexes | 指数列表 (最新行情) |
| GET | /api/market/dashboard | 市场仪表盘 (强弱/波动/回撤 Top5) |
| GET | /api/market/performance | 资产表现表 |
| GET | /api/market/timeseries | 时间序列 (支持多样本, 归一化) |

### 9.2 个股
| GET | /api/stocks/quote?symbol=TSLA.US |
| GET | /api/stocks/history?symbol=TSLA.US |
| GET | /api/stocks/analyze?symbol=TSLA.US&use_llm=true |
| GET | /api/stocks/search?keyword=特斯拉 |

### 9.3 基金/ETF
| GET | /api/funds/info?symbol=QQQ.US |
| GET | /api/funds/quote?symbol=QQQ.US |
| GET | /api/funds/history?symbol=QQQ.US |
| GET | /api/funds/analyze?symbol=QQQ.US&use_llm=true |
| GET | /api/funds/search?keyword=nasdaq |

### 9.4 新闻
| GET | /api/news/latest | 最新新闻 |
| GET | /api/news/search?keyword= | 关键词搜索 |
| GET | /api/news/by-symbol?symbol= | 按资产代码查新闻 |
| POST | /api/news/collect | 触发多源新闻采集 |
| GET | /api/news/intelligence | AI 市场情报 (叙事/主题/情感) |

### 9.5 宏观
| GET | /api/macro/overview | 宏观指标概览 |
| GET | /api/macro/snapshot | 宏观快照 (区域/分类) |
| GET | /api/macro/series | 宏观时间序列 |
| POST | /api/macro/analyze | LLM 宏观问答 |

### 9.6 研究
| GET | /api/research/asset/{symbol} | 单资产研究 (技术面+市场+新闻+宏观) |
| POST | /api/research/multi-asset | 多资产比较 (归一化走势+相关性) |
| POST | /api/research/generate | 生成研究报告 (异步) |

### 9.7 LLM
| POST | /api/llm/quick-summary | AI 快评 |
| POST | /api/llm/chat | 研究对话 |
| POST | /api/llm/pet-summary | AI 宠物摘要 |

### 9.8 报告
| GET | /api/reports | 报告列表 |
| GET | /api/reports/{filename} | 读取报告 |
| DELETE | /api/reports/{filename} | 删除报告 |
| GET | /api/reports/latest | 最新报告 |

### 9.9 任务 & 系统
| GET | /api/tasks | 任务列表 |
| GET | /api/tasks/{task_id} | 任务状态 |
| GET | /api/tasks/{task_id}/result | 任务结果 |
| GET | /api/system/update/status | 数据更新状态 |
| POST | /api/system/update/run | 手动触发更新 |

---

## 10. LLM 集成模式

### 10.1 两个 LLM 客户端
1. **RAbotLLMClient** (`src/RAbot/llm/llm_client.py`)
   - 使用 DeepSeek 的 OpenAI-compatible API
   - 支持 thinking/reasoning_effort 参数
   - 统一的 `generate(system_prompt, user_prompt) → LLMResult` 接口
   - 优雅降级: 无 API Key → 返回规则型 fallback

2. **RAbotResearchChat** (`src/RAbot/llm/research_chat.py`)
   - 更高层封装, 基于 ContextBuilder 构造事实包
   - 三种范围: market / single_asset / multi_asset
   - 先查本地数据库构造上下文, 再调用 LLM

### 10.2 LLM 调用场景
| 场景 | 模块 | 降级策略 |
|------|------|---------|
| 研究报告标题 | research_task_service.py | 规则型标题 |
| 个股研究摘要 | stock_analysis.py | 规则型摘要 |
| 基金研究摘要 | fund_analysis.py | 规则型摘要 |
| AI 快评 | llm_service.py | "需要配置 API Key" |
| 研究对话 | llm_service.py | "需要配置 API Key" |
| 宏观问答 | macro_service.py | 规则型摘要 |
| 核心报告 | markdown_report.py | 纯数据表格 |

### 10.3 环境变量
```
DEEPSEEK_API_KEY=sk-xxx        # 必填, 用于 LLM 调用
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
RABOT_LLM_MODEL=deepseek-v4-flash  # 报告用模型
RABOT_LLM_THINKING=disabled     # thinking 模式 (enabled/disabled)
```

---

## 11. 单资产评分引擎 (research_engine.py)

纯规则判断, 满分100分:

| 维度 | 最高分 | 判断依据 |
|------|--------|---------|
| 趋势 | 40 | 收盘价 vs MA20/MA60/MA120 |
| 回撤风险 | 25 | 当前回撤幅度 |
| 波动 | 20 | 20日年化波动率 |
| 动量 | 15 | 近1月收益率 |

评分→等级映射:
- 82-100: 强势趋势
- 68-81: 偏强震荡
- 52-67: 中性观察
- 36-51: 弱势修复
- 0-35: 风险释放

---

## 12. 关键设计模式

### 12.1 Provider 模式
所有数据源都实现同一接口 (fetch_daily / get_quote / get_history / get_info), 通过 ProviderFactory 或条件分支选择, 支持 fallback 链。

### 12.2 优雅降级
每个模块都有 "无法获取数据的优雅处理":
- 无 API Key → 返回规则型输出 + warning
- API 调用失败 → fallback 到下一个 provider
- 数据库为空 → 返回空数据 + 提示, 不白屏
- LLM 不可用 → 返回规则型摘要

### 12.3 分离关注点
- `src/RAbot/` 是纯研究库, 只依赖 pandas/numpy/SQLite, 不依赖 FastAPI
- `backend/` 是 Web 层, 通过 services 协调 RAbot 模块
- `frontend/` 是展示层, 只通过 REST API 与后端通信

### 12.4 任务管理器
`backend/services/task_manager.py` 是基于内存的任务状态机:
- 状态: pending → running → success / failed / cancelled
- 进度百分比 + 当前步骤描述
- 后台线程执行, 前端轮询状态
- ⚠️ 重启后任务记录丢失 (内存存储)

---

## 13. 已知局限与潜在优化方向

### 13.1 架构层面
1. **任务持久化**: 任务状态仅存内存, 重启丢失 → 可迁移到 Redis/DB
2. **单进程架构**: FastAPI + 后台任务 + LLM 调用全在同一个 Python 进程 → 可拆分 worker
3. **SQLite 并发**: 读写缺乏连接池, 高并发下可能锁竞争 → 可迁移到 PostgreSQL
4. **无缓存层**: 每次 API 请求都直接查 SQLite, 无 Redis 缓存
5. **硬编码**: 部分判断阈值和字段名硬编码在各 service 中

### 13.2 数据层面
6. **数据时效性**: 依赖手动/定时脚本更新, 无实时推送
7. **新闻采集性能**: 8个 provider 串行采集, 每次可能耗时数秒
8. **美股/A股交易日历**: 没有统一的交易日历, 周末/节假日可能显示"数据缺失"
9. **个股/ETF 数据缓存**: stocks/ 和 funds/ 各自独立缓存, 有重复代码

### 13.3 前端层面
10. **14个页面整体懒加载**: 首次访问某个页面时会有延迟
11. **lightweight-charts 图表**: 大量数据点时性能可优化
12. **移动端优化**: 当前主要面向桌面端, 移动端适配可加强
13. **报告库**: 大量报告时无分页, 无全文搜索

### 13.4 LLM 层面
14. **单模型依赖**: 仅支持 DeepSeek, 未抽象为多模型
15. **无流式输出**: LLM 调用全部是同步等待, 无 SSE streaming
16. **Token 用量无监控**: 无 token 计数和费用追踪

### 13.5 测试与运维
17. **无自动化测试**: 项目中没有测试文件
18. **无日志系统**: 只有 print 和 warning 数组, 无结构化日志
19. **无健康监控**: /health 端点过于简单, 不检查 DB/外部 API 联通性
20. **无 CI/CD**: 依赖手动部署

---

## 14. 启动方式

### 开发模式
```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 2. 配置 .env (复制 .env.example 并填写 API keys)

# 3. 启动后端
$env:PYTHONPATH="$PWD\src"
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000

# 4. 启动前端
cd frontend && npm run dev

# 5. 访问 http://127.0.0.1:5173
```

### 生产模式
```bash
cd frontend && npm run build && cd ..
start.bat  # Windows 一键启动 (构建前端 + 启动后端, 单端口 :8000)
```

---

## 15. 项目规模

| 指标 | 数值 |
|------|------|
| Python 源文件 | ~80个 (不含 __pycache__) |
| TypeScript/TSX 文件 | ~60个 |
| 总代码行数 | ~30,000+ |
| SQLite 数据库 | 4个 |
| YAML 配置文件 | 4个 |
| React 页面 | 14个 |
| React 组件 | ~40个 |
| API 路由文件 | 11个 |
| 数据源 Provider | 15+个 |
| 支持的市场 | US / CN / HK / JP / EU / UK / FX / COMMODITY |
| 支持的资产类型 | 指数 / 个股 / ETF / 公募基金 / 宏观指标 |

---

> 此文档由 AI 自动分析生成, 用于辅助 AI 助手快速理解 RAbot 项目架构。
> 最后更新: 2026-05-20
