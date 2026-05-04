import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  MacroAnalysisResponse,
  MacroSnapshotItem,
  MacroSeriesPoint,
  analyzeMacro,
  fetchMacroSeries,
  fetchMacroSnapshot
} from "../api/client";
import DataTable from "../components/DataTable";
import MacroLineChart from "../components/MacroLineChart";
import MetricCard from "../components/MetricCard";
import ResearchPet from "../components/ResearchPet";
import { useI18n } from "../i18n";

function fmt(value: number | null | undefined): string {
  return value === null || value === undefined ? "--" : value.toFixed(2);
}

function MacroResearchPage({ useLlm }: { useLlm: boolean }) {
  const { language, page } = useI18n();
  const [snapshot, setSnapshot] = useState<MacroSnapshotItem[]>([]);
  const [series, setSeries] = useState<MacroSeriesPoint[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [region, setRegion] = useState("");
  const [category, setCategory] = useState("");
  const [warnings, setWarnings] = useState<string[]>([]);
  const [question, setQuestion] = useState("当前全球宏观环境的核心矛盾是什么？");
  const [answer, setAnswer] = useState<MacroAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isEn = language === "en";
  const copy = {
    refresh: isEn ? "Refresh macro data" : "刷新宏观数据",
    refreshing: isEn ? "Refreshing..." : "刷新中...",
    indicators: isEn ? "Indicators" : "宏观指标",
    regions: isEn ? "Regions" : "地区数",
    categories: isEn ? "Categories" : "类别数",
    latestDate: isEn ? "Latest date" : "最新日期",
    allRegions: isEn ? "All regions" : "全部地区",
    allCategories: isEn ? "All categories" : "全部类别",
    apply: isEn ? "Apply filters" : "应用筛选",
    localSeries: isEn ? "Local macro_series" : "本地 macro_series",
    macroCoverage: isEn ? "Local macro coverage" : "本地宏观覆盖",
    tableEmpty: isEn ? "No macro snapshot yet. You can run scripts/update_macro.py first." : "暂无宏观快照。可以先运行 scripts/update_macro.py。",
    chatTitle: isEn ? "Macro LLM interaction" : "宏观大模型交互分析",
    submit: isEn ? "Generate macro analysis" : "生成宏观分析",
    analyzing: isEn ? "Analyzing..." : "分析中...",
    llmOn: isEn ? "LLM on" : "LLM 已开启",
    llmOff: isEn ? "LLM off" : "LLM 已关闭"
  };

  const loadSnapshot = () => {
    setLoading(true);
    setError(null);
    fetchMacroSnapshot(region || undefined, category || undefined)
      .then((response) => {
        setSnapshot(response.items);
        setWarnings(response.warnings);
        const defaults = response.items.slice(0, 4).map((item) => item.symbol);
        setSelected((current) => current.length ? current.filter((symbol) => response.items.some((item) => item.symbol === symbol)) : defaults);
      })
      .catch((exc) => setError(exc instanceof Error ? exc.message : "宏观快照读取失败。"))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadSnapshot();
  }, []);

  useEffect(() => {
    if (!selected.length) {
      setSeries([]);
      return;
    }
    fetchMacroSeries(selected)
      .then((response) => {
        setSeries(response.items);
        setWarnings((items) => [...items, ...response.warnings]);
      })
      .catch(() => setSeries([]));
  }, [selected.join(",")]);

  const regions = useMemo(() => Array.from(new Set(snapshot.map((item) => item.region).filter(Boolean))) as string[], [snapshot]);
  const categories = useMemo(() => Array.from(new Set(snapshot.map((item) => item.category).filter(Boolean))) as string[], [snapshot]);
  const latestDates = snapshot.map((item) => item.latest_date).filter((item): item is string => Boolean(item)).sort();
  const latestDate = latestDates.length ? latestDates[latestDates.length - 1] : "--";

  const toggleSymbol = (symbol: string) => {
    setSelected((items) => items.includes(symbol) ? items.filter((item) => item !== symbol) : [...items, symbol].slice(-6));
  };

  const submitQuestion = (event: FormEvent) => {
    event.preventDefault();
    setChatLoading(true);
    setError(null);
    analyzeMacro({ question, symbols: selected, use_llm: useLlm })
      .then(setAnswer)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "宏观分析失败。"))
      .finally(() => setChatLoading(false));
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-sm font-medium text-brand">{page.macro.eyebrow}</p>
          <h1 className="mt-2 text-3xl font-semibold text-ink">{page.macro.title}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted">{page.macro.subtitle}</p>
        </div>
        <div className="flex flex-col items-start gap-3 md:items-end">
          <ResearchPet
            pageName="macro"
            useLlm={useLlm}
            context={{
              title: page.macro.title,
              subtitle: page.macro.subtitle,
              selected_symbols: selected,
              latest_date: latestDate,
              indicator_count: snapshot.length,
              warnings
            }}
          />
          <button className="primary-button" onClick={loadSnapshot} disabled={loading}>{loading ? copy.refreshing : copy.refresh}</button>
        </div>
      </div>

      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}
      {warnings.length ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
          {Array.from(new Set(warnings)).map((warning) => <p key={warning}>{warning}</p>)}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label={copy.indicators} value={String(snapshot.length)} detail={copy.localSeries} />
        <MetricCard label={copy.regions} value={String(regions.length)} detail={regions.join(" / ") || "--"} />
        <MetricCard label={copy.categories} value={String(categories.length)} detail={isEn ? "Growth, inflation, rates" : "增长、通胀、利率等"} />
        <MetricCard label={copy.latestDate} value={latestDate} detail={copy.macroCoverage} />
      </div>

      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="grid gap-4 md:grid-cols-[180px_220px_auto]">
          <select className="rounded-lg border border-line bg-white px-3 py-2 text-sm" value={region} onChange={(event) => setRegion(event.target.value)}>
            <option value="">{copy.allRegions}</option>
            {regions.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <select className="rounded-lg border border-line bg-white px-3 py-2 text-sm" value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="">{copy.allCategories}</option>
            {categories.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
          <button className="secondary-button" onClick={loadSnapshot}>{copy.apply}</button>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {snapshot.slice(0, 30).map((item) => (
            <button
              key={item.symbol}
              className={`rounded-full border px-3 py-1 text-xs ${selected.includes(item.symbol) ? "border-brand bg-[#fff7ed] text-brand" : "border-line bg-[#fffaf2] text-muted"}`}
              onClick={() => toggleSymbol(item.symbol)}
            >
              {item.name || item.symbol}
            </button>
          ))}
        </div>
      </section>

      <MacroLineChart points={series} symbols={selected} />

      <DataTable<MacroSnapshotItem>
        rows={snapshot}
        columns={[
          { key: "name", header: isEn ? "Indicator" : "指标", render: (row) => row.name ?? row.symbol },
          { key: "region", header: isEn ? "Region" : "地区", render: (row) => row.region ?? "--" },
          { key: "category", header: isEn ? "Category" : "类别", render: (row) => row.category ?? "--" },
          { key: "date", header: isEn ? "Latest date" : "最新日期", render: (row) => row.latest_date ?? "--" },
          { key: "value", header: isEn ? "Latest value" : "最新值", render: (row) => fmt(row.latest_value) },
          { key: "change3m", header: isEn ? "3M change" : "3月变化", render: (row) => fmt(row.change_3m) },
          { key: "trend", header: isEn ? "Trend" : "趋势", render: (row) => row.trend_label ?? "--" },
          { key: "risk", header: isEn ? "Risk" : "风险标签", render: (row) => row.risk_label ?? "--" }
        ]}
        emptyText={copy.tableEmpty}
      />

      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-lg font-semibold text-ink">{copy.chatTitle}</h2>
          <span className="text-xs text-muted">{useLlm ? copy.llmOn : copy.llmOff}</span>
        </div>
        <form className="mt-4 space-y-3" onSubmit={submitQuestion}>
          <textarea className="min-h-24 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm leading-6 outline-none focus:border-brand" value={question} onChange={(event) => setQuestion(event.target.value)} />
          <div className="flex justify-end"><button className="primary-button" disabled={chatLoading}>{chatLoading ? copy.analyzing : copy.submit}</button></div>
        </form>
        {answer ? (
          <div className="mt-4 rounded-lg border border-line bg-[#fffdf8] p-4">
            <p className="whitespace-pre-wrap text-sm leading-7 text-muted">{answer.text}</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}

export default MacroResearchPage;
