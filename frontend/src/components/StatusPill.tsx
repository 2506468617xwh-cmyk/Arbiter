interface StatusPillProps {
  status: string;
}

export default function StatusPill({ status }: StatusPillProps) {
  const isConnected = status === "connected";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-[11px] font-medium border ${
        isConnected
          ? "border-[var(--down)]/30 bg-[var(--down-soft)] text-[var(--down)]"
          : "border-amber-400/30 bg-amber-400/10 text-amber-400"
      }`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${isConnected ? "bg-[var(--down)]" : "bg-amber-400"}`} />
      {isConnected ? "数据已连接" : "等待数据"}
    </span>
  );
}
