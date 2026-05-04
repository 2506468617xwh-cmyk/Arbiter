import { createContext, ReactNode, useContext } from "react";
import { AppLanguage } from "./components/ModelSettingsDrawer";

export const HUMILITY_ZH = "保持谦逊，永远不要预测市场";
export const HUMILITY_EN = "Stay humble. Never predict the market.";

export type PageKey =
  | "home"
  | "dashboard"
  | "charts"
  | "asset"
  | "stock"
  | "fund"
  | "multi"
  | "macro"
  | "news"
  | "ai"
  | "research"
  | "reports";

interface PageText {
  eyebrow: string;
  title: string;
  subtitle: string;
}

const pageText: Record<AppLanguage, Record<PageKey, PageText>> = {
  "zh-CN": {
    home: { eyebrow: "Home Guide", title: "首页导览", subtitle: HUMILITY_ZH },
    dashboard: { eyebrow: "Heatmap", title: "市场热力榜", subtitle: HUMILITY_ZH },
    charts: { eyebrow: "Charts", title: "走势图", subtitle: HUMILITY_ZH },
    asset: { eyebrow: "Single Asset", title: "单资产研究", subtitle: HUMILITY_ZH },
    stock: { eyebrow: "Stock Research", title: "个股分析", subtitle: HUMILITY_ZH },
    fund: { eyebrow: "Fund & ETF Research", title: "基金 ETF", subtitle: HUMILITY_ZH },
    multi: { eyebrow: "Multi Asset", title: "多资产研究", subtitle: HUMILITY_ZH },
    macro: { eyebrow: "Global Macro", title: "宏观研究", subtitle: HUMILITY_ZH },
    news: { eyebrow: "News Radar", title: "新闻雷达", subtitle: HUMILITY_ZH },
    ai: { eyebrow: "LLM Research Analyst", title: "AI 研究", subtitle: HUMILITY_ZH },
    research: { eyebrow: "Research Desk", title: "研究生成", subtitle: HUMILITY_ZH },
    reports: { eyebrow: "Reports", title: "报告库", subtitle: HUMILITY_ZH }
  },
  en: {
    home: { eyebrow: "Home Guide", title: "Home Guide", subtitle: HUMILITY_EN },
    dashboard: { eyebrow: "Heatmap", title: "Market Heatmap", subtitle: HUMILITY_EN },
    charts: { eyebrow: "Charts", title: "Market Charts", subtitle: HUMILITY_EN },
    asset: { eyebrow: "Single Asset", title: "Single Asset Research", subtitle: HUMILITY_EN },
    stock: { eyebrow: "Stock Research", title: "Stock Analysis", subtitle: HUMILITY_EN },
    fund: { eyebrow: "Fund & ETF Research", title: "Funds & ETFs", subtitle: HUMILITY_EN },
    multi: { eyebrow: "Multi Asset", title: "Multi-Asset Research", subtitle: HUMILITY_EN },
    macro: { eyebrow: "Global Macro", title: "Macro Research", subtitle: HUMILITY_EN },
    news: { eyebrow: "News Radar", title: "News Radar", subtitle: HUMILITY_EN },
    ai: { eyebrow: "LLM Research Analyst", title: "AI Research", subtitle: HUMILITY_EN },
    research: { eyebrow: "Research Desk", title: "Report Generator", subtitle: HUMILITY_EN },
    reports: { eyebrow: "Reports", title: "Report Library", subtitle: HUMILITY_EN }
  }
};

const uiText = {
  "zh-CN": {
    refreshOverview: "刷新概览",
    refreshing: "刷新中...",
    openReports: "查看报告库",
    retry: "重试",
    loadingLocal: "正在读取本地研究数据...",
    connected: "已连接",
    pending: "待更新",
    marketStatus: "市场状态",
    indexCount: "指数数量",
    newsCount: "新闻数量",
    macroCount: "宏观指标",
    reportCount: "报告数量",
    lastUpdate: "最后更新",
    latestDisplayableMarket: "最新可展示行情",
    localNewsSample: "本地新闻样本",
    latestMacroCoverage: "最新指标覆盖",
    waitingForReport: "等待报告生成",
    waitingForApi: "等待接口返回。",
    marketObservation: "市场观察",
    newsRisk: "新闻风险",
    macroTemperature: "宏观温度",
    reportStatus: "报告状态",
    dataNotes: "数据说明",
    noMarketSummary: "暂无市场摘要。",
    noNewsSummary: "暂无新闻摘要。",
    noMacroSummary: "暂无宏观摘要。",
    noReportSummary: "暂无报告摘要。",
    latestFile: "最新文件",
    dataNotesBody: "API 读取本地已有结果。缺数据时会展示 warning，页面仍会保持可用。"
  },
  en: {
    refreshOverview: "Refresh",
    refreshing: "Refreshing...",
    openReports: "Open Reports",
    retry: "Retry",
    loadingLocal: "Reading local research data...",
    connected: "Connected",
    pending: "Pending",
    marketStatus: "Market Status",
    indexCount: "Indexes",
    newsCount: "News",
    macroCount: "Macro Indicators",
    reportCount: "Reports",
    lastUpdate: "Last Update",
    latestDisplayableMarket: "Latest displayable market data",
    localNewsSample: "Local news sample",
    latestMacroCoverage: "Latest macro coverage",
    waitingForReport: "Waiting for report generation",
    waitingForApi: "Waiting for API response.",
    marketObservation: "Market Observation",
    newsRisk: "News Risk",
    macroTemperature: "Macro Temperature",
    reportStatus: "Report Status",
    dataNotes: "Data Notes",
    noMarketSummary: "No market summary yet.",
    noNewsSummary: "No news summary yet.",
    noMacroSummary: "No macro summary yet.",
    noReportSummary: "No report summary yet.",
    latestFile: "Latest file",
    dataNotesBody: "The API reads existing local research results. When data is missing, warnings are shown while the page remains usable."
  }
} as const;

type UiText = {
  refreshOverview: string;
  refreshing: string;
  openReports: string;
  retry: string;
  loadingLocal: string;
  connected: string;
  pending: string;
  marketStatus: string;
  indexCount: string;
  newsCount: string;
  macroCount: string;
  reportCount: string;
  lastUpdate: string;
  latestDisplayableMarket: string;
  localNewsSample: string;
  latestMacroCoverage: string;
  waitingForReport: string;
  waitingForApi: string;
  marketObservation: string;
  newsRisk: string;
  macroTemperature: string;
  reportStatus: string;
  dataNotes: string;
  noMarketSummary: string;
  noNewsSummary: string;
  noMacroSummary: string;
  noReportSummary: string;
  latestFile: string;
  dataNotesBody: string;
};

const I18nContext = createContext<{ language: AppLanguage; page: Record<PageKey, PageText>; ui: UiText } | null>(null);

export function I18nProvider({ language, children }: { language: AppLanguage; children: ReactNode }) {
  return <I18nContext.Provider value={{ language, page: pageText[language], ui: uiText[language] }}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const value = useContext(I18nContext);
  if (!value) {
    throw new Error("useI18n must be used inside I18nProvider");
  }
  return value;
}
