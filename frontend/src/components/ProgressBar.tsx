interface Props {
  value: number;
  label?: string;
}

export default function ProgressBar({ value, label }: Props) {
  const safe = Math.max(0, Math.min(100, Math.round(value)));

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-[10px]">
        <span className="text-[var(--ink-muted)] font-medium uppercase tracking-wider">{label || "进度"}</span>
        <span className="text-[var(--ink-primary)] font-mono font-bold tabular-nums">{safe}%</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--bg-elevated)]">
        <div
          className="h-full rounded-full bg-[var(--accent)] transition-all duration-700 ease-out"
          style={{ width: `${safe}%` }}
        />
      </div>
    </div>
  );
}
