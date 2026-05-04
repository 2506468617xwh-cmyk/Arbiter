import { NewsItem } from "../api/client";
import NewsRiskTags from "./NewsRiskTags";

interface NewsItemCardProps {
  item: NewsItem;
  active: boolean;
  onOpen: () => void;
}

function score(value: number | null): string {
  return value === null ? "--" : value.toFixed(0);
}

function dateText(value: string | null): string {
  if (!value) return "--";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function NewsItemCard({ item, active, onOpen }: NewsItemCardProps) {
  return (
    <button
      className={`w-full rounded-lg border p-4 text-left transition ${
        active ? "border-brand bg-[#fff7ed] shadow-soft" : "border-line bg-[#fffdf8] hover:border-brand/50 hover:bg-[#fffaf2]"
      }`}
      onClick={onOpen}
      disabled={!item.id}
    >
      <div className="flex min-w-0 items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="break-words text-sm font-semibold leading-6 text-ink">{item.title}</p>
          <p className="mt-2 line-clamp-2 break-words text-xs leading-5 text-muted">{item.summary || "暂无摘要。"}</p>
        </div>
        <div className="shrink-0 rounded-lg bg-[#fff4e4] px-2 py-1 text-center text-xs font-semibold text-brand">
          <p>质 {score(item.quality_score)}</p>
          <p>重 {score(item.importance_score)}</p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-muted">
        <span className="rounded-full border border-line bg-white px-2 py-1">{item.source ?? "未知来源"}</span>
        <span className="rounded-full border border-line bg-white px-2 py-1">{item.provider ?? "local"}</span>
        <span className="rounded-full border border-line bg-white px-2 py-1">{dateText(item.published_at)}</span>
      </div>
      <div className="mt-3">
        <NewsRiskTags tags={item.risk_tags?.length ? item.risk_tags : item.risk_tag ? [item.risk_tag] : []} />
      </div>
    </button>
  );
}

export default NewsItemCard;
