import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from backend.schemas.market import (
    MarketDashboardResponse,
    MarketIndexItem,
    MarketIndexResponse,
    MarketPerformanceItem,
    MarketPerformanceResponse,
    MarketSeriesPoint,
    MarketTimeseriesResponse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "market" / "index_research.db"


def _local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        f = float(value)
        import math
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _table_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [str(row[0]) for row in rows if row and row[0]]


def _columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return {str(row[1]) for row in rows}


def _choose_market_table(conn: sqlite3.Connection, warnings: list[str]) -> tuple[str | None, set[str]]:
    candidates = _table_names(conn)
    if not candidates:
        warnings.append("本地研究数据库中没有发现数据表。")
        return None, set()

    scored: list[tuple[int, str, set[str]]] = []
    keywords = ("index", "market", "price", "indicator", "research", "daily")
    required_like = {"symbol", "date"}
    useful = {"close", "pct_change", "ma20", "ma60", "name"}

    for table in candidates:
        cols = _columns(conn, table)
        score = sum(3 for key in keywords if key in table.lower())
        score += sum(4 for col in required_like if col in cols)
        score += sum(2 for col in useful if col in cols)
        if "news" in table.lower() or "macro" in table.lower():
            score -= 8
        if score > 0:
            scored.append((score, table, cols))

    if not scored:
        warnings.append("无法在本地数据库中识别行情或指数数据表。")
        return None, set()

    scored.sort(reverse=True, key=lambda item: item[0])
    _, table, cols = scored[0]
    if not {"symbol", "date"}.issubset(cols):
        warnings.append(f"已找到候选表 {table}，但缺少 symbol/date 字段，无法生成指数列表。")
        return None, cols

    return table, cols


def _trend_signal(close: float | None, ma20: float | None, ma60: float | None) -> str | None:
    if close is None:
        return None
    if ma20 is not None and ma60 is not None:
        if close >= ma20 >= ma60:
            return "强势趋势"
        if close < ma20 < ma60:
            return "弱势趋势"
    if ma20 is not None:
        return "站上MA20" if close >= ma20 else "跌破MA20"
    return None


def _risk_level(pct_change: float | None, close: float | None, ma60: float | None) -> str | None:
    if pct_change is not None and abs(pct_change) >= 3:
        return "高波动"
    if close is not None and ma60 is not None and close < ma60:
        return "趋势承压"
    if pct_change is not None and pct_change > 0:
        return "偏积极"
    return "中性观察"


def _summary(symbol: str, name: str | None, close: float | None, pct_change: float | None, trend: str | None) -> str:
    label = name or symbol
    parts = [f"{label}最新收盘"]
    parts.append(f"{close:.2f}" if close is not None else "暂无收盘价")
    if pct_change is not None:
        parts.append(f"日涨跌幅 {pct_change:.2f}%")
    if trend:
        parts.append(f"信号为{trend}")
    return "，".join(parts) + "。"


def _read_index_daily(symbols: list[str] | None = None, start: str | None = None, end: str | None = None) -> tuple[pd.DataFrame, list[str]]:
    warnings: list[str] = []
    if not DB_PATH.exists():
        return pd.DataFrame(), [f"未找到本地研究数据库：{DB_PATH}"]

    where: list[str] = []
    params: list[Any] = []

    if symbols:
        placeholders = ",".join(["?"] * len(symbols))
        where.append(f"symbol IN ({placeholders})")
        params.extend(symbols)
    if start:
        where.append("date >= ?")
        params.append(start)
    if end:
        where.append("date <= ?")
        params.append(end)

    sql = "SELECT * FROM index_daily"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY symbol, date"

    try:
        with sqlite3.connect(DB_PATH) as conn:
            tables = _table_names(conn)
            if "index_daily" not in tables:
                warnings.append("本地数据库中没有 index_daily 表。")
                return pd.DataFrame(), warnings
            df = pd.read_sql_query(sql, conn, params=params)
    except Exception as exc:
        warnings.append(f"读取 index_daily 失败：{type(exc).__name__}: {exc}")
        return pd.DataFrame(), warnings

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        for col in ["close", "pct_change", "ma20", "ma60", "ma120", "drawdown", "volatility_20d", "volume"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    return df, warnings


def _period_return(data: pd.DataFrame, days: int) -> float | None:
    clean = data.dropna(subset=["close"]).sort_values("date")
    if len(clean) < 2:
        return None
    latest = clean.iloc[-1]
    target_date = latest["date"] - pd.Timedelta(days=days)
    base = clean[clean["date"] <= target_date]
    if base.empty:
        base_row = clean.iloc[0]
    else:
        base_row = base.iloc[-1]
    base_close = _to_float(base_row.get("close"))
    latest_close = _to_float(latest.get("close"))
    if base_close in (None, 0) or latest_close is None:
        return None
    return (latest_close / base_close - 1) * 100


def _ytd_return(data: pd.DataFrame) -> float | None:
    clean = data.dropna(subset=["close"]).sort_values("date")
    if clean.empty:
        return None
    latest = clean.iloc[-1]
    start = pd.Timestamp(year=int(latest["date"].year), month=1, day=1)
    base = clean[clean["date"] >= start]
    if base.empty:
        return None
    base_close = _to_float(base.iloc[0].get("close"))
    latest_close = _to_float(latest.get("close"))
    if base_close in (None, 0) or latest_close is None:
        return None
    return (latest_close / base_close - 1) * 100


def _performance_item(symbol: str, data: pd.DataFrame) -> MarketPerformanceItem | None:
    clean = data.dropna(subset=["date"]).sort_values("date")
    if clean.empty:
        return None
    latest = clean.iloc[-1]
    close = _to_float(latest.get("close"))
    ma20 = _to_float(latest.get("ma20"))
    ma60 = _to_float(latest.get("ma60"))
    pct_change = _to_float(latest.get("pct_change"))
    trend = _trend_signal(close, ma20, ma60)
    risk = _risk_level(pct_change, close, ma60)
    return MarketPerformanceItem(
        symbol=symbol,
        name=latest.get("name"),
        latest_date=latest["date"].strftime("%Y-%m-%d") if pd.notna(latest["date"]) else None,
        close=close,
        return_1w=_period_return(clean, 7),
        return_1m=_period_return(clean, 30),
        return_3m=_period_return(clean, 90),
        return_ytd=_ytd_return(clean),
        return_1y=_period_return(clean, 365),
        volatility_20d=_to_float(latest.get("volatility_20d")),
        drawdown=_to_float(latest.get("drawdown")),
        trend_signal=trend,
        risk_level=risk,
    )


def _build_performance(df: pd.DataFrame) -> list[MarketPerformanceItem]:
    if df.empty or "symbol" not in df.columns:
        return []
    items: list[MarketPerformanceItem] = []
    for symbol, group in df.groupby("symbol"):
        item = _performance_item(str(symbol), group)
        if item:
            items.append(item)
    return items


def get_market_indexes(limit: int = 50) -> MarketIndexResponse:
    warnings: list[str] = []
    if not DB_PATH.exists():
        warnings.append(f"未找到本地研究数据库：{DB_PATH}")
        return MarketIndexResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            table, cols = _choose_market_table(conn, warnings)
            if not table:
                return MarketIndexResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

            select_cols = [
                col
                for col in ["symbol", "name", "date", "close", "pct_change", "ma20", "ma60", "updated_at"]
                if col in cols
            ]
            if "symbol" not in select_cols or "date" not in select_cols:
                warnings.append(f"候选行情表 {table} 缺少必要字段。")
                return MarketIndexResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

            select_expr = ", ".join(f'"{col}"' for col in select_cols)
            sql = f"""
                SELECT {select_expr}
                FROM "{table}" t
                WHERE "date" = (
                    SELECT MAX("date") FROM "{table}" t2 WHERE t2."symbol" = t."symbol"
                )
                ORDER BY "symbol"
                LIMIT ?
            """
            rows = conn.execute(sql, (limit,)).fetchall()
    except sqlite3.Error as exc:
        warnings.append(f"读取行情数据失败：{exc}")
        return MarketIndexResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)

    items: list[MarketIndexItem] = []
    for row in rows:
        data = dict(row)
        symbol = str(data.get("symbol") or "")
        if not symbol:
            continue
        close = _to_float(data.get("close"))
        pct_change = _to_float(data.get("pct_change"))
        ma20 = _to_float(data.get("ma20"))
        ma60 = _to_float(data.get("ma60"))
        trend = _trend_signal(close, ma20, ma60)
        risk = _risk_level(pct_change, close, ma60)
        items.append(
            MarketIndexItem(
                symbol=symbol,
                name=data.get("name"),
                date=data.get("date"),
                close=close,
                pct_change=pct_change,
                ma20=ma20,
                ma60=ma60,
                trend_signal=trend,
                risk_level=risk,
                summary=_summary(symbol, data.get("name"), close, pct_change, trend),
            )
        )

    if not items:
        warnings.append("行情数据表可读取，但当前没有可展示的最新指数记录。")

    return MarketIndexResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)


def get_market_performance() -> MarketPerformanceResponse:
    # Only read last 2 years — don't scan the entire history
    two_years_ago = (datetime.now() - pd.DateOffset(years=2)).strftime("%Y-%m-%d")
    df, warnings = _read_index_daily(start=two_years_ago)
    items = _build_performance(df)
    if not items and not warnings:
        warnings.append("当前暂无可展示的市场表现数据。")
    items.sort(key=lambda item: item.return_1m if item.return_1m is not None else -999999, reverse=True)
    return MarketPerformanceResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)


def get_market_dashboard() -> MarketDashboardResponse:
    perf = get_market_performance()
    items = perf.items
    strong = sorted(items, key=lambda item: item.return_1m if item.return_1m is not None else -999999, reverse=True)[:5]
    weak = sorted(items, key=lambda item: item.return_1m if item.return_1m is not None else 999999)[:5]
    high_vol = sorted(items, key=lambda item: item.volatility_20d if item.volatility_20d is not None else -999999, reverse=True)[:5]
    high_drawdown = sorted(items, key=lambda item: item.drawdown if item.drawdown is not None else 999999)[:5]
    latest_date = max((item.latest_date for item in items if item.latest_date), default=None)
    if items:
        summary = f"当前本地行情覆盖 {len(items)} 个资产，近1月强势资产包括：" + "、".join(item.symbol for item in strong[:3]) + "。"
    else:
        summary = "当前暂无本地行情数据，无法生成市场仪表盘。"
    return MarketDashboardResponse(
        market_status="connected" if items else "no_data",
        asset_count=len(items),
        latest_date=latest_date,
        strong_assets=strong,
        weak_assets=weak,
        high_volatility_assets=high_vol,
        high_drawdown_assets=high_drawdown,
        all_items=items,
        summary=summary,
        last_update=_local_now_iso(),
        warnings=perf.warnings,
    )


def get_market_timeseries(
    symbols: list[str],
    start: str | None = None,
    end: str | None = None,
    normalize: bool = False,
) -> MarketTimeseriesResponse:
    symbols = [s.strip().upper() for s in symbols if s.strip()]
    if not symbols:
        return MarketTimeseriesResponse(items=[], symbols=[], count=0, last_update=_local_now_iso(), warnings=["请至少选择一个资产。"])

    df, warnings = _read_index_daily(symbols=symbols, start=start, end=end)
    points: list[MarketSeriesPoint] = []
    if df.empty:
        if not warnings:
            warnings.append("当前筛选条件下没有走势数据。")
        return MarketTimeseriesResponse(items=[], symbols=symbols, count=0, last_update=_local_now_iso(), warnings=warnings)

    for symbol, group in df.groupby("symbol"):
        clean = group.dropna(subset=["date"]).sort_values("date").copy()
        base_close = None
        if normalize:
            first = clean.dropna(subset=["close"]).head(1)
            if not first.empty:
                base_close = _to_float(first.iloc[0].get("close"))
        for _, row in clean.iterrows():
            close = _to_float(row.get("close"))
            normalized = (close / base_close * 100) if normalize and close is not None and base_close not in (None, 0) else None
            points.append(
                MarketSeriesPoint(
                    symbol=str(symbol),
                    name=row.get("name"),
                    date=row["date"].strftime("%Y-%m-%d"),
                    close=close,
                    pct_change=_to_float(row.get("pct_change")),
                    ma20=_to_float(row.get("ma20")),
                    ma60=_to_float(row.get("ma60")),
                    ma120=_to_float(row.get("ma120")),
                    drawdown=_to_float(row.get("drawdown")),
                    volume=_to_float(row.get("volume")),
                    normalized=normalized,
                )
            )
    return MarketTimeseriesResponse(items=points, symbols=symbols, count=len(points), last_update=_local_now_iso(), warnings=warnings)


def get_available_symbols() -> list[str]:
    df, _ = _read_index_daily()
    if df.empty or "symbol" not in df.columns:
        return []
    return sorted(df["symbol"].dropna().astype(str).unique().tolist())
