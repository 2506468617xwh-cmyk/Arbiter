import { MarketPerformanceItem } from "../api/client";

interface Props {
  title: string;
  items: MarketPerformanceItem[];
  metric: keyof MarketPerformanceItem;
  suffix?: string;
}

function valueOf(item: MarketPerformanceItem, metric: keyof MarketPerformanceItem): number {
  const v = item[metric];
  return typeof v === "number" ? v : 0;
}

export default function HeatList({ title, items, metric, suffix = "%" }: Props) {
  const maxAbs = Math.max(1, ...items.map((i) => Math.abs(valueOf(i, metric))));

  return (
    <div className="space-y-1">
      <div className="flex items-center h-5 px-1">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">{title}</span>
      </div>
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        {items.map((item, i) => {
          const val = valueOf(item, metric);
          const width = Math.max(6, (Math.abs(val) / maxAbs) * 100);
          const isPositive = val >= 0;

          return (
            <div
              key={item.symbol}
              className={`flex items-center h-8 px-3 gap-3 ${i > 0 ? "border-t border-[var(--border-subtle)]" : ""}`}
            >
              <span className="text-[11px] font-semibold text-[var(--ink-primary)] font-mono w-20 shrink-0 truncate">
                {item.symbol}
              </span>
              <div className="flex-1 h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                <div
                  className={`h-full rounded-full ${isPositive ? "bg-[var(--down)]" : "bg-[var(--up)]"}`}
                  style={{ width: `${width}%`, opacity: 0.35 + (Math.abs(val) / maxAbs) * 0.45 }}
                />
              </div>
              <span className={`text-financial text-[11px] font-bold w-16 text-right shrink-0 ${isPositive ? "text-[var(--down)]" : "text-[var(--up)]"}`}>
                {isPositive ? "+" : ""}{val.toFixed(2)}{suffix}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
