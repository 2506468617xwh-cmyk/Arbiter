import { motion } from "framer-motion";
import { Home, TrendingUp, Star, Newspaper, MessageCircle } from "lucide-react";

export type TabKey = "home" | "markets" | "watchlist" | "news" | "research";

interface BottomNavProps {
  active: TabKey;
  onTabChange: (tab: TabKey) => void;
}

const tabs: { key: TabKey; icon: typeof Home; labelZh: string; labelEn: string }[] = [
  { key: "home", icon: Home, labelZh: "首页", labelEn: "Home" },
  { key: "markets", icon: TrendingUp, labelZh: "行情", labelEn: "Markets" },
  { key: "watchlist", icon: Star, labelZh: "自选", labelEn: "Watch" },
  { key: "news", icon: Newspaper, labelZh: "资讯", labelEn: "News" },
  { key: "research", icon: MessageCircle, labelZh: "研究", labelEn: "AI" },
];

export default function BottomNav({ active, onTabChange }: BottomNavProps) {
  return (
    <nav className="bottom-nav">
      {tabs.map(({ key, icon: Icon, labelZh }) => {
        const isActive = active === key;
        return (
          <button
            key={key}
            onClick={() => onTabChange(key)}
            className="bottom-nav-item"
          >
            <motion.div
              animate={{ scale: isActive ? 1.08 : 0.94 }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className="flex flex-col items-center gap-1"
            >
              <Icon
                size={20}
                strokeWidth={isActive ? 2.4 : 1.6}
                className={isActive ? "text-[var(--accent)]" : "text-[var(--ink-dim)]"}
              />
              <span
                className={`text-[10px] font-semibold leading-none tracking-wide transition-colors ${
                  isActive ? "text-[var(--accent)]" : "text-[var(--ink-dim)]"
                }`}
              >
                {labelZh}
              </span>
            </motion.div>
            {isActive && (
              <motion.div
                layoutId="nav-indicator"
                className="absolute top-0 left-1/4 right-1/4 h-0.5 rounded-full bg-[var(--accent)]"
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        );
      })}
    </nav>
  );
}
