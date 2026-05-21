import { FormEvent, useEffect, useState } from "react";
import { Search } from "lucide-react";
import { searchStocks } from "../api/client";

interface Props {
  value: string;
  loading?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

const examples = ["600519.SH", "TSLA.US", "700.HK"];

export default function StockSearchBox({ value, loading = false, onChange, onSubmit }: Props) {
  const [suggestions, setSuggestions] = useState<Array<{ symbol: string; name?: string; market?: string }>>([]);

  useEffect(() => {
    const keyword = value.trim();
    if (keyword.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      searchStocks(keyword).then((r) => setSuggestions(r.items.slice(0, 8))).catch(() => setSuggestions([]));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [value]);

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
            className="w-full h-11 pl-9 pr-3 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-sm text-[var(--ink-primary)] font-mono uppercase placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]/40 focus:ring-1 focus:ring-[var(--accent)]/20 transition-all"
            value={value}
            onChange={(e) => onChange(e.target.value.toUpperCase())}
            placeholder="600519.SH / TSLA.US / 700.HK"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !value.trim()}
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

      {suggestions.length > 0 && (
        <div className="grid gap-1.5 sm:grid-cols-2">
          {suggestions.map((item) => (
            <button
              key={item.symbol}
              onClick={() => onChange(item.symbol)}
              className="flex items-center gap-2 px-3 py-2 rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] text-left hover:border-[var(--accent)]/30 active:bg-[var(--bg-card-hover)] transition-all"
            >
              <span className="text-sm font-semibold text-[var(--ink-primary)] font-mono">{item.symbol}</span>
              <span className="text-[11px] text-[var(--ink-muted)] truncate">{item.name || item.market || ""}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
