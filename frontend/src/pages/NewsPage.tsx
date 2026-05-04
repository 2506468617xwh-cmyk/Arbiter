import { useEffect, useState } from "react";
import {
  NewsCollectResponse,
  NewsDetailResponse,
  NewsItem,
  collectNews,
  fetchLatestNews,
  fetchNewsBySymbol,
  fetchNewsDetail,
  searchNews
} from "../api/client";
import MetricCard from "../components/MetricCard";
import NewsFilterBar from "../components/NewsFilterBar";
import NewsItemCard from "../components/NewsItemCard";
import NewsRiskTags from "../components/NewsRiskTags";
import NewsSourcePanel from "../components/NewsSourcePanel";
import PageIntro from "../components/PageIntro";

function score(value: number | null): string {
  return value === null ? "--" : value.toFixed(0);
}

function dateText(value: string | null): string {
  if (!value) return "--";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function NewsPage() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [selected, setSelected] = useState<NewsDetailResponse | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [market, setMarket] = useState("ALL");
  const [topic, setTopic] = useState("");
  const [symbol, setSymbol] = useState("");
  const [keyword, setKeyword] = useState("");
  const [loadingList, setLoadingList] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [collecting, setCollecting] = useState(false);
  const [collectResult, setCollectResult] = useState<NewsCollectResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const openDetail = (id: string | number | null) => {
    if (!id) return;
    setError(null);
    setLoadingDetail(true);
    fetchNewsDetail(id)
      .then(setSelected)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "新闻详情读取失败。"))
      .finally(() => setLoadingDetail(false));
  };

  const applyResponse = (response: { items: NewsItem[]; warnings: string[] }) => {
    setItems(response.items);
    setWarnings(response.warnings);
    const first = response.items.find((item) => item.id !== null);
    if (first?.id) openDetail(first.id);
    else setSelected(null);
  };

  const loadList = () => {
    setError(null);
    setLoadingList(true);
    fetchLatestNews({ limit: 100, market, topic, symbol: symbol.trim() || undefined })
      .then(applyResponse)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "新闻列表读取失败。"))
      .finally(() => setLoadingList(false));
  };

  const runSearch = () => {
    if (!keyword.trim()) {
      loadList();
      return;
    }
    setError(null);
    setLoadingList(true);
    searchNews(keyword.trim(), 100)
      .then(applyResponse)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "新闻搜索失败。"))
      .finally(() => setLoadingList(false));
  };

  const runSymbolSearch = () => {
    if (!symbol.trim()) {
      loadList();
      return;
    }
    setError(null);
    setLoadingList(true);
    fetchNewsBySymbol(symbol.trim().toUpperCase(), 100)
      .then(applyResponse)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "股票相关新闻读取失败。"))
      .finally(() => setLoadingList(false));
  };

  const runCollect = () => {
    setError(null);
    setCollecting(true);
    collectNews({
      limit_per_source: 30,
      markets: market === "ALL" ? ["CN", "US", "HK", "GLOBAL"] : [market],
      symbols: symbol.trim() ? [symbol.trim().toUpperCase()] : [],
      keywords: keyword.trim() ? [keyword.trim()] : ["Federal Reserve", "AI chips", "中国经济"]
    })
      .then((response) => {
        setCollectResult(response);
        setWarnings(response.warnings);
        return fetchLatestNews({ limit: 100, market, topic, symbol: symbol.trim() || undefined });
      })
      .then(applyResponse)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "新闻更新失败。"))
      .finally(() => setCollecting(false));
  };

  useEffect(() => {
    loadList();
  }, []);

  useEffect(() => {
    loadList();
  }, [market, topic]);

  const highImportance = items.filter((item) => (item.importance_score ?? 0) >= 70).length;
  const configuredWarnings = warnings.filter((warning) => warning.includes("未配置") || warning.includes("未安装"));

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <PageIntro pageKey="news" />
      </div>

      <NewsFilterBar
        market={market}
        topic={topic}
        symbol={symbol}
        keyword={keyword}
        onMarketChange={setMarket}
        onTopicChange={setTopic}
        onSymbolChange={setSymbol}
        onKeywordChange={setKeyword}
        onRefresh={loadList}
        onSearch={runSearch}
        onSymbolSearch={runSymbolSearch}
        onCollect={runCollect}
        loading={loadingList}
        collecting={collecting}
      />

      {configuredWarnings.length ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          {configuredWarnings.slice(0, 5).map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      ) : null}
      {warnings.filter((warning) => !configuredWarnings.includes(warning)).length ? (
        <div className="rounded-lg border border-line bg-[#fffaf2] p-4 text-sm leading-6 text-muted">
          {warnings.filter((warning) => !configuredWarnings.includes(warning)).slice(0, 8).map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      ) : null}
      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label="新闻数量" value={String(items.length)} detail="当前筛选结果" />
        <MetricCard label="高重要性" value={String(highImportance)} detail="importance >= 70" />
        <MetricCard label="已选市场" value={market} detail={topic || "全部主题"} />
        <MetricCard label="最近入库" value={String(collectResult?.saved_count ?? "--")} detail="本次更新保存数" />
      </div>

      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
        <section className="min-w-0 rounded-lg border border-line bg-panel p-4 shadow-soft">
          <div className="mb-3 flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-ink">新闻列表</h2>
            <span className="rounded-full border border-line bg-[#fffaf2] px-3 py-1 text-xs text-muted">{loadingList ? "读取中..." : `${items.length} 条`}</span>
          </div>
          <div className="grid max-h-[72vh] gap-3 overflow-auto pr-1 lg:grid-cols-2">
            {items.length ? items.map((item) => (
              <NewsItemCard key={String(item.id ?? item.title)} item={item} active={selected?.id === item.id} onOpen={() => openDetail(item.id)} />
            )) : (
              <div className="rounded-lg border border-dashed border-line p-6 text-sm text-muted">
                暂无新闻数据。可以点击“更新新闻”，或配置 Tushare / Finnhub / NewsAPI / Alpha Vantage 后再更新。
              </div>
            )}
          </div>
        </section>

        <div className="space-y-5">
          <NewsSourcePanel items={items} collectResult={collectResult} />
          <aside className="min-w-0 rounded-lg border border-line bg-panel p-5 shadow-soft">
            {loadingDetail ? (
              <p className="text-sm text-muted">正在读取新闻详情...</p>
            ) : selected ? (
              <div className="space-y-5">
                <div className="border-b border-line pb-4">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="rounded-full bg-[#fff4e4] px-2 py-1 font-semibold text-brand">{selected.source ?? "未知来源"}</span>
                    <span className="rounded-full border border-line px-2 py-1 text-muted">{selected.provider ?? "local"}</span>
                    <span className="rounded-full border border-line px-2 py-1 text-muted">质 {score(selected.quality_score)}</span>
                    <span className="rounded-full border border-line px-2 py-1 text-muted">重 {score(selected.importance_score)}</span>
                  </div>
                  <h2 className="mt-4 break-words text-2xl font-semibold leading-9 text-ink">{selected.title}</h2>
                  <p className="mt-3 text-sm text-muted">{dateText(selected.published_at)}</p>
                </div>
                <NewsRiskTags tags={selected.risk_tags?.length ? selected.risk_tags : selected.risk_tag ? [selected.risk_tag] : []} />
                {selected.url ? (
                  <a className="inline-flex rounded-lg border border-brand bg-[#fff7ed] px-3 py-2 text-sm font-semibold text-brand hover:bg-[#ffedd5]" href={selected.url} target="_blank" rel="noreferrer">
                    打开原文链接
                  </a>
                ) : (
                  <p className="rounded-lg border border-dashed border-line p-3 text-sm text-muted">这条新闻没有原文链接。</p>
                )}
                <div className="rounded-lg border border-line bg-[#fffdf8] p-4">
                  <h3 className="text-sm font-semibold text-ink">摘要</h3>
                  <p className="mt-2 whitespace-pre-wrap break-words text-sm leading-7 text-muted">{selected.summary || selected.content || "暂无摘要。"}</p>
                </div>
                <div className="grid gap-3 text-sm">
                  <div className="rounded-lg border border-line bg-[#fffaf2] p-3">
                    <p className="text-xs text-muted">市场 / 主题 / 代码</p>
                    <p className="mt-1 break-words font-medium text-ink">
                      {[...(selected.markets || []), ...(selected.topics || []), ...(selected.symbols || [])].join(" · ") || "--"}
                    </p>
                  </div>
                  {selected.sentiment_score !== null ? (
                    <div className="rounded-lg border border-line bg-[#fffaf2] p-3">
                      <p className="text-xs text-muted">情绪分</p>
                      <p className="mt-1 font-medium text-ink">{selected.sentiment_score?.toFixed(3)}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted">点击新闻卡片后，在这里查看详情。</p>
            )}
          </aside>
        </div>
      </div>
    </div>
  );
}

export default NewsPage;
