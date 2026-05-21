import { motion } from "framer-motion";

interface SparklinePoint {
  date: string;
  close: number | null;
}

interface Props {
  name: string;
  symbol: string;
  price: number | null;
  change: number | null;
  changePct: number | null;
  sparkline: SparklinePoint[];
  onClick?: () => void;
}

function MiniSparkline({ data, isUp }: { data: SparklinePoint[]; isUp: boolean }) {
  const valid = data.filter((d) => d.close != null).map((d) => d.close!);
  if (valid.length < 2) return <div className="h-full w-full" />;

  const min = Math.min(...valid);
  const max = Math.max(...valid);
  const range = max - min || 1;
  const w = 114;
  const h = 28;

  const points = valid
    .map((v, i) => {
      const x = 2 + (i / (valid.length - 1)) * (w - 4);
      const y = h - 2 - ((v - min) / range) * (h - 4);
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");

  const areaPath = `${points} L${(w - 2).toFixed(1)},${h} L${2},${h} Z`;

  const color = isUp ? "var(--up)" : "var(--down)";
  const fillColor = isUp ? "var(--up-soft)" : "var(--down-soft)";

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-full" preserveAspectRatio="none">
      <path d={areaPath} fill={fillColor} />
      <path d={points} fill="none" stroke={color} strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

const glowStyle = (isUp: boolean, isDown: boolean) => {
  if (isUp) return { border: "1px solid var(--up-soft)", background: "var(--bg-card)" };
  if (isDown) return { border: "1px solid var(--down-soft)", background: "var(--bg-card)" };
  return { border: "1px solid var(--border-card)", background: "var(--bg-card)" };
};

export default function IndexCard({ name, price, change, changePct, sparkline, onClick }: Props) {
  const isUp = changePct != null && changePct > 0;
  const isDown = changePct != null && changePct < 0;
  const style = glowStyle(isUp, isDown);

  return (
    <motion.div
      className="flex-shrink-0 w-[138px] p-3 rounded-2xl cursor-pointer select-none shadow-sm"
      style={style}
      onClick={onClick}
      whileTap={{ scale: 0.97 }}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <div className="text-[10px] font-medium text-[var(--ink-muted)] truncate uppercase tracking-wide">{name}</div>
      <div className="h-7 my-1.5"><MiniSparkline data={sparkline} isUp={isUp} /></div>
      <div className="text-financial text-sm font-bold text-[var(--ink-primary)]">
        {price != null
          ? price >= 100
            ? price.toLocaleString("zh-CN", { maximumFractionDigits: 0 })
            : price.toLocaleString("zh-CN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
          : "-"}
      </div>
      <div className={`text-financial text-[11px] font-semibold mt-0.5 ${isUp ? "text-up" : isDown ? "text-down" : "text-[var(--ink-muted)]"}`}>
        {change != null ? `${change >= 0 ? "+" : ""}${change.toFixed(2)}` : "--"}{"  "}
        {changePct != null ? `${changePct >= 0 ? "+" : ""}${changePct.toFixed(2)}%` : "--"}
      </div>
    </motion.div>
  );
}
