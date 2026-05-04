import { MarketPerformanceItem } from "../api/client";

interface HeatListProps {
  title: string;
  items: MarketPerformanceItem[];
  metric: keyof MarketPerformanceItem;
  suffix?: string;
}

function valueOf(item: MarketPerformanceItem, metric: keyof MarketPerformanceItem): number {
  const value = item[metric];
  return typeof value === "number" ? value : 0;
}

function HeatList({ title, items, metric, suffix = "%" }: HeatListProps) {
  const maxAbs = Math.max(1, ...items.map((item) => Math.abs(valueOf(item, metric))));
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-base font-semibold text-ink">{title}</h2>
      <div className="mt-4 space-y-3">
        {items.map((item) => {
          const value = valueOf(item, metric);
          const width = Math.max(8, Math.abs(value) / maxAbs * 100);
          const positive = value >= 0;
          return (
            <div key={item.symbol} className="grid grid-cols-[82px_1fr_72px] items-center gap-3 text-sm">
              <div className="font-semibold text-ink">{item.symbol}</div>
              <div className="h-2 overflow-hidden rounded-full bg-[#eadfce]">
                <div
                  className={positive ? "h-full rounded-full bg-emerald-500" : "h-full rounded-full bg-amber-600"}
                  style={{ width: `${width}%` }}
                />
              </div>
              <div className={positive ? "text-right font-semibold text-emerald-700" : "text-right font-semibold text-amber-800"}>
                {value.toFixed(2)}{suffix}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default HeatList;
