import { lazy, Suspense } from "react";
import { motion } from "framer-motion";
import { Moon, Globe, Cpu, FileText, ChevronRight } from "lucide-react";
import { AppLanguage, AppTheme } from "../components/ModelSettingsDrawer";

const ReportsPage = lazy(() => import("./ReportsPage"));

interface SettingsPageProps {
  language: AppLanguage;
  theme: AppTheme;
  useLlm: boolean;
  onLanguageChange: (lang: AppLanguage) => void;
  onThemeChange: (theme: AppTheme) => void;
  onUseLlmChange: (val: boolean) => void;
}

const THEME_LABELS: Record<AppTheme, string> = {
  bloomberg: "Bloomberg 终端",
  ocean: "Ocean 深海",
  graphite: "Graphite 石墨",
  "midnight-gold": "午夜金",
  light: "Light 研究",
};

const THEME_CYCLE: AppTheme[] = ["bloomberg", "ocean", "graphite", "midnight-gold", "light"];

function SettingsRow({
  icon: Icon,
  label,
  value,
  onClick,
}: {
  icon: typeof Moon;
  label: string;
  value: string;
  onClick: () => void;
}) {
  return (
    <button
      className="w-full flex items-center justify-between p-4 rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] active:bg-[var(--bg-card-hover)] transition-colors"
      onClick={onClick}
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-xl bg-[var(--bg-elevated)] flex items-center justify-center">
          <Icon size={16} className="text-[var(--ink-secondary)]" />
        </div>
        <span className="text-sm font-medium text-[var(--ink-primary)]">{label}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-[var(--ink-muted)]">{value}</span>
        <ChevronRight size={14} className="text-[var(--ink-dim)]" />
      </div>
    </button>
  );
}

export default function SettingsPage({
  language,
  theme,
  useLlm,
  onLanguageChange,
  onThemeChange,
  onUseLlmChange,
}: SettingsPageProps) {
  const cycleTheme = () => {
    const idx = THEME_CYCLE.indexOf(theme);
    const next = THEME_CYCLE[(idx + 1) % THEME_CYCLE.length];
    onThemeChange(next);
  };

  return (
    <div className="flex flex-col min-h-screen pb-28">
      {/* Header */}
      <motion.div
        className="sticky top-0 z-30 glass-strong px-4 py-4"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h1 className="text-lg font-semibold">设置</h1>
      </motion.div>

      {/* Settings list */}
      <div className="px-4 pt-3 space-y-2">
        <SettingsRow
          icon={Moon}
          label="主题外观"
          value={THEME_LABELS[theme]}
          onClick={cycleTheme}
        />
        <SettingsRow
          icon={Globe}
          label="语言"
          value={language === "zh-CN" ? "简体中文" : "English"}
          onClick={() => onLanguageChange(language === "zh-CN" ? "en" : "zh-CN")}
        />
        <button
          className="w-full flex items-center justify-between p-4 rounded-2xl border border-[var(--border-card)] bg-[var(--bg-card)] active:bg-[var(--bg-card-hover)] transition-colors"
          onClick={() => onUseLlmChange(!useLlm)}
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-[var(--bg-elevated)] flex items-center justify-center">
              <Cpu size={16} className="text-[var(--ink-secondary)]" />
            </div>
            <span className="text-sm font-medium text-[var(--ink-primary)]">AI 模型</span>
          </div>
          <div className={`w-11 h-7 rounded-full flex items-center px-0.5 transition-colors ${
            useLlm ? "bg-[var(--accent)]" : "bg-[var(--ink-dim)]"
          }`}>
            <motion.div
              className="w-6 h-6 bg-white rounded-full shadow-md"
              animate={{ x: useLlm ? 16 : 0 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            />
          </div>
        </button>
      </div>

      {/* Reports section */}
      <div className="px-4 pt-6">
        <div className="flex items-center gap-2 mb-3">
          <FileText size={14} className="text-[var(--ink-muted)]" />
          <span className="text-xs font-semibold text-[var(--ink-secondary)] uppercase tracking-wider">
            报告库
          </span>
        </div>
        <Suspense
          fallback={
            <div className="space-y-2">
              <div className="skeleton h-16 w-full rounded-2xl" />
              <div className="skeleton h-16 w-full rounded-2xl" />
            </div>
          }
        >
          <ReportsPage onOpenResearch={() => {}} />
        </Suspense>
      </div>
    </div>
  );
}
