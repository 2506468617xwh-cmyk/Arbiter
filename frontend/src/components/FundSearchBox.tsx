import { FormEvent } from "react";

const examples = ["510300.SH", "513100.SH", "QQQ.US", "SPY.US", "2800.HK"];

function FundSearchBox({
  value,
  loading,
  onChange,
  onSubmit
}: {
  value: string;
  loading: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit();
  };
  return (
    <form className="rounded-lg border border-line bg-panel p-5 shadow-soft" onSubmit={submit}>
      <div className="flex flex-col gap-3 md:flex-row">
        <input
          className="min-h-11 flex-1 rounded-lg border border-line bg-white px-4 text-sm outline-none focus:border-brand"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder="输入基金/ETF代码，如 510300.SH / 513100.SH / QQQ.US / 2800.HK"
        />
        <button className="primary-button min-h-11" type="submit" disabled={loading}>
          {loading ? "分析中..." : "开始分析"}
        </button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {examples.map((item) => (
          <button key={item} type="button" className="rounded-lg border border-line bg-[#fffaf2] px-3 py-1.5 text-xs text-muted hover:text-ink" onClick={() => onChange(item)}>
            {item}
          </button>
        ))}
      </div>
    </form>
  );
}

export default FundSearchBox;

