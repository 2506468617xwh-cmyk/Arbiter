import { FundQuote } from "../api/client";

function fmt(v: number | null | undefined, d = 2): string {
  return v === null || v === undefined ? "--" : v.toLocaleString(undefined, { maximumFractionDigits: d });
}

export default function FundQuoteCard({ quote }: { quote: FundQuote | null }) {
  const primary = quote?.last_price ?? quote?.nav ?? null;
  const change = primary !== null && quote?.prev_close ? ((primary - quote.prev_close) / quote.prev_close) * 100 : null;
  const isUp = change !== null && change >= 0;
  const isDown = change !== null && change < 0;

  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--accent)]">
            {quote?.market ?? "--"} · {quote?.fund_type ?? "--"} · {quote?.currency ?? "--"}
          </div>
          <div className="mt-0.5 text-[13px] font-bold text-[var(--ink-primary)]">
            {quote?.name || quote?.symbol || "--"}
          </div>
          <div className="text-[10px] font-mono text-[var(--ink-dim)]">{quote?.symbol ?? "--"}</div>
        </div>
        <div className="text-right">
          <div className="text-financial text-xl font-bold text-[var(--ink-primary)]">{fmt(primary)}</div>
          <div className={`text-financial text-xs font-bold mt-0.5 ${isUp ? "text-up" : isDown ? "text-down" : "text-[var(--ink-muted)]"}`}>
            {change === null ? "--" : `${change >= 0 ? "+" : ""}${change.toFixed(2)}%`}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-5 gap-1.5 mt-3 pt-3 border-t border-[var(--border-subtle)]">
        {([
          ["NAV", fmt(quote?.nav)],
          ["PREV", fmt(quote?.prev_close)],
          ["PRM/DSC", quote?.premium_discount != null ? `${quote.premium_discount.toFixed(2)}%` : "--"],
          ["VOL", fmt(quote?.volume, 0)],
          ["TURN", fmt(quote?.turnover, 0)],
        ] as [string, string][]).map(([k, v]) => (
          <div key={k} className="text-center">
            <div className="text-[8px] text-[var(--ink-dim)] uppercase tracking-wider">{k}</div>
            <div className="text-financial text-[11px] font-bold text-[var(--ink-primary)] mt-0.5">{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
