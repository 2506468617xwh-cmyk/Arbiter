interface MetricCardProps {
  label: string;
  value: string;
  detail?: string;
  tone?: "default" | "positive" | "warning";
}

function MetricCard({ label, value, detail, tone = "default" }: MetricCardProps) {
  const toneClass =
    tone === "positive"
      ? "border-emerald-200 bg-emerald-50/70"
      : tone === "warning"
        ? "border-amber-200 bg-amber-50/80"
        : "border-line bg-panel";

  return (
    <section className={`rounded-lg border p-5 shadow-soft ${toneClass}`}>
      <p className="text-sm font-medium text-muted">{label}</p>
      <p className="mt-3 text-2xl font-semibold text-ink">{value}</p>
      {detail ? <p className="mt-2 text-sm leading-6 text-muted">{detail}</p> : null}
    </section>
  );
}

export default MetricCard;
