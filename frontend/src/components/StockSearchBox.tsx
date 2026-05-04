import { FormEvent, useEffect, useState } from "react";
import { searchStocks } from "../api/client";

interface StockSearchBoxProps {
  value: string;
  loading?: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}

const examples = ["600519.SH", "TSLA.US", "700.HK"];

function StockSearchBox({ value, loading = false, onChange, onSubmit }: StockSearchBoxProps) {
  const [suggestions, setSuggestions] = useState<Array<{ symbol: string; name?: string; market?: string }>>([]);

  useEffect(() => {
    const keyword = value.trim();
    if (keyword.length < 2) {
      setSuggestions([]);
      return;
    }
    const timer = window.setTimeout(() => {
      searchStocks(keyword).then((result) => setSuggestions(result.items.slice(0, 8))).catch(() => setSuggestions([]));
    }, 300);
    return () => window.clearTimeout(timer);
  }, [value]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <form className="grid gap-4 lg:grid-cols-[1fr_auto]" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-sm font-medium text-ink">股票代码</label>
          <input
            className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm uppercase outline-none focus:border-brand"
            value={value}
            onChange={(event) => onChange(event.target.value.toUpperCase())}
            placeholder="输入股票代码，如 600519.SH / TSLA.US / 700.HK"
          />
          <div className="flex flex-wrap gap-2">
            {examples.map((item) => (
              <button key={item} type="button" className="rounded-full border border-line bg-[#fffaf2] px-3 py-1 text-xs text-muted hover:text-brand" onClick={() => onChange(item)}>
                {item}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-end">
          <button className="primary-button w-full" disabled={loading || !value.trim()}>
            {loading ? "分析中..." : "开始分析"}
          </button>
        </div>
      </form>
      {suggestions.length ? (
        <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
          {suggestions.map((item) => (
            <button
              key={item.symbol}
              className="rounded-lg border border-line bg-[#fffdf8] px-3 py-2 text-left text-sm hover:border-brand"
              onClick={() => onChange(item.symbol)}
            >
              <span className="font-semibold text-ink">{item.symbol}</span>
              <span className="ml-2 text-muted">{item.name || item.market || ""}</span>
            </button>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export default StockSearchBox;
