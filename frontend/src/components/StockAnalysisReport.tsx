export default function StockAnalysisReport({ text, source }: { text: string; source: string | null }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center justify-between h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">RESEARCH SUMMARY</span>
        <span className="text-[9px] font-mono text-[var(--ink-dim)]">{source || "unknown"}</span>
      </div>
      <p className="p-3 text-[11px] leading-relaxed text-[var(--ink-secondary)] whitespace-pre-wrap">{text}</p>
      <div className="px-3 pb-2 text-[9px] text-[var(--ink-dim)]">仅供研究学习，不构成投资建议</div>
    </div>
  );
}
