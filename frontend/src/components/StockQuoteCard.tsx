import { StockQuote } from "../api/client";

function fmt(value: number | null, digits = 2): string {
  return value === null ? "--" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function StockQuoteCard({ quote }: { quote: StockQuote | null }) {
  const change = quote?.last_price !== null && quote?.prev_close ? ((quote.last_price - quote.prev_close) / quote.prev_close) * 100 : null;
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">{quote?.market ?? "--"} · {quote?.currency ?? "--"}</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink">{quote?.name || quote?.symbol || "--"}</h2>
          <p className="mt-1 text-sm text-muted">{quote?.symbol ?? "--"} · {quote?.source ?? "unknown"}</p>
        </div>
        <div className="text-left md:text-right">
          <p className="text-3xl font-semibold text-ink">{fmt(quote?.last_price ?? null)}</p>
          <p className={`mt-1 text-sm font-medium ${change !== null && change >= 0 ? "text-emerald-700" : "text-red-700"}`}>
            {change === null ? "--" : `${change.toFixed(2)}%`}
          </p>
        </div>
      </div>
      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-4">
        <Field label="开盘" value={fmt(quote?.open ?? null)} />
        <Field label="最高" value={fmt(quote?.high ?? null)} />
        <Field label="最低" value={fmt(quote?.low ?? null)} />
        <Field label="成交量" value={fmt(quote?.volume ?? null, 0)} />
      </div>
    </section>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-line bg-[#fffaf2] p-3">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 font-semibold text-ink">{value}</p>
    </div>
  );
}

export default StockQuoteCard;
