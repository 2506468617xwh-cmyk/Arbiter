import { useEffect, useMemo, useState } from "react";
import {
  AssetResearchResponse,
  MarketPerformanceItem,
  fetchAssetResearch,
  fetchMarketPerformance
} from "../api/client";
import DataTable from "../components/DataTable";
import LineChart from "../components/LineChart";
import MetricCard from "../components/MetricCard";
import PageIntro from "../components/PageIntro";
import ResearchChatPanel from "../components/ResearchChatPanel";
import SectionCard from "../components/SectionCard";

function textValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "--";
  if (typeof value === "number") return value.toFixed(2);
  if (Array.isArray(value)) return value.join("，");
  if (typeof value === "object") return JSON.stringify(value, null, 2);
  return String(value);
}

function defaultStartDate(): string {
  const date = new Date();
  date.setMonth(date.getMonth() - 12);
  return date.toISOString().slice(0, 10);
}

function AssetResearchPage({ useLlm }: { useLlm: boolean }) {
  const [assets, setAssets] = useState<MarketPerformanceItem[]>([]);
  const [symbol, setSymbol] = useState("NASDAQ");
  const [start, setStart] = useState(defaultStartDate());
  const [end, setEnd] = useState("");
  const [data, setData] = useState<AssetResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketPerformance()
      .then((response) => {
        setAssets(response.items);
        if (response.items.length && !response.items.some((item) => item.symbol === symbol)) {
          setSymbol(response.items[0].symbol);
        }
      })
      .catch(() => setAssets([]));
  }, []);

  const selectedName = useMemo(
    () => assets.find((item) => item.symbol === symbol)?.name ?? symbol,
    [assets, symbol]
  );

  const load = () => {
    setError(null);
    fetchAssetResearch(symbol, start || undefined, end || undefined)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "单资产研究读取失败。"));
  };

  useEffect(() => {
    load();
  }, []);

  const tech = data?.technical ?? {};

  return (
    <div className="space-y-6">
      <PageIntro pageKey="asset" />
      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="grid gap-4 lg:grid-cols-[1fr_160px_160px_auto]">
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">资产库</span>
            <select
              className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm"
              value={symbol}
              onChange={(event) => setSymbol(event.target.value)}
            >
              {assets.length ? assets.map((asset) => (
                <option key={asset.symbol} value={asset.symbol}>
                  {asset.symbol} · {asset.name ?? asset.symbol}
                </option>
              )) : (
                <option value={symbol}>{symbol} · {selectedName}</option>
              )}
            </select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">开始日期</span>
            <input className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm" type="date" value={start} onChange={(event) => setStart(event.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">结束日期</span>
            <input className="w-full rounded-lg border border-line bg-white px-3 py-2 text-sm" type="date" value={end} onChange={(event) => setEnd(event.target.value)} />
          </label>
          <div className="flex items-end">
            <button className="primary-button w-full" onClick={load}>读取资产研究</button>
          </div>
        </div>
      </section>
      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="资产" value={data?.symbol ?? symbol} detail={data?.name ?? selectedName} />
        <MetricCard label="评分" value={textValue(tech.score)} detail={textValue(tech.grade)} />
        <MetricCard label="趋势" value={textValue(data?.market?.trend_signal)} detail={textValue(data?.market?.risk_level)} />
        <MetricCard label="最新日期" value={data?.latest_date ?? "--"} detail="本地行情最新记录" />
      </div>
      <SectionCard title="RAbot 研究结论" warnings={data?.warnings}>
        {textValue(tech.summary)}
      </SectionCard>
      <LineChart points={data?.series ?? []} symbols={[data?.symbol ?? symbol]} valueKey="close" />
      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard title="行动提示">{textValue(tech.action_hint)}</SectionCard>
        <SectionCard title="观察点">
          {Array.isArray(tech.watch_points) ? tech.watch_points.map((item) => <p key={String(item)}>{String(item)}</p>) : "--"}
        </SectionCard>
      </div>
      <DataTable
        rows={data?.related_news ?? []}
        columns={[
          { key: "title", header: "相关新闻", render: (row) => row.title },
          { key: "source", header: "来源", render: (row) => row.source ?? "--" },
          { key: "score", header: "评分", render: (row) => row.quality_score ?? row.importance_score ?? "--" }
        ]}
      />
      <ResearchChatPanel
        title="单资产大模型交互分析"
        scope="single_asset"
        assetSymbol={data?.symbol ?? symbol}
        useLlm={useLlm}
        placeholder="例如：这个资产当前主要矛盾是什么？技术面和宏观面是否一致？"
      />
    </div>
  );
}

export default AssetResearchPage;
