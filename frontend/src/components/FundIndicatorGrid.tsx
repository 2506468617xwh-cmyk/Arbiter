function fmt(v: unknown, suffix = "", d = 2): string {
  if (v === null || v === undefined || v === "") return "--";
  const n = Number(v);
  if (Number.isNaN(n)) return String(v);
  return `${n.toLocaleString(undefined, { maximumFractionDigits: d })}${suffix}`;
}

const ITEMS: [string, string, string][] = [
  ["return_1m", "近1月", "%"], ["return_3m", "近3月", "%"], ["return_6m", "近6月", "%"], ["return_1y", "近1年", "%"],
  ["annualized_volatility", "年化波动率", "%"], ["max_drawdown_1y", "最大回撤", "%"],
  ["sharpe_ratio_simple", "Sharpe", ""], ["ma20", "MA20", ""],
  ["ma60", "MA60", ""], ["ma120", "MA120", ""],
  ["liquidity_score", "流动性评分", ""], ["tracking_error", "Tracking Err", ""],
];

export default function FundIndicatorGrid({ indicators }: { indicators: Record<string, number | string | null> }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">KEY METRICS</span>
      </div>
      <div className="grid grid-cols-3 sm:grid-cols-4">
        {ITEMS.map(([k, label, suffix]) => (
          <div key={k} className="px-3 py-2 border-r border-b border-[var(--border-subtle)] last:border-r-0">
            <div className="text-[9px] text-[var(--ink-dim)] uppercase">{label}</div>
            <div className="text-financial text-[12px] font-bold text-[var(--ink-primary)] mt-0.5">{fmt(indicators[k], suffix)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
