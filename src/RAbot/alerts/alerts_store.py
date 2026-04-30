from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pandas as pd

from RAbot.alerts.alerts_engine import ResearchAlert
from RAbot.settings import get_db_path


class AlertsStore:
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
                CREATE TABLE IF NOT EXISTS research_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT,
                    alert_type TEXT,
                    level TEXT,
                    title TEXT,
                    message TEXT,
                    symbols TEXT,
                    evidence_json TEXT,
                    status TEXT DEFAULT 'active',
                    user_note TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_research_alerts_daily_unique
                ON research_alerts (created_at, alert_type, title)
                """
            )

    def save_alerts(self, alerts: list[ResearchAlert]) -> int:
        saved = 0
        with self.connect() as conn:
            for alert in alerts:
                day = str(alert.created_at or "")[:10]
                try:
                    conn.execute(
                        """
                        INSERT OR IGNORE INTO research_alerts (
                            created_at, alert_type, level, title, message,
                            symbols, evidence_json, status, user_note
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'active', '')
                        """,
                        (
                            day,
                            alert.alert_type,
                            alert.level,
                            alert.title,
                            alert.message,
                            ",".join(alert.symbols or []),
                            json.dumps(alert.evidence or {}, ensure_ascii=False),
                        ),
                    )
                    if conn.total_changes > saved:
                        saved += 1
                except Exception:
                    continue
        return saved

    def list_alerts(
        self,
        limit: int = 100,
        status: str | None = None,
        alert_type: str | None = None,
        level: str | None = None,
    ) -> pd.DataFrame:
        query = "SELECT * FROM research_alerts WHERE 1=1"
        params: list[Any] = []

        if status:
            query += " AND status = ?"
            params.append(status)
        if alert_type:
            query += " AND alert_type = ?"
            params.append(alert_type)
        if level:
            query += " AND level = ?"
            params.append(level)

        query += " ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(int(limit or 100))

        try:
            with self.connect() as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception:
            return pd.DataFrame()

    def archive_alert(self, alert_id: int) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    "UPDATE research_alerts SET status = 'archived' WHERE id = ?",
                    (int(alert_id),),
                )
            return True
        except Exception:
            return False

    def update_note(self, alert_id: int, user_note: str) -> bool:
        try:
            with self.connect() as conn:
                conn.execute(
                    "UPDATE research_alerts SET user_note = ? WHERE id = ?",
                    (user_note or "", int(alert_id)),
                )
            return True
        except Exception:
            return False

    def clear_old_alerts(self, keep_latest: int = 300) -> int:
        try:
            with self.connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id FROM research_alerts
                    ORDER BY created_at DESC, id DESC
                    LIMIT -1 OFFSET ?
                    """,
                    (int(keep_latest or 300),),
                ).fetchall()
                ids = [int(row["id"]) for row in rows]
                if not ids:
                    return 0
                placeholders = ",".join(["?"] * len(ids))
                conn.execute(f"DELETE FROM research_alerts WHERE id IN ({placeholders})", ids)
                return len(ids)
        except Exception:
            return 0
