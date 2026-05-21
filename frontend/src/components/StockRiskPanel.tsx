export default function StockRiskPanel({ trend, risk, warnings }: { trend: string; risk: string; warnings: string[] }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">RISK & TREND</span>
      </div>
      <div className="p-3 space-y-3">
        <div className="grid gap-2 sm:grid-cols-2">
          <div>
            <span className="text-[9px] text-[var(--ink-dim)] uppercase tracking-wider">趋势</span>
            <p className="text-[11px] text-[var(--ink-secondary)] leading-relaxed mt-0.5">{trend}</p>
          </div>
          <div>
            <span className="text-[9px] text-[var(--ink-dim)] uppercase tracking-wider">风险</span>
            <p className="text-[11px] text-[var(--ink-secondary)] leading-relaxed mt-0.5">{risk}</p>
          </div>
        </div>
        {warnings.length > 0 && (
          <div className="px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono bg-[var(--bg-elevated)]">
            {warnings.map((w) => <p key={w}>{w}</p>)}
          </div>
        )}
      </div>
    </div>
  );
}
