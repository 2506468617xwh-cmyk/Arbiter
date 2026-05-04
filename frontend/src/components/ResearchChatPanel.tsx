import { FormEvent, useState } from "react";
import { LLMResponse, LLMScope, askResearchChat } from "../api/client";

interface ResearchChatPanelProps {
  title?: string;
  scope: LLMScope;
  assetSymbol?: string | null;
  symbols?: string[];
  useLlm: boolean;
  placeholder?: string;
}

function ResearchChatPanel({
  title = "RAbot 研究对话",
  scope,
  assetSymbol = null,
  symbols = [],
  useLlm,
  placeholder = "问一个研究问题，例如：当前主要矛盾是什么？"
}: ResearchChatPanelProps) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<LLMResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    askResearchChat({ question, scope, asset_symbol: assetSymbol, symbols, use_llm: useLlm })
      .then(setAnswer)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "研究对话失败。"))
      .finally(() => setLoading(false));
  };

  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-lg font-semibold text-ink">{title}</h2>
        <span className="text-xs text-muted">{useLlm ? "LLM 已开启" : "LLM 已关闭"}</span>
      </div>
      <form className="mt-4 space-y-3" onSubmit={submit}>
        <textarea
          className="min-h-24 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-brand"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={placeholder}
        />
        <div className="flex justify-end">
          <button className="primary-button" disabled={loading || !question.trim()}>
            {loading ? "分析中..." : "询问 RAbot"}
          </button>
        </div>
      </form>
      {error ? <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">{error}</div> : null}
      {answer ? (
        <div className="mt-4 rounded-lg border border-line bg-[#fffdf8] p-4">
          <p className="whitespace-pre-wrap text-sm leading-7 text-muted">{answer.text}</p>
          {answer.warnings.length ? (
            <div className="mt-3 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-6 text-amber-900">
              {answer.warnings.map((warning) => <p key={warning}>{warning}</p>)}
            </div>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}

export default ResearchChatPanel;
