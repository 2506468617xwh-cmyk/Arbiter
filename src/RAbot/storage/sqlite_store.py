from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd


class SQLiteStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_daily (
                    date TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    name TEXT,
                    market TEXT,
                    source TEXT,
                    source_symbol TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    pct_change REAL,
                    ma20 REAL,
                    ma60 REAL,
                    ma120 REAL,
                    volatility_20d REAL,
                    drawdown REAL,
                    updated_at TEXT,
                    PRIMARY KEY (date, symbol)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS update_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    status TEXT,
                    message TEXT,
                    rows INTEGER,
                    updated_at TEXT
                )
                """
            )

    def upsert_index_daily(self, df: pd.DataFrame) -> None:
        if df.empty:
            return

        required_columns = [
            "date",
            "symbol",
            "name",
            "market",
            "source",
            "source_symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "amount",
            "pct_change",
            "ma20",
            "ma60",
            "ma120",
            "volatility_20d",
            "drawdown",
            "updated_at",
        ]

        data = df.copy()

        for col in required_columns:
            if col not in data.columns:
                data[col] = None

        data = data[required_columns]

        with self.connect() as conn:
            for _, row in data.iterrows():
                conn.execute(
                    """
                    INSERT OR REPLACE INTO index_daily (
                        date, symbol, name, market, source, source_symbol,
                        open, high, low, close, volume, amount,
                        pct_change, ma20, ma60, ma120, volatility_20d, drawdown,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    tuple(row[col] for col in required_columns),
                )

    def read_index_daily(self, symbol: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM index_daily"
        params: list = []

        if symbol:
            query += " WHERE symbol = ?"
            params.append(symbol)

        query += " ORDER BY date ASC"

        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=params)

    def get_data_status(self) -> pd.DataFrame:
        query = """
        SELECT
            symbol,
            name,
            market,
            source,
            MIN(date) AS start_date,
            MAX(date) AS end_date,
            COUNT(*) AS rows
        FROM index_daily
        GROUP BY symbol, name, market, source
        ORDER BY symbol
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn)

    def log_update(self, symbol: str, status: str, message: str, rows: int) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO update_log (symbol, status, message, rows, updated_at)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'))
                """,
                (symbol, status, message, rows),
            )

    def read_update_log(self, limit: int = 20) -> pd.DataFrame:
        query = """
        SELECT symbol, status, message, rows, updated_at
        FROM update_log
        ORDER BY id DESC
        LIMIT ?
        """

        with self.connect() as conn:
            return pd.read_sql_query(query, conn, params=[limit])