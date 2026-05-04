import { AppLanguage } from "./components/ModelSettingsDrawer";

const exactEn: Record<string, string> = {
  "首页": "Home",
  "仪表盘": "Dashboard",
  "热力图": "Heatmap",
  "走势图": "Charts",
  "单资产": "Asset",
  "个股分析": "Stock Analysis",
  "基金 ETF": "Funds & ETFs",
  "多资产": "Multi Asset",
  "宏观研究": "Macro Research",
  "新闻雷达": "News Radar",
  "AI 研究": "AI Research",
  "研究生成": "Report Generator",
  "报告库": "Report Library",
  "首页导览": "Home Guide",
  "市场仪表盘": "Market Dashboard",
  "市场热力榜": "Market Heatmap",
  "单资产研究": "Single Asset Research",
  "多资产研究": "Multi-Asset Research",
  "保持谦逊，永远不要预测市场": "Stay humble. Never predict the market.",
  "刷新概览": "Refresh",
  "刷新中...": "Refreshing...",
  "查看报告库": "Open Reports",
  "重试": "Retry",
  "正在读取本地研究数据...": "Reading local research data...",
  "市场状态": "Market Status",
  "指数数量": "Indexes",
  "新闻数量": "News",
  "报告数量": "Reports",
  "最后更新": "Last Update",
  "已连接": "Connected",
  "待更新": "Pending",
  "最新可展示行情": "Latest displayable market data",
  "本地新闻样本": "Local news sample",
  "最新指标覆盖": "Latest macro coverage",
  "等待报告生成": "Waiting for report generation",
  "等待接口返回。": "Waiting for API response.",
  "市场观察": "Market Observation",
  "新闻风险": "News Risk",
  "宏观温度": "Macro Temperature",
  "报告状态": "Report Status",
  "数据说明": "Data Notes",
  "提示": "Notice",
  "暂无数据": "No data",
  "暂无摘要。": "No summary yet.",
  "暂无市场摘要。": "No market summary yet.",
  "暂无新闻摘要。": "No news summary yet.",
  "暂无宏观摘要。": "No macro summary yet.",
  "暂无报告摘要。": "No report summary yet.",
  "刷新": "Refresh",
  "搜索": "Search",
  "更新新闻": "Update News",
  "新闻列表": "News List",
  "来源覆盖": "Source Coverage",
  "打开原文链接": "Open Source",
  "摘要": "Summary",
  "市场 / 主题 / 代码": "Market / Topic / Symbol",
  "情绪分": "Sentiment Score",
  "未知来源": "Unknown Source",
  "未标注": "Untagged",
  "质量": "Quality",
  "重要性": "Importance",
  "来源": "Source",
  "代码": "Symbol",
  "名称": "Name",
  "最新日期": "Latest Date",
  "更新时间": "Updated At",
  "资产数量": "Assets",
  "本地行情覆盖": "Local market coverage",
  "总览判断": "Overview",
  "强势资产": "Strong Assets",
  "弱势资产": "Weak Assets",
  "高波动资产": "High Volatility",
  "高回撤资产": "High Drawdown",
  "资产热力排行": "Asset Heat Ranking",
  "资产库": "Asset Universe",
  "资产库多选": "Asset Universe",
  "指标": "Metric",
  "开始日期": "Start Date",
  "结束日期": "End Date",
  "读取": "Load",
  "分析": "Analyze",
  "开始分析": "Start Analysis",
  "分析中...": "Analyzing...",
  "股票代码": "Stock Symbol",
  "基金/ETF 代码": "Fund/ETF Symbol",
  "基金/ETF 名称": "Fund/ETF Name",
  "最新净值": "Latest NAV",
  "最新价": "Latest Price",
  "昨收": "Previous Close",
  "折溢价": "Premium/Discount",
  "成交量": "Volume",
  "成交额": "Turnover",
  "核心指标": "Key Indicators",
  "技术指标": "Technical Indicators",
  "资产类别与风险": "Allocation & Risk",
  "资产类别判断": "Allocation View",
  "主要风险": "Key Risks",
  "流动性观察": "Liquidity View",
  "定投适配度观察": "DCA Fit Observation",
  "研究摘要": "Research Summary",
  "基金/ETF 研究对话": "Fund/ETF Research Chat",
  "询问 RAbot": "Ask RAbot",
  "大盘基准": "Market Benchmark",
  "基金/ETF vs 大盘走势": "Fund/ETF vs Benchmark",
  "个股 vs 大盘走势": "Stock vs Benchmark",
  "归一化表现，起点 = 100": "Normalized performance, first point = 100",
  "原始值": "Raw Value",
  "个股": "Stock",
  "大盘": "Benchmark",
  "趋势与风险": "Trend & Risk",
  "趋势摘要": "Trend Summary",
  "风险摘要": "Risk Summary",
  "本分析仅用于研究与学习，不构成任何投资建议。": "For research and learning only. Not investment advice.",
  "宏观数据": "Macro Data",
  "刷新宏观数据": "Refresh Macro Data",
  "宏观指标": "Macro Indicators",
  "地区数": "Regions",
  "类别数": "Categories",
  "最新观测": "Latest Observation",
  "地区": "Region",
  "类别": "Category",
  "单位": "Unit",
  "最新值": "Latest Value",
  "变化": "Change",
  "趋势": "Trend",
  "宏观问答": "Macro Q&A",
  "研究范围": "Research Scope",
  "全市场": "Market",
  "多资产组合": "Multi-Asset",
  "一键快评": "Quick Summary",
  "模型设置": "Model Settings",
  "报告类型": "Report Type",
  "研究风格": "Research Style",
  "报告板块": "Report Sections",
  "调用大模型": "Use LLM",
  "额外要求": "Extra Instructions",
  "生成研究报告": "Generate Report",
  "任务状态": "Task Status",
  "创建时间": "Created",
  "开始时间": "Started",
  "完成时间": "Finished",
  "报告已生成，正在下方展示最新内容。": "Report generated. Loading the latest content below.",
  "查看最新报告": "Open Latest",
  "刷新列表": "Refresh List",
  "导出当前报告 PDF": "Export Current Report PDF",
  "准备导出...": "Preparing Export...",
  "删除": "Delete",
  "导出 PDF": "Export PDF",
  "正在读取报告...": "Reading report...",
  "报告内容": "Report Content",
  "系统设置": "System Settings",
  "语言": "Language",
  "系统配色": "Theme",
  "默认暖色": "Default Warm",
  "白 + 红": "White + Red",
  "黑 + 蓝": "Black + Blue",
  "白 + 绿": "White + Green",
  "黑 + 金": "Black + Gold",
  "开启": "On",
  "关闭": "Off",
  "当前状态": "Status",
  "收起": "Close"
};

const prefixEn: Array<[string, string]> = [
  ["最新文件：", "Latest file: "],
  ["模型：", "Model: "],
  ["当前状态：", "Status: "],
  ["抓取 ", "Fetched "],
  ["入库 ", "Saved "],
  [" 条", " items"],
  [" 条", " items"],
  [" 条", " items"]
];

function translateText(text: string): string {
  const trimmed = text.trim();
  if (!trimmed) return text;
  if (exactEn[trimmed]) {
    return text.replace(trimmed, exactEn[trimmed]);
  }
  let next = text;
  for (const [from, to] of prefixEn) {
    next = next.split(from).join(to);
  }
  return next;
}

function shouldSkipElement(element: Element | null): boolean {
  if (!element) return true;
  const tag = element.tagName.toLowerCase();
  return ["script", "style", "svg", "path", "canvas"].includes(tag);
}

function translateElement(root: ParentNode): void {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  const nodes: Text[] = [];
  while (walker.nextNode()) {
    const node = walker.currentNode as Text;
    if (!shouldSkipElement(node.parentElement)) {
      nodes.push(node);
    }
  }
  nodes.forEach((node) => {
    const next = translateText(node.nodeValue || "");
    if (next !== node.nodeValue) node.nodeValue = next;
  });

  const controls = root instanceof Element ? root.querySelectorAll("input, textarea, option, button, span, p, h1, h2, h3, th, td, label") : document.querySelectorAll("input, textarea, option, button, span, p, h1, h2, h3, th, td, label");
  controls.forEach((element) => {
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      if (element.placeholder) element.placeholder = translateText(element.placeholder);
    }
    if (element instanceof HTMLOptionElement) {
      element.textContent = translateText(element.textContent || "");
    }
    const title = element.getAttribute("title");
    if (title) element.setAttribute("title", translateText(title));
    const label = element.getAttribute("aria-label");
    if (label) element.setAttribute("aria-label", translateText(label));
  });
}

export function installDomTranslator(language: AppLanguage): () => void {
  if (language !== "en") return () => {};
  const run = () => translateElement(document.body);
  run();
  const observer = new MutationObserver((records) => {
    for (const record of records) {
      record.addedNodes.forEach((node) => {
        if (node.nodeType === Node.TEXT_NODE) {
          const text = node as Text;
          text.nodeValue = translateText(text.nodeValue || "");
        } else if (node instanceof Element) {
          translateElement(node);
        }
      });
      if (record.type === "characterData" && record.target.nodeType === Node.TEXT_NODE) {
        const text = record.target as Text;
        const next = translateText(text.nodeValue || "");
        if (next !== text.nodeValue) text.nodeValue = next;
      }
    }
  });
  observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  return () => observer.disconnect();
}
