import { useEffect, useState } from "react";
import { fetchMarketDashboard, fetchMarketPerformance, MarketDashboardResponse, MarketPerformanceItem } from "../api/client";
import DataTable from "../components/DataTable";
import HeatList from "../components/HeatList";
import MetricCard from "../components/MetricCard";
import PageIntro from "../components/PageIntro";
import SectionCard from "../components/SectionCard";

function fmt(value: number | null): string {
  return value === null ? "--" : `${value.toFixed(2)}%`;
}

function DashboardPage() {
  const [data, setData] = useState<MarketDashboardResponse | null>(null);
  const [items, setItems] = useState<MarketPerformanceItem[]>([]);
  const [metric, setMetric] = useState<keyof MarketPerformanceItem>("return_1m");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMarketDashboard().then(setData).catch((exc) => setError(exc instanceof Error ? exc.message : "仪表盘读取失败。"));
    fetchMarketPerformance().then((response) => setItems(response.items)).catch((exc) => setError(exc instanceof Error ? exc.message : "热力榜读取失败。"));
  }, []);

  const sorted = [...items].sort((a, b) => Number(b[metric] ?? -999999) - Number(a[metric] ?? -999999));

  return (
    <div className="space-y-6">
      <PageIntro pageKey="dashboard" />

      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}

      {/* === 仪表盘 === */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard label="市场状态" value={data?.market_status === "connected" ? "已连接" : "待更新"} detail={data?.summary ?? "正在读取本地行情。"} />
        <MetricCard label="资产数量" value={String(data?.asset_count ?? 0)} detail="本地行情覆盖" />
        <MetricCard label="最新日期" value={data?.latest_date ?? "--"} detail="按资产最新日期汇总" />
        <MetricCard label="更新时间" value={data ? new Date(data.last_update).toLocaleTimeString() : "--:--"} detail="接口读取时间" />
      </div>
      <SectionCard title="总览判断" warnings={data?.warnings}>{data?.summary ?? "暂无总览。"}</SectionCard>
      <div className="grid gap-4 lg:grid-cols-2">
        <HeatList title="强势资产" items={data?.strong_assets ?? []} metric="return_1m" />
        <HeatList title="弱势资产" items={data?.weak_assets ?? []} metric="return_1m" />
        <HeatList title="高波动资产" items={data?.high_volatility_assets ?? []} metric="volatility_20d" />
        <HeatList title="高回撤资产" items={data?.high_drawdown_assets ?? []} metric="drawdown" />
      </div>

      {/* === 分隔 === */}
      <hr className="border-line" />

      {/* === 热力榜 === */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
        <h2 className="text-lg font-semibold text-ink">资产热力排行</h2>
        <select className="rounded-lg border border-line bg-panel px-3 py-2 text-sm" value={metric} onChange={(e) => setMetric(e.target.value as keyof MarketPerformanceItem)}>
          <option value="return_1w">近1周收益</option>
          <option value="return_1m">近1月收益</option>
          <option value="return_3m">近3月收益</option>
          <option value="return_ytd">YTD收益</option>
          <option value="return_1y">近1年收益</option>
          <option value="volatility_20d">20日波动率</option>
          <option value="drawdown">当前回撤</option>
        </select>
      </div>
      <HeatList title="资产热力排行" items={sorted.slice(0, 16)} metric={metric} />
      <DataTable
        rows={sorted}
        columns={[
          { key: "symbol", header: "代码", render: (row) => row.symbol },
          { key: "name", header: "名称", render: (row) => row.name ?? row.symbol },
          { key: "1w", header: "近1周", render: (row) => fmt(row.return_1w) },
          { key: "1m", header: "近1月", render: (row) => fmt(row.return_1m) },
          { key: "3m", header: "近3月", render: (row) => fmt(row.return_3m) },
          { key: "vol", header: "波动率", render: (row) => fmt(row.volatility_20d) },
          { key: "dd", header: "回撤", render: (row) => fmt(row.drawdown) },
          { key: "risk", header: "风险", render: (row) => row.risk_level ?? "--" }
        ]}
      />
    </div>
  );
}

export default DashboardPage;
