export default function FundAnalysisReport({ text, source }: { text: string; source: string | null }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center justify-between h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">RESEARCH SUMMARY</span>
        <span className="text-[9px] font-mono text-[var(--ink-dim)]">{source || "unknown"}</span>
      </div>
      <p className="p-3 text-[11px] leading-relaxed text-[var(--ink-secondary)] whitespace-pre-wrap">{text}</p>
    </div>
  );
}
