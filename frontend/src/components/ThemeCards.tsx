import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { MarketTheme } from "../api/client";

interface Props {
  themes: MarketTheme[];
  loading?: boolean;
  onThemeClick?: (themeName: string) => void;
}

function SentimentIcon({ sentiment }: { sentiment: string }) {
  if (sentiment === "bullish") return <TrendingUp size={10} className="text-up" />;
  if (sentiment === "bearish") return <TrendingDown size={10} className="text-down" />;
  return <Minus size={10} className="text-[var(--ink-dim)]" />;
}

export default function ThemeCards({ themes, loading, onThemeClick }: Props) {
  if (loading) {
    return (
      <div className="px-4 space-y-1">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="skeleton h-2.5 w-20 mb-1.5" />
            <div className="skeleton h-2 w-full mb-1" />
            <div className="skeleton h-2 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (!themes.length) return null;

  return (
    <div className="px-4 space-y-1">
      <div className="flex items-center h-5">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">AI 主题聚类</span>
      </div>

      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        {themes.map((theme, i) => {
          const heatColor =
            theme.heat >= 70 ? "bg-[var(--up)]" : theme.heat >= 40 ? "bg-amber-400" : "bg-[var(--ink-dim)]";

          return (
            <div
              key={theme.name}
              className={`p-2.5 cursor-pointer active:bg-[var(--bg-card-hover)] transition-colors ${i > 0 ? "border-t border-[var(--border-subtle)]" : ""}`}
              onClick={() => onThemeClick?.(theme.name)}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-1.5">
                  <SentimentIcon sentiment={theme.sentiment} />
                  <span className="text-[11px] font-semibold text-[var(--ink-primary)]">{theme.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[9px] text-[var(--ink-dim)] font-mono">{theme.news_count}条</span>
                  <span className={`text-financial text-[10px] font-bold ${
                    theme.sentiment === "bullish" ? "text-up" : theme.sentiment === "bearish" ? "text-down" : "text-[var(--ink-muted)]"
                  }`}>
                    {theme.heat}°
                  </span>
                </div>
              </div>

              <div className="h-1 rounded-full bg-[var(--bg-elevated)] overflow-hidden mb-1.5">
                <div
                  className={`h-full rounded-full ${heatColor}`}
                  style={{ width: `${theme.heat}%`, opacity: 0.4 + theme.heat * 0.006 }}
                />
              </div>

              {theme.summary && (
                <p className="text-[10px] text-[var(--ink-secondary)] leading-relaxed">{theme.summary}</p>
              )}

              {theme.affected_sectors.length > 0 && (
                <div className="flex gap-1 mt-1.5 flex-wrap">
                  {theme.affected_sectors.map((s) => (
                    <span key={s} className="px-1.5 py-0.5 text-[8px] bg-[var(--bg-elevated)] text-[var(--ink-muted)] font-medium">
                      {s}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
