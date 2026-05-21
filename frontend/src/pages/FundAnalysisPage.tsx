import { useState } from "react";
import { FundAnalysisResponse, fetchFundAnalysis } from "../api/client";
import FundAnalysisReport from "../components/FundAnalysisReport";
import FundDcaPanel from "../components/FundDcaPanel";
import FundIndicatorGrid from "../components/FundIndicatorGrid";
import FundNavChart from "../components/FundNavChart";
import FundQuoteCard from "../components/FundQuoteCard";
import FundResearchChatPanel from "../components/FundResearchChatPanel";
import FundRiskPanel from "../components/FundRiskPanel";
import FundSearchBox from "../components/FundSearchBox";

export default function FundAnalysisPage({ useLlm }: { useLlm: boolean }) {
  const [symbol, setSymbol] = useState("QQQ.US");
  const [data, setData] = useState<FundAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setLoading(true);
    fetchFundAnalysis(symbol, useLlm)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "基金/ETF 分析失败"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="px-4 space-y-2">
      <FundSearchBox value={symbol} loading={loading} onChange={setSymbol} onSubmit={load} />

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
          <FundQuoteCard quote={data.quote} />
          <FundNavChart bars={data.bars} benchmarkBars={data.benchmark_bars} benchmarkName={data.benchmark_name} />
          <FundIndicatorGrid indicators={data.indicators} />
          <FundRiskPanel allocation={data.allocation_summary} risk={data.risk_summary} liquidity={data.liquidity_summary} warnings={data.warnings} />
          <FundDcaPanel text={data.dca_summary} />
          <FundAnalysisReport text={data.research_summary} source={data.source} />
          <FundResearchChatPanel symbol={data.symbol} useLlm={useLlm} />
        </>
      ) : !loading ? (
        <div className="py-12 text-center text-[11px] text-[var(--ink-muted)] font-mono">
          输入代码后点击分析 · 示例：510300.SH / QQQ.US / 2800.HK
        </div>
      ) : null}
    </div>
  );
}
