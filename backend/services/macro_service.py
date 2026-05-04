import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.schemas.macro import (
    MacroAnalysisRequest,
    MacroAnalysisResponse,
    MacroIndicatorItem,
    MacroOverviewResponse,
    MacroSeriesPoint,
    MacroSeriesResponse,
    MacroSnapshotItem,
    MacroSnapshotResponse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "market" / "index_research.db"


def _local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return {str(row[1]) for row in rows}


def _trend(change: float | None) -> str | None:
    if change is None:
        return None
    if change > 0:
        return "上行"
    if change < 0:
        return "下行"
    return "持平"


def _summary(name: str | None, indicator: str, latest_value: float | None, change: float | None, trend: str | None) -> str:
    label = name or indicator
    value_text = f"{latest_value:.2f}" if latest_value is not None else "暂无数值"
    if change is None or trend is None:
        return f"{label}最新值为 {value_text}。"
    return f"{label}最新值为 {value_text}，较上一期{trend} {change:.2f}。"


def get_macro_overview(limit: int = 50) -> MacroOverviewResponse:
    warnings: list[str] = []
    if not DB_PATH.exists():
        warnings.append(f"未找到本地研究数据库：{DB_PATH}")
        return MacroOverviewResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "macro_series"):
                warnings.append("本地数据库中没有 macro_series 表。")
                return MacroOverviewResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

            cols = _columns(conn, "macro_series")
            if not {"symbol", "date", "value"}.issubset(cols):
                warnings.append("macro_series 表缺少 symbol/date/value 字段。")
                return MacroOverviewResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

            name_expr = "name" if "name" in cols else "NULL AS name"
            rows = conn.execute(
                f"""
                WITH ranked AS (
                    SELECT
                        symbol,
                        date,
                        value,
                        {name_expr},
                        ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY date DESC) AS rn
                    FROM macro_series
                    WHERE value IS NOT NULL
                )
                SELECT
                    latest.symbol,
                    latest.name,
                    latest.date AS latest_date,
                    latest.value AS latest_value,
                    previous.value AS previous_value
                FROM ranked latest
                LEFT JOIN ranked previous
                    ON latest.symbol = previous.symbol AND previous.rn = 2
                WHERE latest.rn = 1
                ORDER BY latest.symbol
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
    except sqlite3.Error as exc:
        warnings.append(f"读取宏观数据失败：{exc}")
        return MacroOverviewResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

    items: list[MacroIndicatorItem] = []
    for row in rows:
        data = dict(row)
        indicator = str(data.get("symbol") or "").strip()
        if not indicator:
            continue
        latest_value = _to_float(data.get("latest_value"))
        previous_value = _to_float(data.get("previous_value"))
        change = None
        if latest_value is not None and previous_value is not None:
            change = latest_value - previous_value
        trend = _trend(change)
        items.append(
            MacroIndicatorItem(
                indicator=indicator,
                name=data.get("name"),
                latest_value=latest_value,
                latest_date=data.get("latest_date"),
                previous_value=previous_value,
                change=change,
                trend=trend,
                summary=_summary(data.get("name"), indicator, latest_value, change, trend),
            )
        )

    if not items:
        warnings.append("当前未找到宏观数据。可以运行 scripts/update_macro.py 更新。")

    return MacroOverviewResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)


def read_macro_series_frame() -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if not DB_PATH.exists():
        return pd.DataFrame(), [f"未找到本地研究数据库：{DB_PATH}"]

    try:
        with sqlite3.connect(DB_PATH) as conn:
            if not _table_exists(conn, "macro_series"):
                return pd.DataFrame(), ["本地数据库中没有 macro_series 表。"]

            cols = _columns(conn, "macro_series")
            required = {"symbol", "date", "value"}
            if not required.issubset(cols):
                missing = ", ".join(sorted(required - cols))
                return pd.DataFrame(), [f"macro_series 表缺少字段：{missing}。"]

            df = pd.read_sql_query('SELECT * FROM "macro_series" ORDER BY symbol, date', conn)
    except (sqlite3.Error, pd.errors.DatabaseError) as exc:
        return pd.DataFrame(), [f"读取宏观原始序列失败：{exc}"]

    if df.empty:
        warnings.append("macro_series 表当前为空。")
        return df, warnings

    df["symbol"] = df["symbol"].astype(str)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["symbol", "date", "value"])

    if df.empty:
        warnings.append("macro_series 表没有可用于研究的有效 symbol/date/value 数据。")

    return df, warnings


def _json_safe(value: Any) -> Any:
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    try:
        import numpy as np

        if isinstance(value, np.integer):
            return int(value)
        if isinstance(value, np.floating):
            return float(value)
    except Exception:
        pass
    return value


def _build_snapshot_df() -> tuple[pd.DataFrame, list[str]]:
    df, warnings = read_macro_series_frame()
    if df.empty:
        return pd.DataFrame(), warnings
    try:
        from RAbot.analysis.macro_research import build_macro_indicator_snapshot

        snapshot = build_macro_indicator_snapshot(df)
        return snapshot, warnings
    except Exception as exc:
        warnings.append(f"宏观快照生成失败：{type(exc).__name__}: {exc}")
        return pd.DataFrame(), warnings


def get_macro_snapshot(region: str | None = None, category: str | None = None, limit: int = 200) -> MacroSnapshotResponse:
    snapshot, warnings = _build_snapshot_df()
    if snapshot.empty:
        return MacroSnapshotResponse(items=[], count=0, regions=[], categories=[], last_update=_local_now_iso(), warnings=warnings)

    if region:
        snapshot = snapshot[snapshot["region"].astype(str).str.upper() == region.upper()]
    if category:
        snapshot = snapshot[snapshot["category"].astype(str) == category]

    regions = sorted([str(x) for x in snapshot.get("region", pd.Series(dtype=str)).dropna().unique()])
    categories = sorted([str(x) for x in snapshot.get("category", pd.Series(dtype=str)).dropna().unique()])
    snapshot = snapshot.head(max(1, min(limit, 500)))

    items = []
    for row in snapshot.to_dict(orient="records"):
        items.append(MacroSnapshotItem(**{key: _json_safe(value) for key, value in row.items()}))

    return MacroSnapshotResponse(
        items=items,
        count=len(items),
        regions=regions,
        categories=categories,
        last_update=_local_now_iso(),
        warnings=warnings,
    )


def get_macro_series(symbols: list[str] | None = None, limit_per_symbol: int = 240) -> MacroSeriesResponse:
    df, warnings = read_macro_series_frame()
    if df.empty:
        return MacroSeriesResponse(items=[], symbols=[], count=0, last_update=_local_now_iso(), warnings=warnings)

    requested = [symbol.strip() for symbol in symbols or [] if symbol.strip()]
    if requested:
        wanted = {symbol.upper() for symbol in requested}
        df = df[df["symbol"].astype(str).str.upper().isin(wanted)]

    rows = []
    for symbol, group in df.sort_values("date").groupby("symbol"):
        rows.append(group.tail(max(10, min(limit_per_symbol, 1000))))
    view = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()

    items = []
    for row in view.to_dict(orient="records"):
        items.append(
            MacroSeriesPoint(
                symbol=str(row.get("symbol")),
                name=_json_safe(row.get("name")),
                region=_json_safe(row.get("region")),
                category=_json_safe(row.get("category")),
                date=_json_safe(row.get("date")),
                value=_to_float(row.get("value")),
                unit=_json_safe(row.get("unit")),
            )
        )

    return MacroSeriesResponse(
        items=items,
        symbols=sorted({item.symbol for item in items}),
        count=len(items),
        last_update=_local_now_iso(),
        warnings=warnings,
    )


def analyze_macro_with_llm(request: MacroAnalysisRequest) -> MacroAnalysisResponse:
    snapshot = get_macro_snapshot(limit=80)
    series = get_macro_series(request.symbols[:8] if request.symbols else [item.symbol for item in snapshot.items[:8]], limit_per_symbol=24)
    warnings = [*snapshot.warnings, *series.warnings]
    if not request.use_llm:
        return MacroAnalysisResponse(
            ok=False,
            text=_macro_rule_answer(request.question, snapshot.items),
            model=None,
            warnings=warnings + ["当前已关闭大模型调用，返回规则层宏观摘要。"],
        )

    try:
        from RAbot.llm.llm_client import RAbotLLMClient

        client = RAbotLLMClient(max_tokens=900, temperature=0.25)
        if not client.is_available():
            return MacroAnalysisResponse(
                ok=False,
                text=_macro_rule_answer(request.question, snapshot.items),
                model=client.model,
                warnings=warnings + ["未检测到 DEEPSEEK_API_KEY，返回规则层宏观摘要。"],
            )
        facts = {
            "question": request.question,
            "snapshot": [item.model_dump() for item in snapshot.items[:60]],
            "series_tail": [item.model_dump() for item in series.items[-80:]],
        }
        result = client.generate(
            system_prompt="你是 RAbot 全球宏观研究员。只能基于给定宏观事实分析，不编造数据，不给投资买卖建议。",
            user_prompt=f"请基于以下本地宏观数据回答用户问题，输出中文，结构包含核心结论、支撑数据、风险变量、后续观察。\n\n{facts}",
        )
        return MacroAnalysisResponse(ok=result.ok, text=result.text, model=result.model, warnings=warnings + ([result.error] if result.error else []))
    except Exception as exc:
        return MacroAnalysisResponse(
            ok=False,
            text=_macro_rule_answer(request.question, snapshot.items),
            model=None,
            warnings=warnings + [f"宏观 LLM 分析失败：{type(exc).__name__}: {exc}"],
        )


def _macro_rule_answer(question: str, items: list[MacroSnapshotItem]) -> str:
    if not items:
        return "当前暂无可用宏观数据。请先运行 scripts/update_macro.py 更新全球宏观指标。"
    risk = [item for item in items if item.risk_label and ("压力" in item.risk_label or "走弱" in item.risk_label)]
    support = [item for item in items if item.risk_label and ("支撑" in item.risk_label or "改善" in item.risk_label or "修复" in item.risk_label)]
    latest = items[:5]
    lines = [
        f"针对问题“{question or '当前全球宏观环境如何'}”，规则层结论是：当前宏观环境需要同时观察增长、通胀、利率和风险偏好四条线。",
        f"压力线索约 {len(risk)} 条，支撑线索约 {len(support)} 条。",
        "最新重点指标：" + "；".join(f"{item.name or item.symbol}={item.latest_value}" for item in latest),
        "该结论仅基于本地宏观数据快照，不构成投资建议。",
    ]
    return "\n".join(lines)
