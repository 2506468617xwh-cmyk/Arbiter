import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  LLMResponse,
  LLMScope,
  MarketPerformanceItem,
  askResearchChat,
  fetchMarketPerformance,
  generateQuickSummary
} from "../api/client";
import SectionCard from "../components/SectionCard";

interface AIResearchPageProps {
  useLlm: boolean;
  onOpenModelSettings: () => void;
}

interface ChatItem {
  id: string;
  question: string;
  answer: LLMResponse;
  createdAt: string;
}

const scopeOptions: Array<{ value: LLMScope; label: string }> = [
  { value: "market", label: "全市场" },
  { value: "single_asset", label: "单资产" },
  { value: "multi_asset", label: "多资产组合" }
];

function splitSymbols(raw: string): string[] {
  return raw
    .split(/[,，\s]+/)
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean);
}

function AIResearchPage({ useLlm, onOpenModelSettings }: AIResearchPageProps) {
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
    fetchMarketPerformance()
      .then((result) => setAvailable(result.items))
      .catch(() => setAvailable([]));
  }, []);

  const symbols = useMemo(() => splitSymbols(symbolsText), [symbolsText]);

  const payloadBase = {
    scope,
    asset_symbol: scope === "single_asset" ? assetSymbol.trim().toUpperCase() : null,
    symbols: scope === "multi_asset" ? symbols : [],
    use_llm: useLlm
  };

  const handleQuickSummary = async () => {
    setError(null);
    setLoadingSummary(true);
    try {
      const result = await generateQuickSummary(payloadBase);
      setSummary(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "一句话总结生成失败。");
    } finally {
      setLoadingSummary(false);
    }
  };

  const handleAsk = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoadingChat(true);
    try {
      const result = await askResearchChat({ ...payloadBase, question });
      setHistory((items) => [
        {
          id: `${Date.now()}`,
          question,
          answer: result,
          createdAt: new Date().toLocaleString()
        },
        ...items
      ].slice(0, 10));
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "AI 研究对话失败。");
    } finally {
      setLoadingChat(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">LLM Research Analyst</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">AI 研究</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">
            复刻旧版 AI 快评和 AI 研究对话：先由 RAbot 构造本地行情、新闻、宏观和规则层事实包，再交给 DeepSeek OpenAI-compatible 接口回答。
          </p>
        </div>
        <button className="secondary-button" onClick={onOpenModelSettings}>
          模型设置
        </button>
      </div>

      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="grid gap-4 lg:grid-cols-[1fr_1fr_auto]">
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">研究范围</span>
            <select
              className="w-full rounded-lg border border-line bg-white px-3 py-2"
              value={scope}
              onChange={(event) => setScope(event.target.value as LLMScope)}
            >
              {scopeOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>

          {scope === "single_asset" ? (
            <label className="space-y-2 text-sm">
              <span className="font-medium text-ink">资产代码</span>
              <input
                className="w-full rounded-lg border border-line bg-white px-3 py-2 uppercase"
                value={assetSymbol}
                onChange={(event) => setAssetSymbol(event.target.value.toUpperCase())}
                list="asset-symbols"
              />
            </label>
          ) : scope === "multi_asset" ? (
            <label className="space-y-2 text-sm">
              <span className="font-medium text-ink">组合标的</span>
              <input
                className="w-full rounded-lg border border-line bg-white px-3 py-2 uppercase"
                value={symbolsText}
                onChange={(event) => setSymbolsText(event.target.value.toUpperCase())}
              />
            </label>
          ) : (
            <div className="rounded-lg border border-line bg-[#fffaf2] p-3 text-sm leading-6 text-muted">
              全市场模式会读取本地市场、新闻、宏观和规则研究事实包。
            </div>
          )}

          <div className="flex items-end">
            <button className="primary-button w-full" onClick={handleQuickSummary} disabled={loadingSummary}>
              {loadingSummary ? "生成中..." : "生成一句话总结"}
            </button>
          </div>
        </div>
        <datalist id="asset-symbols">
          {available.map((item) => (
            <option key={item.symbol} value={item.symbol}>
              {item.name ?? item.symbol}
            </option>
          ))}
        </datalist>
        <div className="mt-4 flex items-center justify-between rounded-lg border border-line bg-[#fffdf8] p-3 text-sm">
          <span className="text-muted">大模型调用</span>
          <span className={useLlm ? "font-semibold text-brand" : "font-semibold text-muted"}>
            {useLlm ? "已开启" : "已关闭"}
          </span>
        </div>
      </section>

      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}

      {summary ? (
        <SectionCard title="大模型一句话总结" warnings={summary.warnings}>
          <p className="text-base font-medium leading-8 text-ink">{summary.text}</p>
          <p className="mt-3 text-xs text-muted">模型：{summary.model ?? "未调用大模型"}</p>
        </SectionCard>
      ) : null}

      <form className="rounded-lg border border-line bg-panel p-5 shadow-soft" onSubmit={handleAsk}>
        <div className="flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold text-ink">AI 研究对话</h2>
            <p className="mt-1 text-sm text-muted">问题会和当前研究范围一起提交给 RAbot 本地事实包。</p>
          </div>
          <button className="secondary-button" type="button" onClick={() => setHistory([])}>
            清空对话
          </button>
        </div>
        <textarea
          className="mt-4 min-h-28 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-brand"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="例如：当前全球资产主线是什么？美股和黄金哪个风险更需要关注？"
        />
        <div className="mt-4 flex justify-end">
          <button className="primary-button" disabled={loadingChat || !question.trim()}>
            {loadingChat ? "RAbot 思考中..." : "询问 RAbot"}
          </button>
        </div>
      </form>

      <section className="space-y-4">
        {history.length === 0 ? (
          <div className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">
            暂无对话。你可以先问一个全市场问题，例如：当前全球资产主线是什么？
          </div>
        ) : (
          history.map((item) => (
            <article key={item.id} className="rounded-lg border border-line bg-panel p-5 shadow-soft">
              <div className="flex flex-col gap-1 border-b border-line pb-3 text-sm md:flex-row md:items-center md:justify-between">
                <p className="font-semibold text-ink">{item.question}</p>
                <p className="text-xs text-muted">{item.createdAt}</p>
              </div>
              <div className="mt-4 whitespace-pre-wrap text-sm leading-7 text-muted">{item.answer.text}</div>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-muted">
                <span className="rounded-full border border-line bg-[#fffaf2] px-2 py-1">
                  {item.answer.ok ? "LLM 成功" : "未成功"}
                </span>
                <span className="rounded-full border border-line bg-[#fffaf2] px-2 py-1">
                  {item.answer.model ?? "无模型"}
                </span>
              </div>
              {item.answer.warnings.length ? (
                <div className="mt-4 rounded-lg border border-amber-200 bg-amber-50 p-3 text-xs leading-6 text-amber-900">
                  {item.answer.warnings.map((warning) => (
                    <p key={warning}>{warning}</p>
                  ))}
                </div>
              ) : null}
            </article>
          ))
        )}
      </section>
    </div>
  );
}

export default AIResearchPage;
