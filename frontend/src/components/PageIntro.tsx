import { useI18n } from "../i18n";
import { PageKey } from "../i18n";

export default function PageIntro({ pageKey }: { pageKey: PageKey; context?: Record<string, unknown> }) {
  const { page } = useI18n();
  const item = page[pageKey];
  return (
    <div>
      <span className="text-[10px] font-bold uppercase tracking-[0.15em] text-[var(--accent)]">{item.eyebrow}</span>
      <p className="mt-0.5 text-[11px] text-[var(--ink-muted)]">{item.subtitle}</p>
    </div>
  );
}
