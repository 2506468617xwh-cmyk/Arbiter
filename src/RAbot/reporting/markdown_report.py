# src/RAbot/reporting/markdown_report.py

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from RAbot.analysis.indicators import (
    add_technical_indicators,
    build_asset_performance_table,
)
from RAbot.analysis.macro_research import (
    build_asset_macro_research,
    build_macro_indicator_snapshot,
)
from RAbot.analysis.news_research import (
    build_asset_news_research,
    build_news_market_snapshot,
)
from RAbot.analysis.research_engine import (
    build_market_overview,
    build_single_asset_research,
)
from RAbot.llm.research_writer import RAbotResearchWriter
from RAbot.macro.macro_store import MacroStore
from RAbot.news.news_store import NewsStore
from RAbot.settings import PROJECT_DIR, get_db_path
from RAbot.storage.sqlite_store import SQLiteStore


DEFAULT_FOCUS_ASSETS = [
    "NASDAQ",
    "NASDAQ100",
    "SP500",
    "DOW",
    "RUSSELL2000",
    "CSI300",
    "SSE",
    "CSI500",
    "CSI1000",
    "CHINEXT",
    "STAR50",
    "HSI",
    "GOLD",
    "DXY",
    "WTI",
    "VIX",
]


DEFAULT_LLM_FOCUS_ASSETS = [
    "NASDAQ",
    "SP500",
    "CSI300",
    "SSE",
    "HSI",
    "GOLD",
    "DXY",
]


CATEGORY_LABELS = {
    "rates": "利率",
    "policy_rate": "政策利率",
    "inflation": "通胀",
    "employment": "就业",
    "growth": "增长",
    "liquidity": "流动性",
    "risk_appetite": "风险偏好",
}


REGION_LABELS = {
    "US": "美国",
    "CN": "中国",
}


FREQUENCY_LABELS = {
    "daily": "日度",
    "weekly": "周度",
    "monthly": "月度",
    "quarterly": "季度",
    "annual": "年度",
}


LAST_SAVED_REPORT_PATH: Path | None = None


def get_default_report_output_dir() -> Path:
    output_dir = PROJECT_DIR / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def save_report_text(
    markdown_text: str,
    output_dir: str | Path | None = None,
) -> Path:
    """
    将 Markdown 报告保存为 data/reports 下的 .md 文件。

    这个函数会更新模块级 LAST_SAVED_REPORT_PATH，方便前端或脚本读取刚刚保存的报告路径。
    """
    global LAST_SAVED_REPORT_PATH

    if output_dir is None:
        output_dir = get_default_report_output_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"rabot_global_asset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path = output_dir / filename

    path.write_text(markdown_text, encoding="utf-8")

    LAST_SAVED_REPORT_PATH = path

    return path


def get_last_saved_report_path() -> Path | None:
    return LAST_SAVED_REPORT_PATH


def generate_index_markdown_report(
    focus_assets: list[str] | None = None,
    news_limit: int = 500,
    top_news_limit: int = 8,
    enable_llm: bool = True,
    auto_save: bool = True,
    output_dir: str | Path | None = None,
) -> str:
    """
    生成 RAbot 全球资产研究简报。

    重要修复：
    - 默认 auto_save=True；
    - 只要前端或后台任务调用 generate_index_markdown_report()，报告就会自动落盘到 data/reports；
    - 函数仍然返回 Markdown 正文，兼容原来的调用方式；
    - 如果外部只想拿正文、不想保存，可以显式传入 auto_save=False。
    """
    focus_assets = focus_assets or DEFAULT_FOCUS_ASSETS

    store = SQLiteStore(get_db_path())
    news_store = NewsStore(get_db_path())
    macro_store = MacroStore(get_db_path())

    all_data = _safe_call(lambda: store.read_index_daily(), default=pd.DataFrame())
    all_news = _safe_call(lambda: news_store.read_news(limit=news_limit), default=pd.DataFrame())
    all_macro = _safe_call(lambda: macro_store.read_macro_series(), default=pd.DataFrame())

    now = datetime.now()

    lines: list[str] = []

    lines.append("# RAbot 全球资产研究简报")
    lines.append("")
    lines.append(f"> 生成时间：{now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("> 本报告由 RAbot 基于本地行情数据库、新闻数据库、宏观数据库与可选 LLM 研究层自动生成。内容仅用于研究与复盘，不构成任何投资建议。")
    lines.append("")

    if all_data.empty:
        lines.append("## 一、数据状态")
        lines.append("")
        lines.append("当前本地行情数据库暂无可用数据。请先更新行情数据后再生成报告。")
        lines.append("")

        markdown_text = "\n".join(lines)

        if auto_save:
            save_report_text(markdown_text, output_dir=output_dir)

        return markdown_text

    perf_df = _safe_call(lambda: build_asset_performance_table(all_data), default=pd.DataFrame())
    market_overview = _safe_call(lambda: build_market_overview(perf_df), default={})
    news_snapshot = _safe_call(lambda: build_news_market_snapshot(all_news, days=7), default={})
    macro_snapshot = _safe_call(lambda: build_macro_indicator_snapshot(all_macro), default=pd.DataFrame())

    lines.extend(_render_market_overview_section(perf_df, market_overview))
    lines.extend(_render_llm_market_section(all_data, all_news, all_macro, enable_llm=enable_llm))
    lines.extend(_render_macro_section(macro_snapshot, all_macro))
    lines.extend(_render_news_section(all_news, news_snapshot, top_news_limit=top_news_limit))
    lines.extend(
        _render_focus_assets_section(
            all_data=all_data,
            all_news=all_news,
            all_macro=all_macro,
            perf_df=perf_df,
            focus_assets=focus_assets,
            enable_llm=enable_llm,
        )
    )
    lines.extend(_render_data_status_section(all_data, all_news, all_macro))
    lines.extend(_render_risk_disclaimer_section())

    markdown_text = "\n".join(lines)

    if auto_save:
        save_report_text(markdown_text, output_dir=output_dir)

    return markdown_text


def save_index_markdown_report(
    markdown_text: str | None = None,
    output_dir: str | Path | None = None,
) -> Path:
    """
    显式保存 Markdown 报告。

    如果 markdown_text 为 None，则先生成报告正文，但生成阶段 auto_save=False，
    避免重复保存两份文件。
    """
    if markdown_text is None:
        markdown_text = generate_index_markdown_report(auto_save=False)

    return save_report_text(markdown_text, output_dir=output_dir)


def generate_and_save_index_markdown_report(
    focus_assets: list[str] | None = None,
    news_limit: int = 500,
    top_news_limit: int = 8,
    enable_llm: bool = True,
    output_dir: str | Path | None = None,
) -> Path:
    """
    生成并保存报告，直接返回文件路径。

    后续如果你希望前端后台任务拿到稳定路径，优先调用这个函数。
    """
    markdown_text = generate_index_markdown_report(
        focus_assets=focus_assets,
        news_limit=news_limit,
        top_news_limit=top_news_limit,
        enable_llm=enable_llm,
        auto_save=False,
    )

    return save_report_text(markdown_text, output_dir=output_dir)


def _render_market_overview_section(
    perf_df: pd.DataFrame,
    market_overview: dict[str, Any],
) -> list[str]:
    lines: list[str] = []

    lines.append("## 一、市场总览")
    lines.append("")

    if perf_df.empty:
        lines.append("当前暂无足够行情数据生成市场表现总览。")
        lines.append("")
        return lines

    headline = market_overview.get("headline", "市场总览")
    summary = market_overview.get("summary", "")

    lines.append(f"### 1.1 RAbot 规则层市场判断：{headline}")
    lines.append("")

    if summary:
        lines.append(summary)
    else:
        lines.append("RAbot 当前未生成明确市场总览结论。")

    lines.append("")

    return_cols = [
        "symbol",
        "name",
        "近1周收益率%",
        "近1月收益率%",
        "近3月收益率%",
        "YTD收益率%",
        "近1年收益率%",
        "20日年化波动率%",
        "当前回撤%",
    ]

    show_cols = [col for col in return_cols if col in perf_df.columns]

    display = perf_df[show_cols].copy()
    sort_col = "近1月收益率%" if "近1月收益率%" in display.columns else None

    if sort_col:
        display = display.sort_values(sort_col, ascending=False, na_position="last")

    lines.append("### 1.2 多资产表现表")
    lines.append("")
    lines.append(_df_to_markdown(display.head(30)))
    lines.append("")

    lines.append("### 1.3 强弱与风险提示")
    lines.append("")

    if sort_col:
        top = perf_df.dropna(subset=[sort_col]).sort_values(sort_col, ascending=False).head(3)
        bottom = perf_df.dropna(subset=[sort_col]).sort_values(sort_col, ascending=True).head(3)

        if not top.empty:
            lines.append("近1月表现相对强势的资产包括：" + _format_asset_rows(top, sort_col) + "。")
            lines.append("")

        if not bottom.empty:
            lines.append("近1月表现相对弱势的资产包括：" + _format_asset_rows(bottom, sort_col) + "。")
            lines.append("")

    if "20日年化波动率%" in perf_df.columns:
        high_vol = perf_df.dropna(subset=["20日年化波动率%"]).sort_values(
            "20日年化波动率%",
            ascending=False,
        ).head(3)

        if not high_vol.empty:
            lines.append("当前波动较高的资产包括：" + _format_asset_rows(high_vol, "20日年化波动率%") + "。")
            lines.append("")

    return lines


def _render_llm_market_section(
    all_data: pd.DataFrame,
    all_news: pd.DataFrame,
    all_macro: pd.DataFrame,
    enable_llm: bool = True,
) -> list[str]:
    lines: list[str] = []

    lines.append("## 二、RAbot AI 首席观察")
    lines.append("")

    if not enable_llm:
        lines.append("LLM 研究层未启用。")
        lines.append("")
        return lines

    writer = RAbotResearchWriter()
    result = writer.generate_market_observation(
        all_data=all_data,
        all_news=all_news,
        all_macro=all_macro,
        focus_assets=DEFAULT_LLM_FOCUS_ASSETS,
    )

    if result.ok:
        lines.append(result.text)
        lines.append("")
        lines.append(f"> LLM 模型：{result.model}")
        lines.append("")
    else:
        lines.append(result.text)
        lines.append("")
        lines.append("> 当前报告仍保留规则层分析。配置 DEEPSEEK_API_KEY 后，本节将生成真正的 AI 研究观察。")
        lines.append("")

    return lines


def _render_macro_section(
    macro_snapshot: pd.DataFrame,
    all_macro: pd.DataFrame,
) -> list[str]:
    lines: list[str] = []

    lines.append("## 三、宏观环境")
    lines.append("")

    if macro_snapshot.empty:
        lines.append("当前暂无宏观数据。请先更新宏观数据后再生成宏观环境分析。")
        lines.append("")
        return lines

    freshness = _build_macro_freshness_summary(all_macro, macro_snapshot)

    lines.append("### 3.1 宏观数据覆盖口径")
    lines.append("")
    lines.append("宏观数据中同时包含日度、月度等不同频率的指标，因此报告不再使用单一“最新日期”概括全部宏观数据。")
    lines.append("")
    lines.append("需要特别注意：**月度宏观指标通常使用当月1日作为日期戳，代表该月数据期数，并不等于数据只更新到月初。**")
    lines.append("")

    if freshness["overall_table"].empty:
        lines.append("当前无法生成宏观数据覆盖表。")
    else:
        lines.append(_df_to_markdown(freshness["overall_table"]))

    lines.append("")

    if not freshness["frequency_table"].empty:
        lines.append("按频率拆分的最新覆盖情况如下：")
        lines.append("")
        lines.append(_df_to_markdown(freshness["frequency_table"]))
        lines.append("")

    section_no = 1

    for region in ["US", "CN"]:
        part = macro_snapshot[macro_snapshot["region"] == region].copy()

        if part.empty:
            continue

        section_no += 1
        region_label = REGION_LABELS.get(region, region)
        lines.append(f"### 3.{section_no} {region_label}宏观")
        lines.append("")

        region_note = _build_region_macro_freshness_note(part, region)
        if region_note:
            lines.append(region_note)
            lines.append("")

        show = part.copy()
        show["region"] = _get_text_series(show, "region").map(lambda x: REGION_LABELS.get(x, x))
        show["category"] = _get_text_series(show, "category").map(lambda x: CATEGORY_LABELS.get(x, x))
        show["frequency"] = _get_text_series(show, "frequency").map(lambda x: FREQUENCY_LABELS.get(str(x), str(x)))
        show["latest_date"] = pd.to_datetime(show["latest_date"], errors="coerce").dt.strftime("%Y-%m-%d")

        cols = [
            "name",
            "category",
            "frequency",
            "latest_date",
            "latest_value",
            "change_1m",
            "change_3m",
            "trend_label",
            "risk_label",
        ]

        show = show[[col for col in cols if col in show.columns]]
        lines.append(_df_to_markdown(show.head(24)))
        lines.append("")

        if "interpretation" in part.columns:
            interpretations = part["interpretation"].dropna().astype(str).tolist()
            interpretations = [x for x in interpretations if x.strip()]
        else:
            interpretations = []

        if interpretations:
            lines.append("关键观察：")
            lines.append("")
            for item in interpretations[:6]:
                lines.append(f"- {item}")
            lines.append("")

    section_no += 1
    lines.append(f"### 3.{section_no} 跨资产宏观含义")
    lines.append("")
    lines.append(
        "整体上，美股成长资产更需要关注美债利率、核心通胀和风险偏好；A股资产更需要关注中国增长动能、PPI修复、M2/社融与政策环境；港股同时受中国基本面和美国流动性影响；黄金则对实际利率、美元方向与避险情绪更敏感。"
    )
    lines.append("")

    return lines


def _build_macro_freshness_summary(
    all_macro: pd.DataFrame,
    macro_snapshot: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    if macro_snapshot is None or macro_snapshot.empty:
        return {
            "overall_table": pd.DataFrame(),
            "frequency_table": pd.DataFrame(),
        }

    snap = macro_snapshot.copy()
    snap["latest_date"] = pd.to_datetime(snap["latest_date"], errors="coerce")
    snap["frequency"] = _get_text_series(snap, "frequency")
    snap["region"] = _get_text_series(snap, "region")

    rows: list[dict[str, Any]] = []

    for region in ["US", "CN"]:
        part = snap[snap["region"] == region].copy()
        if part.empty:
            continue

        daily = part[part["frequency"] == "daily"].copy()
        monthly = part[part["frequency"] == "monthly"].copy()

        latest_daily = daily["latest_date"].max() if not daily.empty else pd.NaT
        latest_monthly = monthly["latest_date"].max() if not monthly.empty else pd.NaT
        latest_any = part["latest_date"].max()

        rows.append(
            {
                "地区": REGION_LABELS.get(region, region),
                "指标数": int(part["symbol"].nunique()) if "symbol" in part.columns else len(part),
                "日度指标最新日期": _fmt_date(latest_daily),
                "月度指标最新期数": _fmt_month_period(latest_monthly),
                "全部指标最晚日期戳": _fmt_date(latest_any),
                "说明": _macro_region_frequency_note(part),
            }
        )

    overall_table = pd.DataFrame(rows)

    freq_rows: list[dict[str, Any]] = []

    for (region, frequency), part in snap.groupby(["region", "frequency"], dropna=False):
        latest_date = part["latest_date"].max()
        freq_label = FREQUENCY_LABELS.get(str(frequency), str(frequency) if frequency else "未知频率")

        if str(frequency) == "monthly":
            latest_text = _fmt_month_period(latest_date)
        else:
            latest_text = _fmt_date(latest_date)

        freq_rows.append(
            {
                "地区": REGION_LABELS.get(str(region), str(region)),
                "频率": freq_label,
                "指标数": int(part["symbol"].nunique()) if "symbol" in part.columns else len(part),
                "最新覆盖": latest_text,
            }
        )

    frequency_table = pd.DataFrame(freq_rows)

    if not frequency_table.empty:
        frequency_table = frequency_table.sort_values(["地区", "频率"]).reset_index(drop=True)

    return {
        "overall_table": overall_table,
        "frequency_table": frequency_table,
    }


def _build_region_macro_freshness_note(part: pd.DataFrame, region: str) -> str:
    if part is None or part.empty:
        return ""

    data = part.copy()
    data["latest_date"] = pd.to_datetime(data["latest_date"], errors="coerce")
    data["frequency"] = _get_text_series(data, "frequency")

    daily = data[data["frequency"] == "daily"]
    monthly = data[data["frequency"] == "monthly"]

    daily_text = "暂无日度指标"
    monthly_text = "暂无月度指标"

    if not daily.empty:
        daily_text = f"日度指标最新日期为 {_fmt_date(daily['latest_date'].max())}"

    if not monthly.empty:
        monthly_text = f"月度指标最新期数为 {_fmt_month_period(monthly['latest_date'].max())}"

    region_label = REGION_LABELS.get(region, region)

    return f"{region_label}宏观当前覆盖情况：{daily_text}；{monthly_text}。月度指标日期戳通常落在每月1日，代表该月数据期数。"


def _macro_region_frequency_note(part: pd.DataFrame) -> str:
    if part is None or part.empty:
        return "暂无说明"

    frequencies = set(_get_text_series(part, "frequency").tolist())

    has_daily = "daily" in frequencies
    has_monthly = "monthly" in frequencies

    if has_daily and has_monthly:
        return "日度与月度指标混合，需分频率看最新覆盖"

    if has_daily:
        return "以日度指标为主"

    if has_monthly:
        return "以月度指标为主，日期戳代表数据期数"

    return "指标频率不完整"


def _render_news_section(
    all_news: pd.DataFrame,
    news_snapshot: dict[str, Any],
    top_news_limit: int = 8,
) -> list[str]:
    lines: list[str] = []

    lines.append("## 四、新闻面观察")
    lines.append("")

    if all_news.empty:
        lines.append("当前暂无新闻数据。请先更新新闻后再生成新闻面分析。")
        lines.append("")
        return lines

    headline = news_snapshot.get("headline", "新闻市场快照")
    summary = news_snapshot.get("summary", "")

    lines.append(f"### 4.1 新闻市场快照：{headline}")
    lines.append("")

    if summary:
        lines.append(summary)
    else:
        lines.append("RAbot 当前未生成明确新闻市场快照。")

    lines.append("")

    lines.append("### 4.2 高质量新闻")
    lines.append("")

    news = all_news.copy()

    if "quality_score" in news.columns:
        news["quality_score"] = pd.to_numeric(news["quality_score"], errors="coerce")
        news = news.sort_values("quality_score", ascending=False, na_position="last")
    elif "importance_score" in news.columns:
        news["importance_score"] = pd.to_numeric(news["importance_score"], errors="coerce")
        news = news.sort_values("importance_score", ascending=False, na_position="last")

    for _, row in news.head(top_news_limit).iterrows():
        title = row.get("title", "无标题")
        source_name = row.get("source_name", "Unknown")
        event_type = row.get("event_type", "其他")
        sentiment = row.get("sentiment_label", "中性")
        quality = row.get("quality_score", "NA")
        importance = row.get("importance_score", "NA")
        related_assets = row.get("related_assets", "")

        lines.append(
            f"- **{title}**｜来源：{source_name}｜事件：{event_type}｜情绪：{sentiment}｜"
            f"质量：{quality}/100｜重要性：{importance}/100｜关联资产：{related_assets or '暂无'}"
        )

    lines.append("")

    if "sentiment_label" in all_news.columns:
        sentiment_count = all_news["sentiment_label"].fillna("未知").value_counts().reset_index()
        sentiment_count.columns = ["情绪标签", "数量"]

        lines.append("### 4.3 新闻情绪分布")
        lines.append("")
        lines.append(_df_to_markdown(sentiment_count))
        lines.append("")

    if "event_type" in all_news.columns:
        event_count = all_news["event_type"].fillna("其他").value_counts().reset_index()
        event_count.columns = ["事件类型", "数量"]

        lines.append("### 4.4 事件类型分布")
        lines.append("")
        lines.append(_df_to_markdown(event_count.head(12)))
        lines.append("")

    return lines


def _render_focus_assets_section(
    all_data: pd.DataFrame,
    all_news: pd.DataFrame,
    all_macro: pd.DataFrame,
    perf_df: pd.DataFrame,
    focus_assets: list[str],
    enable_llm: bool = True,
) -> list[str]:
    lines: list[str] = []

    lines.append("## 五、重点资产观察")
    lines.append("")

    available_assets = set(all_data["symbol"].dropna().astype(str).unique().tolist())
    selected_assets = [asset for asset in focus_assets if asset in available_assets]

    if not selected_assets:
        lines.append("当前数据库中没有匹配到重点资产行情数据。")
        lines.append("")
        return lines

    writer = RAbotResearchWriter() if enable_llm else None
    llm_assets = set(DEFAULT_LLM_FOCUS_ASSETS)

    for idx, asset in enumerate(selected_assets, start=1):
        df = all_data[all_data["symbol"] == asset].copy()
        df = df.sort_values("date")

        if df.empty:
            continue

        name = _get_asset_name(df, asset)

        lines.append(f"### 5.{idx} {name}（{asset}）")
        lines.append("")

        research = _safe_call(lambda: build_single_asset_research(df), default={})
        asset_news = _safe_call(
            lambda: build_asset_news_research(
                all_news,
                asset_symbol=asset,
                technical_score=research.get("score"),
                days=7,
            ),
            default={},
        )
        asset_macro = _safe_call(
            lambda: build_asset_macro_research(
                all_macro,
                asset_symbol=asset,
                technical_score=research.get("score"),
            ),
            default={},
        )

        latest_status = _build_latest_asset_status(df)

        lines.append("#### 技术面")
        lines.append("")

        tech_score = research.get("score", "NA")
        grade = research.get("grade", "N/A")
        trend_label = research.get("trend_label", "N/A")
        risk_label = research.get("risk_label", "N/A")
        volatility_label = research.get("volatility_label", "N/A")
        momentum_label = research.get("momentum_label", "N/A")

        lines.append(f"- 综合评分：**{tech_score}/100**，状态分级：**{grade}**。")
        lines.append(
            f"- 趋势状态：{trend_label}；风险状态：{risk_label}；波动状态：{volatility_label}；动量状态：{momentum_label}。"
        )

        if latest_status:
            lines.append(
                f"- 最新收盘价：{latest_status.get('close', 'NA')}；近一日涨跌幅：{latest_status.get('pct_change', 'NA')}%；当前回撤：{latest_status.get('drawdown', 'NA')}%。"
            )

        if research.get("summary"):
            lines.append(f"- 综合判断：{research.get('summary')}")

        if research.get("action_hint"):
            lines.append(f"- 行动提示：{research.get('action_hint')}")

        watch_points = research.get("watch_points", [])
        if watch_points:
            for point in watch_points[:3]:
                lines.append(f"- 观察点：{point}")

        lines.append("")

        lines.append("#### 新闻面")
        lines.append("")

        if not asset_news:
            lines.append("暂无可用新闻面判断。")
        else:
            total_news = asset_news.get("total_news", 0)
            high_importance = asset_news.get("high_importance_count", 0)
            bullish = asset_news.get("bullish_count", 0)
            bearish = asset_news.get("bearish_count", 0)
            alignment = asset_news.get("alignment_label", "无法判断")
            summary = asset_news.get("summary", "")

            lines.append(
                f"- 近7天相关新闻：{total_news} 条，其中高重要性新闻 {high_importance} 条，偏利多 {bullish} 条，偏利空 {bearish} 条。"
            )
            lines.append(f"- 新闻面判断：**{alignment}**。")

            if summary:
                lines.append(f"- 新闻面总结：{summary}")

            top_news = asset_news.get("top_news", [])
            if top_news:
                lines.append("- 重点新闻：")
                for item in top_news[:5]:
                    lines.append(f"  - {item}")

        lines.append("")

        lines.append("#### 宏观面")
        lines.append("")

        if not asset_macro:
            lines.append("暂无可用宏观面判断。")
        else:
            macro_score = asset_macro.get("macro_score")
            macro_score_text = "N/A" if macro_score is None else f"{macro_score}/100"
            macro_bias = asset_macro.get("macro_bias", "数据不足")
            alignment = asset_macro.get("alignment_label", "无法判断")
            summary = asset_macro.get("summary", "")

            lines.append(f"- 宏观评分：**{macro_score_text}**；宏观方向：**{macro_bias}**；技术-宏观关系：**{alignment}**。")

            if summary:
                lines.append(f"- 宏观综合判断：{summary}")

            support_points = asset_macro.get("support_points", [])
            risk_points = asset_macro.get("risk_points", [])
            neutral_points = asset_macro.get("neutral_points", [])

            if support_points:
                lines.append("- 宏观支撑因素：")
                for point in support_points[:4]:
                    lines.append(f"  - {point}")

            if risk_points:
                lines.append("- 宏观压力因素：")
                for point in risk_points[:4]:
                    lines.append(f"  - {point}")

            if neutral_points:
                lines.append("- 中性观察因素：")
                for point in neutral_points[:3]:
                    lines.append(f"  - {point}")

        lines.append("")

        if writer is not None and asset in llm_assets:
            lines.append("#### AI 研究点评")
            lines.append("")

            llm_result = writer.generate_asset_observation(
                all_data=all_data,
                all_news=all_news,
                all_macro=all_macro,
                asset_symbol=asset,
            )

            lines.append(llm_result.text)
            lines.append("")

        perf_row = _get_perf_row(perf_df, asset)
        if perf_row:
            lines.append("#### 表现摘要")
            lines.append("")
            perf_items = []

            for col in [
                "近1周收益率%",
                "近1月收益率%",
                "近3月收益率%",
                "YTD收益率%",
                "近1年收益率%",
                "20日年化波动率%",
                "当前回撤%",
            ]:
                if col in perf_row and not pd.isna(perf_row[col]):
                    perf_items.append(f"{col}：{perf_row[col]}")

            if perf_items:
                lines.append("- " + "；".join(perf_items) + "。")
            else:
                lines.append("暂无足够表现摘要数据。")

            lines.append("")

    return lines


def _render_data_status_section(
    all_data: pd.DataFrame,
    all_news: pd.DataFrame,
    all_macro: pd.DataFrame,
) -> list[str]:
    lines: list[str] = []

    lines.append("## 六、数据状态")
    lines.append("")

    market_assets = 0 if all_data.empty else all_data["symbol"].nunique()
    market_rows = 0 if all_data.empty else len(all_data)

    news_rows = 0 if all_news.empty else len(all_news)
    macro_indicators = 0 if all_macro.empty else all_macro["symbol"].nunique()
    macro_rows = 0 if all_macro.empty else len(all_macro)

    lines.append(f"- 行情数据：覆盖 {market_assets} 个资产，共 {market_rows:,} 行。")
    lines.append(f"- 新闻数据：当前读取 {news_rows:,} 条。")
    lines.append(f"- 宏观数据：覆盖 {macro_indicators} 个指标，共 {macro_rows:,} 行。")
    lines.append("")

    if not all_data.empty:
        data_range = all_data.copy()
        data_range["date"] = pd.to_datetime(data_range["date"], errors="coerce")

        min_date = data_range["date"].min()
        max_date = data_range["date"].max()

        min_text = _fmt_date(min_date)
        max_text = _fmt_date(max_date)

        lines.append(f"- 行情数据区间：{min_text} 至 {max_text}。")
        lines.append("")

    if not all_macro.empty:
        macro = all_macro.copy()
        macro["date"] = pd.to_datetime(macro["date"], errors="coerce")
        macro["frequency"] = _get_text_series(macro, "frequency")

        daily = macro[macro["frequency"] == "daily"]
        monthly = macro[macro["frequency"] == "monthly"]

        if not daily.empty:
            lines.append(f"- 宏观日度指标最新日期：{_fmt_date(daily['date'].max())}。")

        if not monthly.empty:
            lines.append(f"- 宏观月度指标最新期数：{_fmt_month_period(monthly['date'].max())}。")

        lines.append("- 注：月度指标日期戳通常为当月1日，代表数据期数，不代表数据只更新到该自然日。")
        lines.append("")

    return lines


def _render_risk_disclaimer_section() -> list[str]:
    lines: list[str] = []

    lines.append("## 七、风险提示")
    lines.append("")
    lines.append(
        "本报告由 RAbot 根据本地行情数据、新闻数据、宏观数据和可选 LLM 研究层自动生成。规则层结论来自程序化指标与模板，LLM 研究层仅基于 RAbot 提供的结构化事实包进行归纳推理。所有结论可能受到数据延迟、数据缺失、接口权限、新闻抓取误差、宏观指标滞后性、模型规则简化和大模型推理偏差等因素影响。"
    )
    lines.append("")
    lines.append(
        "报告内容仅用于个人研究、市场复盘和系统测试，不构成任何投资建议、交易建议或收益承诺。市场有风险，投资需谨慎。"
    )
    lines.append("")

    return lines


def _build_latest_asset_status(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {}

    try:
        data = add_technical_indicators(df)
        latest = data.sort_values("date").iloc[-1]

        return {
            "close": _fmt_num(latest.get("close")),
            "pct_change": _fmt_num(latest.get("pct_change")),
            "drawdown": _fmt_num(latest.get("drawdown")),
            "volatility_20d": _fmt_num(latest.get("volatility_20d")),
        }
    except Exception:
        return {}


def _get_asset_name(df: pd.DataFrame, asset: str) -> str:
    if "name" in df.columns:
        names = df["name"].dropna().astype(str)
        if not names.empty:
            return names.iloc[-1]

    return asset


def _get_perf_row(perf_df: pd.DataFrame, asset: str) -> dict[str, Any]:
    if perf_df.empty or "symbol" not in perf_df.columns:
        return {}

    row = perf_df[perf_df["symbol"] == asset]

    if row.empty:
        return {}

    return row.iloc[0].to_dict()


def _format_asset_rows(df: pd.DataFrame, value_col: str) -> str:
    items = []

    for _, row in df.iterrows():
        symbol = row.get("symbol", "")
        name = row.get("name", symbol)
        value = row.get(value_col, "NA")
        items.append(f"{name}（{symbol}，{value}%）")

    return "、".join(items)


def _df_to_markdown(df: pd.DataFrame) -> str:
    if df is None or df.empty:
        return "暂无数据。"

    clean = df.copy()

    for col in clean.columns:
        if pd.api.types.is_float_dtype(clean[col]):
            clean[col] = clean[col].round(4)

    try:
        return clean.to_markdown(index=False)
    except Exception:
        return clean.to_string(index=False)


def _get_text_series(df: pd.DataFrame, col: str) -> pd.Series:
    if df is None or df.empty:
        return pd.Series(dtype=str)

    if col not in df.columns:
        return pd.Series([""] * len(df), index=df.index, dtype=str)

    return df[col].fillna("").astype(str)


def _fmt_num(value: Any, digits: int = 2) -> str:
    if value is None or pd.isna(value):
        return "NA"

    try:
        return f"{float(value):,.{digits}f}"
    except Exception:
        return str(value)


def _fmt_date(value: Any) -> str:
    dt = pd.to_datetime(value, errors="coerce")

    if pd.isna(dt):
        return "暂无"

    return dt.strftime("%Y-%m-%d")


def _fmt_month_period(value: Any) -> str:
    dt = pd.to_datetime(value, errors="coerce")

    if pd.isna(dt):
        return "暂无"

    return dt.strftime("%Y-%m")


def _safe_call(func, default):
    try:
        return func()
    except Exception:
        return default