function fmt(value: unknown, suffix = "", digits = 2): string {
  if (value === null || value === undefined || value === "") return "--";
  const num = Number(value);
  if (Number.isNaN(num)) return String(value);
  return `${num.toLocaleString(undefined, { maximumFractionDigits: digits })}${suffix}`;
}

const items = [
  ["return_1m", "近1月", "%"],
  ["return_3m", "近3月", "%"],
  ["return_6m", "近6月", "%"],
  ["return_1y", "近1年", "%"],
  ["annualized_volatility", "年化波动率", "%"],
  ["max_drawdown_1y", "最大回撤", "%"],
  ["sharpe_ratio_simple", "简化 Sharpe", ""],
  ["ma20", "MA20", ""],
  ["ma60", "MA60", ""],
  ["ma120", "MA120", ""],
  ["liquidity_score", "流动性评分", ""],
  ["tracking_error", "Tracking Error", ""]
];

function FundIndicatorGrid({ indicators }: { indicators: Record<string, number | string | null> }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">核心指标</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {items.map(([key, label, suffix]) => (
          <div key={key} className="rounded-lg border border-line bg-[#fffaf2] p-3">
            <p className="text-xs text-muted">{label}</p>
            <p className="mt-1 text-lg font-semibold text-ink">{fmt(indicators[key], suffix)}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default FundIndicatorGrid;

