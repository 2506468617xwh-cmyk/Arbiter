import { Flag, TrendingUp, TrendingDown } from "lucide-react";

export type RegionKey = "CN" | "US" | "HK";

const FLAG_COLORS: Record<RegionKey, { bg: string; accent: string; stars?: string }> = {
  CN: { bg: "#DE2910", accent: "#FFDE00" },
  US: { bg: "#002868", accent: "#BF0A30", stars: "#FFFFFF" },
  HK: { bg: "#DE2910", accent: "#FFFFFF" },
};

function CNFlag() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4">
      <rect x="2" y="4" width="20" height="16" rx="1" fill="#DE2910" />
      <path d="M9 8l1.2 3.5h3.8l-3 2.2 1.1 3.5-3.1-2.3-3 2.3 1-3.5-3-2.2h3.8z" fill="#FFDE00" />
    </svg>
  );
}

function USFlag() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4">
      <rect x="2" y="4" width="20" height="16" rx="1" fill="#fff" stroke="#ddd" strokeWidth="0.5" />
      <rect x="2" y="4" width="9" height="9" rx="0.5" fill="#002868" />
      {[5, 7, 9].map((y) => [4, 6, 8].map((x) => (
        <circle key={`s${x}${y}`} cx={x} cy={y} r="0.45" fill="#fff" />
      )))}
      <circle cx="6.5" cy="6.5" r="0.45" fill="#fff" />
      {[4, 6, 8, 10, 12, 14, 16, 18, 20].map((y, i) => (
        <rect key={y} x="2" y={y} width="20" height="1.2" fill={i % 2 === 0 ? "#BF0A30" : "#fff"} />
      ))}
    </svg>
  );
}

function HKFlag() {
  return (
    <svg viewBox="0 0 24 24" className="w-4 h-4">
      <rect x="2" y="4" width="20" height="16" rx="1" fill="#DE2910" />
      <g transform="translate(12,12) scale(0.55)">
        {[0, 72, 144, 216, 288].map((deg) => (
          <path key={deg} d="M0-7L1.5-2.5L6-2.5L2.5 0.5L3.5 5L0 2.5L-3.5 5L-2.5 0.5L-6-2.5L-1.5-2.5Z" fill="#fff" transform={`rotate(${deg})`} />
        ))}
      </g>
    </svg>
  );
}

export default function FlagIcon({ region }: { region: RegionKey }) {
  if (region === "CN") return <CNFlag />;
  if (region === "US") return <USFlag />;
  return <HKFlag />;
}

export const REGIONS: { key: RegionKey; label: string }[] = [
  { key: "CN", label: "中国" },
  { key: "US", label: "美国" },
  { key: "HK", label: "香港" },
];
