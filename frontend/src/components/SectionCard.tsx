import { ReactNode } from "react";

interface SectionCardProps {
  title: string;
  count?: number;
  highlights?: string[];
  warnings?: string[];
  children: ReactNode;
}

export default function SectionCard({ title, count, highlights = [], warnings = [], children }: SectionCardProps) {
  return (
    <section className="rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className="w-1 h-4 rounded-full bg-[var(--accent)]" />
          <h2 className="text-sm font-semibold text-[var(--ink-primary)]">{title}</h2>
        </div>
        {typeof count === "number" && (
          <span className="rounded-md border border-[var(--border-card)] bg-[var(--bg-elevated)] px-2 py-0.5 text-[10px] font-medium text-[var(--ink-muted)]">
            {count}
          </span>
        )}
      </div>

      <div className="text-sm leading-7 text-[var(--ink-secondary)]">{children}</div>

      {highlights.length > 0 && (
        <ul className="mt-4 space-y-2">
          {highlights.map((item) => (
            <li key={item} className="flex items-start gap-2 text-sm text-[var(--ink-primary)]">
              <span className="mt-1.5 w-1 h-1 rounded-full bg-[var(--accent)] shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      )}

      {warnings.length > 0 && (
        <div className="mt-4 rounded-lg border border-[var(--border-card)] bg-[var(--bg-elevated)] px-3 py-2.5 text-xs leading-5 text-[var(--ink-secondary)]">
          {warnings.map((w) => (
            <p key={w}>{w}</p>
          ))}
        </div>
      )}
    </section>
  );
}
