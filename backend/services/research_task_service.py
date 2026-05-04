from __future__ import annotations

import os
import re
from html import escape
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from backend.schemas.research import ResearchGenerateRequest, ResearchGenerateResponse
from backend.services import task_manager
from backend.services.macro_service import get_macro_overview, get_macro_series
from backend.services.market_service import get_market_indexes
from backend.services.market_service import get_market_timeseries
from backend.services.news_service import get_latest_news
from backend.services.report_service import REPORTS_DIR, REPORT_ASSETS_DIR, save_report_content
from RAbot.funds.fund_analysis import analyze_fund


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_research_report_task(request: ResearchGenerateRequest) -> ResearchGenerateResponse:
    task = task_manager.create_task(
        task_type="research_report",
        message="研究报告生成任务已创建",
    )
    task_manager.run_task_in_background(task.task_id, run_research_report_task, request)
    return ResearchGenerateResponse(
        task_id=task.task_id,
        status=task.status,
        message="研究报告生成任务已创建",
    )


def _update(task_id: str, progress: int, step: str, message: str) -> None:
    task_manager.update_task(
        task_id,
        status="running",
        progress=progress,
        current_step=step,
        message=message,
    )


def _has_deepseek_key() -> bool:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        pass
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


def _fmt_number(value: float | int | None) -> str:
    if value is None:
        return "暂无"
    try:
        return f"{float(value):,.2f}"
    except (TypeError, ValueError):
        return str(value)


def _collect_warnings(*groups: list[str]) -> list[str]:
    warnings: list[str] = []
    for group in groups:
        warnings.extend(group or [])
    return warnings


def _chart_value(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _svg_polyline(points: list[tuple[float, float]], color: str) -> str:
    if not points:
        return ""
    joined = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
    return f'<polyline points="{joined}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />'


def _build_market_svg_chart(series_by_symbol: dict[str, list[Any]], title: str) -> str:
    width = 920
    height = 390
    left = 64
    right = 28
    top = 86
    bottom = 58
    chart_width = width - left - right
    chart_height = height - top - bottom
    palette = ["#d97706", "#2563eb", "#059669", "#7c3aed", "#dc2626"]

    all_values: list[float] = []
    max_len = 0
    for rows in series_by_symbol.values():
        max_len = max(max_len, len(rows))
        for row in rows:
            value = _chart_value(getattr(row, "normalized", None) or getattr(row, "close", None))
            if value is not None:
                all_values.append(value)

    if not all_values or max_len < 2:
        return ""

    y_min = min(all_values)
    y_max = max(all_values)
    if y_min == y_max:
        y_min -= 1
        y_max += 1
    padding = (y_max - y_min) * 0.08
    y_min -= padding
    y_max += padding

    def x_at(index: int, total: int) -> float:
        if total <= 1:
            return left
        return left + chart_width * index / (total - 1)

    def y_at(value: float) -> float:
        return top + chart_height * (1 - (value - y_min) / (y_max - y_min))

    grid_lines: list[str] = []
    for idx in range(5):
        value = y_min + (y_max - y_min) * idx / 4
        y = y_at(value)
        grid_lines.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#eadfce" stroke-width="1" />')
        grid_lines.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#74685c">{value:.1f}</text>')

    x_labels: list[str] = []
    longest_rows = max(series_by_symbol.values(), key=len)
    label_indexes = sorted({0, max(0, len(longest_rows) // 2), len(longest_rows) - 1})
    for idx in label_indexes:
        row = longest_rows[idx]
        x = x_at(idx, len(longest_rows))
        label = str(getattr(row, "date", ""))[:10]
        x_labels.append(f'<text x="{x:.1f}" y="{height - 24}" text-anchor="middle" font-size="11" fill="#74685c">{escape(label)}</text>')

    lines: list[str] = []
    legends: list[str] = []
    for color_index, (symbol, rows) in enumerate(series_by_symbol.items()):
        points: list[tuple[float, float]] = []
        for idx, row in enumerate(rows):
            value = _chart_value(getattr(row, "normalized", None) or getattr(row, "close", None))
            if value is not None:
                points.append((x_at(idx, len(rows)), y_at(value)))
        color = palette[color_index % len(palette)]
        lines.append(_svg_polyline(points, color))
        legend_x = left + (color_index % 4) * 180
        legend_y = 54 + (color_index // 4) * 18
        legends.append(f'<circle cx="{legend_x}" cy="{legend_y}" r="4" fill="{color}" />')
        legends.append(f'<text x="{legend_x + 10}" y="{legend_y + 4}" font-size="12" fill="#4d3a2a">{escape(symbol)}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" rx="14" fill="#fffdf8" />
  <text x="{left}" y="28" font-size="16" font-weight="700" fill="#1f1a17">{escape(title)}</text>
  {''.join(legends)}
  <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#cdbfae" stroke-width="1.2" />
  <line x1="{left}" y1="{height - bottom}" x2="{width - right}" y2="{height - bottom}" stroke="#cdbfae" stroke-width="1.2" />
  {''.join(grid_lines)}
  {''.join(lines)}
  {''.join(x_labels)}
  <text x="{width - right}" y="{height - 8}" text-anchor="end" font-size="10" fill="#9a8d7f">normalized price, first visible point = 100</text>
</svg>'''


def _build_bar_svg_chart(items: list[tuple[str, float]], title: str, unit: str = "") -> str:
    width = 920
    height = 360
    left = 70
    right = 32
    top = 58
    bottom = 78
    chart_width = width - left - right
    chart_height = height - top - bottom
    if not items:
        return ""

    values = [value for _, value in items]
    min_value = min(0, min(values))
    max_value = max(0, max(values))
    if min_value == max_value:
        min_value -= 1
        max_value += 1
    pad = (max_value - min_value) * 0.1
    min_value -= pad
    max_value += pad

    def y_at(value: float) -> float:
        return top + chart_height * (1 - (value - min_value) / (max_value - min_value))

    zero_y = y_at(0)
    slot = chart_width / max(len(items), 1)
    bar_width = min(52, slot * 0.56)
    bars: list[str] = []
    for index, (label, value) in enumerate(items):
        x = left + slot * index + (slot - bar_width) / 2
        y = y_at(max(value, 0))
        h = abs(y_at(value) - zero_y)
        color = "#d97706" if value >= 0 else "#2563eb"
        short_label = label[:12]
        bars.append(f'<rect x="{x:.1f}" y="{min(y, zero_y):.1f}" width="{bar_width:.1f}" height="{max(h, 1):.1f}" rx="5" fill="{color}" opacity="0.88" />')
        bars.append(f'<text x="{x + bar_width / 2:.1f}" y="{min(y, zero_y) - 7:.1f}" text-anchor="middle" font-size="11" fill="#4d3a2a">{value:.1f}{escape(unit)}</text>')
        bars.append(f'<text x="{x + bar_width / 2:.1f}" y="{height - 38}" text-anchor="middle" font-size="10" fill="#74685c">{escape(short_label)}</text>')

    grid = []
    for idx in range(5):
        value = min_value + (max_value - min_value) * idx / 4
        y = y_at(value)
        grid.append(f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="#eadfce" stroke-width="1" />')
        grid.append(f'<text x="{left - 10}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="#74685c">{value:.1f}</text>')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" rx="14" fill="#fffdf8" />
  <text x="{left}" y="30" font-size="16" font-weight="700" fill="#1f1a17">{escape(title)}</text>
  <line x1="{left}" y1="{zero_y:.1f}" x2="{width - right}" y2="{zero_y:.1f}" stroke="#cdbfae" stroke-width="1.2" />
  <line x1="{left}" y1="{top}" x2="{left}" y2="{height - bottom}" stroke="#cdbfae" stroke-width="1.2" />
  {''.join(grid)}
  {''.join(bars)}
</svg>'''


def _write_report_chart(name: str, svg: str, title: str, caption: str) -> dict[str, str] | None:
    if not svg:
        return None
    REPORT_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    chart_path = REPORT_ASSETS_DIR / name
    chart_path.write_text(svg, encoding="utf-8")
    return {
        "title": title,
        "url": f"/api/reports/assets/{name}",
        "caption": caption,
    }


def _generate_market_charts(market: Any, warnings: list[str], stamp: str) -> list[dict[str, str]]:
    charts: list[dict[str, str]] = []
    symbols = [str(item.symbol).strip().upper() for item in (getattr(market, "items", []) or [])[:4] if getattr(item, "symbol", None)]
    if not symbols:
        warnings.append("未生成走势图：当前没有可用市场资产代码。")
        return []

    try:
        response = get_market_timeseries(symbols=symbols, normalize=True)
    except Exception as exc:
        warnings.append(f"未生成走势图：读取市场时间序列失败，{type(exc).__name__}: {exc}")
        return []

    warnings.extend(getattr(response, "warnings", []) or [])
    rows = getattr(response, "items", []) or []
    if not rows:
        warnings.append("未生成走势图：当前没有可用市场时间序列数据。")
        return []

    series_by_symbol: dict[str, list[Any]] = {}
    for symbol in symbols:
        symbol_rows = [row for row in rows if getattr(row, "symbol", "") == symbol]
        if len(symbol_rows) >= 2:
            series_by_symbol[symbol] = symbol_rows[-160:]

    if not series_by_symbol:
        warnings.append("未生成走势图：有效时间序列不足。")
        return []

    svg = _build_market_svg_chart(series_by_symbol, "主要资产归一化走势")
    chart = _write_report_chart(
        f"market_trend_{stamp}.svg",
        svg,
        "主要资产归一化走势",
        "以首个可见交易日为 100，展示主要资产的相对走势。",
    )
    if chart:
        charts.append(chart)

    pct_items = []
    for item in (getattr(market, "items", []) or [])[:10]:
        value = _chart_value(getattr(item, "pct_change", None))
        if value is not None:
            pct_items.append((getattr(item, "name", None) or getattr(item, "symbol", ""), value))
    chart = _write_report_chart(
        f"market_pct_change_{stamp}.svg",
        _build_bar_svg_chart(pct_items[:8], "主要资产日涨跌幅", "%"),
        "主要资产日涨跌幅",
        "展示本地最新行情快照中的主要资产单日涨跌幅。",
    )
    if chart:
        charts.append(chart)

    if not charts:
        warnings.append("未生成市场图表：图表数据不足。")
    return charts


def _generate_news_charts(news: Any, warnings: list[str], stamp: str) -> list[dict[str, str]]:
    items = []
    for item in (getattr(news, "items", []) or [])[:10]:
        score = _chart_value(getattr(item, "quality_score", None))
        if score is None:
            score = _chart_value(getattr(item, "importance_score", None))
        if score is not None:
            items.append((getattr(item, "source", None) or getattr(item, "title", "新闻"), score))

    chart = _write_report_chart(
        f"news_score_{stamp}.svg",
        _build_bar_svg_chart(items[:8], "重点新闻质量/重要性评分"),
        "重点新闻质量/重要性评分",
        "按新闻源或标题展示本次报告读取到的重点新闻评分。",
    )
    if not chart and getattr(news, "count", 0):
        warnings.append("未生成新闻图表：新闻评分字段不足。")
    return [chart] if chart else []


def _generate_macro_charts(macro: Any, warnings: list[str], stamp: str) -> list[dict[str, str]]:
    symbols = [str(item.indicator).strip() for item in (getattr(macro, "items", []) or [])[:4] if getattr(item, "indicator", None)]
    if not symbols:
        return []
    try:
        response = get_macro_series(symbols=symbols, limit_per_symbol=120)
    except Exception as exc:
        warnings.append(f"未生成宏观图表：读取宏观时间序列失败，{type(exc).__name__}: {exc}")
        return []

    warnings.extend(getattr(response, "warnings", []) or [])
    rows = getattr(response, "items", []) or []
    series_by_symbol: dict[str, list[Any]] = {}
    for symbol in symbols:
        symbol_rows = [row for row in rows if getattr(row, "symbol", "") == symbol]
        if len(symbol_rows) >= 2:
            base = _chart_value(getattr(symbol_rows[0], "value", None))
            normalized_rows = []
            for row in symbol_rows:
                value = _chart_value(getattr(row, "value", None))
                normalized_rows.append(
                    SimpleNamespace(
                        symbol=getattr(row, "symbol", symbol),
                        date=getattr(row, "date", ""),
                        normalized=value / base * 100 if base not in (None, 0) and value is not None else None,
                    )
                )
            series_by_symbol[symbol] = normalized_rows

    chart = _write_report_chart(
        f"macro_trend_{stamp}.svg",
        _build_market_svg_chart(series_by_symbol, "核心宏观指标归一化走势"),
        "核心宏观指标归一化走势",
        "以每个指标首个可见观测值为 100，展示核心宏观变量的相对变化。",
    )
    if not chart and getattr(macro, "count", 0):
        warnings.append("未生成宏观图表：有效宏观时间序列不足。")
    return [chart] if chart else []


def _try_core_markdown_report(use_llm: bool, warnings: list[str]) -> str:
    try:
        from RAbot.reporting import markdown_report
    except Exception as exc:
        warnings.append(f"核心报告模块导入失败：{type(exc).__name__}: {exc}")
        return ""

    generator = getattr(markdown_report, "generate_index_markdown_report", None)
    if not callable(generator):
        warnings.append("核心报告模块未发现 generate_index_markdown_report 函数。")
        return ""

    try:
        return generator(
            focus_assets=["NASDAQ", "SP500", "CSI300", "SSE", "HSI", "GOLD", "DXY", "WTI", "VIX"],
            news_limit=120,
            top_news_limit=8,
            enable_llm=use_llm,
            auto_save=False,
        )
    except Exception as exc:
        warnings.append(f"核心报告模块生成失败，已使用工作台兼容报告：{type(exc).__name__}: {exc}")
        return ""


def _table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    lines = [
        "|" + "|".join(headers) + "|",
        "|" + "|".join(["---"] * len(headers)) + "|",
    ]
    if not rows:
        lines.append("|" + "|".join(["暂无数据"] + [""] * (len(headers) - 1)) + "|")
        return lines
    for row in rows:
        cells = [
            str(cell if cell is not None and cell != "" else "暂无").replace("\n", " ").replace("|", "｜")
            for cell in row
        ]
        lines.append("|" + "|".join(cells) + "|")
    return lines


def _market_lines(items: list[Any]) -> list[str]:
    if not items:
        return _table(
            ["资产", "代码", "收盘", "日涨跌幅", "趋势信号", "风险状态", "说明"],
            [["暂无数据", "", "", "", "", "", "当前未读取到市场行情数据，无法形成有效的市场强弱判断。"]],
        )
    rows = []
    for item in items[:10]:
        rows.append(
            [
                item.name or item.symbol,
                item.symbol,
                _fmt_number(item.close),
                f"{_fmt_number(item.pct_change)}%",
                item.trend_signal or "暂无",
                item.risk_level or "暂无",
                item.summary or "",
            ]
        )
    return _table(["资产", "代码", "收盘", "日涨跌幅", "趋势信号", "风险状态", "摘要"], rows)


def _news_lines(items: list[Any]) -> list[str]:
    if not items:
        return _table(
            ["标题", "来源", "标签", "评分", "发布时间", "说明"],
            [["暂无数据", "", "", "", "", "当前暂无本地新闻数据，等待 scripts/update_news.py 更新后再评估。"]],
        )
    rows = []
    for item in items[:8]:
        score = item.quality_score if item.quality_score is not None else item.importance_score
        rows.append(
            [
                item.title,
                item.source or "未知",
                item.risk_tag or "暂无",
                _fmt_number(score),
                item.published_at or "暂无",
                item.summary or "",
            ]
        )
    return _table(["标题", "来源", "标签", "评分", "发布时间", "摘要"], rows)


def _macro_lines(items: list[Any]) -> list[str]:
    if not items:
        return _table(
            ["指标", "名称", "最新值", "最新日期", "上期值", "变化", "趋势", "说明"],
            [["暂无数据", "", "", "", "", "", "", "当前未找到宏观指标数据，等待 scripts/update_macro.py 更新后再评估。"]],
        )
    rows = []
    for item in items[:10]:
        rows.append(
            [
                item.indicator,
                item.name or "",
                _fmt_number(item.latest_value),
                item.latest_date or "暂无",
                _fmt_number(item.previous_value),
                _fmt_number(item.change),
                item.trend or "暂无",
                item.summary or "",
            ]
        )
    return _table(["指标", "名称", "最新值", "最新日期", "上期值", "变化", "趋势", "摘要"], rows)


def _clean_report_title(raw: str) -> str:
    title = str(raw or "").strip()
    title = re.sub(r"^#+\s*", "", title)
    title = title.strip(" \t\r\n\"'“”‘’《》")
    title = re.sub(r"\s+", " ", title)
    if not title:
        return ""
    title = title.splitlines()[0].strip()
    return title[:42]


def _fallback_report_title(market: Any, news: Any, macro: Any, request: ResearchGenerateRequest) -> str:
    leading_asset = None
    for item in getattr(market, "items", []) or []:
        if item.trend_signal or item.risk_level or item.pct_change is not None:
            leading_asset = item
            break

    if leading_asset:
        asset_name = leading_asset.name or leading_asset.symbol
        trend = leading_asset.trend_signal or "趋势待确认"
        risk = leading_asset.risk_level or "风险中性"
        if str(risk).endswith("观察"):
            return f"{asset_name}{trend}下的{risk}"
        return f"{asset_name}{trend}下的{risk}观察"

    if getattr(macro, "count", 0):
        first_macro = macro.items[0]
        return f"{first_macro.name or first_macro.indicator}牵引下的宏观线索观察"

    if getattr(news, "count", 0):
        return "新闻风险驱动下的市场线索观察"

    target_text = request.target.replace("_", " ").strip() or "市场"
    return f"{target_text}本地数据缺口与研究框架检查"


def _generate_report_title(
    *,
    request: ResearchGenerateRequest,
    market: Any,
    news: Any,
    macro: Any,
    warnings: list[str],
    use_llm: bool,
    llm_available: bool,
) -> str:
    fallback = _fallback_report_title(market, news, macro, request)
    if not use_llm or not llm_available:
        return fallback

    try:
        from RAbot.llm.llm_client import RAbotLLMClient

        market_items = [
            {
                "symbol": item.symbol,
                "name": item.name,
                "pct_change": item.pct_change,
                "trend_signal": item.trend_signal,
                "risk_level": item.risk_level,
                "summary": item.summary,
            }
            for item in (market.items or [])[:8]
        ]
        news_items = [
            {
                "title": item.title,
                "source": item.source,
                "risk_tag": item.risk_tag,
                "summary": item.summary,
            }
            for item in (news.items or [])[:5]
        ]
        macro_items = [
            {
                "indicator": item.indicator,
                "name": item.name,
                "trend": item.trend,
                "summary": item.summary,
            }
            for item in (macro.items or [])[:8]
        ]

        client = RAbotLLMClient(max_tokens=120, temperature=0.2)
        result = client.generate(
            system_prompt=(
                "你是金融研究报告标题编辑。只输出一个中文标题，不要解释。"
                "标题必须概括全文中心思想，避免使用'RAbot研究报告'这类泛化名称。"
            ),
            user_prompt=(
                f"报告类型：{request.target}\n"
                f"研究风格：{request.report_style}\n"
                f"市场数据：{market_items}\n"
                f"新闻数据：{news_items}\n"
                f"宏观数据：{macro_items}\n"
                "请生成一个 12 到 28 个中文字符的研报标题。"
            ),
        )
        title = _clean_report_title(result.text)
        if result.ok and title:
            return title
        warnings.append(f"LLM 标题生成未成功，已使用规则标题：{result.error or result.text}")
    except Exception as exc:
        warnings.append(f"LLM 标题生成失败，已使用规则标题：{type(exc).__name__}: {exc}")

    return fallback


def _strategy_text(market_count: int, news_count: int, macro_count: int) -> str:
    if market_count == 0:
        return "行情数据缺失时，不建议给出方向性判断，应先补齐本地市场数据库。"
    if news_count == 0 or macro_count == 0:
        return "当前可以做市场技术面观察，但新闻或宏观维度不完整，策略含义应保持审慎，避免把单一行情信号外推为完整投资结论。"
    return (
        "综合市场、新闻和宏观三类信号，当前更适合采用分层观察框架："
        "先识别趋势较强且风险状态可控的资产，再用新闻事件和宏观变量确认其持续性；"
        "若价格信号与宏观/新闻信号背离，应降低结论置信度，等待后续数据验证。"
    )


def _build_workspace_report(
    *,
    request: ResearchGenerateRequest,
    market: Any,
    news: Any,
    macro: Any,
    warnings: list[str],
    charts: dict[str, list[dict[str, str]]],
    core_report: str,
    llm_available: bool,
    task_log: list[str],
    report_title: str,
) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sections = set(request.sections or [])
    lines: list[str] = []

    lines.append(f"# {report_title}")
    lines.append("")
    lines.append(f"生成时间：{now}")
    lines.append(f"报告类型：{request.target}")
    lines.append(f"研究风格：{request.report_style}")
    lines.append(f"是否启用 LLM：{'是' if request.use_llm else '否'}")
    lines.append("")
    lines.append("## 数据状态")
    lines.append("")
    status_rows = [
        ["市场数据", f"读取 {market.count} 个指数/资产。"],
        ["新闻数据", f"读取 {news.count} 条本地新闻。"],
        ["宏观数据", f"读取 {macro.count} 个宏观指标。"],
    ]
    if request.use_llm and not llm_available:
        status_rows.append(["LLM 状态", "当前未检测到 DEEPSEEK_API_KEY，本报告使用规则型摘要生成。"])
    elif request.use_llm:
        status_rows.append(["LLM 状态", "已检测到 DeepSeek API key，核心报告模块会尝试调用 OpenAI-compatible 接口。"])
    else:
        status_rows.append(["LLM 状态", "本次请求关闭 LLM，仅使用规则型摘要。"])
    lines.extend(_table(["数据项", "状态"], status_rows))
    lines.append("")

    lines.append("## 一、核心结论")
    lines.append("")
    if market.count == 0 and news.count == 0 and macro.count == 0:
        lines.append("本次任务没有读取到市场、新闻和宏观数据，报告只能作为系统连通性验证，不能形成研究判断。")
    else:
        lines.append(
            f"本次报告基于 {market.count} 个市场资产、{news.count} 条新闻和 {macro.count} 个宏观指标生成。"
            f"{_strategy_text(market.count, news.count, macro.count)}"
        )
    lines.append("")

    if "market" in sections:
        lines.append("## 二、市场观察")
        lines.append("")
        if charts.get("market"):
            lines.append("### 走势图")
            lines.append("")
            for chart in charts["market"]:
                lines.append(f"![{chart['title']}]({chart['url']})")
                lines.append("")
                lines.append(f"*{chart['caption']}*")
                lines.append("")
        lines.extend(_market_lines(market.items))
        lines.append("")

    if "news" in sections:
        lines.append("## 三、新闻与风险信号")
        lines.append("")
        if charts.get("news"):
            lines.append("### 新闻评分图")
            lines.append("")
            for chart in charts["news"]:
                lines.append(f"![{chart['title']}]({chart['url']})")
                lines.append("")
                lines.append(f"*{chart['caption']}*")
                lines.append("")
        lines.extend(_news_lines(news.items))
        lines.append("")

    if "macro" in sections:
        lines.append("## 四、宏观环境观察")
        lines.append("")
        if charts.get("macro"):
            lines.append("### 宏观走势图")
            lines.append("")
            for chart in charts["macro"]:
                lines.append(f"![{chart['title']}]({chart['url']})")
                lines.append("")
                lines.append(f"*{chart['caption']}*")
                lines.append("")
        lines.extend(_macro_lines(macro.items))
        lines.append("")

    if "strategy" in sections:
        lines.append("## 五、策略含义")
        lines.append("")
        lines.append(_strategy_text(market.count, news.count, macro.count))
        if request.extra_instruction.strip():
            lines.append("")
            lines.append(f"用户额外要求：{request.extra_instruction.strip()}")
        lines.append("")

    lines.append("## 六、数据缺口与风险提示")
    lines.append("")
    if warnings:
        for warning in warnings:
            lines.append(f"- {warning}")
    else:
        lines.append("- 本次读取未返回显式 warning，但仍需注意本地数据可能存在延迟、缺口或数据源误差。")
    lines.append("- 本报告不会伪造不存在的数据；缺失数据会降低研究结论置信度。")
    lines.append("")

    if core_report:
        lines.append("## 七、附录：RAbot 核心报告模块输出")
        lines.append("")
        lines.append("> 以下内容来自现有 `RAbot.reporting.markdown_report.generate_index_markdown_report`，用于保留核心研究模块的原始输出。")
        lines.append("")
        lines.append(core_report)
        lines.append("")

    lines.append("## 八、附录：本次任务日志")
    lines.append("")
    for item in task_log:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("本报告由 RAbot 自动生成，仅用于研究与学习，不构成任何投资建议。")
    lines.append("")
    return "\n".join(lines)


def _build_fund_report(result: Any, request: ResearchGenerateRequest, task_log: list[str]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    info = result.info
    quote = result.quote
    indicators = result.indicators or {}
    lines: list[str] = []
    lines.append("# RAbot 基金/ETF研究报告")
    lines.append("")
    lines.append(f"生成时间：{now}")
    lines.append(f"研究对象：{result.name or result.symbol} ({result.symbol})")
    lines.append(f"报告风格：{request.report_style}")
    lines.append("")
    lines.append("## 一、核心结论")
    lines.append("")
    lines.append(result.research_summary or "当前数据不足，暂不能形成稳定研究摘要。")
    lines.append("")
    lines.append("## 二、基金/ETF 基础信息")
    lines.append("")
    lines.extend(
        _table(
            ["项目", "内容"],
            [
                ["代码", result.symbol],
                ["名称", result.name or "暂无"],
                ["市场", result.market],
                ["类型", result.fund_type],
                ["币种", result.currency or "暂无"],
                ["资产类别", getattr(info, "asset_class", None) or result.allocation_summary],
                ["基准", getattr(info, "benchmark", None) or "暂无"],
                ["基金公司", getattr(info, "fund_company", None) or "暂无"],
                ["成立日期", getattr(info, "inception_date", None) or "暂无"],
                ["费率", _fmt_number(getattr(info, "expense_ratio", None))],
                ["规模/AUM", _fmt_number(getattr(info, "aum", None))],
                ["数据源", result.source or "暂无"],
            ],
        )
    )
    lines.append("")
    lines.append("## 三、收益表现")
    lines.append("")
    lines.append(result.performance_summary)
    lines.extend(
        _table(
            ["指标", "数值"],
            [
                ["近1月收益", f"{_fmt_number(indicators.get('return_1m'))}%"],
                ["近3月收益", f"{_fmt_number(indicators.get('return_3m'))}%"],
                ["近6月收益", f"{_fmt_number(indicators.get('return_6m'))}%"],
                ["近1年收益", f"{_fmt_number(indicators.get('return_1y'))}%"],
                ["YTD", f"{_fmt_number(indicators.get('return_ytd'))}%"],
                ["年化收益", f"{_fmt_number(indicators.get('annualized_return'))}%"],
            ],
        )
    )
    lines.append("")
    lines.append("## 四、波动与回撤")
    lines.append("")
    lines.extend(
        _table(
            ["指标", "数值"],
            [
                ["年化波动率", f"{_fmt_number(indicators.get('annualized_volatility'))}%"],
                ["近一年最大回撤", f"{_fmt_number(indicators.get('max_drawdown_1y'))}%"],
                ["简化 Sharpe", _fmt_number(indicators.get("sharpe_ratio_simple"))],
                ["MA20", _fmt_number(indicators.get("ma20"))],
                ["MA60", _fmt_number(indicators.get("ma60"))],
                ["MA120", _fmt_number(indicators.get("ma120"))],
                ["Tracking Error", _fmt_number(indicators.get("tracking_error"))],
            ],
        )
    )
    lines.append("")
    lines.append("## 五、流动性观察")
    lines.append("")
    lines.append(result.liquidity_summary)
    if quote:
        lines.extend(
            _table(
                ["项目", "数值"],
                [
                    ["最新价", _fmt_number(quote.last_price)],
                    ["最新净值", _fmt_number(quote.nav)],
                    ["折溢价", f"{_fmt_number(quote.premium_discount)}%"],
                    ["成交量", _fmt_number(quote.volume)],
                    ["成交额", _fmt_number(quote.turnover)],
                ],
            )
        )
    lines.append("")
    lines.append("## 六、定投适配度观察")
    lines.append("")
    lines.append(result.dca_summary)
    lines.append("")
    lines.append("## 七、主要风险")
    lines.append("")
    lines.append(result.risk_summary)
    lines.append("")
    lines.append("## 八、数据缺口与免责声明")
    lines.append("")
    for warning in result.warnings or []:
        lines.append(f"- {warning}")
    lines.append("- ETF 二级市场价格可能与净值存在折溢价，跨境 ETF 还可能受到汇率、额度、时区和流动性影响。")
    lines.append("- 杠杆 ETF 不适合简单长期持有分析，需要单独风险框架。")
    lines.append("- 本报告仅用于研究和学习，不构成任何投资建议。")
    lines.append("")
    lines.append("## 附录：本次任务日志")
    lines.append("")
    for item in task_log:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def _run_fund_research_report_task(task_id: str, request: ResearchGenerateRequest) -> dict[str, Any]:
    task_log: list[str] = []
    symbol = (request.symbol or request.index_symbol or "").strip()
    if not symbol:
        raise ValueError("target=fund_analysis 时需要传入 symbol。")
    _update(task_id, 15, "正在读取基金/ETF数据", f"分析 {symbol}")
    task_log.append(f"开始读取基金/ETF 数据：{symbol}。")
    result = analyze_fund(symbol, use_llm=request.use_llm, count=500)
    task_log.append(f"基金/ETF 分析完成：{result.symbol}，样本 {len(result.bars)} 条。")
    _update(task_id, 85, "正在写入基金/ETF报告", "保存 Markdown 到 data/reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"fund_analysis_{result.symbol.replace('.', '_')}_{stamp}.md"
    markdown = _build_fund_report(result, request, task_log)
    meta = save_report_content(filename, markdown)
    task_log.append(f"报告已保存：{meta.filename}。")
    return {
        "filename": meta.filename,
        "title": meta.title,
        "path": str((REPORTS_DIR / meta.filename).resolve()),
        "updated_at": meta.updated_at,
        "size_bytes": meta.size_bytes,
        "warnings": result.warnings,
    }


def run_research_report_task(task_id: str, request: ResearchGenerateRequest) -> dict[str, Any]:
    if request.target == "fund_analysis":
        return _run_fund_research_report_task(task_id, request)

    task_log: list[str] = []

    _update(task_id, 5, "正在初始化研究任务", "正在准备报告生成参数")
    task_log.append("初始化研究任务完成。")

    _update(task_id, 20, "正在读取市场数据", "读取本地指数行情与技术状态")
    market = get_market_indexes(limit=60)
    task_log.append(f"市场数据读取完成：{market.count} 条。")

    _update(task_id, 35, "正在整理新闻与风险信号", "读取本地新闻与质量评分")
    news = get_latest_news(limit=80)
    if news.count == 0:
        try:
            from RAbot.news.news_engine import collect_all_news

            collect_result = collect_all_news(
                limit_per_source=10,
                markets=["CN", "US", "HK", "GLOBAL"],
                keywords=["Federal Reserve", "AI chips", "中国经济"],
            )
            task_log.append(f"新闻库为空，已尝试轻量采集，写入/更新 {collect_result.get('saved_count', 0)} 条。")
            news = get_latest_news(limit=80)
        except Exception as exc:
            task_log.append(f"新闻库为空，轻量采集失败：{type(exc).__name__}: {exc}")
    task_log.append(f"新闻数据读取完成：{news.count} 条。")

    _update(task_id, 50, "正在整理宏观数据", "读取本地宏观指标快照")
    macro = get_macro_overview(limit=80)
    task_log.append(f"宏观数据读取完成：{macro.count} 条。")

    warnings = _collect_warnings(market.warnings, news.warnings, macro.warnings)
    llm_available = _has_deepseek_key()
    effective_use_llm = bool(request.use_llm and llm_available)
    if request.use_llm and not llm_available:
        warnings.append("当前未检测到 DEEPSEEK_API_KEY，本报告使用规则型摘要生成。")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    charts = {
        "market": _generate_market_charts(market=market, warnings=warnings, stamp=stamp),
        "news": _generate_news_charts(news=news, warnings=warnings, stamp=stamp),
        "macro": _generate_macro_charts(macro=macro, warnings=warnings, stamp=stamp),
    }
    chart_count = sum(len(group) for group in charts.values())
    if chart_count:
        task_log.append(f"图表生成完成：{chart_count} 张。")

    _update(task_id, 70, "正在生成研究判断", "调用 RAbot 核心报告模块并生成兼容层判断")
    core_report = _try_core_markdown_report(use_llm=effective_use_llm, warnings=warnings)
    if core_report:
        task_log.append("已成功调用 RAbot 核心 Markdown 报告模块。")
    else:
        task_log.append("核心 Markdown 报告模块不可用或生成失败，已使用工作台兼容报告。")

    _update(task_id, 90, "正在写入 Markdown 报告", "保存报告到 data/reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"research_report_{stamp}.md"
    report_title = _generate_report_title(
        request=request,
        market=market,
        news=news,
        macro=macro,
        warnings=warnings,
        use_llm=effective_use_llm,
        llm_available=llm_available,
    )
    markdown = _build_workspace_report(
        request=request,
        market=market,
        news=news,
        macro=macro,
        warnings=warnings,
        charts=charts,
        core_report=core_report,
        llm_available=llm_available,
        task_log=task_log,
        report_title=report_title,
    )
    meta = save_report_content(filename, markdown)
    task_log.append(f"报告已保存：{meta.filename}。")

    return {
        "filename": meta.filename,
        "title": meta.title,
        "path": str((REPORTS_DIR / meta.filename).resolve()),
        "updated_at": meta.updated_at,
        "size_bytes": meta.size_bytes,
        "warnings": warnings,
    }
