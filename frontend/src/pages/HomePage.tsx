import { useCallback, useEffect, useState } from "react";
import { fetchOverview, OverviewResponse } from "../api/client";
import MetricCard from "../components/MetricCard";
import ResearchPet from "../components/ResearchPet";
import SectionCard from "../components/SectionCard";
import StatusPill from "../components/StatusPill";
import { useI18n } from "../i18n";

interface HomePageProps {
  onOpenReports: () => void;
}

function HomePage({ onOpenReports }: HomePageProps) {
  const { language, ui, page } = useI18n();
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadOverview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setOverview(await fetchOverview());
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "概览接口暂时不可用。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  const englishSummary = (kind: "market" | "news" | "macro" | "report") => {
    if (!overview) return "";
    if (kind === "market") {
      return `Loaded ${overview.market.count} market/index assets. Use the data as context, not as a forecast.`;
    }
    if (kind === "news") {
      return `Loaded ${overview.news.count} local news items. Treat headlines as signals to verify, not conclusions.`;
    }
    if (kind === "macro") {
      return `Loaded ${overview.macro.count} macro indicators. Macro data is a map, not a crystal ball.`;
    }
    return `There are ${overview.reports.count} saved reports in the local report library.`;
  };

  const summaryText = (kind: "market" | "news" | "macro" | "report", fallback: string | undefined) => {
    if (language === "en") return englishSummary(kind);
    return fallback || (
      kind === "market" ? ui.noMarketSummary :
      kind === "news" ? ui.noNewsSummary :
      kind === "macro" ? ui.noMacroSummary :
      ui.noReportSummary
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-start">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-brand">{page.home.eyebrow}</p>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            <h1 className="text-3xl font-semibold text-ink">{page.home.title}</h1>
            {overview ? <StatusPill status={overview.market_status} /> : null}
          </div>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-muted">{page.home.subtitle}</p>
        </div>
        <div className="flex flex-col items-start gap-3 md:items-end">
          <ResearchPet
            pageName="home"
            context={{
              title: page.home.title,
              subtitle: page.home.subtitle,
              market_summary: overview?.market_summary,
              news_summary: overview?.news_summary,
              macro_summary: overview?.macro_summary,
              report_summary: overview?.report_summary
            }}
          />
          <div className="flex flex-wrap gap-3">
            <button className="secondary-button" onClick={loadOverview} disabled={loading}>
              {loading ? ui.refreshing : ui.refreshOverview}
            </button>
            <button className="primary-button" onClick={onOpenReports}>
              {ui.openReports}
            </button>
          </div>
        </div>
      </div>

      {error ? (
        <div className="flex flex-col gap-3 rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 md:flex-row md:items-center md:justify-between">
          <span>{error}</span>
          <button className="secondary-button bg-white" onClick={loadOverview}>
            {ui.retry}
          </button>
        </div>
      ) : null}

      {loading && !overview ? (
        <div className="rounded-lg border border-line bg-panel p-5 text-sm text-muted shadow-soft">
          {ui.loadingLocal}
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-6">
        <MetricCard
          label={ui.marketStatus}
          value={overview?.market_status === "connected" ? ui.connected : ui.pending}
          detail={language === "en" ? "Local research database status." : overview?.market_summary ?? "正在连接本地研究数据库。"}
          tone={overview?.market_status === "connected" ? "positive" : "warning"}
        />
        <MetricCard
          label={ui.indexCount}
          value={String(overview?.market.count ?? 0)}
          detail={ui.latestDisplayableMarket}
        />
        <MetricCard
          label={ui.newsCount}
          value={String(overview?.news.count ?? 0)}
          detail={ui.localNewsSample}
        />
        <MetricCard
          label={ui.macroCount}
          value={String(overview?.macro.count ?? 0)}
          detail={ui.latestMacroCoverage}
        />
        <MetricCard
          label={ui.reportCount}
          value={String(overview?.reports.count ?? 0)}
          detail={language === "en" ? (overview?.reports.latest_title ? "Latest saved report" : ui.waitingForReport) : overview?.reports.latest_title ?? ui.waitingForReport}
        />
        <MetricCard
          label={ui.lastUpdate}
          value={overview ? new Date(overview.last_update).toLocaleTimeString() : "--:--"}
          detail={overview ? new Date(overview.last_update).toLocaleDateString() : ui.waitingForApi}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard
          title={ui.marketObservation}
          count={overview?.market.count}
          highlights={language === "en" ? [] : overview?.market.highlights}
          warnings={overview?.market.warnings}
        >
          {summaryText("market", overview?.market_summary)}
        </SectionCard>
        <SectionCard
          title={ui.newsRisk}
          count={overview?.news.count}
          highlights={language === "en" ? [] : overview?.news.highlights}
          warnings={overview?.news.warnings}
        >
          {summaryText("news", overview?.news_summary)}
        </SectionCard>
        <SectionCard
          title={ui.macroTemperature}
          count={overview?.macro.count}
          highlights={language === "en" ? [] : overview?.macro.highlights}
          warnings={overview?.macro.warnings}
        >
          {summaryText("macro", overview?.macro_summary)}
        </SectionCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <SectionCard title={ui.reportStatus} count={overview?.reports.count}>
          {summaryText("report", overview?.report_summary)}
          {overview?.reports.latest_filename ? (
            <p className="mt-2 break-all text-xs text-muted">
              {ui.latestFile}: {overview.reports.latest_filename}
            </p>
          ) : null}
        </SectionCard>
        <SectionCard title={ui.dataNotes}>
          {ui.dataNotesBody}
        </SectionCard>
      </div>

      {overview?.warnings.length ? (
        <section className="rounded-lg border border-amber-200 bg-amber-50 p-4">
          <h2 className="text-sm font-semibold text-amber-950">提示</h2>
          <ul className="mt-2 space-y-1 text-sm leading-6 text-amber-900">
            {overview.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

export default HomePage;
