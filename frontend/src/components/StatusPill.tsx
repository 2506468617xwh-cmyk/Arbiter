interface StatusPillProps {
  status: string;
}

function StatusPill({ status }: StatusPillProps) {
  const isConnected = status === "connected";
  return (
    <span
      className={
        isConnected
          ? "rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-800"
          : "rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-900"
      }
    >
      {isConnected ? "数据已连接" : "等待数据"}
    </span>
  );
}

export default StatusPill;
