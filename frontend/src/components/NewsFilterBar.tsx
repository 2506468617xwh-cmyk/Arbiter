interface NewsFilterBarProps {
  market: string;
  topic: string;
  symbol: string;
  keyword: string;
  onMarketChange: (value: string) => void;
  onTopicChange: (value: string) => void;
  onSymbolChange: (value: string) => void;
  onKeywordChange: (value: string) => void;
  onRefresh: () => void;
  onSearch: () => void;
  onSymbolSearch: () => void;
  onCollect: () => void;
  loading: boolean;
  collecting: boolean;
}

const markets = ["ALL", "CN", "US", "HK", "GLOBAL"];
const topics = ["", "央行政策", "财政政策", "宏观经济", "通胀", "就业", "贸易", "科技", "能源", "金融", "房地产", "消费", "医疗", "军事", "企业财报", "并购重组", "融资上市", "大宗商品", "加密货币", "外汇"];

function NewsFilterBar(props: NewsFilterBarProps) {
  return (
    <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="grid gap-3 lg:grid-cols-[140px_180px_1fr_1fr_auto]">
        <select className="rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand" value={props.market} onChange={(e) => props.onMarketChange(e.target.value)}>
          {markets.map((item) => <option key={item}>{item}</option>)}
        </select>
        <select className="rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand" value={props.topic} onChange={(e) => props.onTopicChange(e.target.value)}>
          {topics.map((item) => <option key={item} value={item}>{item || "全部主题"}</option>)}
        </select>
        <input className="rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand" value={props.symbol} onChange={(e) => props.onSymbolChange(e.target.value)} placeholder="股票代码，如 TSLA.US / 700.HK" />
        <input className="rounded-lg border border-line bg-[var(--bg-card)] px-3 py-2 text-sm outline-none focus:border-brand" value={props.keyword} onChange={(e) => props.onKeywordChange(e.target.value)} placeholder="关键词，如 Federal Reserve / AI chips" />
        <div className="flex flex-wrap gap-2">
          <button className="secondary-button px-3 py-2 text-sm" onClick={props.onRefresh} disabled={props.loading}>刷新</button>
          <button className="secondary-button px-3 py-2 text-sm" onClick={props.onSymbolSearch} disabled={props.loading}>查股票</button>
          <button className="secondary-button px-3 py-2 text-sm" onClick={props.onSearch} disabled={props.loading}>搜索</button>
          <button className="primary-button px-3 py-2 text-sm" onClick={props.onCollect} disabled={props.collecting}>{props.collecting ? "更新中..." : "更新新闻"}</button>
        </div>
      </div>
    </section>
  );
}

export default NewsFilterBar;
