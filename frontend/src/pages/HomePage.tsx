import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Settings } from "lucide-react";
import MarketOverview from "../components/MarketOverview";
import AISummary from "../components/AISummary";
import HotSectors from "../components/HotSectors";
import TickerTape from "../components/TickerTape";
import FlagIcon, { RegionKey, REGIONS } from "../components/FlagIcon";
import { TabKey } from "../components/BottomNav";
import { fetchOverview } from "../api/client";

interface HomePageProps {
  onNavigate?: (tab: TabKey) => void;
  onOpenSettings?: () => void;
}

function SectionLabel({ children, live }: { children: React.ReactNode; live?: boolean }) {
  return (
    <div className="flex items-center gap-2 mb-3">
      <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--ink-muted)]">
        {children}
      </span>
      <div className="flex-1 h-px bg-[var(--border-subtle)]" />
      {live && <div className="live-dot" />}
    </div>
  );
}

export default function HomePage({ onNavigate, onOpenSettings }: HomePageProps) {
  const [region, setRegion] = useState<RegionKey>("CN");
  const [lastUpdate, setLastUpdate] = useState<string | null>(null);

  useEffect(() => {
    fetchOverview()
      .then((r) => {
        if (r.last_update) {
          setLastUpdate(new Date(r.last_update).toLocaleString("zh-CN", {
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          }));
        }
      })
      .catch(() => {});
  }, []);

  return (
    <div className="flex flex-col min-h-screen pb-28">
      {/* Sticky header */}
      <motion.header
        className="sticky top-0 z-40 bg-[var(--bg-deep)]/95 backdrop-blur-md border-b border-[var(--border-subtle)] px-4 py-2.5"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[var(--accent-gradient)] flex items-center justify-center shadow-lg shadow-[var(--accent)]/20">
              <span className="text-sm font-bold text-white">R</span>
            </div>
            <span className="text-base font-bold gradient-text tracking-tight">RAbot</span>
            <button
              className="w-7 h-7 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-card)] flex items-center justify-center text-[var(--ink-muted)] hover:text-[var(--ink-primary)] active:scale-90 transition-all"
              onClick={() => onOpenSettings?.()}
            >
              <Settings size={13} />
            </button>
          </div>

          {/* Region toggle */}
          <div className="flex gap-0.5 p-0.5 rounded-full bg-[var(--bg-elevated)] border border-[var(--border-card)]">
            {REGIONS.map(({ key, label }) => {
              const isActive = region === key;
              return (
                <button
                  key={key}
                  onClick={() => setRegion(key)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[11px] font-semibold transition-all active:scale-95 ${
                    isActive
                      ? "bg-[var(--accent)] text-white shadow-md"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink-secondary)]"
                  }`}
                >
                  <FlagIcon region={key} />
                  <span>{label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {lastUpdate && (
          <div className="mt-2 flex items-center gap-1.5 text-[10px] text-[var(--ink-muted)]">
            <div className="live-dot" />
            <span>数据更新于 {lastUpdate}</span>
          </div>
        )}
      </motion.header>

      {/* Ticker Tape */}
      <TickerTape />

      {/* Global Indexes */}
      <section className="pt-4 pb-1">
        <div className="px-4">
          <SectionLabel live>全球指数</SectionLabel>
        </div>
        <MarketOverview region={region} />
      </section>

      {/* Market pulse */}
      <section className="pt-2 pb-1">
        <div className="px-4">
          <SectionLabel>AI 市场脉搏</SectionLabel>
        </div>
        <AISummary />
      </section>

      {/* Hot sectors */}
      <section className="pt-2 pb-1">
        <div className="px-4">
          <SectionLabel>热门板块</SectionLabel>
        </div>
        <HotSectors />
      </section>

      {/* Quick actions */}
      <motion.section
        className="px-4 pt-3 pb-6"
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4, duration: 0.25 }}
      >
        <SectionLabel>快捷研究</SectionLabel>
        <div className="grid grid-cols-2 gap-2">
          {[
            { label: "个股分析", desc: "财务 · 技术 · 估值", tab: "markets" as TabKey },
            { label: "基金 ETF", desc: "费率 · 持仓 · 回撤", tab: "markets" as TabKey },
            { label: "宏观研究", desc: "利率 · CPI · 就业", tab: "research" as TabKey },
            { label: "AI 报告", desc: "自动生成研究简报", tab: "research" as TabKey },
          ].map((item) => (
            <div
              key={item.label}
              className="p-3.5 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] active:bg-[var(--bg-card-hover)] cursor-pointer transition-all hover:border-[var(--border-glow)] group"
              onClick={() => onNavigate?.(item.tab)}
            >
              <div className="text-sm font-semibold text-[var(--ink-primary)] group-hover:text-[var(--accent)] transition-colors">
                {item.label}
              </div>
              <div className="text-[11px] text-[var(--ink-muted)] mt-1">
                {item.desc}
              </div>
            </div>
          ))}
        </div>
      </motion.section>
    </div>
  );
}
