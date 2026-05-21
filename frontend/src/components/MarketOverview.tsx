import { useEffect, useState, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchMarketIndexes, fetchMarketTimeseries, MarketIndexItem } from "../api/client";
import IndexCard from "./IndexCard";
import type { RegionKey } from "./FlagIcon";

interface IndexData {
  item: MarketIndexItem;
  sparkline: { date: string; close: number | null }[];
}

// Map index symbols to regions
const CN_SYMBOLS = ["SSE", "CSI300", "CSI500", "CSI1000", "CHINEXT", "STAR50"];
const US_SYMBOLS = ["SP500", "NASDAQ", "NASDAQ100", "DOW", "RUSSELL2000", "VIX"];
const HK_SYMBOLS = ["HSI"];

function getRegion(symbol: string): RegionKey | null {
  if (CN_SYMBOLS.includes(symbol)) return "CN";
  if (US_SYMBOLS.includes(symbol)) return "US";
  if (HK_SYMBOLS.includes(symbol)) return "HK";
  return null;
}

interface MarketOverviewProps {
  region: RegionKey;
}

export default function MarketOverview({ region }: MarketOverviewProps) {
  const [allIndexes, setAllIndexes] = useState<IndexData[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    try {
      const resp = await fetchMarketIndexes();
      if (!resp.items?.length) return;

      const symbols = resp.items.map((i) => i.symbol);
      const tsResp = await fetchMarketTimeseries(symbols, false);

      const sparklineMap: Record<string, { date: string; close: number | null }[]> = {};
      if (tsResp.items) {
        for (const pt of tsResp.items) {
          if (!sparklineMap[pt.symbol]) sparklineMap[pt.symbol] = [];
          sparklineMap[pt.symbol].push({ date: pt.date, close: pt.close });
        }
      }

      const merged: IndexData[] = resp.items
        .filter((item) => getRegion(item.symbol) !== null)
        .map((item) => ({
          item,
          sparkline: sparklineMap[item.symbol] || [],
        }));

      setAllIndexes(merged);
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const filteredIndexes = useMemo(
    () => allIndexes.filter((d) => getRegion(d.item.symbol) === region),
    [allIndexes, region]
  );

  if (loading) {
    return (
      <div className="flex gap-2.5 overflow-hidden px-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex-shrink-0 w-[138px] p-3 rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)]">
            <div className="skeleton h-3 w-16 mb-2" />
            <div className="skeleton h-8 w-full mb-2" />
            <div className="skeleton h-4 w-20 mb-1" />
            <div className="skeleton h-3 w-14" />
          </div>
        ))}
      </div>
    );
  }

  return (
    <AnimatePresence mode="wait">
      {filteredIndexes.length === 0 ? (
        <motion.div
          key="empty"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="px-4 py-6 text-center text-xs text-[var(--ink-muted)]"
        >
          {allIndexes.length === 0 ? "暂未加载指数数据" : "该区域暂无指数数据"}
        </motion.div>
      ) : (
        <motion.div
          key={region}
          className="scroll-x px-4 pb-2"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        >
          {filteredIndexes.map(({ item, sparkline }) => {
            const changeAbs =
              item.close != null && item.pct_change != null
                ? item.close - item.close / (1 + item.pct_change / 100)
                : null;
            return (
              <IndexCard
                key={item.symbol}
                name={item.name || item.symbol}
                symbol={item.symbol}
                price={item.close}
                change={changeAbs}
                changePct={item.pct_change}
                sparkline={sparkline}
              />
            );
          })}
        </motion.div>
      )}
    </AnimatePresence>
  );
}
