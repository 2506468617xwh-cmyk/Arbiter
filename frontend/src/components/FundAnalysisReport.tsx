function FundAnalysisReport({ text, source }: { text: string; source: string | null }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-lg font-semibold text-ink">研究摘要</h2>
        <span className="rounded-lg border border-line bg-[#fffaf2] px-3 py-1 text-xs text-muted">{source || "unknown"}</span>
      </div>
      <p className="mt-4 whitespace-pre-wrap text-sm leading-7 text-ink">{text}</p>
    </section>
  );
}

export default FundAnalysisReport;

