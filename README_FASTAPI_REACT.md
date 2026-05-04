# RAbot FastAPI + React

## 一键启动（生产模式）

构建前端 + 启动后端，单端口 `http://0.0.0.0:8000` 访问：

**Windows:**
```bat
start.bat
```

**macOS / Linux:**
```bash
chmod +x start.sh
./start.sh
```

启动后打开 http://localhost:8000 即可使用。

---

## 开发模式启动

在项目根目录执行：

```bat
pip install -r requirements.txt
```

如果依赖没有装成功，再执行：

```bat
pip install fastapi uvicorn pydantic
```

设置 `PYTHONPATH`：

Windows CMD:

```bat
set PYTHONPATH=%cd%\src
```

PowerShell:

```powershell
$env:PYTHONPATH="$PWD\src"
```

启动后端：

```bat
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

测试：

http://127.0.0.1:8000/health

## 前端启动

```bat
cd frontend
npm install
npm run dev
```

访问：

http://127.0.0.1:5173

## 说明

- 新版入口是 FastAPI + React。Streamlit 旧版已移除。
- 如果 `data/market/index_research.db` 不存在，首页会显示 fallback 数据。
- 如果 `data/reports/` 没有报告，报告库会显示空状态。

## 第二阶段接口

新增读取型 API：

- `GET /api/market/indexes`
- `GET /api/news/latest`
- `GET /api/macro/overview`
- `GET /api/overview`

这些接口默认读取本地已有数据，不会在 API 请求中执行抓取、更新或报告生成任务。

如果数据还没有更新，可以先在项目根目录运行已有脚本：

```bat
python scripts/update_data.py
python scripts/update_news.py
python scripts/update_macro.py
```

如果脚本因为 API key、数据源权限或网络问题失败，不会影响前端基础页面打开。FastAPI 会返回空数据和 `warnings`，React 首页会展示提示而不是白屏。

## 第三阶段：研究报告生成工作台

### 后端启动

Windows PowerShell:

```powershell
$env:PYTHONPATH="$PWD\src"
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Windows CMD:

```bat
set PYTHONPATH=%cd%\src
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

### 前端启动

```bat
cd frontend
npm install
npm run dev
```

### 页面访问

http://127.0.0.1:5173

### 新增接口

- `POST /api/research/generate`
- `GET /api/tasks/{task_id}`
- `GET /api/tasks`
- `GET /api/tasks/{task_id}/result`
- `GET /api/reports/latest`

### 第四阶段：前端研究工作台页面

新版 React 前端已补齐迁移前主要工作台板块：

- 首页
- 市场仪表盘
- 市场热力榜
- 走势图
- 单资产研究
- 多资产研究
- 研究生成
- 报告库

新增读取型接口：

- `GET /api/market/dashboard`
- `GET /api/market/performance`
- `GET /api/market/timeseries`
- `GET /api/research/asset/{symbol}`
- `POST /api/research/multi-asset`

这些接口只读取本地已有数据库和已有 RAbot 研究模块，不会在页面请求时抓取外部数据或改写核心研究逻辑。

### 说明

- 报告生成是后台任务，不会阻塞页面。
- 当前任务状态保存在内存中，重启后任务记录会消失，但已生成的 Markdown 报告仍保存在 `data/reports/`。
- 如果没有 LLM API key，会生成规则型 fallback 报告。
- 如果数据不足，报告会显示数据缺口和 warning。
- 本报告由 RAbot 自动生成，仅用于研究与学习，不构成任何投资建议。
## AI Research Page

The React frontend now includes an `AI 研究` page.

New APIs:

- `POST /api/llm/quick-summary`
- `POST /api/llm/chat`

Notes:

- The backend reuses `RAbot.llm.research_chat.RAbotResearchChat`.
- The DeepSeek OpenAI-compatible API path is unchanged.
- Scopes include market, single asset, and multi-asset research.
- If the model switch is off, the API does not call the LLM and returns a local rule-layer summary or a clear warning.
- If `DEEPSEEK_API_KEY` is missing, the page stays usable and shows warnings instead of a blank screen.

## Stock Analysis

The React frontend now includes a `个股分析` page.

Supported symbol formats:

- A shares: `600519.SH`, `000001.SZ`, `300750.SZ`, `688981.SH`
- US stocks: `TSLA.US`, `NVDA.US`, `AAPL.US`, `MSFT.US`
- HK stocks: `700.HK`, `9988.HK`, `3690.HK`

Data sources:

- A shares use Tushare first.
- US and HK stocks use Longbridge / LongPort OpenAPI first.
- If Longbridge is not configured or unavailable, US/HK stocks try `yfinance` fallback when available.
- Longbridge Python SDK is now installed with `pip install longbridge`. The old `longport` package name is deprecated.

Environment variables:

```text
TUSHARE_TOKEN

LONGBRIDGE_APP_KEY
LONGBRIDGE_APP_SECRET
LONGBRIDGE_ACCESS_TOKEN
```

Alternative LongPort names are also supported:

```text
LONGPORT_APP_KEY
LONGPORT_APP_SECRET
LONGPORT_ACCESS_TOKEN
```

Windows PowerShell:

```powershell
$env:LONGBRIDGE_APP_KEY="你的 App Key"
$env:LONGBRIDGE_APP_SECRET="你的 App Secret"
$env:LONGBRIDGE_ACCESS_TOKEN="你的 Access Token"
```

Windows CMD:

```bat
setx LONGBRIDGE_APP_KEY "你的 App Key"
setx LONGBRIDGE_APP_SECRET "你的 App Secret"
setx LONGBRIDGE_ACCESS_TOKEN "你的 Access Token"
```

You can also put these values in the project root `.env` file.

New APIs:

- `GET /api/stocks/quote`
- `GET /api/stocks/history`
- `GET /api/stocks/analyze`
- `GET /api/stocks/search`

Benchmark comparison:

- A shares compare against `000300.SH` / 沪深300.
- US stocks compare against `^GSPC` / 标普500.
- HK stocks compare against `^HSI` / 恒生指数.
- The frontend stock trend chart uses normalized performance, with the first visible point set to `100`, so the stock and benchmark can be compared on the same axis.

Examples:

```text
http://127.0.0.1:8000/api/stocks/analyze?symbol=600519.SH
http://127.0.0.1:8000/api/stocks/analyze?symbol=TSLA.US
http://127.0.0.1:8000/api/stocks/analyze?symbol=700.HK
```

Frontend:

```text
http://127.0.0.1:5173
```

Use the top navigation item `个股分析`.

If you have Tushare or Longbridge credentials, fill them manually in `.env` at the project root.

### TickFlow Stock Fallback

RAbot can use TickFlow as an optional stock data fallback before Finnhub/yfinance.

Fill these values in `.env`:

```text
TICKFLOW_API_KEY=your_tickflow_api_key_here
TICKFLOW_BASE_URL=https://api.tickflow.example.com
TICKFLOW_QUOTE_PATH=/quote
TICKFLOW_HISTORY_PATH=/history
TICKFLOW_SYMBOL_PARAM=symbol
TICKFLOW_TOKEN_HEADER=Authorization
TICKFLOW_TOKEN_PREFIX=Bearer
```

If your provider name is spelled `TICKFOLW`, RAbot also accepts:

```text
TICKFOLW_API_KEY=your_tickfolw_api_key_here
TICKFOLW_BASE_URL=https://api.tickfolw.example.com
```

Current stock fallback order:

- A shares: Tushare -> TickFlow -> yfinance
- US/HK: Longbridge -> TickFlow -> Finnhub -> yfinance

TickFlow is configurable because different accounts may expose different REST paths. If your TickFlow quote/history endpoint path or symbol parameter differs, adjust `TICKFLOW_QUOTE_PATH`, `TICKFLOW_HISTORY_PATH`, and `TICKFLOW_SYMBOL_PARAM` in `.env`.

## Macro Research

The React frontend now includes a `宏观研究` page.

New APIs:

- `GET /api/macro/snapshot`
- `GET /api/macro/series`
- `POST /api/macro/analyze`

Features:

- Reads local global macro data from `macro_series`.
- Shows macro indicator snapshots, regions, categories, latest values, trend labels, and risk labels.
- Shows normalized macro indicator trend charts.
- Supports LLM-powered macro Q&A through the existing DeepSeek OpenAI-compatible client.
- If LLM is disabled or `DEEPSEEK_API_KEY` is missing, the backend returns a rule-layer macro summary with warnings.

Existing single-asset and multi-asset research pages also include a RAbot LLM interaction panel.

## Report Library Management

The React report library supports:

- Reading local Markdown reports from `data/reports/`.
- Deleting a selected Markdown report through `DELETE /api/reports/{filename}`.
- Exporting a report to PDF through the browser print dialog. Choose `Save as PDF` in the system dialog and select the target folder yourself.

The backend keeps the existing path safety checks, so only `.md` files inside `data/reports/` can be read or deleted.

## News Sources

The `新闻雷达` page supports multi-source news collection, deduplication, scoring, risk tags, and local SQLite storage.

Environment variables:

```text
FINNHUB_API_KEY
NEWSAPI_KEY
ALPHAVANTAGE_API_KEY
```

Fill these values in the project root `.env` file:

```text
FINNHUB_API_KEY=your_finnhub_api_key_here
NEWSAPI_KEY=your_newsapi_key_here
ALPHAVANTAGE_API_KEY=your_alphavantage_api_key_here
```

Tushare news is not enabled by default because it requires separate Tushare news permissions. `TUSHARE_TOKEN` may still be used by A-share market/stock data modules.

RSSHub does not usually require an API key, but the configured RSSHub base URL must be reachable. AKShare does not require an API key, but it requires the `akshare` Python package:

```powershell
pip install akshare
```

If a key or optional package is missing, RAbot still runs normally. The corresponding provider returns a warning and the frontend shows it as an optional enhancement source.

News storage:

```text
data/news/news_research.db
```

News APIs:

- `GET /api/news/latest`
- `GET /api/news/search`
- `GET /api/news/by-symbol`
- `POST /api/news/collect`

Manual update:

1. Start the backend and frontend.
2. Open `http://127.0.0.1:5173`.
3. Enter the `新闻雷达` page.
4. Click `更新新闻`.

News source coverage improves as more providers are configured, but collection may take longer. Report generation reads high-quality and high-importance local news first; if the local news store is empty, it tries a small news collection pass and records warnings instead of blocking the report.

## Automatic Data Refresh

FastAPI starts a background local refresh by default when the backend process starts.

Configuration in `.env`:

```text
RABOT_AUTO_UPDATE_ON_START=true
RABOT_MARKET_REFRESH_DAYS=520
RABOT_NEWS_REFRESH_LIMIT=40
RABOT_MACRO_REFRESH_START=2020-01-01
```

Status and manual refresh APIs:

- `GET /api/system/update/status`
- `POST /api/system/update/run`

The refresh runs in the background so the UI does not freeze. On weekends and market holidays, market data may legitimately stop at the latest trading day, for example a Sunday can still show Friday market data. News should refresh from configured providers and is stored in `data/news/news_research.db`.
# 基金 ETF 分析

RAbot 现在提供独立的基金/ETF 分析模块，不与个股分析混用。顶部导航进入“基金 ETF”页面，输入代码后会调用统一后端接口生成行情、净值、收益、风险、流动性、定投观察和研究摘要。

支持示例：

- `510300.SH`
- `513100.SH`
- `QQQ.US`
- `SPY.US`
- `2800.HK`

数据源优先级：

- A 股 ETF / 公募基金：Tushare、AKShare
- 美股 / 港股 ETF：Longbridge / LongPort OpenAPI
- Longbridge 不可用时：yfinance fallback，响应中会明确标注 `source` 和 `warnings`

环境变量：

```env
TUSHARE_TOKEN=

LONGBRIDGE_APP_KEY=
LONGBRIDGE_APP_SECRET=
LONGBRIDGE_ACCESS_TOKEN=

LONGPORT_APP_KEY=
LONGPORT_APP_SECRET=
LONGPORT_ACCESS_TOKEN=
```

新增 API：

- `GET /api/funds/info?symbol=QQQ.US`
- `GET /api/funds/quote?symbol=QQQ.US`
- `GET /api/funds/history?symbol=QQQ.US&period=day&count=500`
- `GET /api/funds/analyze?symbol=QQQ.US&use_llm=true`
- `GET /api/funds/search?keyword=nasdaq`

报告生成页支持 `fund_analysis`，并可传入基金/ETF `symbol`，报告会保存到 `data/reports/`。

风险提示：

- ETF 价格可能与净值存在折溢价。
- 跨境 ETF 受汇率、额度、时区和溢价影响。
- 杠杆 ETF 不适合简单长期持有分析，需要单独风险提示。
- 本系统输出仅用于研究和学习，不构成投资建议。
# 新闻系统说明

新闻雷达现在优先使用新结构化新闻库 `data/news/news_research.db`，并通过 AKShare / RSSHub / Finnhub / NewsAPI / Alpha Vantage 采集后入库。旧版 `data/market/index_research.db` 不再默认兜底，避免页面反复显示旧新闻。

可配置的新闻 API 环境变量：

```env
FINNHUB_API_KEY=
NEWSAPI_KEY=
NEWS_API_KEY=
ALPHAVANTAGE_API_KEY=
ALPHA_VANTAGE_API_KEY=
```

如果新库为空、数据过期或筛选条件无匹配，后端会自动尝试一次轻量新源采集。需要显式恢复旧库兼容兜底时，才设置：

```env
RABOT_NEWS_ALLOW_LEGACY_FALLBACK=true
```
