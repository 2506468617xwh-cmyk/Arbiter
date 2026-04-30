from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


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