function FundRiskPanel({
  allocation,
  risk,
  liquidity,
  warnings
}: {
  allocation: string;
  risk: string;
  liquidity: string;
  warnings: string[];
}) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">资产类别与风险</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <Panel title="资产类别判断" text={allocation} />
        <Panel title="主要风险" text={risk} />
        <Panel title="流动性观察" text={liquidity} />
      </div>
      {warnings.length ? (
        <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          <p className="font-medium">数据提示</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            {warnings.map((warning) => <li key={warning}>{warning}</li>)}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function Panel({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border border-line bg-[#fffaf2] p-4">
      <p className="text-sm font-medium text-ink">{title}</p>
      <p className="mt-2 text-sm leading-6 text-muted">{text}</p>
    </div>
  );
}

export default FundRiskPanel;

