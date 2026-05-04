from __future__ import annotations

import os
from datetime import datetime, timedelta
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


def _finnhub_symbol(symbol: str) -> str:
    value = normalize_symbol(symbol)
    market = detect_market(value)
    if market == "US":
        return value.removesuffix(".US")
    if market == "HK":
        code = value.split(".")[0].zfill(4)
        return f"{code}.HK"
    return value


def _currency(market: str) -> str | None:
    if market == "US":
        return "USD"
    if market == "HK":
        return "HKD"
    return "CNY" if market == "CN" else None


class FinnhubStockProvider(BaseStockProvider):
    source = "finnhub_fallback"

    def __init__(self) -> None:
        load_dotenv(get_project_dir() / ".env", override=False)
        self.api_key = os.getenv("FINNHUB_API_KEY", "").strip()
        self.warnings: list[str] = []

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("未配置 FINNHUB_API_KEY。")
        response = requests.get(
            f"https://finnhub.io/api/v1/{path.lstrip('/')}",
            params={**params, "token": self.api_key},
            timeout=15,
        )
        response.raise_for_status()
        return response.json()

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = normalize_symbol(symbol)
        market = detect_market(symbol)
        try:
            data = self._get("quote", {"symbol": _finnhub_symbol(symbol)})
            return StockQuote(
                symbol=symbol,
                market=market,
                currency=_currency(market),
                last_price=_to_float(data.get("c")),
                prev_close=_to_float(data.get("pc")),
                open=_to_float(data.get("o")),
                high=_to_float(data.get("h")),
                low=_to_float(data.get("l")),
                quote_time=datetime.now().astimezone().isoformat(timespec="seconds"),
                source=self.source,
                warnings=list(self.warnings),
            )
        except Exception as exc:
            return StockQuote(
                symbol=symbol,
                market=market,
                currency=_currency(market),
                source=self.source,
                warnings=list(self.warnings) + [f"Finnhub 行情兜底失败：{type(exc).__name__}: {exc}"],
            )

    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        if period != "day":
            return []
        end = int(datetime.now().timestamp())
        start = int((datetime.now() - timedelta(days=max(count * 2, 90))).timestamp())
        try:
            data = self._get(
                "stock/candle",
                {"symbol": _finnhub_symbol(symbol), "resolution": "D", "from": start, "to": end},
            )
            if data.get("s") != "ok":
                self.warnings.append(f"Finnhub K线返回状态：{data.get('s')}")
                return []
            bars: list[StockBar] = []
            timestamps = data.get("t") or []
            for idx, ts in enumerate(timestamps):
                bars.append(
                    StockBar(
                        symbol=symbol,
                        date=datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d"),
                        open=_to_float((data.get("o") or [None])[idx]),
                        high=_to_float((data.get("h") or [None])[idx]),
                        low=_to_float((data.get("l") or [None])[idx]),
                        close=_to_float((data.get("c") or [None])[idx]),
                        volume=_to_float((data.get("v") or [None])[idx]),
                        source=self.source,
                    )
                )
            return sorted(bars, key=lambda item: item.date)[-count:]
        except Exception as exc:
            self.warnings.append(f"Finnhub K线兜底失败：{type(exc).__name__}: {exc}")
            return []
