export interface OverviewSection {
  count: number;
  highlights: string[];
  warnings: string[];
}

export interface OverviewReports {
  count: number;
  latest_title: string | null;
  latest_filename: string | null;
}

export interface OverviewResponse {
  market_status: string;
  market_summary: string;
  news_summary: string;
  macro_summary: string;
  report_summary: string;
  last_update: string;
  warnings: string[];
  market: OverviewSection;
  news: OverviewSection;
  macro: OverviewSection;
  reports: OverviewReports;
}

export interface MarketIndexItem {
  symbol: string;
  name: string | null;
  date: string | null;
  close: number | null;
  pct_change: number | null;
  ma20: number | null;
  ma60: number | null;
  trend_signal: string | null;
  risk_level: string | null;
  summary: string;
}

export interface MarketIndexResponse {
  items: MarketIndexItem[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface NewsItem {
  id: string | number | null;
  title: string;
  source: string | null;
  provider: string | null;
  published_at: string | null;
  url: string | null;
  quality_score: number | null;
  importance_score: number | null;
  sentiment_score: number | null;
  risk_tag: string | null;
  risk_tags: string[];
  markets: string[];
  topics: string[];
  symbols: string[];
  summary: string | null;
}

export interface NewsDetailResponse extends NewsItem {
  source_id: string | null;
  query: string | null;
  related_assets: string | null;
  sentiment_label: string | null;
  event_type: string | null;
  source_score: number | null;
  source_tier: string | null;
  freshness_score: number | null;
  interpretation: string | null;
  content: string | null;
  language: string | null;
  created_at: string | null;
  raw: Record<string, unknown>;
}

export interface NewsLatestResponse {
  items: NewsItem[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface NewsCollectRequest {
  limit_per_source: number;
  markets: string[];
  symbols: string[];
  keywords: string[];
}

export interface NewsCollectResponse {
  items: NewsItem[];
  saved_count: number;
  provider_stats: Record<string, { fetched?: number; saved?: number; warnings?: string[] }>;
  warnings: string[];
  last_update: string;
}

export interface MacroIndicatorItem {
  indicator: string;
  name: string | null;
  latest_value: number | null;
  latest_date: string | null;
  previous_value: number | null;
  change: number | null;
  trend: string | null;
  summary: string;
}

export interface MacroOverviewResponse {
  items: MacroIndicatorItem[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface MacroSnapshotItem {
  symbol: string;
  name: string | null;
  region: string | null;
  category: string | null;
  source: string | null;
  unit: string | null;
  latest_date: string | null;
  latest_value: number | null;
  change_1m: number | null;
  change_3m: number | null;
  change_6m: number | null;
  change_1y: number | null;
  trend_label: string | null;
  risk_label: string | null;
  interpretation: string | null;
  direction_note: string | null;
  related_assets: string | null;
}

export interface MacroSnapshotResponse {
  items: MacroSnapshotItem[];
  count: number;
  regions: string[];
  categories: string[];
  last_update: string;
  warnings: string[];
}

export interface MacroSeriesPoint {
  symbol: string;
  name: string | null;
  region: string | null;
  category: string | null;
  date: string;
  value: number | null;
  unit: string | null;
}

export interface MacroSeriesResponse {
  items: MacroSeriesPoint[];
  symbols: string[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface MacroAnalysisResponse {
  ok: boolean;
  text: string;
  model: string | null;
  warnings: string[];
}

export interface MarketPerformanceItem {
  symbol: string;
  name: string | null;
  latest_date: string | null;
  close: number | null;
  return_1w: number | null;
  return_1m: number | null;
  return_3m: number | null;
  return_ytd: number | null;
  return_1y: number | null;
  volatility_20d: number | null;
  drawdown: number | null;
  trend_signal: string | null;
  risk_level: string | null;
}

export interface MarketPerformanceResponse {
  items: MarketPerformanceItem[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface MarketDashboardResponse {
  market_status: string;
  asset_count: number;
  latest_date: string | null;
  strong_assets: MarketPerformanceItem[];
  weak_assets: MarketPerformanceItem[];
  high_volatility_assets: MarketPerformanceItem[];
  high_drawdown_assets: MarketPerformanceItem[];
  summary: string;
  last_update: string;
  warnings: string[];
}

export interface MarketSeriesPoint {
  symbol: string;
  name: string | null;
  date: string;
  close: number | null;
  pct_change: number | null;
  ma20: number | null;
  ma60: number | null;
  ma120: number | null;
  drawdown: number | null;
  volume: number | null;
  normalized: number | null;
}

export interface MarketTimeseriesResponse {
  items: MarketSeriesPoint[];
  symbols: string[];
  count: number;
  last_update: string;
  warnings: string[];
}

export interface AssetResearchResponse {
  symbol: string;
  name: string | null;
  latest_date: string | null;
  technical: Record<string, unknown>;
  market: MarketPerformanceItem | null;
  news: Record<string, unknown>;
  macro: Record<string, unknown>;
  series: MarketSeriesPoint[];
  related_news: NewsItem[];
  related_macro: MacroIndicatorItem[];
  warnings: string[];
}

export interface MultiAssetResponse {
  symbols: string[];
  normalized_series: MarketSeriesPoint[];
  performance: MarketPerformanceItem[];
  correlation: Record<string, string | number | null>[];
  warnings: string[];
}

export interface ReportMeta {
  filename: string;
  title: string;
  updated_at: string;
  size_bytes: number;
}

export interface ReportListResponse {
  reports: ReportMeta[];
  warnings: string[];
}

export interface ReportContentResponse extends ReportMeta {
  content: string;
}

export interface ReportDeleteResponse {
  filename: string;
  deleted: boolean;
  message: string;
}

export interface ResearchGenerateRequest {
  target: string;
  index_symbol: string | null;
  symbol?: string | null;
  report_style: string;
  use_llm: boolean;
  sections: string[];
  extra_instruction: string;
}

export interface ResearchGenerateResponse {
  task_id: string;
  status: string;
  message: string;
}

export type TaskStatus = "pending" | "running" | "success" | "failed" | "cancelled";

export interface TaskResponse {
  task_id: string;
  task_type: string;
  status: TaskStatus;
  progress: number;
  current_step: string;
  message: string;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
}

export interface TaskListResponse {
  tasks: TaskResponse[];
  count: number;
}

export interface TaskResultResponse {
  task_id: string;
  status: TaskStatus;
  progress: number;
  current_step: string;
  message: string;
  result: Record<string, unknown> | null;
  error: string | null;
}

export type LLMScope = "market" | "single_asset" | "multi_asset";

export interface LLMRequestBase {
  scope: LLMScope;
  asset_symbol?: string | null;
  symbols?: string[];
  use_llm: boolean;
}

export interface LLMChatRequest extends LLMRequestBase {
  question: string;
}

export interface PetSummaryRequest {
  page_name: string;
  mode: "market" | "page";
  context: Record<string, unknown>;
  use_llm: boolean;
}

export interface LLMResponse {
  ok: boolean;
  text: string;
  model: string | null;
  scope: string;
  asset_symbol: string | null;
  symbols: string[];
  context: Record<string, unknown> | null;
  warnings: string[];
}

export interface StockQuote {
  symbol: string;
  name: string | null;
  market: string;
  currency: string | null;
  last_price: number | null;
  prev_close: number | null;
  open: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
  turnover: number | null;
  trade_status: string | null;
  quote_time: string | null;
  source: string | null;
  warnings: string[];
}

export interface StockBar {
  symbol: string;
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  volume: number | null;
  turnover: number | null;
  source: string | null;
}

export interface StockAnalysisResponse {
  symbol: string;
  name: string | null;
  market: string;
  currency: string | null;
  quote: StockQuote | null;
  bars: StockBar[];
  benchmark_symbol: string | null;
  benchmark_name: string | null;
  benchmark_bars: StockBar[];
  indicators: Record<string, number | string | null>;
  trend_summary: string;
  risk_summary: string;
  research_summary: string;
  warnings: string[];
  source: string | null;
}

export interface StockSearchResponse {
  items: Array<{ symbol: string; name?: string; market?: string; source?: string }>;
  warnings: string[];
}

export interface FundInfo {
  symbol: string;
  name: string | null;
  market: string;
  fund_type: string;
  asset_class: string | null;
  currency: string | null;
  benchmark: string | null;
  fund_company: string | null;
  inception_date: string | null;
  expense_ratio: number | null;
  aum: number | null;
  source: string | null;
  warnings: string[];
}

export interface FundQuote {
  symbol: string;
  name: string | null;
  market: string;
  fund_type: string;
  currency: string | null;
  last_price: number | null;
  nav: number | null;
  prev_close: number | null;
  premium_discount: number | null;
  volume: number | null;
  turnover: number | null;
  quote_time: string | null;
  source: string | null;
  warnings: string[];
}

export interface FundBar {
  symbol: string;
  date: string;
  open: number | null;
  high: number | null;
  low: number | null;
  close: number | null;
  nav: number | null;
  volume: number | null;
  turnover: number | null;
  source: string | null;
}

export interface FundAnalysisResponse {
  symbol: string;
  name: string | null;
  market: string;
  fund_type: string;
  currency: string | null;
  info: FundInfo | null;
  quote: FundQuote | null;
  bars: FundBar[];
  indicators: Record<string, number | string | null>;
  allocation_summary: string;
  performance_summary: string;
  risk_summary: string;
  liquidity_summary: string;
  dca_summary: string;
  research_summary: string;
  warnings: string[];
  source: string | null;
  benchmark_symbol: string | null;
  benchmark_name: string | null;
  benchmark_bars: FundBar[];
}

export interface FundSearchResponse {
  items: Array<{ symbol: string; name?: string; market?: string; fund_type?: string; source?: string }>;
  warnings: string[];
}

function getApiBaseUrl(): string {
  const env = import.meta.env.VITE_API_BASE_URL;
  if (env) {
    return env.replace(/\/+$/, "");
  }
  return "http://127.0.0.1:8000";
}

function apiUrl(path: string): string {
  const base = getApiBaseUrl();
  const clean = path.startsWith("/") ? path : `/${path}`;
  return `${base}${clean}`;
}

async function requestJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(url), options);
  if (!response.ok) {
    throw new Error(`请求失败：${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

async function requestJsonPost<T>(url: string, body: unknown): Promise<T> {
  return requestJson<T>(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export function fetchOverview(): Promise<OverviewResponse> {
  return requestJson<OverviewResponse>("/api/overview");
}

export function fetchMarketIndexes(): Promise<MarketIndexResponse> {
  return requestJson<MarketIndexResponse>("/api/market/indexes");
}

export function fetchMarketDashboard(): Promise<MarketDashboardResponse> {
  return requestJson<MarketDashboardResponse>("/api/market/dashboard");
}

export function fetchMarketPerformance(): Promise<MarketPerformanceResponse> {
  return requestJson<MarketPerformanceResponse>("/api/market/performance");
}

export function fetchMarketTimeseries(
  symbols: string[],
  normalize = false,
  start?: string,
  end?: string
): Promise<MarketTimeseriesResponse> {
  const params = new URLSearchParams({
    symbols: symbols.join(","),
    normalize: String(normalize)
  });
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  return requestJson<MarketTimeseriesResponse>(`/api/market/timeseries?${params.toString()}`);
}

export function fetchLatestNews(params?: {
  limit?: number;
  market?: string;
  topic?: string;
  symbol?: string;
}): Promise<NewsLatestResponse> {
  const search = new URLSearchParams();
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.market && params.market !== "ALL") search.set("market", params.market);
  if (params?.topic) search.set("topic", params.topic);
  if (params?.symbol) search.set("symbol", params.symbol);
  const suffix = search.toString() ? `?${search.toString()}` : "";
  return requestJson<NewsLatestResponse>(`/api/news/latest${suffix}`);
}

export function fetchNewsDetail(newsId: string | number): Promise<NewsDetailResponse> {
  return requestJson<NewsDetailResponse>(`/api/news/${encodeURIComponent(String(newsId))}`);
}

export function searchNews(keyword: string, limit = 100): Promise<NewsLatestResponse> {
  const params = new URLSearchParams({ keyword, limit: String(limit) });
  return requestJson<NewsLatestResponse>(`/api/news/search?${params.toString()}`);
}

export function fetchNewsBySymbol(symbol: string, limit = 100): Promise<NewsLatestResponse> {
  const params = new URLSearchParams({ symbol, limit: String(limit) });
  return requestJson<NewsLatestResponse>(`/api/news/by-symbol?${params.toString()}`);
}

export async function collectNews(payload: NewsCollectRequest): Promise<NewsCollectResponse> {
  return requestJsonPost<NewsCollectResponse>("/api/news/collect", payload);
}

export function fetchMacroOverview(): Promise<MacroOverviewResponse> {
  return requestJson<MacroOverviewResponse>("/api/macro/overview");
}

export function fetchMacroSnapshot(region?: string, category?: string): Promise<MacroSnapshotResponse> {
  const params = new URLSearchParams();
  if (region) params.set("region", region);
  if (category) params.set("category", category);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return requestJson<MacroSnapshotResponse>(`/api/macro/snapshot${suffix}`);
}

export function fetchMacroSeries(symbols: string[], limitPerSymbol = 240): Promise<MacroSeriesResponse> {
  const params = new URLSearchParams({ symbols: symbols.join(","), limit_per_symbol: String(limitPerSymbol) });
  return requestJson<MacroSeriesResponse>(`/api/macro/series?${params.toString()}`);
}

export async function analyzeMacro(payload: { question: string; symbols: string[]; use_llm: boolean }): Promise<MacroAnalysisResponse> {
  return requestJsonPost<MacroAnalysisResponse>("/api/macro/analyze", payload);
}

export function fetchReports(): Promise<ReportListResponse> {
  return requestJson<ReportListResponse>("/api/reports");
}

export function fetchReport(filename: string): Promise<ReportContentResponse> {
  return requestJson<ReportContentResponse>(`/api/reports/${encodeURIComponent(filename)}`);
}

export function fetchLatestReport(): Promise<ReportContentResponse> {
  return requestJson<ReportContentResponse>("/api/reports/latest");
}

export async function deleteReport(filename: string): Promise<ReportDeleteResponse> {
  return requestJson<ReportDeleteResponse>(`/api/reports/${encodeURIComponent(filename)}`, {
    method: "DELETE"
  });
}

export async function generateResearchReport(
  payload: ResearchGenerateRequest
): Promise<ResearchGenerateResponse> {
  return requestJsonPost<ResearchGenerateResponse>("/api/research/generate", payload);
}

export function fetchTask(taskId: string): Promise<TaskResponse> {
  return requestJson<TaskResponse>(`/api/tasks/${encodeURIComponent(taskId)}`);
}

export function fetchTasks(): Promise<TaskListResponse> {
  return requestJson<TaskListResponse>("/api/tasks");
}

export function fetchTaskResult(taskId: string): Promise<TaskResultResponse> {
  return requestJson<TaskResultResponse>(`/api/tasks/${encodeURIComponent(taskId)}/result`);
}

export function fetchAssetResearch(symbol: string, start?: string, end?: string): Promise<AssetResearchResponse> {
  const params = new URLSearchParams();
  if (start) params.set("start", start);
  if (end) params.set("end", end);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return requestJson<AssetResearchResponse>(`/api/research/asset/${encodeURIComponent(symbol)}${suffix}`);
}

export async function fetchMultiAssetResearch(
  symbols: string[],
  start?: string,
  end?: string
): Promise<MultiAssetResponse> {
  return requestJsonPost<MultiAssetResponse>("/api/research/multi-asset", { symbols, start: start || null, end: end || null });
}

export async function generateQuickSummary(payload: LLMRequestBase): Promise<LLMResponse> {
  return requestJsonPost<LLMResponse>("/api/llm/quick-summary", payload);
}

export async function askResearchChat(payload: LLMChatRequest): Promise<LLMResponse> {
  return requestJsonPost<LLMResponse>("/api/llm/chat", payload);
}

export async function generatePetSummary(payload: PetSummaryRequest): Promise<LLMResponse> {
  return requestJsonPost<LLMResponse>("/api/llm/pet-summary", payload);
}

export function fetchStockAnalysis(symbol: string, useLlm = true, count = 250): Promise<StockAnalysisResponse> {
  const params = new URLSearchParams({ symbol, use_llm: String(useLlm), count: String(count) });
  return requestJson<StockAnalysisResponse>(`/api/stocks/analyze?${params.toString()}`);
}

export function searchStocks(keyword: string): Promise<StockSearchResponse> {
  return requestJson<StockSearchResponse>(`/api/stocks/search?keyword=${encodeURIComponent(keyword)}`);
}

export function fetchFundAnalysis(symbol: string, useLlm = true, count = 500): Promise<FundAnalysisResponse> {
  const params = new URLSearchParams({ symbol, use_llm: String(useLlm), count: String(count) });
  return requestJson<FundAnalysisResponse>(`/api/funds/analyze?${params.toString()}`);
}

export function searchFunds(keyword: string): Promise<FundSearchResponse> {
  return requestJson<FundSearchResponse>(`/api/funds/search?keyword=${encodeURIComponent(keyword)}`);
}

export async function askFundChat(payload: { symbol: string; question: string; use_llm: boolean }): Promise<LLMResponse> {
  return requestJsonPost<LLMResponse>("/api/funds/chat", payload);
}
