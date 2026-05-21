import { AlertTriangle, TrendingUp, TrendingDown, Zap } from "lucide-react";
import type { MarketEvent_ } from "../api/client";

interface Props {
  events: MarketEvent_[];
  loading?: boolean;
}

function ImpactBadge({ impact }: { impact: string }) {
  if (impact === "critical") return <Zap size={10} className="text-[var(--up)] shrink-0" />;
  if (impact === "high") return <AlertTriangle size={10} className="text-amber-400 shrink-0" />;
  return null;
}

export default function EventTimeline({ events, loading }: Props) {
  if (loading) {
    return (
      <div className="px-4 space-y-1">
        {[1, 2, 3].map((i) => (
          <div key={i} className="p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="skeleton h-2.5 w-3/4" />
          </div>
        ))}
      </div>
    );
  }

  if (!events.length) return null;

  return (
    <div className="px-4 space-y-1">
      <div className="flex items-center h-5">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">重点事件</span>
      </div>

      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        {events.map((event, i) => {
          const dirColor =
            event.direction === "bullish" ? "text-up" : event.direction === "bearish" ? "text-down" : "text-[var(--ink-muted)]";
          const DirIcon =
            event.direction === "bullish" ? TrendingUp : event.direction === "bearish" ? TrendingDown : null;

          return (
            <div
              key={event.title}
              className={`p-3 ${i > 0 ? "border-t border-[var(--border-subtle)]" : ""}`}
            >
              <div className="flex items-start gap-2">
                <ImpactBadge impact={event.impact} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-[11px] font-semibold text-[var(--ink-primary)] truncate">
                      {event.title}
                    </span>
                    {DirIcon && <DirIcon size={10} className={dirColor} />}
                  </div>
                  {event.ai_analysis && (
                    <p className="mt-0.5 text-[10px] text-[var(--ink-secondary)] leading-relaxed line-clamp-2">
                      {event.ai_analysis}
                    </p>
                  )}
                  {event.affected_assets.length > 0 && (
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {event.affected_assets.map((a) => (
                        <span key={a} className="px-1.5 py-0.5 text-[9px] bg-[var(--bg-elevated)] text-[var(--accent)] font-medium">
                          {a}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
