import { useEffect, useMemo, useState } from "react";
import {
  MarketPerformanceItem,
  MultiAssetResponse,
  fetchMarketPerformance,
  fetchMultiAssetResearch
} from "../api/client";
import DataTable from "../components/DataTable";
import LineChart from "../components/LineChart";
import PageIntro from "../components/PageIntro";
import ResearchChatPanel from "../components/ResearchChatPanel";

const defaultSymbols = ["NASDAQ", "SP500", "CSI300", "SSE", "HSI", "GOLD", "DXY"];

function fmt(value: number | null): string {
  return value === null ? "--" : `${value.toFixed(2)}%`;
}

function defaultStartDate(): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

function MultiAssetPage({ useLlm }: { useLlm: boolean }) {
  const [assets, setAssets] = useState<MarketPerformanceItem[]>([]);
  const [selected, setSelected] = useState<string[]>(defaultSymbols);
  const [start, setStart] = useState(defaultStartDate());
  const [end, setEnd] = useState("");
  const [data, setData] = useState<MultiAssetResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketPerformance()
      .then((response) => {
        setAssets(response.items);
        const availableSymbols = new Set(response.items.map((item) => item.symbol));
        const next = defaultSymbols.filter((symbol) => availableSymbols.has(symbol));
        if (next.length) setSelected(next);
      })
      .catch(() => setAssets([]));
  }, []);

  const symbols = useMemo(() => selected.filter(Boolean), [selected]);

  const toggleSymbol = (symbol: string) => {
    setSelected((items) => items.includes(symbol) ? items.filter((item) => item !== symbol) : [...items, symbol]);
  };

  const load = () => {
    setError(null);
    fetchMultiAssetResearch(symbols, start || undefined, end || undefined)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "多资产研究读取失败。"));
  };

  useEffect(() => {
    load();
  }, []);

  const corrColumns = data?.symbols.map((symbol) => ({
    key: symbol,
    header: symbol,
    render: (row: Record<string, string | number | null>) => {
      const value = row[symbol];
      return typeof value === "number" ? value.toFixed(2) : String(value ?? "--");
    }
  })) ?? [];

  return (
    <div className="space-y-6">
      <PageIntro pageKey="multi" />
      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="grid gap-4 lg:grid-cols-[1fr_160px_160px_auto]">
          <div className="space-y-2">
            <span className="text-sm font-medium text-ink">资产库多选</span>
            <div className="max-h-36 overflow-auto rounded-lg border border-line bg-[var(--bg-card)] p-2">
              <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {(assets.length ? assets : defaultSymbols.map((symbol) => ({ symbol, name: symbol } as MarketPerformanceItem))).map((asset) => (
                  <label key={asset.symbol} className="flex cursor-pointer items-center gap-2 rounded-md px-2 py-1 text-sm hover:bg-[var(--bg-card-hover)]">
                    <input type="checkbox" checked={selected.includes(asset.symbol)} onChange={() => toggleSymbol(asset.symbol)} />
                    <span className="font-medium text-ink">{asset.symbol}</span>
                    <span className="truncate text-muted">{asset.name ?? asset.symbol}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">开始日期</span>
            <input className="w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm" type="date" value={start} onChange={(event) => setStart(event.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">结束日期</span>
            <input className="w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm" type="date" value={end} onChange={(event) => setEnd(event.target.value)} />
          </label>
          <div className="flex items-end">
            <button className="primary-button w-full" onClick={load} disabled={!symbols.length}>刷新对比</button>
          </div>
        </div>
      </section>
      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}
      <LineChart points={data?.normalized_series ?? []} symbols={symbols} valueKey="normalized" />
      <DataTable<MarketPerformanceItem>
        rows={data?.performance ?? []}
        columns={[
          { key: "symbol", header: "代码", render: (row) => row.symbol },
          { key: "name", header: "名称", render: (row) => row.name ?? row.symbol },
          { key: "1m", header: "近1月", render: (row) => fmt(row.return_1m) },
          { key: "3m", header: "近3月", render: (row) => fmt(row.return_3m) },
          { key: "vol", header: "波动率", render: (row) => fmt(row.volatility_20d) },
          { key: "dd", header: "回撤", render: (row) => fmt(row.drawdown) }
        ]}
      />
      <DataTable<Record<string, string | number | null>>
        rows={data?.correlation ?? []}
        columns={[{ key: "symbol", header: "相关性", render: (row) => row.symbol }, ...corrColumns]}
        emptyText="暂无相关性矩阵。"
      />
      <ResearchChatPanel
        title="多资产大模型交互分析"
        scope="multi_asset"
        symbols={data?.symbols ?? symbols}
        useLlm={useLlm}
        placeholder="例如：这组资产当前谁更强？相关性和主要风险点在哪里？"
      />
    </div>
  );
}

export default MultiAssetPage;
