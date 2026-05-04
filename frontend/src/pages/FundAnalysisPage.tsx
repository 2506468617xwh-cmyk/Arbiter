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
import PageIntro from "../components/PageIntro";

function FundAnalysisPage({ useLlm }: { useLlm: boolean }) {
  const [symbol, setSymbol] = useState("QQQ.US");
  const [data, setData] = useState<FundAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    setLoading(true);
    fetchFundAnalysis(symbol, useLlm)
      .then(setData)
      .catch((exc) => setError(exc instanceof Error ? exc.message : "基金/ETF 分析失败。"))
      .finally(() => setLoading(false));
  };

  return (
    <div className="space-y-6">
      <PageIntro pageKey="fund" />

      <FundSearchBox value={symbol} loading={loading} onChange={setSymbol} onSubmit={load} />

      {error ? <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">{error}</div> : null}

      {loading ? <section className="rounded-lg border border-line bg-panel p-6 text-sm text-muted">正在读取数据源并计算基金/ETF指标...</section> : null}

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
      ) : (
        <section className="rounded-lg border border-dashed border-line bg-panel p-6 text-sm text-muted">
          输入或选择基金/ETF代码后开始分析。示例：510300.SH、513100.SH、QQQ.US、SPY.US、2800.HK。
        </section>
      )}
    </div>
  );
}

export default FundAnalysisPage;
