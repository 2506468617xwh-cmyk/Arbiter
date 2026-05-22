export type RegionKey = "CN" | "US" | "HK";

function HKFlag() {
  return (
    <svg viewBox="0 0 24 24" className="w-5 h-5">
      <rect x="2" y="4" width="20" height="16" rx="1" fill="#DE2910" />
      <g transform="translate(12,12) scale(0.55)">
        {[0, 72, 144, 216, 288].map((deg) => (
          <path key={deg} d="M0-7L1.5-2.5L6-2.5L2.5 0.5L3.5 5L0 2.5L-3.5 5L-2.5 0.5L-6-2.5L-1.5-2.5Z" fill="#fff" transform={`rotate(${deg})`} />
        ))}
      </g>
    </svg>
  );
}

// Flag images at fixed 24x16 aspect ratio, displayed at consistent 20x13 pixels
const flagStyle: React.CSSProperties = {
  width: 20,
  height: 13,
  objectFit: "cover",
  borderRadius: 1,
  flexShrink: 0,
};

export default function FlagIcon({ region }: { region: RegionKey }) {
  if (region === "CN") return <img src="/cn.png" alt="CN" style={flagStyle} />;
  if (region === "US") return <img src="/us.png" alt="US" style={flagStyle} />;
  return <HKFlag />;
}

export const REGIONS: { key: RegionKey; label: string }[] = [
  { key: "CN", label: "CN" },
  { key: "US", label: "US" },
  { key: "HK", label: "HK" },
];
