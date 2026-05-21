import { motion } from "framer-motion";
import type { SentimentGauge as SentimentGaugeData } from "../api/client";

interface Props {
  data: SentimentGaugeData;
  loading?: boolean;
}

function Ring({ label, value, delay }: { label: string; value: number; delay: number }) {
  const hue = value <= 50 ? (value / 50) * 40 : 40 + ((value - 50) / 50) * 80;
  const color = `hsl(${hue}, 65%, 50%)`;

  return (
    <div className="flex flex-col items-center gap-0.5">
      <div className="relative w-9 h-9">
        <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
          <circle cx="18" cy="18" r="14" fill="none" stroke="var(--bg-elevated)" strokeWidth="2.5" />
          <motion.circle
            cx="18" cy="18" r="14" fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round"
            strokeDasharray={`${(value / 100) * 88} 88`}
            initial={{ strokeDasharray: "0 88" }}
            animate={{ strokeDasharray: `${(value / 100) * 88} 88` }}
            transition={{ delay, duration: 0.6, ease: "easeOut" }}
          />
        </svg>
        <span className="absolute inset-0 flex items-center justify-center text-financial text-[9px] font-bold" style={{ color }}>
          {value}
        </span>
      </div>
      <span className="text-[8px] text-[var(--ink-dim)] tracking-wide">{label}</span>
    </div>
  );
}

export default function SentimentGaugeView({ data, loading }: Props) {
  if (loading) {
    return (
      <div className="px-4">
        <div className="p-3 border border-[var(--border-subtle)] bg-[var(--bg-card)]">
          <div className="skeleton h-2.5 w-24" />
        </div>
      </div>
    );
  }

  const appetiteLabel = data.risk_appetite === "风险偏好" ? "风险偏好" : data.risk_appetite === "风险规避" ? "风险规避" : "中性";
  const appetiteColor = data.risk_appetite === "风险偏好" ? "text-up" : data.risk_appetite === "风险规避" ? "text-down" : "text-[var(--ink-muted)]";

  return (
    <div className="px-4">
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">市场情绪</span>
          <span className={`text-[10px] font-bold ${appetiteColor}`}>{appetiteLabel}</span>
        </div>
        <div className="flex justify-between px-2">
          <Ring label="综合" value={data.overall} delay={0.1} />
          <Ring label="AI科技" value={data.ai_tech} delay={0.15} />
          <Ring label="半导体" value={data.semiconductors} delay={0.2} />
          <Ring label="宏观" value={data.macro_policy} delay={0.25} />
          <Ring label="地缘" value={data.geopolitics} delay={0.3} />
        </div>
        <div className="flex justify-between mt-2 text-[7px] text-[var(--ink-dim)] font-mono px-1">
          <span>恐惧</span><span>中性</span><span>贪婪</span>
        </div>
      </div>
    </div>
  );
}
