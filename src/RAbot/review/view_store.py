from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from RAbot.settings import get_db_path


class ViewStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or get_db_path())
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_tables()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_views (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    updated_at TEXT,
                    source TEXT,
                    scope TEXT,
                    symbol TEXT,
                    title TEXT,
                    view_text TEXT,
                    thesis TEXT,
                    horizon_days INTEGER,
                    base_date TEXT,
                    base_price REAL,
                    status TEXT,
                    user_note TEXT,
                    review_result TEXT,
                    forward_return_1d REAL,
                    forward_return_5d REAL,
                    forward_return_20d REAL
                )
                """
            )

    def create_view(
        self,
        source: str,
        scope: str,
        symbol: str | None,
        title: str,
        view_text: str,
        thesis: str | None = None,
        horizon_days: int = 7,
        base_date: str | None = None,
        base_price: float | None = None,
        status: str = "observing",
        user_note: str | None = None,
    ) -> int | None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.connect() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO research_views (
                        created_at, updated_at, source, scope, symbol, title,
                        view_text, thesis, horizon_days, base_date, base_price,
                        status, user_note, review_result,
                        forward_return_1d, forward_return_5d, forward_return_20d
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        now,
                        now,
                        source,
                        scope,
                        symbol or "",
                        title,
                        view_text,
                        thesis or "",
                        int(horizon_days or 7),
                        base_date,
                        base_price,
                        status or "observing",
                        user_note or "",
                        "",
                        None,
                        None,
                        None,
                    ),
                )
                return int(cursor.lastrowid)
        except Exception:
            return None

    def list_views(
        self,
        limit: int = 100,
        status: str | None = None,
        symbol: str | None = None,
        source: str | None = None,
    ) -> pd.DataFrame:
        query = "SELECT * FROM research_views WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if symbol:
            query += " AND symbol LIKE ?"
            params.append(f"%{symbol}%")

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit or 100))

        try:
            with self.connect() as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()

    def get_view(self, view_id: int) -> dict[str, Any] | None:
        try:
            with self.connect() as conn:
                row = conn.execute(
                    "SELECT * FROM research_views WHERE id = ?",
                    (int(view_id),),
                ).fetchone()
                return dict(row) if row else None
        except Exception:
            return None

    def update_view_status(
        self,
        view_id: int,
        status: str,
        user_note: str | None = None,
    ) -> bool:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.connect() as conn:
                conn.execute(
                    """
                    UPDATE research_views
                    SET status = ?, user_note = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (status, user_note or "", now, int(view_id)),
                )
            return True
        except Exception:
            return False

    def update_review_metrics(self, view_id: int, metrics: dict[str, Any]) -> bool:
        allowed = {
            "review_result",
            "forward_return_1d",
            "forward_return_5d",
            "forward_return_20d",
        }
        updates = {key: value for key, value in metrics.items() if key in allowed}
        if not updates:
            return False

        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        set_clause = ", ".join([f"{key} = ?" for key in updates])
        params = list(updates.values()) + [int(view_id)]

        try:
            with self.connect() as conn:
                conn.execute(
                    f"UPDATE research_views SET {set_clause} WHERE id = ?",
                    params,
                )
            return True
        except Exception:
            return False

    def delete_view(self, view_id: int) -> bool:
        try:
            with self.connect() as conn:
                conn.execute("DELETE FROM research_views WHERE id = ?", (int(view_id),))
            return True
        except Exception:
            return False
