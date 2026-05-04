import { useI18n } from "../i18n";
import { PageKey } from "../i18n";
import ResearchPet from "./ResearchPet";

function PageIntro({ pageKey, context }: { pageKey: PageKey; context?: Record<string, unknown> }) {
  const { page } = useI18n();
  const item = page[pageKey];
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
      <div>
        <p className="text-sm font-medium text-brand">{item.eyebrow}</p>
        <h1 className="mt-2 text-3xl font-semibold text-ink">{item.title}</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{item.subtitle}</p>
      </div>
      <ResearchPet pageName={pageKey} context={{ title: item.title, subtitle: item.subtitle, ...context }} />
    </div>
  );
}

export default PageIntro;
