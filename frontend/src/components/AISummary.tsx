import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import { generateQuickSummary, LLMResponse } from "../api/client";

export default function AISummary() {
  const [data, setData] = useState<LLMResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    generateQuickSummary({ scope: "market", use_llm: false })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="px-4">
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
        <div className="flex items-center gap-1.5 mb-2">
          <Sparkles size={11} className="text-[var(--accent)]" />
          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">AI 市场速览</span>
          {!loading && <span className="live-dot" />}
        </div>

        {loading ? (
          <div className="space-y-1.5">
            <div className="skeleton h-2.5 w-full" />
            <div className="skeleton h-2.5 w-4/5" />
            <div className="skeleton h-2.5 w-3/5" />
          </div>
        ) : data?.text ? (
          <p className="text-[11px] leading-relaxed text-[var(--ink-secondary)]">{data.text}</p>
        ) : (
          <p className="text-[11px] text-[var(--ink-muted)]">AI 分析暂不可用</p>
        )}

        {data?.warnings?.length ? (
          <div className="mt-2 text-[10px] text-[var(--ink-muted)] font-mono">
            {data.warnings.map((w, i) => <span key={i} className="block">{w}</span>)}
          </div>
        ) : null}
      </div>
    </div>
  );
}
