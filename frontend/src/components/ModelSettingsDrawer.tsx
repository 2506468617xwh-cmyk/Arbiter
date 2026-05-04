export type AppLanguage = "zh-CN" | "en";
export type AppTheme = "warm" | "white-red" | "black-blue" | "white-green" | "black-gold";

interface ModelSettingsDrawerProps {
  open: boolean;
  useLlm: boolean;
  language: AppLanguage;
  theme: AppTheme;
  onToggleOpen: () => void;
  onUseLlmChange: (value: boolean) => void;
  onLanguageChange: (value: AppLanguage) => void;
  onThemeChange: (value: AppTheme) => void;
}

const copy = {
  "zh-CN": {
    eyebrow: "Settings",
    title: "系统设置",
    close: "收起",
    llmTitle: "调用大模型",
    llmBody: "关闭后，报告生成和研究对话默认使用规则型摘要，不调用 DeepSeek。",
    llmStatus: "当前状态",
    on: "开启",
    off: "关闭",
    language: "语言",
    zh: "简体中文",
    en: "English",
    theme: "系统配色",
    themes: {
      warm: "默认暖色",
      "white-red": "白 + 红",
      "black-blue": "黑 + 蓝",
      "white-green": "白 + 绿",
      "black-gold": "黑 + 金"
    }
  },
  en: {
    eyebrow: "Settings",
    title: "System Settings",
    close: "Close",
    llmTitle: "Use LLM",
    llmBody: "When off, reports and research chat use rule-based summaries instead of DeepSeek.",
    llmStatus: "Status",
    on: "On",
    off: "Off",
    language: "Language",
    zh: "Simplified Chinese",
    en: "English",
    theme: "Theme",
    themes: {
      warm: "Default Warm",
      "white-red": "White + Red",
      "black-blue": "Black + Blue",
      "white-green": "White + Green",
      "black-gold": "Black + Gold"
    }
  }
} as const;

const themeOptions: AppTheme[] = ["warm", "white-red", "black-blue", "white-green", "black-gold"];

function ModelSettingsDrawer({
  open,
  useLlm,
  language,
  theme,
  onToggleOpen,
  onUseLlmChange,
  onLanguageChange,
  onThemeChange
}: ModelSettingsDrawerProps) {
  const t = copy[language];
  return (
    <>
      <aside
        className={
          open
            ? "fixed right-0 top-0 z-30 h-full w-[340px] border-l border-line bg-panel p-5 shadow-soft transition-transform"
            : "fixed right-0 top-0 z-30 h-full w-[340px] translate-x-full border-l border-line bg-panel p-5 shadow-soft transition-transform"
        }
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-brand">{t.eyebrow}</p>
            <h2 className="mt-1 text-xl font-semibold text-ink">{t.title}</h2>
          </div>
          <button className="secondary-button px-3 py-1.5" onClick={onToggleOpen}>
            {t.close}
          </button>
        </div>

        <div className="mt-6 rounded-lg border border-line bg-panel p-4">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold text-ink">{t.llmTitle}</p>
              <p className="mt-1 text-xs leading-5 text-muted">{t.llmBody}</p>
            </div>
            <button
              className={useLlm ? "toggle-switch toggle-switch-on" : "toggle-switch"}
              onClick={() => onUseLlmChange(!useLlm)}
              aria-pressed={useLlm}
              aria-label={t.llmTitle}
            >
              <span />
            </button>
          </div>
          <p className="mt-4 text-xs text-muted">
            {t.llmStatus}: {useLlm ? t.on : t.off}
          </p>
        </div>

        <div className="mt-4 rounded-lg border border-line bg-panel p-4">
          <p className="text-sm font-semibold text-ink">{t.language}</p>
          <div className="mt-3 grid grid-cols-2 gap-2">
            <button className={language === "zh-CN" ? "primary-button py-2 text-sm" : "secondary-button py-2 text-sm"} onClick={() => onLanguageChange("zh-CN")}>
              简体中文
            </button>
            <button className={language === "en" ? "primary-button py-2 text-sm" : "secondary-button py-2 text-sm"} onClick={() => onLanguageChange("en")}>
              English
            </button>
          </div>
        </div>

        <div className="mt-4 rounded-lg border border-line bg-panel p-4">
          <p className="text-sm font-semibold text-ink">{t.theme}</p>
          <div className="mt-3 grid gap-2">
            {themeOptions.map((item) => (
              <button
                key={item}
                className={theme === item ? "primary-button py-2 text-left text-sm" : "secondary-button py-2 text-left text-sm"}
                onClick={() => onThemeChange(item)}
              >
                {t.themes[item]}
              </button>
            ))}
          </div>
        </div>
      </aside>
      {open ? <button className="fixed inset-0 z-20 bg-black/20" onClick={onToggleOpen} aria-label={t.close} /> : null}
    </>
  );
}

export default ModelSettingsDrawer;
