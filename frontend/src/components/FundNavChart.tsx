import { MouseEvent, useMemo, useRef, useState } from "react";
import { FundBar } from "../api/client";

const width = 780;
const height = 240;
const margin = { top: 14, right: 20, bottom: 34, left: 52 };

interface Active {
  date: string;
  x: number;
  fund: number | null;
  ma20: number | null;
  ma60: number | null;
  benchmark: number | null;
  raw: number | null;
}

function FundNavChart({
  bars,
  benchmarkBars = [],
  benchmarkName = "大盘基准"
}: {
  bars: FundBar[];
  benchmarkBars?: FundBar[];
  benchmarkName?: string | null;
}) {
  const [active, setActive] = useState<Active | null>(null);
  const lastDate = useRef<string | null>(null);
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const data = useMemo(() => {
    const rawRows = priceRows(bars).slice(-260);
    const fundRows = normalizeRows(rawRows);
    const benchmarkMap = new Map(normalizeRows(priceRows(benchmarkBars)).map((row) => [row.date, row.value]));
    const rawMap = new Map(rawRows.map((row) => [row.date, row.value]));
    const rows = fundRows.map((row, index) => {
      const ma20 = index >= 19 ? avg(fundRows.slice(index - 19, index + 1).map((item) => item.value)) : null;
      const ma60 = index >= 59 ? avg(fundRows.slice(index - 59, index + 1).map((item) => item.value)) : null;
      return { ...row, raw: rawMap.get(row.date) ?? null, ma20, ma60, benchmark: benchmarkMap.get(row.date) ?? null };
    });
    const values = rows.flatMap((row) => [row.value, row.ma20, row.ma60, row.benchmark]).filter((value): value is number => value !== null && !Number.isNaN(value));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const pad = (max - min || 1) * 0.08;
    return { rows, min: min - pad, max: max + pad };
  }, [bars, benchmarkBars]);

  if (!data.rows.length) {
    return <section className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">暂无可绘制的净值/价格曲线。</section>;
  }

  const xFor = (index: number) => margin.left + (data.rows.length <= 1 ? 0 : (index / (data.rows.length - 1)) * innerWidth);
  const yFor = (value: number) => margin.top + innerHeight - ((value - data.min) / (data.max - data.min || 1)) * innerHeight;
  const pathFor = (key: "value" | "ma20" | "ma60" | "benchmark") =>
    data.rows
      .map((row, index) => {
        const value = row[key];
        if (value === null) return "";
        return `${index === 0 ? "M" : "L"}${xFor(index).toFixed(1)},${yFor(value).toFixed(1)}`;
      })
      .filter(Boolean)
      .join(" ");

  const updateActive = (clientX: number, svg: SVGSVGElement) => {
    const rect = svg.getBoundingClientRect();
    const svgX = ((clientX - rect.left) / rect.width) * width;
    const index = Math.max(0, Math.min(data.rows.length - 1, Math.round(((svgX - margin.left) / innerWidth) * (data.rows.length - 1))));
    const row = data.rows[index];
    if (row.date === lastDate.current) return;
    lastDate.current = row.date;
    setActive({ date: row.date, x: xFor(index), fund: row.value, ma20: row.ma20, ma60: row.ma60, benchmark: row.benchmark, raw: row.raw });
  };

  const ticks = [data.min, data.min + (data.max - data.min) / 2, data.max];
  const xTicks = [0, Math.floor(data.rows.length / 2), data.rows.length - 1];

  return (
    <section className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xs font-semibold text-ink">基金/ETF vs 大盘走势</h2>
        <p className="text-xs text-muted">归一化表现，起点 = 100</p>
      </div>
      <div className="relative mt-4 overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="min-w-[640px] touch-pan-y select-none"
          onMouseMove={(event: MouseEvent<SVGSVGElement>) => updateActive(event.clientX, event.currentTarget)}
          onMouseLeave={() => { lastDate.current = null; setActive(null); }}
          onClick={(event) => updateActive(event.clientX, event.currentTarget)}
        >
          <rect width={width} height={height} fill="var(--bg-card)" />
          {ticks.map((tick) => {
            const y = yFor(tick);
            return (
              <g key={tick}>
                <line x1={margin.left} y1={y} x2={width - margin.right} y2={y} stroke="var(--border-card)" />
                <text x={margin.left - 10} y={y + 4} textAnchor="end" fontSize="11" fill="var(--ink-muted)">{tick.toFixed(1)}</text>
              </g>
            );
          })}
          <line x1={margin.left} y1={margin.top} x2={margin.left} y2={height - margin.bottom} stroke="var(--border-card)" />
          <line x1={margin.left} y1={height - margin.bottom} x2={width - margin.right} y2={height - margin.bottom} stroke="var(--border-card)" />
          {xTicks.map((index) => {
            const row = data.rows[index];
            if (!row) return null;
            const x = xFor(index);
            return <text key={row.date} x={x} y={height - 18} textAnchor="middle" fontSize="11" fill="var(--ink-muted)">{row.date.slice(5)}</text>;
          })}
          <path d={pathFor("value")} fill="none" stroke="#d97706" strokeWidth="2.4" />
          <path d={pathFor("benchmark")} fill="none" stroke="#7c3aed" strokeWidth="2" strokeDasharray="6 4" />
          <path d={pathFor("ma20")} fill="none" stroke="#2563eb" strokeWidth="1.4" />
          <path d={pathFor("ma60")} fill="none" stroke="#16a34a" strokeWidth="1.4" />
          {active ? <line x1={active.x} y1={margin.top} x2={active.x} y2={height - margin.bottom} stroke="var(--ink-dim)" strokeDasharray="4 4" /> : null}
        </svg>
        {active ? (
          <div className="pointer-events-none absolute top-4 rounded-lg border border-line bg-panel p-3 text-xs shadow-soft" style={{ left: Math.min(Math.max(active.x - 18, 12), width - 230) }}>
            <p className="font-semibold text-ink">{active.date}</p>
            <p className="mt-1 text-muted">原始值：{fmt(active.raw)}</p>
            <p className="text-muted">基金/ETF：{fmt(active.fund)}</p>
            <p className="text-muted">{benchmarkName || "大盘"}：{fmt(active.benchmark)}</p>
            <p className="text-muted">MA20：{fmt(active.ma20)}</p>
            <p className="text-muted">MA60：{fmt(active.ma60)}</p>
          </div>
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
        <Legend color="#d97706" label="基金/ETF" />
        <Legend color="#7c3aed" label={benchmarkName || "大盘基准"} />
        <Legend color="#2563eb" label="MA20" />
        <Legend color="#16a34a" label="MA60" />
      </div>
    </section>
  );
}

function priceRows(bars: FundBar[]): Array<{ date: string; value: number }> {
  return bars
    .map((bar) => ({ date: bar.date, value: bar.close ?? bar.nav }))
    .filter((row): row is { date: string; value: number } => row.value !== null && row.value !== undefined && !Number.isNaN(Number(row.value)))
    .sort((a, b) => a.date.localeCompare(b.date));
}

function normalizeRows(rows: Array<{ date: string; value: number }>): Array<{ date: string; value: number }> {
  const base = rows.find((row) => row.value > 0)?.value;
  if (!base) return [];
  return rows.map((row) => ({ date: row.date, value: (row.value / base) * 100 }));
}

function avg(values: number[]): number {
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function fmt(value: number | null): string {
  return value === null ? "--" : value.toFixed(2);
}

function Legend({ color, label }: { color: string; label: string }) {
  return <span className="inline-flex items-center gap-2"><span className="h-2 w-5 rounded-full" style={{ background: color }} />{label}</span>;
}

export default FundNavChart;
