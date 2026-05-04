import { FundQuote } from "../api/client";

function fmt(value: number | null | undefined, digits = 2): string {
  return value === null || value === undefined ? "--" : value.toLocaleString(undefined, { maximumFractionDigits: digits });
}

function FundQuoteCard({ quote }: { quote: FundQuote | null }) {
  const primary = quote?.last_price ?? quote?.nav ?? null;
  const change = primary !== null && quote?.prev_close ? ((primary - quote.prev_close) / quote.prev_close) * 100 : null;
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">{quote?.market ?? "--"} · {quote?.fund_type ?? "--"} · {quote?.currency ?? "--"}</p>
          <h2 className="mt-2 text-2xl font-semibold text-ink">{quote?.name || quote?.symbol || "--"}</h2>
          <p className="mt-1 text-sm text-muted">{quote?.symbol ?? "--"} · {quote?.source ?? "unknown"}</p>
        </div>
        <div className="text-left md:text-right">
          <p className="text-3xl font-semibold text-ink">{fmt(primary)}</p>
          <p className={`mt-1 text-sm font-medium ${change !== null && change >= 0 ? "text-emerald-700" : "text-red-700"}`}>
            {change === null ? "--" : `${change.toFixed(2)}%`}
          </p>
        </div>
      </div>
      <div className="mt-5 grid gap-3 text-sm sm:grid-cols-5">
        <Field label="最新净值" value={fmt(quote?.nav)} />
        <Field label="昨收" value={fmt(quote?.prev_close)} />
        <Field label="折溢价" value={quote?.premium_discount === null || quote?.premium_discount === undefined ? "--" : `${quote.premium_discount.toFixed(2)}%`} />
        <Field label="成交量" value={fmt(quote?.volume, 0)} />
        <Field label="成交额" value={fmt(quote?.turnover, 0)} />
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

export default FundQuoteCard;

