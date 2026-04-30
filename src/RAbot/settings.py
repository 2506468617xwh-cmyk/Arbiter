from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


# 当前文件一般位于：
# E:\RAbot\src\RAbot\settings.py
#
# Path(__file__).resolve().parents[0] = E:\RAbot\src\RAbot
# Path(__file__).resolve().parents[1] = E:\RAbot\src
# Path(__file__).resolve().parents[2] = E:\RAbot
PROJECT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_DIR / ".env")


def get_project_dir() -> Path:
    return PROJECT_DIR


def get_config_path() -> Path:
    return PROJECT_DIR / "config" / "indexes.yaml"


def get_db_path() -> Path:
    db_path = os.getenv("DB_PATH", "data/market/index_research.db")
    path = PROJECT_DIR / db_path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir() -> Path:
    path = PROJECT_DIR / "data" / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tushare_token() -> str | None:
    token = os.getenv("TUSHARE_TOKEN", "").strip()
    return token or None