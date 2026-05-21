import { FormEvent, useState } from "react";
import { LLMResponse, LLMScope, askResearchChat } from "../api/client";

interface Props {
  title?: string;
  scope: LLMScope;
  assetSymbol?: string | null;
  symbols?: string[];
  useLlm: boolean;
  placeholder?: string;
}

export default function ResearchChatPanel({
  title = "RAbot 研究对话",
  scope,
  assetSymbol = null,
  symbols = [],
  useLlm,
  placeholder = "问一个研究问题，例如：当前主要矛盾是什么？",
}: Props) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<LLMResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    askResearchChat({ question, scope, asset_symbol: assetSymbol, symbols, use_llm: useLlm })
      .then(setAnswer)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "研究对话失败"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
      <div className="flex items-center justify-between h-8 px-3 border-b border-[var(--border-subtle)]">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">RESEARCH CHAT</span>
        <span className="text-[9px] font-mono text-[var(--ink-dim)]">{useLlm ? "LLM ON" : "LLM OFF"}</span>
      </div>
      <form className="p-3 space-y-2" onSubmit={submit}>
        <textarea
          className="w-full min-h-20 p-2 text-[11px] leading-relaxed border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--ink-primary)] placeholder:text-[var(--ink-dim)] font-mono outline-none resize-y focus:border-[var(--accent)]"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={placeholder}
        />
        <button
          className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider bg-[var(--accent)] text-white disabled:opacity-30 transition-opacity"
          disabled={loading || !question.trim()}
        >
          {loading ? "分析中…" : "ASK RABOT"}
        </button>
      </form>
      {error && (
        <div className="mx-3 mb-3 px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono bg-[var(--bg-elevated)]">{error}</div>
      )}
      {answer && (
        <div className="mx-3 mb-3 p-3 bg-[var(--bg-elevated)]">
          <p className="text-[11px] leading-relaxed text-[var(--ink-secondary)] whitespace-pre-wrap">{answer.text}</p>
          {answer.warnings.length > 0 && (
            <div className="mt-2 text-[10px] text-[var(--ink-muted)] font-mono">
              {answer.warnings.map((w) => <p key={w}>{w}</p>)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
