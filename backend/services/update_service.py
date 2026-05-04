from __future__ import annotations

import os
import threading
from datetime import datetime, timedelta
from typing import Any

from RAbot.settings import get_project_dir


class LocalUpdateService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._running = False
        self._last_result: dict[str, Any] | None = None
        self._started_at: str | None = None
        self._finished_at: str | None = None

    def status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "started_at": self._started_at,
            "finished_at": self._finished_at,
            "last_result": self._last_result,
        }

    def run_background(self, reason: str = "manual") -> dict[str, Any]:
        with self._lock:
            if self._running:
                return {"started": False, "message": "本地数据更新已经在运行中。", **self.status()}
            self._running = True
            self._started_at = datetime.now().astimezone().isoformat(timespec="seconds")
            self._finished_at = None
            thread = threading.Thread(target=self._run_safe, args=(reason,), daemon=True)
            thread.start()
            return {"started": True, "message": "本地数据更新已在后台启动。", **self.status()}

    def _run_safe(self, reason: str) -> None:
        try:
            self._last_result = self.run_once(reason=reason)
        except Exception as exc:
            self._last_result = {
                "ok": False,
                "reason": reason,
                "warnings": [f"本地数据更新失败：{type(exc).__name__}: {exc}"],
                "modules": {},
            }
        finally:
            self._finished_at = datetime.now().astimezone().isoformat(timespec="seconds")
            self._running = False

    def run_once(self, reason: str = "manual") -> dict[str, Any]:
        warnings: list[str] = []
        modules: dict[str, Any] = {}
        try:
            from dotenv import load_dotenv

            load_dotenv(get_project_dir() / ".env", override=False)
        except Exception:
            pass

        start = (datetime.now() - timedelta(days=int(os.getenv("RABOT_MARKET_REFRESH_DAYS", "520")))).strftime("%Y-%m-%d")

        try:
            from RAbot.data.pipeline import update_all_indexes

            df = update_all_indexes(start=start, end=None)
            modules["market"] = {
                "ok": True,
                "rows": int(df["rows"].sum()) if "rows" in df.columns and not df.empty else 0,
                "success": int(df["success"].sum()) if "success" in df.columns and not df.empty else 0,
                "total": int(len(df)),
            }
        except Exception as exc:
            message = f"行情更新失败：{type(exc).__name__}: {exc}"
            warnings.append(message)
            modules["market"] = {"ok": False, "warning": message}

        try:
            from RAbot.news.news_engine import collect_all_news

            result = collect_all_news(
                limit_per_source=int(os.getenv("RABOT_NEWS_REFRESH_LIMIT", "40")),
                markets=["CN", "US", "HK", "GLOBAL"],
                keywords=["Federal Reserve", "AI chips", "中国经济"],
            )
            modules["news"] = {
                "ok": True,
                "saved_count": result.get("saved_count", 0),
                "provider_stats": result.get("provider_stats", {}),
            }
            warnings.extend(result.get("warnings", []))
        except Exception as exc:
            message = f"新闻更新失败：{type(exc).__name__}: {exc}"
            warnings.append(message)
            modules["news"] = {"ok": False, "warning": message}

        try:
            from scripts.update_macro import update_macro

            update_macro(start_date=os.getenv("RABOT_MACRO_REFRESH_START", "2020-01-01"), end_date=None)
            modules["macro"] = {"ok": True, "message": "宏观更新脚本已执行。"}
        except Exception as exc:
            message = f"宏观更新失败：{type(exc).__name__}: {exc}"
            warnings.append(message)
            modules["macro"] = {"ok": False, "warning": message}

        return {
            "ok": not any(not module.get("ok", False) for module in modules.values()),
            "reason": reason,
            "started_at": self._started_at,
            "finished_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "modules": modules,
            "warnings": warnings,
        }


update_service = LocalUpdateService()
