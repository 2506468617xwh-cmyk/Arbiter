import { useState, useEffect, lazy, Suspense } from "react";
import { motion } from "framer-motion";
import { TrendingUp, BarChart3, TrendingDown } from "lucide-react";
import { fetchMarketDashboard, MarketDashboardResponse, MarketPerformanceItem } from "../api/client";

const StockAnalysisPage = lazy(() => import("./StockAnalysisPage"));
const FundAnalysisPage = lazy(() => import("./FundAnalysisPage"));

type SubTab = "heatmap" | "stock" | "fund";

interface Props {
  useLlm: boolean;
  language: string;
}

function fmt(v: number | null): string {
  return v === null ? "--" : `${v >= 0 ? "+" : ""}${v.toFixed(2)}%`;
}

function HeatmapView() {
  const [data, setData] = useState<MarketDashboardResponse | null>(null);
  const [items, setItems] = useState<MarketPerformanceItem[]>([]);
  const [metric, setMetric] = useState<keyof MarketPerformanceItem>("return_1m");
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (loaded) return;
    fetchMarketDashboard()
      .then((d) => { setData(d); setItems(d.all_items || []); setLoaded(true); })
      .catch(() => setLoaded(true));
  }, [loaded]);

  const sorted = [...items]
    .filter((i) => i[metric] != null)
    .sort((a, b) => (Number(b[metric]) || 0) - (Number(a[metric]) || 0));

  const topGainers = sorted.slice(0, 10);
  const topLosers = [...sorted].sort((a, b) => (Number(a[metric]) || 0) - (Number(b[metric]) || 0)).slice(0, 10);

  const metrics: { key: keyof MarketPerformanceItem; label: string }[] = [
    { key: "return_1w", label: "1W" },
    { key: "return_1m", label: "1M" },
    { key: "return_3m", label: "3M" },
    { key: "return_ytd", label: "YTD" },
    { key: "volatility_20d", label: "VOL" },
    { key: "drawdown", label: "DD" },
  ];

  if (!loaded) {
    return (
      <div className="px-4 space-y-1.5">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="skeleton h-8 w-full" />
        ))}
      </div>
    );
  }

  return (
    <div className="px-4 space-y-3">
      {/* Metric selector */}
      <div className="flex gap-0.5 p-0.5 bg-[var(--bg-card)] border border-[var(--border-subtle)] overflow-x-auto">
        {metrics.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setMetric(key)}
            className={`shrink-0 px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all ${
              metric === key ? "bg-[var(--accent)] text-white" : "text-[var(--ink-dim)] hover:text-[var(--ink-secondary)]"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Data bar */}
      <div className="flex gap-3 text-[10px] text-[var(--ink-muted)] font-mono">
        {data && <span>ASSETS {data.asset_count}</span>}
        {data && <span className="text-[var(--ink-dim)]">|</span>}
        {data && <span>DATE {data.latest_date || "--"}</span>}
      </div>

      {/* Gainers */}
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        <div className="flex items-center justify-between h-7 px-3 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-1.5">
            <TrendingUp size={11} className="text-[var(--up)]" />
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">
              GAINERS
            </span>
          </div>
          <span className="text-[9px] text-[var(--ink-dim)] font-mono">{metric.toUpperCase()}</span>
        </div>
        {topGainers.map((item, i) => {
          const val = Number(item[metric]) || 0;
          const w = Math.max(3, Math.min(100, Math.abs(val) * 6));
          return (
            <div
              key={item.symbol}
              className={`flex items-center h-9 px-3 gap-3 ${i > 0 ? "border-t border-[var(--border-subtle)]" : ""}`}
            >
              <div className="flex-1 min-w-0 flex items-center gap-2">
                <span className="text-[11px] font-semibold text-[var(--ink-primary)] font-mono truncate">
                  {item.symbol}
                </span>
                <span className="text-[10px] text-[var(--ink-dim)] truncate hidden sm:inline">
                  {item.name}
                </span>
              </div>
              <div className="hidden sm:block flex-1 h-0.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--up)]"
                  style={{ width: `${w}%`, opacity: 0.3 + Math.abs(val) * 0.08 }}
                />
              </div>
              <span className="text-financial text-[11px] font-bold text-[var(--up)] w-16 text-right shrink-0">
                {fmt(val)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Losers */}
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        <div className="flex items-center justify-between h-7 px-3 border-b border-[var(--border-subtle)]">
          <div className="flex items-center gap-1.5">
            <TrendingDown size={11} className="text-[var(--down)]" />
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">
              LOSERS
            </span>
          </div>
          <span className="text-[9px] text-[var(--ink-dim)] font-mono">{metric.toUpperCase()}</span>
        </div>
        {topLosers.map((item, i) => {
          const val = Number(item[metric]) || 0;
          const w = Math.max(3, Math.min(100, Math.abs(val) * 6));
          return (
            <div
              key={item.symbol}
              className={`flex items-center h-9 px-3 gap-3 ${i > 0 ? "border-t border-[var(--border-subtle)]" : ""}`}
            >
              <div className="flex-1 min-w-0 flex items-center gap-2">
                <span className="text-[11px] font-semibold text-[var(--ink-primary)] font-mono truncate">
                  {item.symbol}
                </span>
                <span className="text-[10px] text-[var(--ink-dim)] truncate hidden sm:inline">
                  {item.name}
                </span>
              </div>
              <div className="hidden sm:block flex-1 h-0.5 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className="h-full rounded-full bg-[var(--down)]"
                  style={{ width: `${w}%`, opacity: 0.3 + Math.abs(val) * 0.08 }}
                />
              </div>
              <span className="text-financial text-[11px] font-bold text-[var(--down)] w-16 text-right shrink-0">
                {fmt(val)}
              </span>
            </div>
          );
        })}
      </div>

      {data?.warnings?.length ? (
        <div className="px-3 py-2 border border-[var(--border-subtle)] text-[10px] text-[var(--ink-muted)] font-mono">
          {data.warnings.map((w, i) => <p key={i}>{w}</p>)}
        </div>
      ) : null}
    </div>
  );
}

export default function MarketsPage({ useLlm, language }: Props) {
  const [subTab, setSubTab] = useState<SubTab>("heatmap");

  return (
    <div className="flex flex-col min-h-screen pb-24">
      {/* Header */}
      <div className="sticky top-0 z-30 bg-[var(--bg-deep)]/95 backdrop-blur-md border-b border-[var(--border-subtle)]">
        <div className="flex items-center justify-between px-4 h-12">
          <div className="flex items-center gap-2">
            <BarChart3 size={14} className="text-[var(--accent)]" />
            <span className="text-[13px] font-bold uppercase tracking-[0.15em] text-[var(--ink-primary)]">MARKETS</span>
          </div>
          <div className="flex gap-0.5 p-0.5 bg-[var(--bg-card)] border border-[var(--border-subtle)]">
            {([
              { key: "heatmap" as SubTab, label: "热力榜" },
              { key: "stock" as SubTab, label: "个股" },
              { key: "fund" as SubTab, label: "基金" },
            ]).map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setSubTab(key)}
                className={`px-3 py-1.5 text-[10px] font-bold uppercase tracking-wider transition-all ${
                  subTab === key ? "bg-[var(--accent)] text-white" : "text-[var(--ink-dim)] hover:text-[var(--ink-secondary)]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="pt-3">
        {subTab === "heatmap" ? (
          <HeatmapView />
        ) : subTab === "stock" ? (
          <Suspense fallback={<div className="px-4"><div className="skeleton h-48 w-full" /></div>}>
            <StockAnalysisPage useLlm={useLlm} />
          </Suspense>
        ) : (
          <Suspense fallback={<div className="px-4"><div className="skeleton h-48 w-full" /></div>}>
            <FundAnalysisPage useLlm={useLlm} />
          </Suspense>
        )}
      </div>
    </div>
  );
}
