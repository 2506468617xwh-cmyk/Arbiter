from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd

from RAbot.news.news_models import NewsItem
from RAbot.settings import get_data_dir


def get_news_research_db_path() -> Path:
    path = get_data_dir() / "news" / "news_research.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _json_dumps(value) -> str:
    return json.dumps(value or [], ensure_ascii=False)


def _json_loads(value) -> list:
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


class NewsResearchStore:
    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path or get_news_research_db_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS news_items (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT,
                    content TEXT,
                    source TEXT,
                    provider TEXT,
                    url TEXT,
                    published_at TEXT,
                    symbols_json TEXT,
                    markets_json TEXT,
                    topics_json TEXT,
                    language TEXT,
                    importance_score REAL,
                    quality_score REAL,
                    sentiment_score REAL,
                    risk_tags_json TEXT,
                    raw_json TEXT,
                    created_at TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news_items(published_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_provider ON news_items(provider)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_news_scores ON news_items(quality_score, importance_score)")

    def save_news_items(self, items: list[NewsItem]) -> int:
        if not items:
            return 0
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        saved = 0
        with self.connect() as conn:
            for item in items:
                if not item.title:
                    continue
                conn.execute(
                    """
                    INSERT INTO news_items (
                        id, title, summary, content, source, provider, url, published_at,
                        symbols_json, markets_json, topics_json, language,
                        importance_score, quality_score, sentiment_score, risk_tags_json,
                        raw_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        title=excluded.title,
                        summary=excluded.summary,
                        content=excluded.content,
                        source=excluded.source,
                        provider=excluded.provider,
                        url=excluded.url,
                        published_at=excluded.published_at,
                        symbols_json=excluded.symbols_json,
                        markets_json=excluded.markets_json,
                        topics_json=excluded.topics_json,
                        language=excluded.language,
                        importance_score=excluded.importance_score,
                        quality_score=excluded.quality_score,
                        sentiment_score=excluded.sentiment_score,
                        risk_tags_json=excluded.risk_tags_json,
                        raw_json=excluded.raw_json,
                        created_at=excluded.created_at
                    """,
                    (
                        item.id,
                        item.title,
                        item.summary,
                        item.content,
                        item.source,
                        item.provider,
                        item.url,
                        item.published_at,
                        _json_dumps(item.symbols),
                        _json_dumps(item.markets),
                        _json_dumps(item.topics),
                        item.language,
                        item.importance_score,
                        item.quality_score,
                        item.sentiment_score,
                        _json_dumps(item.risk_tags),
                        json.dumps(item.raw or {}, ensure_ascii=False, default=str),
                        now,
                    ),
                )
                saved += 1
        return saved

    def _rows_to_items(self, rows: list[sqlite3.Row]) -> list[NewsItem]:
        items = []
        for row in rows:
            data = dict(row)
            raw = {}
            try:
                raw = json.loads(data.get("raw_json") or "{}")
            except Exception:
                raw = {}
            items.append(
                NewsItem(
                    id=data.get("id"),
                    title=data.get("title") or "",
                    summary=data.get("summary"),
                    content=data.get("content"),
                    source=data.get("source") or "unknown",
                    provider=data.get("provider") or "unknown",
                    url=data.get("url"),
                    published_at=data.get("published_at"),
                    symbols=_json_loads(data.get("symbols_json")),
                    markets=_json_loads(data.get("markets_json")),
                    topics=_json_loads(data.get("topics_json")),
                    language=data.get("language") or "unknown",
                    importance_score=data.get("importance_score"),
                    quality_score=data.get("quality_score"),
                    sentiment_score=data.get("sentiment_score"),
                    risk_tags=_json_loads(data.get("risk_tags_json")),
                    raw=raw,
                )
            )
        return items

    def list_latest(self, limit: int = 100, market: str | None = None, topic: str | None = None, symbol: str | None = None) -> list[NewsItem]:
        query = "SELECT * FROM news_items WHERE 1=1"
        params: list = []
        if market and market.upper() != "ALL":
            query += " AND markets_json LIKE ?"
            params.append(f"%{market.upper()}%")
        if topic:
            query += " AND (topics_json LIKE ? OR risk_tags_json LIKE ?)"
            params.extend([f"%{topic}%", f"%{topic}%"])
        if symbol:
            query += " AND symbols_json LIKE ?"
            params.append(f"%{symbol.upper()}%")
        query += """
            ORDER BY
              CASE WHEN published_at IS NULL OR published_at = '' THEN 1 ELSE 0 END,
              published_at DESC,
              COALESCE(quality_score, 0) DESC,
              COALESCE(importance_score, 0) DESC
            LIMIT ?
        """
        params.append(max(1, min(limit, 500)))
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        return self._rows_to_items(rows)

    def search_news(self, keyword: str, limit: int = 100) -> list[NewsItem]:
        like = f"%{keyword}%"
        with self.connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM news_items
                WHERE title LIKE ? OR summary LIKE ? OR content LIKE ? OR source LIKE ?
                ORDER BY COALESCE(quality_score, 0) DESC, COALESCE(importance_score, 0) DESC, published_at DESC
                LIMIT ?
                """,
                (like, like, like, like, max(1, min(limit, 500))),
            ).fetchall()
        return self._rows_to_items(rows)

    def list_by_symbol(self, symbol: str, limit: int = 100) -> list[NewsItem]:
        return self.list_latest(limit=limit, symbol=symbol)

    def provider_summary(self) -> dict[str, int]:
        with self.connect() as conn:
            rows = conn.execute("SELECT provider, COUNT(*) FROM news_items GROUP BY provider").fetchall()
        return {str(provider): int(count) for provider, count in rows}


def news_items_to_dataframe(items: list[NewsItem]) -> pd.DataFrame:
    """将新版 NewsResearchStore 的 list[NewsItem] 转为旧版兼容的 DataFrame。

    下游模块（context_builder, alerts_engine, news_research）期望 DataFrame 带有
    related_assets / sentiment_label / source_name / published_at / importance_score /
    quality_score / title / summary / event_type / link 等列。
    """
    if not items:
        return pd.DataFrame()

    rows = []
    for item in items:
        sentiment_label = "中性"
        if item.sentiment_score is not None:
            if item.sentiment_score > 0.2:
                sentiment_label = "偏利多"
            elif item.sentiment_score < -0.2:
                sentiment_label = "偏利空"

        event_type = item.risk_tags[0] if item.risk_tags else "其他"

        rows.append({
            "id": item.id,
            "title": item.title,
            "summary": item.summary,
            "source_name": item.source,
            "source_id": item.provider,
            "link": item.url,
            "url": item.url,
            "published_at": item.published_at,
            "related_assets": ",".join(item.symbols) if item.symbols else "",
            "sentiment_label": sentiment_label,
            "importance_score": item.importance_score,
            "quality_score": item.quality_score,
            "sentiment_score": item.sentiment_score,
            "event_type": event_type,
            "risk_tags": item.risk_tags,
            "markets": item.markets,
            "topics": item.topics,
            "language": item.language,
            "source_score": None,
            "source_tier": None,
            "freshness_score": None,
            "normalized_title": None,
            "title_hash": None,
            "interpretation": None,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        })

    return pd.DataFrame(rows)


class NewsStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
        self._ensure_columns()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS news_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT,
                    source_name TEXT,
                    query TEXT,
                    title TEXT NOT NULL,
                    summary TEXT,
                    link TEXT,
                    published_at TEXT,
                    related_assets TEXT,
                    sentiment_label TEXT,
                    importance_score INTEGER,
                    interpretation TEXT,
                    created_at TEXT,
                    UNIQUE(link, title)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS news_update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    status TEXT,
                    message TEXT,
                    rows INTEGER,
                    updated_at TEXT
                )
                """
            )

    def _get_existing_columns(self, table_name: str) -> set[str]:
        with self.connect() as conn:
            rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row[1] for row in rows}

    def _ensure_columns(self) -> None:
        required_columns = {
            "event_type": "TEXT",
            "source_score": "INTEGER",
            "source_tier": "TEXT",
            "freshness_score": "INTEGER",
            "quality_score": "INTEGER",
            "normalized_title": "TEXT",
            "title_hash": "TEXT",
        }

        existing = self._get_existing_columns("news_items")

        with self.connect() as conn:
            for col, col_type in required_columns.items():
                if col not in existing:
                    conn.execute(f"ALTER TABLE news_items ADD COLUMN {col} {col_type}")

    def upsert_news(self, df: pd.DataFrame) -> int:
        if df.empty:
            self.log_update("EMPTY", "没有获取到新闻。", 0)
            return 0

        required_columns = [
            "source_id",
            "source_name",
            "query",
            "title",
            "summary",
            "link",
            "published_at",
            "related_assets",
            "sentiment_label",
            "importance_score",
            "event_type",
            "source_score",
            "source_tier",
            "freshness_score",
            "quality_score",
            "normalized_title",
            "title_hash",
            "interpretation",
        ]

        data = df.copy()

        for col in required_columns:
            if col not in data.columns:
                data[col] = None

        inserted_or_updated = 0

        with self.connect() as conn:
            for _, row in data.iterrows():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO news_items (
                        source_id,
                        source_name,
                        query,
                        title,
                        summary,
                        link,
                        published_at,
                        related_assets,
                        sentiment_label,
                        importance_score,
                        event_type,
                        source_score,
                        source_tier,
                        freshness_score,
                        quality_score,
                        normalized_title,
                        title_hash,
                        interpretation,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                    """,
                    tuple(row[col] for col in required_columns),
                )
                inserted_or_updated += 1

        self.log_update("SUCCESS", f"新闻更新成功，写入/更新 {inserted_or_updated} 条。", inserted_or_updated)
        return inserted_or_updated

    def read_news(
        self,
        limit: int = 100,
        asset: str | None = None,
        sentiment: str | None = None,
        source_id: str | None = None,
        keyword: str | None = None,
        event_type: str | None = None,
        source_tier: str | None = None,
        min_quality_score: int | None = None,
    ) -> pd.DataFrame:
        query = """
        SELECT
            id,
            source_id,
            source_name,
            query,
            title,
            summary,
            link,
            published_at,
            related_assets,
            sentiment_label,
            importance_score,
            event_type,
            source_score,
            source_tier,
            freshness_score,
            quality_score,
            normalized_title,
            title_hash,
            interpretation,
            created_at
        FROM news_items
        WHERE 1 = 1
        """

        params: list = []

        if asset and asset != "全部":
            query += " AND related_assets LIKE ?"
            params.append(f"%{asset}%")

        if sentiment and sentiment != "全部":
            query += " AND sentiment_label = ?"
            params.append(sentiment)

        if source_id and source_id != "全部":
            query += " AND source_id = ?"
            params.append(source_id)

        if event_type and event_type != "全部":
            query += " AND event_type = ?"
            params.append(event_type)

        if source_tier and source_tier != "全部":
            query += " AND source_tier = ?"
            params.append(source_tier)

        if min_quality_score is not None:
            query += " AND COALESCE(quality_score, 0) >= ?"
            params.append(int(min_quality_score))

        if keyword:
            query += " AND (title LIKE ? OR summary LIKE ? OR query LIKE ? OR event_type LIKE ?)"
            like = f"%{keyword}%"
            params.extend([like, like, like, like])

        query += """
        ORDER BY
            COALESCE(quality_score, 0) DESC,
            COALESCE(importance_score, 0) DESC,
            CASE WHEN published_at IS NULL OR published_at = '' THEN 1 ELSE 0 END,
            published_at DESC
        LIMIT ?
        """

        params.append(limit)

        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def read_news_sources(self) -> pd.DataFrame:
        query = """
        SELECT
            source_id,
            source_name,
            COUNT(*) AS rows,
            ROUND(AVG(COALESCE(source_score, 0)), 1) AS avg_source_score,
            ROUND(AVG(COALESCE(quality_score, 0)), 1) AS avg_quality_score,
            MAX(published_at) AS latest_published_at,
            MAX(created_at) AS latest_created_at
        FROM news_items
        GROUP BY source_id, source_name
        ORDER BY source_id
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn)

    def read_event_types(self) -> pd.DataFrame:
        query = """
        SELECT
            event_type,
            COUNT(*) AS rows,
            ROUND(AVG(COALESCE(quality_score, 0)), 1) AS avg_quality_score
        FROM news_items
        GROUP BY event_type
        ORDER BY rows DESC
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn)

    def log_update(self, status: str, message: str, rows: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO news_update_log (status, message, rows, updated_at)
                VALUES (?, ?, ?, datetime('now', 'localtime'))
                """,
                (status, message, rows),
            )

    def read_update_log(self, limit: int = 20) -> pd.DataFrame:
        query = """
        SELECT status, message, rows, updated_at
        FROM news_update_log
        ORDER BY id DESC
        LIMIT ?
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=[limit])
