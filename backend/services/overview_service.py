from datetime import datetime

from backend.schemas.overview import OverviewReports, OverviewResponse, OverviewSection
from backend.services.macro_service import get_macro_overview
from backend.services.market_service import get_market_indexes
from backend.services.news_service import get_latest_news
from backend.services.report_service import list_reports


def _local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _extend_warnings(warnings: list[str], prefix: str, module_warnings: list[str]) -> None:
    for warning in module_warnings:
        warnings.append(f"{prefix}：{warning}")


def _market_summary(count: int, highlights: list[str]) -> str:
    if count <= 0:
        return "当前暂无可展示的本地指数行情数据。"
    if highlights:
        return f"已读取 {count} 个指数/资产的最新行情，重点观察：{highlights[0]}"
    return f"已读取 {count} 个指数/资产的最新行情。"


def _news_summary(count: int, highlights: list[str]) -> str:
    if count <= 0:
        return "当前暂无本地新闻数据。"
    if highlights:
        return f"已读取 {count} 条本地新闻，最新关注：{highlights[0]}"
    return f"已读取 {count} 条本地新闻。"


def _macro_summary(count: int, highlights: list[str]) -> str:
    if count <= 0:
        return "当前未找到宏观数据。"
    if highlights:
        return f"已读取 {count} 个宏观指标，关键变化：{highlights[0]}"
    return f"已读取 {count} 个宏观指标。"


def _report_summary(count: int, latest_title: str | None) -> str:
    if count <= 0:
        return "当前报告库暂无 Markdown 报告。"
    if latest_title:
        return f"报告库共有 {count} 份 Markdown 报告，最新报告为《{latest_title}》。"
    return f"报告库共有 {count} 份 Markdown 报告。"


def build_overview() -> OverviewResponse:
    warnings: list[str] = []

    try:
        market_result = get_market_indexes(limit=12)
        market_highlights = [item.summary for item in market_result.items[:3]]
        market_section = OverviewSection(
            count=market_result.count,
            highlights=market_highlights,
            warnings=market_result.warnings,
        )
        _extend_warnings(warnings, "市场", market_result.warnings)
    except Exception as exc:
        market_section = OverviewSection(warnings=[str(exc)])
        warnings.append(f"市场模块读取失败：{exc}")

    try:
        news_result = get_latest_news(limit=8)
        news_highlights = [item.title for item in news_result.items[:3]]
        news_section = OverviewSection(
            count=news_result.count,
            highlights=news_highlights,
            warnings=news_result.warnings,
        )
        _extend_warnings(warnings, "新闻", news_result.warnings)
    except Exception as exc:
        news_section = OverviewSection(warnings=[str(exc)])
        warnings.append(f"新闻模块读取失败：{exc}")

    try:
        macro_result = get_macro_overview(limit=12)
        macro_highlights = [item.summary for item in macro_result.items[:3]]
        macro_section = OverviewSection(
            count=macro_result.count,
            highlights=macro_highlights,
            warnings=macro_result.warnings,
        )
        _extend_warnings(warnings, "宏观", macro_result.warnings)
    except Exception as exc:
        macro_section = OverviewSection(warnings=[str(exc)])
        warnings.append(f"宏观模块读取失败：{exc}")

    try:
        report_result = list_reports()
        latest = report_result.reports[0] if report_result.reports else None
        report_section = OverviewReports(
            count=len(report_result.reports),
            latest_title=latest.title if latest else None,
            latest_filename=latest.filename if latest else None,
        )
        _extend_warnings(warnings, "报告", report_result.warnings)
    except Exception as exc:
        report_section = OverviewReports()
        warnings.append(f"报告模块读取失败：{exc}")

    market_summary = _market_summary(market_section.count, market_section.highlights)
    news_summary = _news_summary(news_section.count, news_section.highlights)
    macro_summary = _macro_summary(macro_section.count, macro_section.highlights)
    report_summary = _report_summary(report_section.count, report_section.latest_title)

    return OverviewResponse(
        market_status="connected" if market_section.count > 0 else "no_data",
        market_summary=market_summary,
        news_summary=news_summary,
        macro_summary=macro_summary,
        report_summary=report_summary,
        last_update=_local_now_iso(),
        warnings=warnings,
        market=market_section,
        news=news_section,
        macro=macro_section,
        reports=report_section,
    )
