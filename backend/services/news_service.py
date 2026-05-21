from __future__ import annotations

import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from backend.schemas.news import NewsCollectRequest, NewsCollectResponse, NewsDetailResponse, NewsItem, NewsLatestResponse


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "market" / "index_research.db"
_NEWS_COLLECT_LOCK = threading.Lock()
_LAST_AUTO_COLLECT_AT: datetime | None = None


def _local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env", override=False)
    except Exception:
        pass


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _json_loads(value: str | None) -> list:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def _from_model_item(item: Any) -> NewsItem:
    risk_tags = list(getattr(item, "risk_tags", []) or [])
    return NewsItem(
        id=getattr(item, "id", None),
        title=getattr(item, "title", ""),
        source=getattr(item, "source", None),
        provider=getattr(item, "provider", None),
        published_at=getattr(item, "published_at", None),
        url=getattr(item, "url", None),
        quality_score=_to_float(getattr(item, "quality_score", None)),
        importance_score=_to_float(getattr(item, "importance_score", None)),
        sentiment_score=_to_float(getattr(item, "sentiment_score", None)),
        risk_tag=risk_tags[0] if risk_tags else None,
        risk_tags=risk_tags,
        markets=list(getattr(item, "markets", []) or []),
        topics=list(getattr(item, "topics", []) or []),
        symbols=list(getattr(item, "symbols", []) or []),
        summary=getattr(item, "summary", None),
        language=getattr(item, "language", None),
    )


def _read_new_store(
    limit: int,
    market: str | None = None,
    topic: str | None = None,
    symbol: str | None = None,
    keyword: str | None = None,
) -> tuple[list[NewsItem], list[str]]:
    warnings: list[str] = []
    try:
        from RAbot.news.news_store import NewsResearchStore

        store = NewsResearchStore()
        if keyword:
            model_items = store.search_news(keyword, limit=limit)
        elif symbol:
            model_items = store.list_by_symbol(symbol, limit=limit)
        else:
            model_items = store.list_latest(limit=limit, market=market, topic=topic, symbol=symbol)
        return [_from_model_item(item) for item in model_items], warnings
    except Exception as exc:
        warnings.append(f"读取新新闻库失败：{type(exc).__name__}: {exc}")
        return [], warnings


def _new_store_stats() -> dict[str, Any]:
    try:
        from RAbot.news.news_store import NewsResearchStore

        store = NewsResearchStore()
        with store.connect() as conn:
            row = conn.execute("SELECT COUNT(*), MAX(created_at), MAX(published_at) FROM news_items").fetchone()
            providers = store.provider_summary()
        return {
            "count": int(row[0] or 0) if row else 0,
            "latest_created_at": row[1] if row else None,
            "latest_published_at": row[2] if row else None,
            "providers": providers,
        }
    except Exception:
        return {"count": 0, "latest_created_at": None, "latest_published_at": None, "providers": {}}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        import pandas as pd

        dt = pd.to_datetime(value, errors="coerce")
        if pd.isna(dt):
            return None
        py_dt = dt.to_pydatetime()
        return py_dt.astimezone().replace(tzinfo=None) if py_dt.tzinfo else py_dt
    except Exception:
        return None


def _auto_refresh_minutes() -> int:
    try:
        return max(5, int(os.getenv("RABOT_NEWS_AUTO_REFRESH_MINUTES", "60")))
    except Exception:
        return 60


def _legacy_fallback_enabled() -> bool:
    return os.getenv("RABOT_NEWS_ALLOW_LEGACY_FALLBACK", "false").strip().lower() in {"1", "true", "yes", "on"}


def _should_auto_collect(stats: dict[str, Any], *, filtered: bool) -> bool:
    if _auto_refresh_minutes() == 0:
        return False
    global _LAST_AUTO_COLLECT_AT
    now = datetime.now()
    if _LAST_AUTO_COLLECT_AT and (now - _LAST_AUTO_COLLECT_AT) < timedelta(minutes=5):
        return False
    if int(stats.get("count") or 0) == 0:
        return True
    latest = _parse_dt(stats.get("latest_created_at") or stats.get("latest_published_at"))
    if latest is None:
        return True
    if now - latest > timedelta(minutes=_auto_refresh_minutes()):
        return True
    return filtered and int(stats.get("count") or 0) < 20


def _auto_collect_news(
    *,
    reason: str,
    limit_per_source: int,
    market: str | None = None,
    symbol: str | None = None,
    topic: str | None = None,
    keyword: str | None = None,
) -> tuple[int, dict[str, Any], list[str]]:
    global _LAST_AUTO_COLLECT_AT
    if not _NEWS_COLLECT_LOCK.acquire(blocking=False):
        return 0, {}, ["新闻采集正在进行中，本次请求先返回当前缓存。"]
    try:
        _load_env()
        from RAbot.news.news_engine import collect_all_news

        markets = [market.upper()] if market and market.upper() != "ALL" else ["CN", "US", "HK", "GLOBAL"]
        symbols = [symbol.strip().upper()] if symbol and symbol.strip() else []
        keywords: list[str] = []
        if keyword and keyword.strip():
            keywords.append(keyword.strip())
        if topic and topic.strip():
            keywords.append(topic.strip().replace("_", " "))
        if not keywords:
            keywords = ["Federal Reserve", "AI chips", "China economy", "Hong Kong stocks", "A shares"]
        result = collect_all_news(
            limit_per_source=max(5, min(limit_per_source, 80)),
            markets=markets,
            symbols=symbols,
            keywords=keywords,
        )
        _LAST_AUTO_COLLECT_AT = datetime.now()
        warnings = list(result.get("warnings", []) or [])
        warnings.append(f"已自动使用新新闻源刷新：{reason}；保存/更新 {result.get('saved_count', 0)} 条。")
        return int(result.get("saved_count", 0) or 0), result.get("provider_stats", {}) or {}, warnings
    except Exception as exc:
        _LAST_AUTO_COLLECT_AT = datetime.now()
        return 0, {}, [f"自动新闻采集失败：{type(exc).__name__}: {exc}"]
    finally:
        _NEWS_COLLECT_LOCK.release()


def _stats_warning(prefix: str, provider_stats: dict[str, Any]) -> str | None:
    if not provider_stats:
        return None
    parts = [
        f"{name} fetched={stats.get('fetched', 0)} saved={stats.get('saved', 0)}"
        for name, stats in provider_stats.items()
    ]
    return f"{prefix}：" + "; ".join(parts)


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table_name}")').fetchall()
    return {str(row[1]) for row in rows}


def get_latest_news(limit: int = 30, market: str | None = None, topic: str | None = None, symbol: str | None = None) -> NewsLatestResponse:
    _load_env()
    filtered = bool((market and market.upper() != "ALL") or topic or symbol)
    warnings: list[str] = []
    stats = _new_store_stats()
    if _should_auto_collect(stats, filtered=filtered):
        _, provider_stats, collect_warnings = _auto_collect_news(
            reason="新新闻库为空、过期或需要补齐筛选结果",
            limit_per_source=max(20, min(limit, 80)),
            market=market,
            symbol=symbol,
            topic=topic,
        )
        warnings.extend(collect_warnings)
        stat_warning = _stats_warning("新新闻源统计", provider_stats)
        if stat_warning:
            warnings.append(stat_warning)

    items, read_warnings = _read_new_store(limit=limit, market=market, topic=topic, symbol=symbol)
    warnings.extend(read_warnings)
    if not items and filtered:
        _, provider_stats, collect_warnings = _auto_collect_news(
            reason="当前筛选条件新库无匹配，按筛选条件补采",
            limit_per_source=max(20, min(limit, 80)),
            market=market,
            symbol=symbol,
            topic=topic,
        )
        warnings.extend(collect_warnings)
        stat_warning = _stats_warning("筛选补采统计", provider_stats)
        if stat_warning:
            warnings.append(stat_warning)
        items, read_warnings = _read_new_store(limit=limit, market=market, topic=topic, symbol=symbol)
        warnings.extend(read_warnings)
    if items:
        return NewsLatestResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)
    if filtered:
        warnings.append("当前筛选条件下新新闻库没有匹配结果；已尝试使用新 API 补采，未再使用旧库兜底。")
        return NewsLatestResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)
    if not _legacy_fallback_enabled():
        warnings.append("新新闻库暂无数据，且 RABOT_NEWS_ALLOW_LEGACY_FALLBACK 未开启，因此不再使用旧库兜底。请检查新 API provider_stats 或点击更新新闻。")
        return NewsLatestResponse(items=[], count=0, last_update=_local_now_iso(), warnings=warnings)
    legacy_items, legacy_warnings = _read_legacy_news(limit=limit)
    return NewsLatestResponse(items=legacy_items, count=len(legacy_items), last_update=_local_now_iso(), warnings=[*warnings, *legacy_warnings])


def search_news(keyword: str, limit: int = 100) -> NewsLatestResponse:
    _load_env()
    keyword = keyword.strip()
    if not keyword:
        return NewsLatestResponse(items=[], count=0, last_update=_local_now_iso(), warnings=["请输入搜索关键词。"])
    items, warnings = _read_new_store(limit=limit, keyword=keyword)
    if not items:
        _, provider_stats, collect_warnings = _auto_collect_news(
            reason="搜索关键词新库无匹配，按关键词补采",
            limit_per_source=max(20, min(limit, 80)),
            keyword=keyword,
        )
        warnings.extend(collect_warnings)
        stat_warning = _stats_warning("搜索补采统计", provider_stats)
        if stat_warning:
            warnings.append(stat_warning)
        items, read_warnings = _read_new_store(limit=limit, keyword=keyword)
        warnings.extend(read_warnings)
    return NewsLatestResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)


def get_news_by_symbol(symbol: str, limit: int = 100) -> NewsLatestResponse:
    _load_env()
    symbol = symbol.strip().upper()
    if not symbol:
        return NewsLatestResponse(items=[], count=0, last_update=_local_now_iso(), warnings=["请输入股票代码。"])
    items, warnings = _read_new_store(limit=limit, symbol=symbol)
    if not items:
        _, provider_stats, collect_warnings = _auto_collect_news(
            reason="代码相关新闻新库无匹配，按 symbol 补采",
            limit_per_source=max(20, min(limit, 80)),
            symbol=symbol,
        )
        warnings.extend(collect_warnings)
        stat_warning = _stats_warning("代码补采统计", provider_stats)
        if stat_warning:
            warnings.append(stat_warning)
        items, read_warnings = _read_new_store(limit=limit, symbol=symbol)
        warnings.extend(read_warnings)
    return NewsLatestResponse(items=items, count=len(items), last_update=_local_now_iso(), warnings=warnings)


def collect_news(request: NewsCollectRequest) -> NewsCollectResponse:
    try:
        _load_env()
        from RAbot.news.news_engine import collect_all_news

        result = collect_all_news(
            limit_per_source=max(1, min(request.limit_per_source, 100)),
            markets=request.markets,
            symbols=request.symbols,
            keywords=request.keywords,
        )
        return NewsCollectResponse(
            items=[_from_model_item(item) for item in result.get("items", [])[:100]],
            saved_count=int(result.get("saved_count", 0)),
            provider_stats=result.get("provider_stats", {}),
            warnings=result.get("warnings", []),
            last_update=result.get("last_update") or _local_now_iso(),
        )
    except Exception as exc:
        return NewsCollectResponse(
            items=[],
            saved_count=0,
            provider_stats={},
            warnings=[f"新闻采集失败：{type(exc).__name__}: {exc}"],
            last_update=_local_now_iso(),
        )


def get_news_detail(news_id: str) -> NewsDetailResponse:
    if not str(news_id).strip():
        raise HTTPException(status_code=400, detail="Invalid news id.")
    item = _get_new_news_detail(news_id)
    if item:
        return item
    if _legacy_fallback_enabled():
        item = _get_legacy_news_detail(news_id)
        if item:
            return item
    raise HTTPException(status_code=404, detail="News item not found.")


def _get_new_news_detail(news_id: str) -> NewsDetailResponse | None:
    try:
        from RAbot.news.news_store import NewsResearchStore

        store = NewsResearchStore()
        with store.connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM news_items WHERE id = ? LIMIT 1", (news_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        raw = {}
        try:
            raw = json.loads(data.get("raw_json") or "{}")
        except Exception:
            raw = {}
        risk_tags = _json_loads(data.get("risk_tags_json"))
        return NewsDetailResponse(
            id=data.get("id"),
            title=data.get("title") or "",
            source=data.get("source"),
            provider=data.get("provider"),
            published_at=data.get("published_at"),
            url=data.get("url"),
            quality_score=_to_float(data.get("quality_score")),
            importance_score=_to_float(data.get("importance_score")),
            sentiment_score=_to_float(data.get("sentiment_score")),
            risk_tag=risk_tags[0] if risk_tags else None,
            risk_tags=risk_tags,
            markets=_json_loads(data.get("markets_json")),
            topics=_json_loads(data.get("topics_json")),
            symbols=_json_loads(data.get("symbols_json")),
            summary=data.get("summary"),
            content=data.get("content"),
            language=data.get("language"),
            created_at=data.get("created_at"),
            raw=raw,
        )
    except Exception:
        return None


def _read_legacy_news(limit: int) -> tuple[list[NewsItem], list[str]]:
    warnings: list[str] = ["当前启用了旧版新闻库兜底：RABOT_NEWS_ALLOW_LEGACY_FALLBACK=true。"]
    if not DB_PATH.exists():
        warnings.append(f"未找到旧版研究数据库：{DB_PATH}")
        return [], warnings
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "news_items"):
                warnings.append("旧版数据库中没有 news_items 表。")
                return [], warnings
            cols = _columns(conn, "news_items")
            select_cols = [
                col
                for col in [
                    "id",
                    "title",
                    "source_name",
                    "published_at",
                    "link",
                    "quality_score",
                    "importance_score",
                    "sentiment_label",
                    "event_type",
                    "summary",
                    "interpretation",
                    "created_at",
                ]
                if col in cols
            ]
            if "title" not in select_cols:
                warnings.append("旧版 news_items 表缺少 title 字段。")
                return [], warnings
            rows = conn.execute(
                f"""SELECT {", ".join(f'"{col}"' for col in select_cols)}
                FROM news_items
                ORDER BY
                  CASE WHEN published_at IS NULL OR published_at = '' THEN 1 ELSE 0 END,
                  published_at DESC,
                  COALESCE(quality_score, 0) DESC,
                  COALESCE(importance_score, 0) DESC
                LIMIT ?""",
                (limit,),
            ).fetchall()
    except sqlite3.Error as exc:
        warnings.append(f"读取旧版新闻库失败：{exc}")
        return [], warnings
    items = []
    for row in rows:
        data = dict(row)
        title = str(data.get("title") or "").strip()
        if not title:
            continue
        risk_tag = data.get("event_type") or data.get("sentiment_label")
        items.append(
            NewsItem(
                id=data.get("id"),
                title=title,
                source=data.get("source_name"),
                published_at=data.get("published_at"),
                url=data.get("link"),
                quality_score=_to_float(data.get("quality_score")),
                importance_score=_to_float(data.get("importance_score")),
                risk_tag=risk_tag,
                risk_tags=[risk_tag] if risk_tag else [],
                summary=data.get("summary") or data.get("interpretation"),
            )
        )
    return items, warnings


def _get_legacy_news_detail(news_id: str) -> NewsDetailResponse | None:
    if not DB_PATH.exists():
        return None
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            if not _table_exists(conn, "news_items"):
                return None
            cols = _columns(conn, "news_items")
            id_col = "id" if "id" in cols else "rowid"
            row = conn.execute(
                f'SELECT rowid AS __rowid__, * FROM "news_items" WHERE "{id_col}" = ? LIMIT 1',
                (news_id,),
            ).fetchone()
    except sqlite3.Error:
        return None
    if row is None:
        return None
    data = dict(row)
    title = str(data.get("title") or "").strip()
    if not title:
        return None
    risk_tag = data.get("event_type") or data.get("sentiment_label")
    return NewsDetailResponse(
        id=data.get("id") or data.get("__rowid__"),
        title=title,
        source=data.get("source_name"),
        published_at=data.get("published_at"),
        url=data.get("link"),
        quality_score=_to_float(data.get("quality_score")),
        importance_score=_to_float(data.get("importance_score")),
        risk_tag=risk_tag,
        risk_tags=[risk_tag] if risk_tag else [],
        summary=data.get("summary") or data.get("interpretation"),
        source_id=data.get("source_id"),
        query=data.get("query"),
        related_assets=data.get("related_assets"),
        sentiment_label=data.get("sentiment_label"),
        event_type=data.get("event_type"),
        source_score=_to_float(data.get("source_score")),
        source_tier=data.get("source_tier"),
        freshness_score=_to_float(data.get("freshness_score")),
        interpretation=data.get("interpretation"),
        created_at=data.get("created_at"),
        raw={k: v for k, v in data.items() if k != "__rowid__"},
    )
