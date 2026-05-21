export default function FundDcaPanel({ text }: { text: string }) {
  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">DCA FIT</span>
      </div>
      <p className="p-3 text-[11px] leading-relaxed text-[var(--ink-secondary)]">{text}</p>
    </div>
  );
}
