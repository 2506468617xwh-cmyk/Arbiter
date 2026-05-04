from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime

from RAbot.funds.fund_models import FundAnalysisResult, FundBar, FundInfo, FundQuote
from RAbot.settings import get_data_dir


DB_PATH = get_data_dir() / "funds" / "fund_research.db"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fund_info (
            symbol TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fund_quotes (
            symbol TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS fund_bars (
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
        CREATE TABLE IF NOT EXISTS fund_analysis (
            symbol TEXT PRIMARY KEY,
            payload TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    return conn


def save_info(info: FundInfo | None) -> None:
    if info is None:
        return
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO fund_info(symbol, payload, updated_at) VALUES (?, ?, ?)",
            (info.symbol, json.dumps(asdict(info), ensure_ascii=False, default=str), now),
        )


def save_quote(quote: FundQuote | None) -> None:
    if quote is None:
        return
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO fund_quotes(symbol, payload, updated_at) VALUES (?, ?, ?)",
            (quote.symbol, json.dumps(asdict(quote), ensure_ascii=False, default=str), now),
        )


def save_bars(symbol: str, bars: list[FundBar]) -> None:
    if not bars:
        return
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.executemany(
            "INSERT OR REPLACE INTO fund_bars(symbol, date, payload, updated_at) VALUES (?, ?, ?, ?)",
            [(symbol, bar.date, json.dumps(asdict(bar), ensure_ascii=False, default=str), now) for bar in bars],
        )


def save_analysis(result: FundAnalysisResult) -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO fund_analysis(symbol, payload, updated_at) VALUES (?, ?, ?)",
            (result.symbol, json.dumps(result.to_dict(), ensure_ascii=False, default=str), now),
        )
