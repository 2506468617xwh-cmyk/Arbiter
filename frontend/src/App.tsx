import { useEffect, useState } from "react";
import AIResearchPage from "./pages/AIResearchPage";
import AssetResearchPage from "./pages/AssetResearchPage";
import ChartsPage from "./pages/ChartsPage";
import DashboardPage from "./pages/DashboardPage";
import FundAnalysisPage from "./pages/FundAnalysisPage";

import HomePage from "./pages/HomePage";
import MacroResearchPage from "./pages/MacroResearchPage";
import MultiAssetPage from "./pages/MultiAssetPage";
import NewsPage from "./pages/NewsPage";
import ResearchPage from "./pages/ResearchPage";
import ReportsPage from "./pages/ReportsPage";
import StockAnalysisPage from "./pages/StockAnalysisPage";
import ModelSettingsDrawer, { AppLanguage, AppTheme } from "./components/ModelSettingsDrawer";
import { I18nProvider } from "./i18n";
import { installDomTranslator } from "./i18n-dom";

type Page = "home" | "dashboard" | "charts" | "asset" | "stock" | "fund" | "multi" | "macro" | "news" | "ai" | "research" | "reports";

const navLabels: Record<AppLanguage, Record<Page, string>> = {
  "zh-CN": {
    home: "首页",
    dashboard: "市场热力榜",
    charts: "走势图",
    asset: "单资产",
    stock: "个股分析",
    fund: "基金 ETF",
    multi: "多资产",
    macro: "宏观研究",
    news: "新闻雷达",
    ai: "AI 研究",
    research: "研究生成",
    reports: "报告库"
  },
  en: {
    home: "Home",
    dashboard: "Heatmap",
    charts: "Charts",
    asset: "Asset",
    stock: "Stocks",
    fund: "Funds ETF",
    multi: "Multi Asset",
    macro: "Macro",
    news: "News",
    ai: "AI Research",
    research: "Reports",
    reports: "Library"
  }
};

const navPages: Page[] = ["home", "dashboard", "charts", "asset", "stock", "fund", "multi", "macro", "news", "ai", "research", "reports"];

const pageHeaderText: Record<AppLanguage, Record<Page, { eyebrow: string; title: string; subtitle: string }>> = {
  "zh-CN": {
    home: { eyebrow: "Home Guide", title: "首页导览", subtitle: "保持谦逊，永远不要预测市场" },
    dashboard: { eyebrow: "Heatmap", title: "市场热力榜", subtitle: "保持谦逊，永远不要预测市场" },
    charts: { eyebrow: "Charts", title: "走势图", subtitle: "保持谦逊，永远不要预测市场" },
    asset: { eyebrow: "Single Asset", title: "单资产研究", subtitle: "保持谦逊，永远不要预测市场" },
    stock: { eyebrow: "Stock Research", title: "个股分析", subtitle: "保持谦逊，永远不要预测市场" },
    fund: { eyebrow: "Fund & ETF Research", title: "基金 ETF", subtitle: "保持谦逊，永远不要预测市场" },
    multi: { eyebrow: "Multi Asset", title: "多资产研究", subtitle: "保持谦逊，永远不要预测市场" },
    macro: { eyebrow: "Global Macro", title: "宏观研究", subtitle: "保持谦逊，永远不要预测市场" },
    news: { eyebrow: "News Radar", title: "新闻雷达", subtitle: "保持谦逊，永远不要预测市场" },
    ai: { eyebrow: "LLM Research Analyst", title: "AI 研究", subtitle: "保持谦逊，永远不要预测市场" },
    research: { eyebrow: "Research Desk", title: "研究生成", subtitle: "保持谦逊，永远不要预测市场" },
    reports: { eyebrow: "Reports", title: "报告库", subtitle: "保持谦逊，永远不要预测市场" }
  },
  en: {
    home: { eyebrow: "Home Guide", title: "Home Guide", subtitle: "Stay humble. Never predict the market." },
    dashboard: { eyebrow: "Heatmap", title: "Market Heatmap", subtitle: "Stay humble. Never predict the market." },
    charts: { eyebrow: "Charts", title: "Market Charts", subtitle: "Stay humble. Never predict the market." },
    asset: { eyebrow: "Single Asset", title: "Single Asset Research", subtitle: "Stay humble. Never predict the market." },
    stock: { eyebrow: "Stock Research", title: "Stock Analysis", subtitle: "Stay humble. Never predict the market." },
    fund: { eyebrow: "Fund & ETF Research", title: "Funds & ETFs", subtitle: "Stay humble. Never predict the market." },
    multi: { eyebrow: "Multi Asset", title: "Multi-Asset Research", subtitle: "Stay humble. Never predict the market." },
    macro: { eyebrow: "Global Macro", title: "Macro Research", subtitle: "Stay humble. Never predict the market." },
    news: { eyebrow: "News Radar", title: "News Radar", subtitle: "Stay humble. Never predict the market." },
    ai: { eyebrow: "LLM Research Analyst", title: "AI Research", subtitle: "Stay humble. Never predict the market." },
    research: { eyebrow: "Research Desk", title: "Report Generator", subtitle: "Stay humble. Never predict the market." },
    reports: { eyebrow: "Reports", title: "Report Library", subtitle: "Stay humble. Never predict the market." }
  }
};

function isLanguage(value: string | null): value is AppLanguage {
  return value === "zh-CN" || value === "en";
}

function isTheme(value: string | null): value is AppTheme {
  return value === "warm" || value === "white-red" || value === "black-blue" || value === "white-green" || value === "black-gold";
}

function App() {
  const [page, setPage] = useState<Page>("home");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [language, setLanguage] = useState<AppLanguage>(() => {
    const saved = window.localStorage.getItem("rabot_language");
    return isLanguage(saved) ? saved : "zh-CN";
  });
  const [theme, setTheme] = useState<AppTheme>(() => {
    const saved = window.localStorage.getItem("rabot_theme");
    return isTheme(saved) ? saved : "warm";
  });
  const [useLlm, setUseLlm] = useState(() => {
    const saved = window.localStorage.getItem("rabot_use_llm");
    return saved === null ? true : saved === "true";
  });

  useEffect(() => {
    window.localStorage.setItem("rabot_use_llm", String(useLlm));
  }, [useLlm]);

  useEffect(() => {
    window.localStorage.setItem("rabot_language", language);
    document.documentElement.lang = language === "en" ? "en" : "zh-CN";
  }, [language]);

  useEffect(() => {
    window.localStorage.setItem("rabot_theme", theme);
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    const syncHeader = () => {
      const main = document.querySelector("main");
      const text = pageHeaderText[language][page];
      const eyebrow = main?.querySelector("p.text-brand");
      const title = main?.querySelector("h1");
      const subtitle =
        main?.querySelector("p.max-w-3xl.text-sm") ||
        main?.querySelector("p.max-w-2xl.text-sm") ||
        main?.querySelector("h1")?.parentElement?.parentElement?.querySelector("p.text-muted");
      if (eyebrow) eyebrow.textContent = text.eyebrow;
      if (title) title.textContent = text.title;
      if (subtitle) subtitle.textContent = text.subtitle;
    };
    window.setTimeout(syncHeader, 0);
  }, [language, page]);

  useEffect(() => {
    let cleanup = () => {};
    const timer = window.setTimeout(() => {
      cleanup = installDomTranslator(language);
    }, 0);
    return () => {
      window.clearTimeout(timer);
      cleanup();
    };
  }, [language, page]);

  const toggleLanguage = () => setLanguage((value) => (value === "zh-CN" ? "en" : "zh-CN"));

  return (
    <div className="min-h-screen bg-warm text-ink">
      <header className="sticky top-0 z-10 border-b border-line bg-panel/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center gap-3 px-5 py-4">
          <button className="shrink-0 text-left text-xl font-semibold tracking-normal" onClick={() => setPage("home")}>
            RAbot
          </button>
          <nav className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
            {navPages.map((item) => (
              <button key={item} className={page === item ? "nav-button-active" : "nav-button"} onClick={() => setPage(item)}>
                {navLabels[language][item]}
              </button>
            ))}
          </nav>
          <div className="flex shrink-0 items-center gap-2">
            <button className="settings-icon-button settings-icon-button-globe" onClick={toggleLanguage} aria-label={language === "zh-CN" ? "Switch to English" : "切换到简体中文"} title={language === "zh-CN" ? "English" : "简体中文"}>
              <GlobeIcon />
            </button>
            <button className="settings-icon-button" onClick={() => setSettingsOpen(true)} aria-label={language === "zh-CN" ? "系统设置" : "Settings"} title={language === "zh-CN" ? "系统设置" : "Settings"}>
              <GearIcon />
            </button>
          </div>
        </div>
      </header>

      <I18nProvider language={language}>
        <ModelSettingsDrawer
          open={settingsOpen}
          useLlm={useLlm}
          language={language}
          theme={theme}
          onToggleOpen={() => setSettingsOpen((value) => !value)}
          onUseLlmChange={setUseLlm}
          onLanguageChange={setLanguage}
          onThemeChange={setTheme}
        />

        <main className="mx-auto max-w-6xl px-5 py-8">
          {page === "home" ? (
            <HomePage onOpenReports={() => setPage("reports")} />
          ) : page === "dashboard" ? (
            <DashboardPage />
          ) : page === "charts" ? (
            <ChartsPage />
          ) : page === "asset" ? (
            <AssetResearchPage useLlm={useLlm} />
          ) : page === "stock" ? (
            <StockAnalysisPage useLlm={useLlm} />
          ) : page === "fund" ? (
            <FundAnalysisPage useLlm={useLlm} />
          ) : page === "multi" ? (
            <MultiAssetPage useLlm={useLlm} />
          ) : page === "macro" ? (
            <MacroResearchPage useLlm={useLlm} />
          ) : page === "news" ? (
            <NewsPage />
          ) : page === "ai" ? (
            <AIResearchPage useLlm={useLlm} onOpenModelSettings={() => setSettingsOpen(true)} />
          ) : page === "research" ? (
            <ResearchPage defaultUseLlm={useLlm} />
          ) : (
            <ReportsPage onOpenResearch={() => setPage("research")} />
          )}
        </main>
      </I18nProvider>
    </div>
  );
}

function GlobeIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="9" />
      <path d="M3 12h18" />
      <path d="M12 3c2.1 2.4 3.2 5.4 3.2 9S14.1 18.6 12 21" />
      <path d="M12 3C9.9 5.4 8.8 8.4 8.8 12S9.9 18.6 12 21" />
    </svg>
  );
}

function GearIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 15.5A3.5 3.5 0 1 0 12 8a3.5 3.5 0 0 0 0 7.5Z" />
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1-1.5 1.7 1.7 0 0 0-1.9.3l-.1.1A2 2 0 1 1 4.2 17l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1 1.7 1.7 0 0 0-.3-1.9l-.1-.1A2 2 0 1 1 7 4.2l.1.1a1.7 1.7 0 0 0 1.9.3h.1a1.7 1.7 0 0 0 .9-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1A2 2 0 1 1 19.8 7l-.1.1a1.7 1.7 0 0 0-.3 1.9v.1a1.7 1.7 0 0 0 1.5.9h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z" />
    </svg>
  );
}

export default App;
