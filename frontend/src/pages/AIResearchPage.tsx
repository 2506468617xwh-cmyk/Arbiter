import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  LLMResponse, LLMScope, MarketPerformanceItem,
  askResearchChat, fetchMarketPerformance, generateQuickSummary,
} from "../api/client";

interface Props {
  useLlm: boolean;
  onOpenModelSettings: () => void;
}

interface ChatItem {
  id: string;
  question: string;
  answer: LLMResponse;
  createdAt: string;
}

const SCOPE_OPTIONS: Array<{ value: LLMScope; label: string }> = [
  { value: "market", label: "全市场" },
  { value: "single_asset", label: "单资产" },
  { value: "multi_asset", label: "多资产" },
];

function splitSymbols(raw: string): string[] {
  return raw.split(/[,，\s]+/).map((s) => s.trim().toUpperCase()).filter(Boolean);
}

export default function AIResearchPage({ useLlm, onOpenModelSettings }: Props) {
  const [scope, setScope] = useState<LLMScope>("market");
  const [assetSymbol, setAssetSymbol] = useState("NASDAQ");
  const [symbolsText, setSymbolsText] = useState("NASDAQ, SP500, CSI300, GOLD");
  const [question, setQuestion] = useState("当前全球资产主线是什么？");
  const [summary, setSummary] = useState<LLMResponse | null>(null);
  const [history, setHistory] = useState<ChatItem[]>([]);
  const [available, setAvailable] = useState<MarketPerformanceItem[]>([]);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketPerformance().then((r) => setAvailable(r.items)).catch(() => setAvailable([]));
  }, []);

  const symbols = useMemo(() => splitSymbols(symbolsText), [symbolsText]);

  const payload = {
    scope,
    asset_symbol: scope === "single_asset" ? assetSymbol.trim().toUpperCase() : null,
    symbols: scope === "multi_asset" ? symbols : [],
    use_llm: useLlm,
  };

  const doSummary = async () => {
    setError(null);
    setLoadingSummary(true);
    try { setSummary(await generateQuickSummary(payload)); } catch (exc: any) { setError(exc?.message || "生成失败"); }
    finally { setLoadingSummary(false); }
  };

  const doAsk = async (e: FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    setError(null);
    setLoadingChat(true);
    try {
      const result = await askResearchChat({ ...payload, question });
      setHistory((prev) => [{ id: `${Date.now()}`, question, answer: result, createdAt: new Date().toLocaleString() }, ...prev].slice(0, 10));
    } catch (exc: any) { setError(exc?.message || "对话失败"); }
    finally { setLoadingChat(false); }
  };

  return (
    <div className="space-y-2">
      {/* Research config */}
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">SCOPE</span>
          <span className="text-[9px] font-mono text-[var(--ink-dim)]">{useLlm ? "LLM ON" : "LLM OFF"}</span>
        </div>
        <div className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
          <select
            className="h-8 px-2 text-[11px] border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--ink-primary)] font-mono outline-none"
            value={scope}
            onChange={(e) => setScope(e.target.value as LLMScope)}
          >
            {SCOPE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          {scope === "single_asset" ? (
            <input
              className="h-8 px-2 text-[11px] border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--ink-primary)] font-mono uppercase placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]"
              value={assetSymbol}
              onChange={(e) => setAssetSymbol(e.target.value.toUpperCase())}
            />
          ) : scope === "multi_asset" ? (
            <input
              className="h-8 px-2 text-[11px] border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--ink-primary)] font-mono uppercase placeholder:text-[var(--ink-dim)] outline-none focus:border-[var(--accent)]"
              value={symbolsText}
              onChange={(e) => setSymbolsText(e.target.value.toUpperCase())}
            />
          ) : (
            <div className="h-8 px-2 flex items-center text-[10px] text-[var(--ink-dim)] font-mono bg-[var(--bg-elevated)] border border-[var(--border-subtle)]">全市场模式</div>
          )}

          <button
            className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider bg-[var(--accent)] text-white disabled:opacity-30"
            onClick={doSummary}
            disabled={loadingSummary}
          >
            {loadingSummary ? "生成中…" : "生成摘要"}
          </button>
        </div>
      </div>

      {error && (
        <div className="px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono border border-[var(--border-subtle)]">{error}</div>
      )}

      {summary && (
        <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
          <div className="flex items-center justify-between h-8 px-3 border-b border-[var(--border-subtle)]">
            <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">SUMMARY</span>
            <span className="text-[9px] font-mono text-[var(--ink-dim)]">{summary.model || "unknown"}</span>
          </div>
          <p className="p-3 text-[11px] leading-relaxed text-[var(--ink-secondary)]">{summary.text}</p>
          {summary.warnings.length > 0 && (
            <div className="mx-3 mb-3 px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono bg-[var(--bg-elevated)]">
              {summary.warnings.map((w) => <p key={w}>{w}</p>)}
            </div>
          )}
        </div>
      )}

      {/* Chat form */}
      <div className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
        <div className="flex items-center justify-between h-8 px-3 border-b border-[var(--border-subtle)]">
          <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">RESEARCH CHAT</span>
          <button className="text-[9px] font-mono text-[var(--ink-dim)] hover:text-[var(--accent)]" onClick={() => setHistory([])}>CLEAR</button>
        </div>
        <form className="p-3 space-y-2" onSubmit={doAsk}>
          <textarea
            className="w-full min-h-16 p-2 text-[11px] leading-relaxed border border-[var(--border-subtle)] bg-[var(--bg-elevated)] text-[var(--ink-primary)] placeholder:text-[var(--ink-dim)] font-mono outline-none resize-y focus:border-[var(--accent)]"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="例如：当前全球资产主线是什么？"
          />
          <button
            className="h-8 px-4 text-[10px] font-bold uppercase tracking-wider bg-[var(--accent)] text-white disabled:opacity-30"
            disabled={loadingChat || !question.trim()}
          >
            {loadingChat ? "思考中…" : "ASK RABOT"}
          </button>
        </form>
      </div>

      {/* History */}
      <div className="space-y-1.5">
        {history.length === 0 && <div className="py-8 text-center text-[10px] text-[var(--ink-dim)] font-mono">暂无对话</div>}
        {history.map((item) => (
          <div key={item.id} className="border border-[var(--border-subtle)] bg-[var(--bg-card)]">
            <div className="flex items-center justify-between h-7 px-3 border-b border-[var(--border-subtle)]">
              <span className="text-[10px] font-semibold text-[var(--ink-primary)] truncate mr-2">{item.question}</span>
              <span className="text-[9px] font-mono text-[var(--ink-dim)] shrink-0">{item.createdAt}</span>
            </div>
            <p className="p-3 text-[11px] leading-relaxed text-[var(--ink-secondary)] whitespace-pre-wrap">{item.answer.text}</p>
            <div className="flex gap-2 px-3 pb-2">
              <span className="text-[9px] font-mono text-[var(--ink-dim)]">{item.answer.model || "unknown"}</span>
              <span className="text-[9px] font-mono text-[var(--ink-dim)]">{item.answer.ok ? "OK" : "FAIL"}</span>
            </div>
            {item.answer.warnings.length > 0 && (
              <div className="mx-3 mb-3 px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono bg-[var(--bg-elevated)]">
                {item.answer.warnings.map((w) => <p key={w}>{w}</p>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
