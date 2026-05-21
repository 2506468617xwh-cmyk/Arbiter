import { MouseEvent, useMemo, useRef, useState } from "react";
import { MacroSeriesPoint } from "../api/client";

const width = 780;
const height = 240;
const margin = { top: 14, right: 20, bottom: 34, left: 52 };
const colors = ["#d97706", "#2563eb", "#16a34a", "#dc2626", "#7c3aed", "#0891b2"];

interface Active {
  date: string;
  x: number;
  rows: Array<{ symbol: string; value: number | null; color: string }>;
}

function MacroLineChart({ points, symbols }: { points: MacroSeriesPoint[]; symbols: string[] }) {
  const [active, setActive] = useState<Active | null>(null);
  const lastDate = useRef<string | null>(null);
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const data = useMemo(() => {
    const selected = new Set(symbols);
    const normalized = new Map<string, Array<{ date: string; value: number }>>();
    const dates = new Set<string>();
    const values: number[] = [];
    for (const symbol of symbols) {
      const rows = points
        .filter((point) => selected.has(point.symbol) && point.symbol === symbol && point.value !== null)
        .map((point) => ({ date: point.date, value: Number(point.value) }))
        .sort((a, b) => a.date.localeCompare(b.date));
      const base = rows.find((row) => row.value !== 0)?.value;
      const series = base ? rows.map((row) => ({ date: row.date, value: (row.value / base) * 100 })) : [];
      normalized.set(symbol, series);
      for (const row of series) {
        dates.add(row.date);
        values.push(row.value);
      }
    }
    const dateList = Array.from(dates).sort();
    const min = Math.min(...values);
    const max = Math.max(...values);
    const padding = (max - min || 1) * 0.08;
    return { series: normalized, dates: dateList, min: min - padding, max: max + padding, values };
  }, [points, symbols]);

  if (!data.values.length) {
    return <div className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">暂无可绘制宏观走势数据。</div>;
  }

  const xFor = (date: string) => margin.left + (data.dates.length <= 1 ? 0 : (data.dates.indexOf(date) / (data.dates.length - 1)) * innerWidth);
  const yFor = (value: number) => margin.top + innerHeight - ((value - data.min) / (data.max - data.min || 1)) * innerHeight;
  const pathFor = (symbol: string) => (data.series.get(symbol) ?? []).map((row, index) => `${index === 0 ? "M" : "L"}${xFor(row.date).toFixed(1)},${yFor(row.value).toFixed(1)}`).join(" ");
  const ticks = [data.min, data.min + (data.max - data.min) / 2, data.max];

  const updateActive = (clientX: number, svg: SVGSVGElement) => {
    const rect = svg.getBoundingClientRect();
    const svgX = ((clientX - rect.left) / rect.width) * width;
    const index = Math.max(0, Math.min(data.dates.length - 1, Math.round(((svgX - margin.left) / innerWidth) * (data.dates.length - 1))));
    const date = data.dates[index];
    if (date === lastDate.current) return;
    lastDate.current = date;
    const rows = symbols.map((symbol, symbolIndex) => {
      const found = (data.series.get(symbol) ?? []).find((row) => row.date === date);
      return { symbol, value: found?.value ?? null, color: colors[symbolIndex % colors.length] };
    });
    setActive({ date, x: xFor(date), rows });
  };

  return (
    <section className="border border-[var(--border-subtle)] bg-[var(--bg-card)] p-3">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-xs font-semibold text-ink">宏观指标走势</h2>
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
            return <g key={tick}><line x1={margin.left} y1={y} x2={width - margin.right} y2={y} stroke="var(--border-card)" /><text x={margin.left - 10} y={y + 4} textAnchor="end" fontSize="11" fill="var(--ink-muted)">{tick.toFixed(1)}</text></g>;
          })}
          <line x1={margin.left} y1={margin.top} x2={margin.left} y2={height - margin.bottom} stroke="var(--border-card)" />
          <line x1={margin.left} y1={height - margin.bottom} x2={width - margin.right} y2={height - margin.bottom} stroke="var(--border-card)" />
          {symbols.map((symbol, index) => <path key={symbol} d={pathFor(symbol)} fill="none" stroke={colors[index % colors.length]} strokeWidth="2" />)}
          {active ? <line x1={active.x} y1={margin.top} x2={active.x} y2={height - margin.bottom} stroke="var(--ink-dim)" strokeDasharray="4 4" /> : null}
        </svg>
        {active ? (
          <div className="pointer-events-none absolute top-4 min-w-48 rounded-lg border border-line bg-panel p-3 text-xs shadow-soft" style={{ left: Math.min(Math.max(active.x - 18, 12), width - 250) }}>
            <p className="font-semibold text-ink">{active.date}</p>
            {active.rows.map((row) => <p key={row.symbol} className="mt-1 flex justify-between gap-4 text-muted"><span>{row.symbol}</span><span>{row.value === null ? "--" : row.value.toFixed(2)}</span></p>)}
          </div>
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-muted">
        {symbols.map((symbol, index) => <span key={symbol} className="inline-flex items-center gap-2"><span className="h-2 w-5 rounded-full" style={{ background: colors[index % colors.length] }} />{symbol}</span>)}
      </div>
    </section>
  );
}

export default MacroLineChart;
