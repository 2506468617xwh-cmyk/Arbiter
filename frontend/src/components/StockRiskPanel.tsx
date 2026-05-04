function StockRiskPanel({ trend, risk, warnings }: { trend: string; risk: string; warnings: string[] }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">趋势与风险</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-line bg-[#fffdf8] p-4">
          <p className="text-sm font-semibold text-ink">趋势摘要</p>
          <p className="mt-2 text-sm leading-7 text-muted">{trend}</p>
        </div>
        <div className="rounded-lg border border-line bg-[#fffdf8] p-4">
          <p className="text-sm font-semibold text-ink">风险摘要</p>
          <p className="mt-2 text-sm leading-7 text-muted">{risk}</p>
        </div>
      </div>
      {warnings.length ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm leading-6 text-amber-900">
          {warnings.map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      ) : null}
    </section>
  );
}

export default StockRiskPanel;
