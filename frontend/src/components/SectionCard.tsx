import { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  count?: number;
  highlights?: string[];
  warnings?: string[];
  children: ReactNode;
}

function SectionCard({ title, count, highlights = [], warnings = [], children }: SectionCardProps) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-ink">{title}</h2>
        {typeof count === "number" ? (
          <span className="rounded-full border border-line bg-[#f8efe4] px-2.5 py-1 text-xs text-muted">
            {count} 条
          </span>
        ) : null}
      </div>
      <div className="mt-3 text-sm leading-7 text-muted">{children}</div>
      {highlights.length ? (
        <ul className="mt-4 space-y-2 text-sm leading-6 text-ink">
          {highlights.map((item) => (
            <li key={item} className="border-l-2 border-brand/60 pl-3">
              {item}
            </li>
          ))}
        </ul>
      ) : null}
      {warnings.length ? (
        <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-900">
          {warnings.map((warning) => (
            <p key={warning}>{warning}</p>
          ))}
        </div>
      ) : null}
    </section>
  );
}

export default SectionCard;
