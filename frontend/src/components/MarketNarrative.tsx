import { motion } from "framer-motion";
import { Sparkles, AlertTriangle, Shield } from "lucide-react";

interface Props {
  headline: string;
  body: string;
  keyThemes: string[];
  riskLevel: string;
  loading?: boolean;
}

export default function MarketNarrative({ headline, body, keyThemes, riskLevel, loading }: Props) {
  if (loading) {
    return (
      <div className="px-4">
        <div className="p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)]">
          <div className="skeleton h-3 w-2/3 mb-2" />
          <div className="skeleton h-2.5 w-full mb-1.5" />
          <div className="skeleton h-2.5 w-4/5" />
        </div>
      </div>
    );
  }

  const riskColor = riskLevel === "high" ? "text-[var(--up)]" : riskLevel === "elevated" ? "text-amber-400" : "text-[var(--down)]";
  const RiskIcon = riskLevel === "high" ? AlertTriangle : Shield;

  return (
    <div className="px-4">
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <Sparkles size={11} className="text-[var(--accent)]" />
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--accent)]">AI 市场主线</span>
          </div>
          <div className="flex items-center gap-1">
            <RiskIcon size={10} className={riskColor} />
            <span className={`text-[10px] font-bold ${riskColor}`}>
              {riskLevel === "high" ? "高风险" : riskLevel === "elevated" ? "关注" : "正常"}
            </span>
          </div>
        </div>

        <h2 className="text-[12px] font-bold text-[var(--ink-primary)] leading-snug">{headline}</h2>
        <p className="mt-1 text-[11px] text-[var(--ink-secondary)] leading-relaxed">{body}</p>

        {keyThemes.length > 0 && (
          <div className="flex gap-1 mt-2 flex-wrap">
            {keyThemes.map((t) => (
              <span key={t} className="px-1.5 py-0.5 text-[9px] font-medium bg-[var(--accent-soft)] text-[var(--accent)]">
                {t}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
