function FundDcaPanel({ text }: { text: string }) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <h2 className="text-lg font-semibold text-ink">定投适配度观察</h2>
      <p className="mt-3 text-sm leading-7 text-muted">{text}</p>
    </section>
  );
}

export default FundDcaPanel;

