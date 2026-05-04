from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

from RAbot.settings import get_project_dir
from RAbot.stocks.stock_models import StockBar, StockQuote
from RAbot.stocks.stock_provider import BaseStockProvider
from RAbot.stocks.symbols import detect_market, normalize_symbol


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _first(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return None


def _extract_payload(data: Any) -> Any:
    if isinstance(data, dict):
        for key in ["data", "result", "quote", "quotes", "items", "bars", "candles", "history"]:
            if key in data and data[key] not in (None, ""):
                return data[key]
    return data


def _currency(market: str) -> str | None:
    return "CNY" if market == "CN" else "USD" if market == "US" else "HKD" if market == "HK" else None


class TickFlowStockProvider(BaseStockProvider):
    source = "tickflow"

    def __init__(self) -> None:
        load_dotenv(get_project_dir() / ".env", override=False)
        self.api_key = (
            os.getenv("TICKFLOW_API_KEY")
            or os.getenv("TICKFOLW_API_KEY")
            or os.getenv("TICKFLOW_TOKEN")
            or ""
        ).strip()
        self.base_url = (os.getenv("TICKFLOW_BASE_URL") or os.getenv("TICKFOLW_BASE_URL") or "").strip().rstrip("/")
        self.quote_path = os.getenv("TICKFLOW_QUOTE_PATH", "/quote").strip()
        self.history_path = os.getenv("TICKFLOW_HISTORY_PATH", "/history").strip()
        self.symbol_param = os.getenv("TICKFLOW_SYMBOL_PARAM", "symbol").strip()
        self.token_header = os.getenv("TICKFLOW_TOKEN_HEADER", "Authorization").strip()
        self.token_prefix = os.getenv("TICKFLOW_TOKEN_PREFIX", "Bearer").strip()
        self.warnings: list[str] = []

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers[self.token_header] = f"{self.token_prefix} {self.api_key}".strip()
            headers["X-API-Key"] = self.api_key
        return headers

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        if not self.base_url or not self.api_key:
            raise RuntimeError("未配置 TICKFLOW_BASE_URL 或 TICKFLOW_API_KEY。")
        response = requests.get(
            f"{self.base_url}/{path.lstrip('/')}",
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = normalize_symbol(symbol)
        market = detect_market(symbol)
        try:
            raw = self._get(self.quote_path, {self.symbol_param: symbol})
            payload = _extract_payload(raw)
            if isinstance(payload, list):
                payload = payload[0] if payload else {}
            if not isinstance(payload, dict):
                payload = {}
            return StockQuote(
                symbol=symbol,
                name=_first(payload, ["name", "security_name", "short_name"]),
                market=market,
                currency=_first(payload, ["currency"]) or _currency(market),
                last_price=_to_float(_first(payload, ["last_price", "last", "price", "close", "c"])),
                prev_close=_to_float(_first(payload, ["prev_close", "previous_close", "pc"])),
                open=_to_float(_first(payload, ["open", "o"])),
                high=_to_float(_first(payload, ["high", "h"])),
                low=_to_float(_first(payload, ["low", "l"])),
                volume=_to_float(_first(payload, ["volume", "vol", "v"])),
                turnover=_to_float(_first(payload, ["turnover", "amount"])),
                trade_status=_first(payload, ["trade_status", "status"]),
                quote_time=str(_first(payload, ["quote_time", "time", "timestamp", "date"]) or datetime.now().astimezone().isoformat(timespec="seconds")),
                source=self.source,
                warnings=list(self.warnings),
            )
        except Exception as exc:
            return StockQuote(
                symbol=symbol,
                market=market,
                currency=_currency(market),
                source=self.source,
                warnings=list(self.warnings) + [f"TickFlow 行情兜底失败：{type(exc).__name__}: {exc}"],
            )

    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        try:
            raw = self._get(
                self.history_path,
                {self.symbol_param: symbol, "period": period, "count": count},
            )
            payload = _extract_payload(raw)
            rows = payload if isinstance(payload, list) else []
            bars: list[StockBar] = []
            for row in rows:
                if not isinstance(row, dict):
                    continue
                date_value = _first(row, ["date", "time", "timestamp", "trade_date"])
                if not date_value:
                    continue
                bars.append(
                    StockBar(
                        symbol=symbol,
                        date=pd.to_datetime(date_value).strftime("%Y-%m-%d"),
                        open=_to_float(_first(row, ["open", "o"])),
                        high=_to_float(_first(row, ["high", "h"])),
                        low=_to_float(_first(row, ["low", "l"])),
                        close=_to_float(_first(row, ["close", "c", "price"])),
                        volume=_to_float(_first(row, ["volume", "vol", "v"])),
                        turnover=_to_float(_first(row, ["turnover", "amount"])),
                        source=self.source,
                    )
                )
            return sorted(bars, key=lambda item: item.date)[-count:]
        except Exception as exc:
            self.warnings.append(f"TickFlow K线兜底失败：{type(exc).__name__}: {exc}")
            return []
