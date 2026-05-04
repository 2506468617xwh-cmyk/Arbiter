from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_DIR / ".env")


def get_project_dir() -> Path:
    return PROJECT_DIR


def get_data_dir() -> Path:
    """Return the root data directory, respecting RABOT_DATA_DIR env var."""
    override = os.getenv("RABOT_DATA_DIR", "").strip()
    if override:
        path = Path(override).resolve()
    else:
        path = PROJECT_DIR / "data"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_config_path() -> Path:
    return PROJECT_DIR / "config" / "indexes.yaml"


def get_db_path() -> Path:
    db_path = os.getenv("DB_PATH", "")
    if db_path:
        path = Path(db_path)
        if not path.is_absolute():
            path = PROJECT_DIR / db_path
    else:
        path = get_data_dir() / "market" / "index_research.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_reports_dir() -> Path:
    path = get_data_dir() / "reports"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_tushare_token() -> str | None:
    token = os.getenv("TUSHARE_TOKEN", "").strip()
    return token or None