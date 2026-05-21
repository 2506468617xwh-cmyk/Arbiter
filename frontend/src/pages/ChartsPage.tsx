import { useEffect, useMemo, useState } from "react";
import { fetchMarketPerformance, fetchMarketTimeseries, MarketPerformanceItem, MarketSeriesPoint } from "../api/client";
import LineChart from "../components/LineChart";
import PageIntro from "../components/PageIntro";

const defaultSymbols = ["NASDAQ", "SP500", "CSI300", "SSE", "HSI", "GOLD", "DXY"];

function defaultStartDate(): string {
  const date = new Date();
  date.setFullYear(date.getFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

function ChartsPage() {
  const [assets, setAssets] = useState<MarketPerformanceItem[]>([]);
  const [selected, setSelected] = useState<string[]>(defaultSymbols);
  const [start, setStart] = useState(defaultStartDate());
  const [end, setEnd] = useState("");
  const [points, setPoints] = useState<MarketSeriesPoint[]>([]);
  const [valueKey, setValueKey] = useState<"close" | "normalized" | "drawdown">("normalized");
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
    setSelected((items) =>
      items.includes(symbol) ? items.filter((item) => item !== symbol) : [...items, symbol]
    );
  };

  const load = () => {
    setError(null);
    fetchMarketTimeseries(symbols, valueKey === "normalized", start || undefined, end || undefined)
      .then((response) => setPoints(response.items))
      .catch((exc) => setError(exc instanceof Error ? exc.message : "走势图读取失败。"));
  };

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="space-y-6">
      <PageIntro pageKey="charts" />
      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="grid gap-4 lg:grid-cols-[1fr_180px_150px_150px_auto]">
          <div className="space-y-2">
            <span className="text-sm font-medium text-ink">资产库多选</span>
            <div className="max-h-32 overflow-auto rounded-lg border border-line bg-[var(--bg-card)] p-2">
              <div className="grid gap-2 sm:grid-cols-2">
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
            <span className="font-medium text-ink">指标</span>
            <select className="w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm" value={valueKey} onChange={(e) => setValueKey(e.target.value as "close" | "normalized" | "drawdown")}>
              <option value="normalized">归一化走势</option>
              <option value="close">收盘价</option>
              <option value="drawdown">回撤</option>
            </select>
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">开始日期</span>
            <input className="w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm" type="date" value={start} onChange={(event) => setStart(event.target.value)} />
          </label>
          <label className="space-y-2 text-sm">
            <span className="font-medium text-ink">结束日期</span>
            <input className="w-full rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm" type="date" value={end} onChange={(event) => setEnd(event.target.value)} />
          </label>
          <div className="flex items-end">
            <button className="primary-button w-full" onClick={load} disabled={!symbols.length}>刷新走势</button>
          </div>
        </div>
      </section>
      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}
      <LineChart points={points} symbols={symbols} valueKey={valueKey} />
    </div>
  );
}

export default ChartsPage;
