import { useState } from "react";
import { StockAnalysisResponse, fetchStockAnalysis } from "../api/client";
import StockAnalysisReport from "../components/StockAnalysisReport";
import StockIndicatorGrid from "../components/StockIndicatorGrid";
import StockKlineChart from "../components/StockKlineChart";
import StockQuoteCard from "../components/StockQuoteCard";
import StockRiskPanel from "../components/StockRiskPanel";
import StockSearchBox from "../components/StockSearchBox";
import PageIntro from "../components/PageIntro";

function StockAnalysisPage({ useLlm }: { useLlm: boolean }) {
  const [symbol, setSymbol] = useState("TSLA.US");
  const [data, setData] = useState<StockAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setLoading(true);
    fetchStockAnalysis(symbol, useLlm)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "个股分析失败。"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-6">
      <PageIntro pageKey="stock" />

      <StockSearchBox value={symbol} loading={loading} onChange={setSymbol} onSubmit={load} />

      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}

      {data ? (
        <>
          <StockQuoteCard quote={data.quote} />
          <StockKlineChart bars={data.bars} benchmarkBars={data.benchmark_bars} benchmarkName={data.benchmark_name} />
          <StockIndicatorGrid indicators={data.indicators} />
          <StockRiskPanel trend={data.trend_summary} risk={data.risk_summary} warnings={data.warnings} />
          <StockAnalysisReport text={data.research_summary} source={data.source} />
        </>
      ) : (
        <section className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">
          输入或选择股票代码后开始分析。示例：600519.SH、TSLA.US、700.HK。
        </section>
      )}
    </div>
  );
}

export default StockAnalysisPage;
