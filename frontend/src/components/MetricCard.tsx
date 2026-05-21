interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "positive" | "warning" | "negative";
}

const toneBorder: Record<string, string> = {
  positive: "border-l-[3px] border-l-[var(--down)]",
  warning: "border-l-[3px] border-l-amber-400",
  negative: "border-l-[3px] border-l-[var(--up)]",
  default: "",
};

export default function MetricCard({ label, value, detail, tone = "default" }: MetricCardProps) {
  return (
    <div className={`rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] p-4 shadow-sm transition-colors ${toneBorder[tone] ?? ""}`}>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--ink-muted)]">{label}</p>
      <p className="mt-2 text-2xl font-bold text-[var(--ink-primary)] text-financial tabular-nums">{value}</p>
      {detail && (
        <p className="mt-1.5 text-[11px] leading-relaxed text-[var(--ink-secondary)]">{detail}</p>
      )}
    </div>
  );
}
