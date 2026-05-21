import { useEffect, useState, useCallback, useMemo } from "react";
import { RefreshCw, Search, Newspaper, X } from "lucide-react";
import { fetchLatestNews, searchNews, collectNews, fetchNewsIntelligence, NewsItem, NewsCollectRequest, NewsIntelligenceResponse } from "../api/client";
import MarketNarrative from "../components/MarketNarrative";
import ThemeCards from "../components/ThemeCards";
import SentimentGaugeView from "../components/SentimentGauge";
import EventTimeline from "../components/EventTimeline";

const TAG_CN: Record<string, string> = {
  AI: "人工智能", chips: "芯片", semiconductor: "半导体", NVIDIA: "英伟达",
  Apple: "苹果", Tesla: "特斯拉", "Federal Reserve": "美联储", Fed: "美联储",
  inflation: "通胀", CPI: "CPI", "rate cut": "降息", "rate hike": "加息",
  China: "中国", gold: "黄金", oil: "原油", crypto: "加密货币", Bitcoin: "比特币",
  earnings: "财报", tech: "科技", EV: "电动车",
};

type Tab = "intelligence" | "feed";

export default function NewsPage() {
  const [tab, setTab] = useState<Tab>("intelligence");
  const [intel, setIntel] = useState<NewsIntelligenceResponse | null>(null);
  const [intelLoading, setIntelLoading] = useState(true);

  const [allItems, setAllItems] = useState<NewsItem[]>([]);
  const [feedLoading, setFeedLoading] = useState(false);
  const [search, setSearch] = useState("");
  const [topicFilter, setTopicFilter] = useState<string | null>(null);
  const [count, setCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState("");
  const [collecting, setCollecting] = useState(false);
  const [marketFilter, setMarketFilter] = useState<string>("ALL");

  const [intelLoaded, setIntelLoaded] = useState(false);
  const loadIntelligence = useCallback(async () => {
    if (intelLoaded) return;
    setIntelLoading(true);
    try { setIntel(await fetchNewsIntelligence(true)); } catch {}
    finally { setIntelLoading(false); setIntelLoaded(true); }
  }, [intelLoaded]);

  const loadFeed = useCallback(async () => {
    setFeedLoading(true);
    try {
      const result = search.trim()
        ? await searchNews(search.trim(), 60)
        : await fetchLatestNews({ limit: 80, market: marketFilter !== "ALL" ? marketFilter : undefined });
      setAllItems(result.items || []);
      setTopicFilter(null);
      setCount(result.count);
      setLastUpdate(result.last_update);
    } catch {}
    finally { setFeedLoading(false); }
  }, [search, marketFilter]);

  useEffect(() => { loadIntelligence(); }, [loadIntelligence]);
  useEffect(() => { if (tab === "feed") loadFeed(); }, [loadFeed, tab]);

  const handleThemeClick = (themeName: string) => {
    setSearch("");
    setTopicFilter(themeName);
    setTab("feed");
  };

  // Filter feed items by topic tag (exact match on topics/risk_tags)
  const displayItems = useMemo(() => {
    if (!topicFilter) return allItems;
    const f = topicFilter.toLowerCase();
    return allItems.filter((item) => {
      const tags = [...(item.topics || []), ...(item.risk_tags || [])];
      return tags.some((t) => t.toLowerCase() === f || t.toLowerCase().includes(f));
    });
  }, [allItems, topicFilter]);

  const handleCollect = async () => {
    setCollecting(true);
    try {
      const req: NewsCollectRequest = { limit_per_source: 5, markets: ["CN", "US", "HK", "GLOBAL"], symbols: [], keywords: [] };
      await collectNews(req);
      setIntelLoaded(false);
      loadIntelligence();
      loadFeed();
    } catch {}
    finally { setCollecting(false); }
  };

  return (
    <div className="flex flex-col min-h-screen pb-24">
      {/* Terminal header */}
      <div className="sticky top-0 z-30 bg-[var(--bg-deep)]/95 backdrop-blur-md border-b border-[var(--border-subtle)]">
        <div className="flex items-center justify-between px-4 h-12">
          <div className="flex items-center gap-2">
            <Newspaper size={14} className="text-[var(--accent)]" />
            <span className="text-[13px] font-bold uppercase tracking-[0.15em] text-[var(--ink-primary)]">AI 情报中心</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className="flex gap-0.5 p-0.5 bg-[var(--bg-card)] border border-[var(--border-subtle)]">
              {([
                { key: "intelligence" as Tab, label: "情报" },
                { key: "feed" as Tab, label: "新闻" },
              ]).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setTab(key)}
                  className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all ${
                    tab === key ? "bg-[var(--accent)] text-white" : "text-[var(--ink-dim)] hover:text-[var(--ink-secondary)]"
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
            <button
              className="w-7 h-7 bg-[var(--bg-card)] border border-[var(--border-subtle)] flex items-center justify-center text-[var(--ink-muted)] active:scale-90 transition-transform"
              onClick={handleCollect}
              disabled={collecting}
            >
              <RefreshCw size={11} className={collecting ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
      </div>

      {/* Intelligence View */}
      {tab === "intelligence" && (
        <div className="pt-3 space-y-3">
          <MarketNarrative
            headline={intel?.narrative.headline || "正在分析市场..."}
            body={intel?.narrative.body || ""}
            keyThemes={intel?.narrative.key_themes || []}
            riskLevel={intel?.narrative.risk_level || "normal"}
            loading={intelLoading}
          />
          <SentimentGaugeView
            data={intel?.sentiment || { overall: 50, ai_tech: 50, semiconductors: 50, macro_policy: 50, geopolitics: 50, risk_appetite: "neutral" }}
            loading={intelLoading}
          />
          <ThemeCards themes={intel?.themes || []} loading={intelLoading} onThemeClick={handleThemeClick} />
          <EventTimeline events={intel?.events || []} loading={intelLoading} />

          {intel?.briefing && !intelLoading && (
            <div className="px-4">
              <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
                <div className="flex items-center gap-1.5 mb-2">
                  <Newspaper size={11} className="text-[var(--down)]" />
                  <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--down)]">AI 简报</span>
                </div>
                {intel.briefing.watch_today.length > 0 && (
                  <div className="mb-1.5">
                    <span className="text-[9px] text-[var(--ink-dim)] font-mono">WATCH</span>
                    <div className="flex gap-1 mt-0.5 flex-wrap">
                      {intel.briefing.watch_today.map((t) => (
                        <span key={t} className="px-1.5 py-0.5 text-[9px] bg-[var(--down-soft)] text-[var(--down)] font-medium">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {intel.briefing.key_risks.length > 0 && (
                  <div>
                    <span className="text-[9px] text-[var(--ink-dim)] font-mono">RISK</span>
                    <div className="flex gap-1 mt-0.5 flex-wrap">
                      {intel.briefing.key_risks.map((r) => (
                        <span key={r} className="px-1.5 py-0.5 text-[9px] bg-[var(--up-soft)] text-[var(--up)] font-medium">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {intel?.warnings?.length ? (
            <div className="px-4">
              <div className="px-3 py-2 border border-[var(--border-subtle)] text-[10px] text-[var(--ink-muted)] font-mono">
                {intel.warnings.map((w, i) => <p key={i}>{w}</p>)}
              </div>
            </div>
          ) : null}
        </div>
      )}

      {/* Feed View */}
      {tab === "feed" && (
        <div className="pt-3">
          <div className="px-4 mb-3">
            <div className="relative mb-2">
              <Search size={12} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--ink-dim)]" />
              <input
                className="w-full h-8 pl-8 pr-3 border border-[var(--border-subtle)] bg-[var(--bg-card)] text-[11px] text-[var(--ink-primary)] font-mono placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]"
                placeholder="搜索新闻..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            {/* Market + source filter */}
            <div className="flex gap-1.5 items-center">
              {["ALL", "CN", "US"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMarketFilter(m)}
                  className={`px-2 py-0.5 text-[9px] font-bold uppercase tracking-wider border transition-all ${
                    marketFilter === m
                      ? "border-[var(--accent)] bg-[var(--accent-soft)] text-[var(--accent)]"
                      : "border-[var(--border-subtle)] text-[var(--ink-dim)] hover:text-[var(--ink-secondary)]"
                  }`}
                >
                  {m === "ALL" ? "全部" : m}
                </button>
              ))}
            </div>
            {lastUpdate && (
              <div className="mt-1 text-[9px] text-[var(--ink-dim)] font-mono">{count} ITEMS · {new Date(lastUpdate).toLocaleString("zh-CN")}</div>
            )}
            {topicFilter && (
              <div className="mt-2 flex items-center gap-2 px-2.5 py-1.5 border border-[var(--accent)]/30 bg-[var(--accent-soft)] text-[10px] text-[var(--accent)] font-medium">
                <span>🔍 主题筛选: {topicFilter}</span>
                <span className="text-[var(--ink-dim)]">({displayItems.length}条)</span>
                <button onClick={() => setTopicFilter(null)} className="ml-auto"><X size={12} /></button>
              </div>
            )}
          </div>

          <div className="px-4 space-y-1">
            {feedLoading ? (
              [1, 2, 3, 4].map((i) => (
                <div key={i} className="p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)]">
                  <div className="skeleton h-2.5 w-3/4 mb-1.5" />
                  <div className="skeleton h-2 w-full mb-1" />
                  <div className="skeleton h-2 w-1/2" />
                </div>
              ))
            ) : displayItems.length === 0 ? (
              <div className="py-12 text-center text-[11px] text-[var(--ink-muted)]">
                {topicFilter ? `没有找到关于 "${topicFilter}" 的新闻` : search ? "未找到相关新闻" : "暂无新闻"}
              </div>
            ) : (
              displayItems.map((item, i) => (
                <a
                  key={item.id ?? i}
                  href={item.url || "#"}
                  target={item.url ? "_blank" : undefined}
                  rel="noopener"
                  className={`block p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)] active:bg-[var(--bg-card-hover)] transition-colors ${i > 0 ? "" : ""}`}
                >
                  <h3 className="text-[11px] font-semibold text-[var(--ink-primary)] line-clamp-2 leading-snug">{item.title || "(untitled)"}</h3>
                  {(item.summary || "").length > 0 && (
                    <p className="mt-0.5 text-[10px] text-[var(--ink-secondary)] line-clamp-2 leading-relaxed">
                      {(item.summary || "").slice(0, 140)}
                    </p>
                  )}
                  <div className="mt-1.5 flex items-center gap-3 text-[9px] text-[var(--ink-dim)] font-mono">
                    <span>{item.source || "?"}</span>
                    {item.published_at && <span>{new Date(item.published_at).toLocaleDateString("zh-CN")}</span>}
                    {item.sentiment_score != null && (
                      <span className={item.sentiment_score > 0 ? "text-up" : item.sentiment_score < 0 ? "text-down" : ""}>
                        {item.sentiment_score > 0 ? "+" : ""}{item.sentiment_score.toFixed(1)}
                      </span>
                    )}
                  </div>
                </a>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
