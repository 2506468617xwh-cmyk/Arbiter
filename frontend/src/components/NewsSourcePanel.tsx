import { NewsCollectResponse, NewsItem } from "../api/client";

interface NewsSourcePanelProps {
  items: NewsItem[];
  collectResult: NewsCollectResponse | null;
}

function NewsSourcePanel({ items, collectResult }: NewsSourcePanelProps) {
  const localStats = items.reduce<Record<string, number>>((acc, item) => {
    const key = item.provider || "local";
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});
  const stats = collectResult?.provider_stats;

  return (
    <aside className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <h2 className="text-sm font-semibold text-ink">来源覆盖</h2>
      <div className="mt-3 space-y-2">
        {Object.entries(stats || localStats).map(([name, value]) => {
          const fetched = typeof value === "number" ? value : value.fetched ?? 0;
          const saved = typeof value === "number" ? value : value.saved ?? 0;
          const warnings = typeof value === "number" ? [] : value.warnings ?? [];
          return (
            <div key={name} className="rounded-lg border border-line bg-[var(--bg-elevated)] p-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-sm font-semibold text-ink">{name}</p>
                <p className="text-xs text-muted">{typeof value === "number" ? `${fetched} 条` : `抓取 ${fetched} / 入库 ${saved}`}</p>
              </div>
              {warnings.length ? <p className="mt-2 text-xs leading-5 text-amber-800">{warnings[0]}</p> : null}
            </div>
          );
        })}
        {!Object.keys(stats || localStats).length ? <p className="text-sm text-muted">暂无来源统计。</p> : null}
      </div>
    </aside>
  );
}

export default NewsSourcePanel;
