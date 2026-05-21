function fmt(v: unknown): string {
  if (v === null || v === undefined || v === "") return "--";
  if (typeof v === "number") return v.toFixed(2);
  return String(v);
}

const ITEMS: [string, string][] = [
  ["ma20", "MA20"], ["ma60", "MA60"], ["ma120", "MA120"],
  ["return_5d", "5日收益%"], ["return_20d", "20日收益%"], ["return_60d", "60日收益%"],
  ["benchmark_return_20d", "大盘20日%"], ["relative_return_20d", "相对大盘20日%"], ["relative_return_60d", "相对大盘60日%"],
  ["volatility_20d", "20日波动率%"], ["max_drawdown_120d", "120日最大回撤%"], ["volume_ratio_20d", "量比20日"],
];

export default function StockIndicatorGrid({ indicators }: { indicators: Record<string, unknown> }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">TECHNICALS</span>
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4">
        {ITEMS.map(([k, label]) => (
          <div key={k} className="px-3 py-2 border-r border-b border-[var(--border-subtle)] last:border-r-0">
            <div className="text-[9px] text-[var(--ink-dim)] uppercase">{label}</div>
            <div className="text-financial text-[12px] font-bold text-[var(--ink-primary)] mt-0.5">{fmt(indicators[k])}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
