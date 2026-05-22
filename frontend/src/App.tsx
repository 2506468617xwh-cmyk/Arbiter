import React, { useState, useEffect, useRef, lazy, Suspense } from "react";
import BottomNav, { TabKey } from "./components/BottomNav";
import ModelSettingsDrawer, { AppLanguage, AppTheme } from "./components/ModelSettingsDrawer";
import { I18nProvider } from "./i18n";
import { installDomTranslator } from "./i18n-dom";

// Lazy-load pages
const HomePage = lazy(() => import("./pages/HomePage"));
const MarketsPage = lazy(() => import("./pages/MarketsPage"));
const WatchlistPage = lazy(() => import("./pages/WatchlistPage"));
const NewsPage = lazy(() => import("./pages/NewsPage"));
const InstitutePage = lazy(() => import("./pages/InstitutePage")) as unknown as React.ComponentType<{ useLlm: boolean }>;

function isLanguage(value: string | null): value is AppLanguage {
  return value === "zh-CN" || value === "en";
}

function isTheme(value: string | null): value is AppTheme {
  return value === "bloomberg" || value === "ocean" || value === "graphite" || value === "midnight-gold" || value === "light";
}

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="space-y-3 w-full max-w-xs px-4">
        <div className="skeleton h-4 w-3/4" />
        <div className="skeleton h-32 w-full rounded-2xl" />
        <div className="skeleton h-20 w-full rounded-2xl" />
        <div className="skeleton h-24 w-full rounded-2xl" />
      </div>
    </div>
  );
}

// Keep pages mounted, just toggle visibility — preserves state & avoids refetching
function PageSlot({ show, children }: { show: boolean; children: React.ReactNode }) {
  return (
    <div style={{ display: show ? "block" : "none" }} aria-hidden={!show}>
      {children}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<TabKey>("home");
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [language, setLanguage] = useState<AppLanguage>(() => {
    const saved = window.localStorage.getItem("rabot_language");
    return isLanguage(saved) ? saved : "zh-CN";
  });
  const [useLlm, setUseLlm] = useState(() => {
    const saved = window.localStorage.getItem("rabot_use_llm");
    return saved === null ? true : saved === "true";
  });
  const [theme, setTheme] = useState<AppTheme>(() => {
    const saved = window.localStorage.getItem("rabot_theme");
    return isTheme(saved) ? saved : "graphite";
  });

  // Track which tabs have been mounted (lazy mount once, keep alive)
  const mountedTabs = useRef<Set<TabKey>>(new Set(["home"]));
  if (!mountedTabs.current.has(tab)) {
    mountedTabs.current.add(tab);
  }
  const mounted = mountedTabs.current;

  // Persist settings
  useEffect(() => {
    window.localStorage.setItem("rabot_language", language);
    document.documentElement.lang = language === "en" ? "en" : "zh-CN";
  }, [language]);

  useEffect(() => {
    window.localStorage.setItem("rabot_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
  }, [theme]);

  useEffect(() => {
    window.localStorage.setItem("rabot_use_llm", String(useLlm));
  }, [useLlm]);

  // DOM translator
  useEffect(() => {
    let cleanup = () => {};
    const timer = window.setTimeout(() => {
      cleanup = installDomTranslator(language);
    }, 0);
    return () => {
      window.clearTimeout(timer);
      cleanup();
    };
  }, [language, tab]);

  return (
    <I18nProvider language={language}>
      <div className="min-h-screen bg-[var(--bg-deep)] text-[var(--ink-primary)]">
        <ModelSettingsDrawer
          open={settingsOpen}
          useLlm={useLlm}
          language={language}
          theme={theme}
          onToggleOpen={() => setSettingsOpen((v) => !v)}
          onUseLlmChange={setUseLlm}
          onLanguageChange={setLanguage}
          onThemeChange={setTheme}
        />

        <main className="min-h-screen pb-20">
          <Suspense fallback={<PageLoader />}>
            <PageSlot show={tab === "home"}>
              {mounted.has("home") && <HomePage onNavigate={setTab} onOpenSettings={() => setSettingsOpen(true)} />}
            </PageSlot>
            <PageSlot show={tab === "markets"}>
              {mounted.has("markets") && <MarketsPage useLlm={useLlm} language={language} />}
            </PageSlot>
            <PageSlot show={tab === "watchlist"}>
              {mounted.has("watchlist") && <WatchlistPage />}
            </PageSlot>
            <PageSlot show={tab === "news"}>
              {mounted.has("news") && <NewsPage />}
            </PageSlot>
            <PageSlot show={tab === "research"}>
              {mounted.has("research") && <InstitutePage useLlm={useLlm} />}
            </PageSlot>
          </Suspense>
        </main>

        <BottomNav active={tab} onTabChange={setTab} />
      </div>
    </I18nProvider>
  );
}
