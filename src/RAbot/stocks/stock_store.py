from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from RAbot.settings import get_data_dir
from RAbot.stocks.stock_models import StockAnalysisResult, StockBar, StockQuote


DB_PATH = get_data_dir() / "stocks" / "stock_research.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_quotes (
            symbol TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_bars (
            symbol TEXT NOT NULL,
            date TEXT NOT NULL,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(symbol, date)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS stock_analysis (
            symbol TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def save_quote(quote: StockQuote | None) -> None:
    if quote is None:
        return
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO stock_quotes(symbol, payload, updated_at) VALUES (?, ?, ?)",
            (quote.symbol, json.dumps(asdict(quote), ensure_ascii=False, default=str), now),
        )


def save_bars(symbol: str, bars: list[StockBar]) -> None:
    if not bars:
        return
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO stock_bars(symbol, date, payload, updated_at) VALUES (?, ?, ?, ?)",
            [(symbol, bar.date, json.dumps(asdict(bar), ensure_ascii=False, default=str), now) for bar in bars],
        )


def save_analysis(result: StockAnalysisResult) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO stock_analysis(symbol, payload, updated_at) VALUES (?, ?, ?)",
            (result.symbol, json.dumps(result.to_dict(), ensure_ascii=False, default=str), now),
        )
