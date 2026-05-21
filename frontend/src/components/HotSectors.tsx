import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Cpu, Bot, Sparkles, Zap, Smartphone, Pill, Shield, Building2, Cloud, Car } from "lucide-react";

interface Sector {
  name: string;
  icon: typeof Cpu;
  changePct: number;
}

const SECTORS: Sector[] = [
  { name: "芯片半导体", icon: Cpu, changePct: 5.57 },
  { name: "机器人", icon: Bot, changePct: 5.09 },
  { name: "AIGC", icon: Sparkles, changePct: 0.72 },
  { name: "新能源", icon: Zap, changePct: -1.23 },
  { name: "消费电子", icon: Smartphone, changePct: 2.34 },
  { name: "生物医药", icon: Pill, changePct: -0.89 },
  { name: "国防军工", icon: Shield, changePct: 1.45 },
  { name: "银行金融", icon: Building2, changePct: -0.34 },
  { name: "云计算", icon: Cloud, changePct: 3.21 },
  { name: "自动驾驶", icon: Car, changePct: 4.56 },
];

export default function HotSectors() {
  const sorted = [...SECTORS].sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct));

  return (
    <div className="px-4 space-y-1.5">
      <div className="flex items-center justify-between h-5">
        <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-[var(--ink-muted)]">热门板块</span>
        <span className="text-[9px] text-[var(--ink-dim)] font-mono">按热度排序</span>
      </div>

      <div className="grid grid-cols-2 gap-1">
        {sorted.map((sector, i) => {
          const isUp = sector.changePct > 0;
          const Icon = sector.icon;
          return (
            <motion.div
              key={sector.name}
              className="flex items-center justify-between px-2.5 py-2 border border-[var(--border-subtle)] bg-[var(--bg-card)] cursor-pointer select-none"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.1 + i * 0.02, duration: 0.2 }}
              whileTap={{ scale: 0.98 }}
            >
              <div className="flex items-center gap-1.5 min-w-0">
                <Icon size={12} className="text-[var(--ink-dim)] shrink-0" />
                <span className="text-[11px] font-medium text-[var(--ink-primary)] truncate">{sector.name}</span>
              </div>
              <span className={`text-financial text-[11px] font-bold shrink-0 ml-1 ${isUp ? "text-up" : "text-down"}`}>
                {isUp ? "+" : ""}{sector.changePct.toFixed(2)}%
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
