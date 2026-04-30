# src/RAbot/macro/macro_store.py

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

from RAbot.settings import PROJECT_DIR


DEFAULT_DB_PATH = PROJECT_DIR / "data" / "market" / "index_research.db"


class MacroStore:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = Path(db_path or DEFAULT_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_tables()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def ensure_tables(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS macro_series (
                    symbol TEXT NOT NULL,
                    date TEXT NOT NULL,
                    value REAL,
                    name TEXT,
                    region TEXT,
                    category TEXT,
                    source TEXT,
                    unit TEXT,
                    frequency TEXT,
                    direction_note TEXT,
                    related_assets TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (symbol, date)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS macro_update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    name TEXT,
                    region TEXT,
                    source TEXT,
                    status TEXT,
                    rows INTEGER,
                    message TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            conn.commit()

    def upsert_macro_series(self, df: pd.DataFrame) -> int:
        if df is None or df.empty:
            return 0

        required = [
            "symbol",
            "date",
            "value",
            "name",
            "region",
            "category",
            "source",
            "unit",
            "frequency",
            "direction_note",
            "related_assets",
        ]

        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"macro_series 缺少字段：{missing}")

        clean = df[required].copy()
        clean["date"] = pd.to_datetime(clean["date"], errors="coerce").dt.strftime("%Y-%m-%d")
        clean["value"] = pd.to_numeric(clean["value"], errors="coerce")
        clean = clean.dropna(subset=["symbol", "date", "value"])

        if clean.empty:
            return 0

        rows = list(clean.itertuples(index=False, name=None))

        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO macro_series (
                    symbol,
                    date,
                    value,
                    name,
                    region,
                    category,
                    source,
                    unit,
                    frequency,
                    direction_note,
                    related_assets,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(symbol, date) DO UPDATE SET
                    value = excluded.value,
                    name = excluded.name,
                    region = excluded.region,
                    category = excluded.category,
                    source = excluded.source,
                    unit = excluded.unit,
                    frequency = excluded.frequency,
                    direction_note = excluded.direction_note,
                    related_assets = excluded.related_assets,
                    updated_at = CURRENT_TIMESTAMP
                """,
                rows,
            )
            conn.commit()

        return len(rows)

    def log_update(
        self,
        symbol: str,
        name: str,
        region: str,
        source: str,
        status: str,
        rows: int,
        message: str = "",
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO macro_update_log (
                    symbol,
                    name,
                    region,
                    source,
                    status,
                    rows,
                    message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (symbol, name, region, source, status, rows, message),
            )
            conn.commit()

    def read_macro_series(
        self,
        symbols: list[str] | None = None,
        region: str | None = None,
        category: str | None = None,
    ) -> pd.DataFrame:
        where = []
        params = []

        if symbols:
            placeholders = ",".join(["?"] * len(symbols))
            where.append(f"symbol IN ({placeholders})")
            params.extend(symbols)

        if region:
            where.append("region = ?")
            params.append(region)

        if category:
            where.append("category = ?")
            params.append(category)

        sql = "SELECT * FROM macro_series"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY symbol, date"

        with self.connect() as conn:
            df = pd.read_sql_query(sql, conn, params=params)

        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df["value"] = pd.to_numeric(df["value"], errors="coerce")

        return df

    def read_update_log(self, limit: int = 50) -> pd.DataFrame:
        with self.connect() as conn:
            df = pd.read_sql_query(
                """
                SELECT *
                FROM macro_update_log
                ORDER BY updated_at DESC, id DESC
                LIMIT ?
                """,
                conn,
                params=(limit,),
            )

        return df