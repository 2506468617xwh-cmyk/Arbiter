export default function FundRiskPanel({
  allocation, risk, liquidity, warnings,
}: {
  allocation: string; risk: string; liquidity: string; warnings: string[];
}) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">ALLOCATION & RISK</span>
      </div>
      <div className="p-3 space-y-3">
        <div className="grid gap-2 sm:grid-cols-3">
          {([
            ["资产类别", allocation],
            ["主要风险", risk],
            ["流动性", liquidity],
          ] as [string, string][]).map(([title, text]) => (
            <div key={title}>
              <span className="text-[9px] text-[var(--ink-dim)] uppercase tracking-wider">{title}</span>
              <p className="text-[11px] text-[var(--ink-secondary)] leading-relaxed mt-0.5">{text}</p>
            </div>
          ))}
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
