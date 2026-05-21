import { useEffect, useState } from "react";

interface TickerItem {
  symbol: string;
  name: string;
  price: number;
  changePct: number;
}

const FALLBACK: TickerItem[] = [
  { symbol: "AAPL", name: "Apple", price: 227.63, changePct: 1.24 },
  { symbol: "NVDA", name: "NVIDIA", price: 1025.00, changePct: 3.57 },
  { symbol: "TSLA", name: "Tesla", price: 285.10, changePct: -0.82 },
  { symbol: "MSFT", name: "Microsoft", price: 442.30, changePct: 0.45 },
  { symbol: "GOOGL", name: "Alphabet", price: 191.20, changePct: 0.93 },
  { symbol: "META", name: "Meta", price: 576.45, changePct: 2.11 },
  { symbol: "000300", name: "沪深300", price: 3785.62, changePct: -0.34 },
  { symbol: "000001", name: "上证指数", price: 3352.48, changePct: 0.12 },
];

export default function TickerTape() {
  const [items] = useState<TickerItem[]>(FALLBACK);
  const doubled = [...items, ...items];

  return (
    <div className="ticker-tape">
      <div className="ticker-track py-1.5">
        {doubled.map((item, i) => {
          const isUp = item.changePct > 0;
          const isDown = item.changePct < 0;
          return (
            <span key={`${item.symbol}-${i}`} className="inline-flex items-center gap-2 mr-6 text-xs select-none">
              <span className="text-[var(--ink-dim)] font-semibold text-[10px] uppercase tracking-wide min-w-[40px]">
                {item.symbol}
              </span>
              <span className="text-[var(--ink-primary)] font-medium text-financial tabular-nums">
                {item.price.toFixed(2)}
              </span>
              <span className={`text-financial font-bold tabular-nums ${isUp ? "text-up" : isDown ? "text-down" : "text-[var(--ink-muted)]"}`}>
                {isUp ? "+" : ""}{item.changePct.toFixed(2)}%
              </span>
              <span className="text-[var(--ink-dim)] opacity-30 mx-1">|</span>
            </span>
          );
        })}
      </div>
    </div>
  );
}
