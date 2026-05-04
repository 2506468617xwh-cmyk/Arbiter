interface NewsRiskTagsProps {
  tags: string[];
}

const labelMap: Record<string, string> = {
  macro_policy: "宏观政策",
  earnings: "财报",
  regulation: "监管",
  geopolitics: "地缘",
  liquidity: "流动性",
  credit: "信用",
  ai_chip: "AI芯片",
  china_market: "中国市场",
  us_market: "美股",
  hk_market: "港股",
  commodity: "商品",
  fx_rate: "汇率"
};

function NewsRiskTags({ tags }: NewsRiskTagsProps) {
  if (!tags.length) {
    return <span className="rounded-full border border-line bg-white px-2 py-1 text-xs text-muted">未标注</span>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {tags.map((tag) => (
        <span key={tag} className="rounded-full border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-900">
          {labelMap[tag] ?? tag}
        </span>
      ))}
    </div>
  );
}

export default NewsRiskTags;
