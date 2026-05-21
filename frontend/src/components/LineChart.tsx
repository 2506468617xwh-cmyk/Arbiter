import { MouseEvent, TouchEvent, useMemo, useRef, useState } from "react";
import { MarketSeriesPoint } from "../api/client";

interface LineChartProps {
  points: MarketSeriesPoint[];
  symbols: string[];
  valueKey?: "close" | "normalized" | "drawdown";
  height?: number;
}

interface ActivePoint {
  date: string;
  x: number;
  rows: Array<{ symbol: string; value: number | null; color: string; y: number | null }>;
}

const colors = ["#d97706", "#2563eb", "#16a34a", "#dc2626", "#7c3aed", "#0891b2", "#b45309"];
const width = 780;
const margin = { top: 14, right: 20, bottom: 34, left: 52 };
const maxPointsPerSeries = 650;

function formatValue(value: number | null, key: string): string {
  if (value === null || Number.isNaN(value)) {
    return "--";
  }
  if (key === "drawdown") {
    return `${value.toFixed(2)}%`;
  }
  return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
}

function niceTicks(min: number, max: number, count = 5): number[] {
  if (min === max) {
    return [min];
  }
  const step = (max - min) / Math.max(1, count - 1);
  return Array.from({ length: count }, (_, index) => min + step * index);
}

function sampleSeries(series: MarketSeriesPoint[]): MarketSeriesPoint[] {
  if (series.length <= maxPointsPerSeries) {
    return series;
  }
  const step = (series.length - 1) / (maxPointsPerSeries - 1);
  return Array.from({ length: maxPointsPerSeries }, (_, index) => series[Math.round(index * step)]);
}

function LineChart({ points, symbols, valueKey = "close", height = 260 }: LineChartProps) {
  const [active, setActive] = useState<ActivePoint | null>(null);
  const lastActiveDateRef = useRef<string | null>(null);
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;

  const prepared = useMemo(() => {
    const selected = new Set(symbols);
    const bySymbol = new Map<string, MarketSeriesPoint[]>();
    for (const point of points) {
      if (!selected.has(point.symbol) || point[valueKey] === null) continue;
      const bucket = bySymbol.get(point.symbol) ?? [];
      bucket.push(point);
      bySymbol.set(point.symbol, bucket);
    }

    const sampledBySymbol = new Map<string, MarketSeriesPoint[]>();
    const valueByDate = new Map<string, Map<string, number>>();
    const allDates = new Set<string>();
    const values: number[] = [];

    for (const symbol of symbols) {
      const series = (bySymbol.get(symbol) ?? []).sort((a, b) => a.date.localeCompare(b.date));
      const sampled = sampleSeries(series);
      sampledBySymbol.set(symbol, sampled);
      for (const point of sampled) {
        const value = Number(point[valueKey]);
        if (Number.isNaN(value)) continue;
        allDates.add(point.date);
        values.push(value);
        const row = valueByDate.get(point.date) ?? new Map<string, number>();
        row.set(symbol, value);
        valueByDate.set(point.date, row);
      }
    }

    const dates = Array.from(allDates).sort();
    const dateIndex = new Map(dates.map((date, index) => [date, index]));

    return { dates, dateIndex, sampledBySymbol, valueByDate, values };
  }, [points, symbols, valueKey]);

  const chart = useMemo(() => {
    const min = Math.min(...prepared.values);
    const max = Math.max(...prepared.values);
    const padding = (max - min || 1) * 0.08;
    const yMin = min - padding;
    const yMax = max + padding;
    const ySpan = yMax - yMin || 1;
    const xFor = (date: string) => {
      const index = prepared.dateIndex.get(date) ?? 0;
      return margin.left + (prepared.dates.length <= 1 ? 0 : (index / (prepared.dates.length - 1)) * innerWidth);
    };
    const yFor = (value: number) => margin.top + innerHeight - ((value - yMin) / ySpan) * innerHeight;

    return { yMin, yMax, xFor, yFor, ticks: niceTicks(yMin, yMax) };
  }, [innerHeight, innerWidth, prepared.dateIndex, prepared.dates.length, prepared.values]);

  if (!prepared.values.length) {
    return <div className="rounded-xl border border-dashed border-[var(--border-card)] bg-[var(--bg-card)] p-6 text-center text-sm text-[var(--ink-muted)]">暂无可绘制走势数据。</div>;
  }

  const updateActive = (clientX: number, svg: SVGSVGElement) => {
    const rect = svg.getBoundingClientRect();
    const svgX = ((clientX - rect.left) / rect.width) * width;
    const clamped = Math.max(margin.left, Math.min(width - margin.right, svgX));
    const ratio = innerWidth <= 0 ? 0 : (clamped - margin.left) / innerWidth;
    const index = Math.max(0, Math.min(prepared.dates.length - 1, Math.round(ratio * (prepared.dates.length - 1))));
    const date = prepared.dates[index];

    if (date === lastActiveDateRef.current) {
      return;
    }
    lastActiveDateRef.current = date;

    const valueMap = prepared.valueByDate.get(date) ?? new Map<string, number>();
    const rows = symbols.map((symbol, symbolIndex) => {
      const value = valueMap.get(symbol) ?? null;
      return {
        symbol,
        value,
        color: colors[symbolIndex % colors.length],
        y: value === null ? null : chart.yFor(value)
      };
    });
    setActive({ date, x: chart.xFor(date), rows });
  };

  const clearActive = () => {
    lastActiveDateRef.current = null;
    setActive(null);
  };

  const handleMouseMove = (event: MouseEvent<SVGSVGElement>) => updateActive(event.clientX, event.currentTarget);
  const handleClick = (event: MouseEvent<SVGSVGElement>) => updateActive(event.clientX, event.currentTarget);
  const handleTouch = (event: TouchEvent<SVGSVGElement>) => {
    const touch = event.touches[0] ?? event.changedTouches[0];
    if (touch) {
      updateActive(touch.clientX, event.currentTarget);
    }
  };

  const xTickDates = prepared.dates.length <= 6
    ? prepared.dates
    : [
        prepared.dates[0],
        prepared.dates[Math.floor(prepared.dates.length * 0.25)],
        prepared.dates[Math.floor(prepared.dates.length * 0.5)],
        prepared.dates[Math.floor(prepared.dates.length * 0.75)],
        prepared.dates[prepared.dates.length - 1]
      ];

  return (
    <section className="rounded-xl border border-[var(--border-card)] bg-[var(--bg-card)] p-4">
      <div className="relative overflow-x-auto">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="min-w-[640px] touch-pan-y select-none"
          onMouseMove={handleMouseMove}
          onMouseLeave={clearActive}
          onClick={handleClick}
          onTouchStart={handleTouch}
          onTouchMove={handleTouch}
          role="img"
          aria-label="资产走势图"
        >
          <rect x="0" y="0" width={width} height={height} fill="var(--bg-card)" />

          {chart.ticks.map((tick) => {
            const y = chart.yFor(tick);
            return (
              <g key={tick}>
                <line x1={margin.left} y1={y} x2={width - margin.right} y2={y} stroke="var(--border-card)" />
                <text x={margin.left - 10} y={y + 4} textAnchor="end" fontSize="11" fill="var(--ink-muted)">
                  {formatValue(tick, valueKey)}
                </text>
              </g>
            );
          })}

          <line x1={margin.left} y1={margin.top} x2={margin.left} y2={height - margin.bottom} stroke="var(--border-card)" />
          <line x1={margin.left} y1={height - margin.bottom} x2={width - margin.right} y2={height - margin.bottom} stroke="var(--border-card)" />

          {xTickDates.map((date) => {
            const x = chart.xFor(date);
            return (
              <g key={date}>
                <line x1={x} y1={height - margin.bottom} x2={x} y2={height - margin.bottom + 5} stroke="var(--border-card)" />
                <text x={x} y={height - 18} textAnchor="middle" fontSize="11" fill="var(--ink-muted)">
                  {date.slice(5)}
                </text>
              </g>
            );
          })}

          {symbols.map((symbol, index) => {
            const series = prepared.sampledBySymbol.get(symbol) ?? [];
            const d = series
              .map((point, pointIndex) => {
                const value = Number(point[valueKey]);
                const prefix = pointIndex === 0 ? "M" : "L";
                return `${prefix}${chart.xFor(point.date).toFixed(1)},${chart.yFor(value).toFixed(1)}`;
              })
              .join(" ");
            return <path key={symbol} d={d} fill="none" stroke={colors[index % colors.length]} strokeWidth="2.2" />;
          })}

          {active ? (
            <g>
              <line x1={active.x} y1={margin.top} x2={active.x} y2={height - margin.bottom} stroke="var(--ink-dim)" strokeDasharray="4 4" />
              {active.rows.map((row) =>
                row.y === null ? null : (
                  <circle key={row.symbol} cx={active.x} cy={row.y} r="4" fill={row.color} stroke="var(--bg-card)" strokeWidth="2" />
                )
              )}
            </g>
          ) : null}
        </svg>

        {active ? (
          <div
            className="pointer-events-none absolute top-4 min-w-44 rounded-xl border border-[var(--border-card)] bg-[var(--bg-elevated)] backdrop-blur-md p-3 text-xs shadow-lg"
            style={{ left: Math.min(Math.max(active.x - 18, 12), width - 220) }}
          >
            <p className="font-semibold text-[var(--ink-primary)]">{active.date}</p>
            <div className="mt-2 space-y-1.5">
              {active.rows.map((row) => (
                <p key={row.symbol} className="flex items-center justify-between gap-4 text-[var(--ink-secondary)]">
                  <span className="inline-flex items-center gap-1.5">
                    <span className="h-1.5 w-3 rounded-full" style={{ background: row.color }} />
                    {row.symbol}
                  </span>
                  <span className="font-semibold text-[var(--ink-primary)]">{formatValue(row.value, valueKey)}</span>
                </p>
              ))}
            </div>
          </div>
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5 text-[11px] text-[var(--ink-muted)]">
        {symbols.map((symbol, index) => (
          <span key={symbol} className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-4 rounded-full" style={{ background: colors[index % colors.length] }} />
            {symbol}
          </span>
        ))}
      </div>
    </section>
  );
}

export default LineChart;
