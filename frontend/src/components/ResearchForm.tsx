import { FormEvent, useEffect, useState } from "react";
import { ResearchGenerateRequest } from "../api/client";

interface ResearchFormProps {
  submitting: boolean;
  defaultUseLlm: boolean;
  onSubmit: (payload: ResearchGenerateRequest) => void;
}

const sectionOptions = [
  { value: "market", label: "市场" },
  { value: "news", label: "新闻" },
  { value: "macro", label: "宏观" },
  { value: "strategy", label: "策略" }
];

const targetOptions = [
  { value: "market_overview", label: "市场总览" },
  { value: "stock_analysis", label: "个股分析" },
  { value: "fund_analysis", label: "基金/ETF 分析" },
  { value: "portfolio_overview", label: "组合总览" }
];

function ResearchForm({ submitting, defaultUseLlm, onSubmit }: ResearchFormProps) {
  const [target, setTarget] = useState("market_overview");
  const [symbol, setSymbol] = useState("QQQ.US");
  const [reportStyle, setReportStyle] = useState("券商研报风");
  const [useLlm, setUseLlm] = useState(defaultUseLlm);
  const [sections, setSections] = useState(["market", "news", "macro", "strategy"]);
  const [extraInstruction, setExtraInstruction] = useState("");

  useEffect(() => {
    setUseLlm(defaultUseLlm);
  }, [defaultUseLlm]);

  const toggleSection = (value: string) => {
    setSections((current) =>
      current.includes(value) ? current.filter((item) => item !== value) : [...current, value]
    );
  };

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit({
      target,
      index_symbol: null,
      symbol: target === "fund_analysis" || target === "stock_analysis" ? symbol : null,
      report_style: reportStyle,
      use_llm: useLlm,
      sections,
      extra_instruction: extraInstruction
    });
  };

  return (
    <form className="rounded-lg border border-line bg-panel p-5 shadow-soft" onSubmit={handleSubmit}>
      <div>
        <p className="text-sm font-medium text-brand">Research Generator</p>
        <h2 className="mt-1 text-xl font-semibold text-ink">生成研究报告</h2>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <label className="block text-sm">
          <span className="font-medium text-ink">报告类型</span>
          <select
            className="mt-2 w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand"
            value={target}
            onChange={(event) => setTarget(event.target.value)}
          >
            {targetOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </label>

        <label className="block text-sm">
          <span className="font-medium text-ink">研究风格</span>
          <input
            className="mt-2 w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand"
            value={reportStyle}
            onChange={(event) => setReportStyle(event.target.value)}
          />
        </label>
      </div>

      {target === "fund_analysis" || target === "stock_analysis" ? (
        <label className="mt-5 block text-sm">
          <span className="font-medium text-ink">{target === "fund_analysis" ? "基金/ETF 代码" : "股票代码"}</span>
          <input
            className="mt-2 w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand"
            value={symbol}
            onChange={(event) => setSymbol(event.target.value)}
            placeholder={target === "fund_analysis" ? "如 510300.SH / QQQ.US / 2800.HK" : "如 600519.SH / TSLA.US / 700.HK"}
          />
        </label>
      ) : null}

      <div className="mt-5">
        <p className="text-sm font-medium text-ink">报告板块</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {sectionOptions.map((option) => (
            <label key={option.value} className="flex cursor-pointer items-center gap-2 rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm text-muted">
              <input type="checkbox" checked={sections.includes(option.value)} onChange={() => toggleSection(option.value)} />
              {option.label}
            </label>
          ))}
        </div>
      </div>

      <div className="mt-5 rounded-lg border border-line bg-[var(--bg-card)] p-3">
        <div className="flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-ink">调用大模型</p>
            <p className="mt-1 text-xs text-muted">跟随右侧隐藏栏的全局设置，也可以本次单独调整。</p>
          </div>
          <button type="button" className={useLlm ? "toggle-switch toggle-switch-on" : "toggle-switch"} onClick={() => setUseLlm(!useLlm)} aria-pressed={useLlm}>
            <span />
          </button>
        </div>
      </div>

      <label className="mt-5 block text-sm">
        <span className="font-medium text-ink">额外要求</span>
        <textarea
          className="mt-2 min-h-28 w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm leading-6 outline-none focus:border-brand"
          value={extraInstruction}
          onChange={(event) => setExtraInstruction(event.target.value)}
          placeholder="例如：更关注风险提示和数据缺口，结论要更凝练。"
        />
      </label>

      <button className="primary-button mt-5 w-full md:w-auto" type="submit" disabled={submitting}>
        {submitting ? "任务提交中..." : "生成研究报告"}
      </button>
    </form>
  );
}

export default ResearchForm;
