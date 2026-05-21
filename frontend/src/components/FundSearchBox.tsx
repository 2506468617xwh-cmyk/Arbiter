import { FormEvent } from "react";
import { Search } from "lucide-react";

const examples = ["510300.SH", "513100.SH", "QQQ.US", "SPY.US", "2800.HK"];

interface Props {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

export default function FundSearchBox({ value, loading, onChange, onSubmit }: Props) {
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    onSubmit();
  };

  return (
    <div className="space-y-3">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="relative flex-1">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--ink-dim)]" />
          <input
            className="w-full h-11 pl-9 pr-3 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-sm text-[var(--ink-primary)] font-mono placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]/40 focus:ring-1 focus:ring-[var(--accent)]/20 transition-all"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder="510300.SH / QQQ.US / 2800.HK"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="shrink-0 h-11 px-5 rounded-xl bg-[var(--accent)] text-white text-sm font-semibold disabled:opacity-40 active:scale-95 transition-all"
        >
          {loading ? "分析中…" : "分析"}
        </button>
      </form>

      <div className="flex gap-1.5 flex-wrap">
        {examples.map((item) => (
          <button
            key={item}
            type="button"
            onClick={() => onChange(item)}
            className="px-2.5 py-1 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] text-[11px] font-mono text-[var(--ink-muted)] hover:text-[var(--accent)] hover:border-[var(--accent)]/30 active:scale-95 transition-all"
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}
