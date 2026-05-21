import { motion, AnimatePresence } from "framer-motion";
import { X, Brain, Globe, Palette } from "lucide-react";

export type AppLanguage = "zh-CN" | "en";
export type AppTheme = "bloomberg" | "ocean" | "graphite" | "midnight-gold" | "light";

interface Props {
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
    title: "系统设置",
    llmTitle: "AI 模型调用",
    llmBody: "关闭后，报告生成和研究对话使用规则型摘要，不调用 DeepSeek。",
    on: "已开启",
    off: "已关闭",
    language: "界面语言",
    zh: "简体中文",
    en: "English",
    theme: "系统配色",
    themes: {
      bloomberg: "Bloomberg 终端",
      ocean: "Ocean 深海",
      graphite: "Graphite 石墨",
      "midnight-gold": "午夜金",
      light: "Light 研究",
    },
  },
  en: {
    title: "Settings",
    llmTitle: "AI Model",
    llmBody: "When off, reports and research use rule-based summaries instead of DeepSeek.",
    on: "On",
    off: "Off",
    language: "Language",
    zh: "简体中文",
    en: "English",
    theme: "Theme",
    themes: {
      bloomberg: "Bloomberg Terminal",
      ocean: "Ocean Depth",
      graphite: "Graphite",
      "midnight-gold": "Midnight Gold",
      light: "Light Research",
    },
  },
} as const;

const themeOptions: AppTheme[] = ["bloomberg", "ocean", "graphite", "midnight-gold", "light"];

type ThemeColor = { from: string; to: string };

const themePreview: Record<AppTheme, ThemeColor> = {
  bloomberg: { from: "#000000", to: "#F5A623" },
  ocean: { from: "#060B16", to: "#38BDF8" },
  graphite: { from: "#121418", to: "#A0AEC0" },
  "midnight-gold": { from: "#080808", to: "#C9A96E" },
  light: { from: "#F8FAFC", to: "#3B5998" },
};

export default function ModelSettingsDrawer({
  open,
  useLlm,
  language,
  theme,
  onToggleOpen,
  onUseLlmChange,
  onLanguageChange,
  onThemeChange,
}: Props) {
  const t = copy[language];

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onToggleOpen}
          />

          {/* Bottom sheet */}
          <motion.aside
            className="fixed bottom-0 left-0 right-0 z-50 max-h-[85vh] overflow-y-auto rounded-t-3xl bg-[var(--bg-primary)] border-t border-[var(--border-card)] shadow-2xl"
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", stiffness: 400, damping: 40 }}
          >
            {/* Drag handle */}
            <div className="sticky top-0 z-10 bg-[var(--bg-primary)] pt-3 pb-2 flex justify-center rounded-t-3xl">
              <div className="w-10 h-1 rounded-full bg-[var(--ink-dim)]" />
            </div>

            {/* Header */}
            <div className="px-5 pb-2 flex items-center justify-between">
              <h2 className="text-lg font-bold text-[var(--ink-primary)]">{t.title}</h2>
              <button
                onClick={onToggleOpen}
                className="w-8 h-8 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-card)] flex items-center justify-center text-[var(--ink-muted)] active:scale-90 transition-transform"
              >
                <X size={14} />
              </button>
            </div>

            <div className="px-5 pb-8 space-y-3">
              {/* LLM toggle */}
              <div className="rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-[var(--accent-soft)] flex items-center justify-center">
                      <Brain size={18} className="text-[var(--accent)]" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-[var(--ink-primary)]">{t.llmTitle}</p>
                      <p className="text-[11px] text-[var(--ink-muted)] mt-0.5 max-w-[220px]">{t.llmBody}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => onUseLlmChange(!useLlm)}
                    className={`relative w-11 h-7 rounded-full flex items-center px-0.5 transition-colors ${
                      useLlm ? "bg-[var(--accent)]" : "bg-[var(--ink-dim)]"
                    }`}
                  >
                    <motion.div
                      className="w-6 h-6 bg-white rounded-full shadow-md"
                      animate={{ x: useLlm ? 16 : 0 }}
                      transition={{ type: "spring", stiffness: 500, damping: 30 }}
                    />
                  </button>
                </div>
                <p className="mt-3 text-[11px] text-[var(--ink-muted)]">
                  {useLlm ? t.on : t.off}
                </p>
              </div>

              {/* Language */}
              <div className="rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-xl bg-[var(--bg-elevated)] flex items-center justify-center">
                    <Globe size={18} className="text-[var(--ink-secondary)]" />
                  </div>
                  <p className="text-sm font-semibold text-[var(--ink-primary)]">{t.language}</p>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={() => onLanguageChange("zh-CN")}
                    className={`py-2.5 px-4 rounded-xl text-sm font-medium transition-all active:scale-95 ${
                      language === "zh-CN"
                        ? "bg-[var(--accent)] text-white"
                        : "bg-[var(--bg-elevated)] text-[var(--ink-secondary)] border border-[var(--border-card)]"
                    }`}
                  >
                    {t.zh}
                  </button>
                  <button
                    onClick={() => onLanguageChange("en")}
                    className={`py-2.5 px-4 rounded-xl text-sm font-medium transition-all active:scale-95 ${
                      language === "en"
                        ? "bg-[var(--accent)] text-white"
                        : "bg-[var(--bg-elevated)] text-[var(--ink-secondary)] border border-[var(--border-card)]"
                    }`}
                  >
                    {t.en}
                  </button>
                </div>
              </div>

              {/* Theme */}
              <div className="rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] p-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-9 h-9 rounded-xl bg-[var(--bg-elevated)] flex items-center justify-center">
                    <Palette size={18} className="text-[var(--ink-secondary)]" />
                  </div>
                  <p className="text-sm font-semibold text-[var(--ink-primary)]">{t.theme}</p>
                </div>
                <div className="grid grid-cols-1 gap-2">
                  {themeOptions.map((item) => {
                    const prev = themePreview[item];
                    return (
                      <button
                        key={item}
                        onClick={() => onThemeChange(item)}
                        className={`flex items-center gap-3 py-3 px-4 rounded-xl text-sm font-medium transition-all active:scale-[0.98] ${
                          theme === item
                            ? "bg-[var(--accent-soft)] border border-[var(--accent)]/30 text-[var(--accent)]"
                            : "bg-[var(--bg-elevated)] border border-[var(--border-card)] text-[var(--ink-secondary)]"
                        }`}
                      >
                        <div
                          className="w-8 h-8 rounded-lg border border-[var(--border-card)] shrink-0"
                          style={{
                            background: `linear-gradient(135deg, ${prev.from} 50%, ${prev.to} 100%)`,
                          }}
                        />
                        <div className="text-left">
                          <span className="text-sm font-semibold">{t.themes[item]}</span>
                        </div>
                        {theme === item && (
                          <div className="ml-auto w-5 h-5 rounded-full bg-[var(--accent)] flex items-center justify-center">
                            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                              <path d="M2.5 6L5 8.5L9.5 3.5" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                            </svg>
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
