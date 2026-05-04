function fmt(value: unknown): string {
  if (value === null || value === undefined || value === "") return "--";
  if (typeof value === "number") return value.toFixed(2);
  return String(value);
}

const items = [
  ["ma20", "MA20"],
  ["ma60", "MA60"],
  ["ma120", "MA120"],
  ["return_5d", "5日收益%"],
  ["return_20d", "20日收益%"],
  ["return_60d", "60日收益%"],
  ["benchmark_return_20d", "大盘20日收益%"],
  ["relative_return_20d", "相对大盘20日%"],
  ["relative_return_60d", "相对大盘60日%"],
  ["volatility_20d", "20日波动率%"],
  ["max_drawdown_120d", "120日最大回撤%"],
  ["volume_ratio_20d", "量比20日"]
];

function StockIndicatorGrid({ indicators }: { indicators: Record<string, unknown> }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">技术指标</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {items.map(([key, label]) => (
          <div key={key} className="rounded-lg border border-line bg-[#fffdf8] p-3">
            <p className="text-xs text-muted">{label}</p>
            <p className="mt-1 text-lg font-semibold text-ink">{fmt(indicators[key])}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default StockIndicatorGrid;
