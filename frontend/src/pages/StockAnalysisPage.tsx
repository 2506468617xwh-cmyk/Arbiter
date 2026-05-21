import { useState } from "react";
import { StockAnalysisResponse, fetchStockAnalysis } from "../api/client";
import StockAnalysisReport from "../components/StockAnalysisReport";
import StockIndicatorGrid from "../components/StockIndicatorGrid";
import StockKlineChart from "../components/StockKlineChart";
import StockQuoteCard from "../components/StockQuoteCard";
import StockRiskPanel from "../components/StockRiskPanel";
import StockSearchBox from "../components/StockSearchBox";

export default function StockAnalysisPage({ useLlm }: { useLlm: boolean }) {
  const [symbol, setSymbol] = useState("TSLA.US");
  const [data, setData] = useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setLoading(true);
    fetchStockAnalysis(symbol, useLlm)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "个股分析失败"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="px-4 space-y-2">
      <StockSearchBox value={symbol} loading={loading} onChange={setSymbol} onSubmit={load} />

      {error && (
        <div className="px-3 py-2 text-[10px] text-[var(--ink-muted)] font-mono border border-[var(--border-subtle)]">{error}</div>
      )}

      {loading && (
        <div className="space-y-1.5 pt-1">
          <div className="skeleton h-16 w-full" />
          <div className="skeleton h-36 w-full" />
          <div className="skeleton h-24 w-full" />
        </div>
      )}

      {data ? (
        <>
          <StockQuoteCard quote={data.quote} />
          <StockKlineChart bars={data.bars} benchmarkBars={data.benchmark_bars} benchmarkName={data.benchmark_name} />
          <StockIndicatorGrid indicators={data.indicators} />
          <StockRiskPanel trend={data.trend_summary} risk={data.risk_summary} warnings={data.warnings} />
          <StockAnalysisReport text={data.research_summary} source={data.source} />
        </>
      ) : !loading ? (
        <div className="py-12 text-center text-[11px] text-[var(--ink-muted)] font-mono">
          输入代码后点击分析 · 示例：600519.SH / TSLA.US / 700.HK
        </div>
      ) : null}
    </div>
  );
}
