interface NewsRiskTagsProps {
  tags: string[];
}

const labelMap: Record<string, string> = {
  地缘风险: "地缘风险",
  监管风险: "监管风险",
  流动性风险: "流动性风险",
  信用风险: "信用风险",
  市场波动: "市场波动",
  政策收紧: "政策收紧",
  政策宽松: "政策宽松",
  经济衰退: "经济衰退",
  通胀压力: "通胀压力",
  汇率风险: "汇率风险",
  行业利空: "行业利空",
  行业利好: "行业利好",
  公司负面: "公司负面",
  公司正面: "公司正面",
  突发事件: "突发事件",
  // Legacy key fallback
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
    return <span className="rounded-full border border-line bg-[var(--bg-card)] px-2 py-1 text-xs text-muted">未标注</span>;
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
