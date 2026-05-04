from __future__ import annotations

import os
from datetime import datetime
from typing import Any

import pandas as pd
from dotenv import load_dotenv

from RAbot.settings import get_project_dir
from RAbot.stocks.stock_models import StockBar, StockQuote
from RAbot.stocks.stock_provider import BaseStockProvider
from RAbot.stocks.symbols import detect_market, normalize_symbol, to_longbridge_symbol


PLACEHOLDERS = {
    "",
    "--",
    "-",
    "YOUR_ACCESS_TOKEN",
    "YOURACCESSTOKEN",
    "ACCESS_TOKEN",
    "你的 ACCESS TOKEN",
    "你的ACCESSTOKEN",
    "你的TOKEN",
}


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class LongbridgeStockProvider(BaseStockProvider):
    source = "longbridge"

    def __init__(self) -> None:
        load_dotenv(get_project_dir() / ".env")
        self.client_id = os.getenv("LONGBRIDGE_CLIENT_ID", "").strip()
        self.app_key = (os.getenv("LONGBRIDGE_APP_KEY") or os.getenv("LONGPORT_APP_KEY") or "").strip()
        self.app_secret = (os.getenv("LONGBRIDGE_APP_SECRET") or os.getenv("LONGPORT_APP_SECRET") or "").strip()
        self.access_token = (os.getenv("LONGBRIDGE_ACCESS_TOKEN") or os.getenv("LONGPORT_ACCESS_TOKEN") or "").strip()
        self.warnings: list[str] = []
        self._sdk_name = ""

    def _has_legacy_api_key(self) -> bool:
        if not (self.app_key and self.app_secret and self.access_token):
            return False
        compact_token = self.access_token.replace(" ", "").upper()
        if compact_token in {item.replace(" ", "").upper() for item in PLACEHOLDERS}:
            return False
        if "你的" in self.access_token or "YOUR" in self.access_token.upper():
            return False
        return True

    def _quote_context(self):
        try:
            from longbridge.openapi import Config, OAuthBuilder, QuoteContext

            self._sdk_name = "longbridge"
        except Exception as exc:
            self.warnings.append(
                "未安装 Longbridge Python SDK 或导入失败。请在当前虚拟环境运行：pip install longbridge。"
                f" 当前错误：{type(exc).__name__}: {exc}"
            )
            return None

        config = None
        if self.client_id:
            try:
                oauth = OAuthBuilder(self.client_id).build(lambda url: print("请访问此 URL 授权：" + url))
                config = Config.from_oauth(oauth)
            except Exception as exc:
                self.warnings.append(
                    "Longbridge 未完成 OAuth 授权，当前使用 yfinance fallback，仅供研究参考。"
                    f" OAuth 错误：{type(exc).__name__}: {exc}"
                )

        if config is None and self._has_legacy_api_key():
            try:
                os.environ["LONGBRIDGE_APP_KEY"] = self.app_key
                os.environ["LONGBRIDGE_APP_SECRET"] = self.app_secret
                os.environ["LONGBRIDGE_ACCESS_TOKEN"] = self.access_token
                config = Config.from_apikey_env()
            except Exception as exc:
                self.warnings.append(f"Longbridge Legacy API Key 初始化失败：{type(exc).__name__}: {exc}")

        if config is None:
            if not self.client_id:
                self.warnings.append("Longbridge 未完成 OAuth 授权，当前使用 yfinance fallback，仅供研究参考。")
            return None

        try:
            return QuoteContext(config)
        except Exception as exc:
            self.warnings.append(f"Longbridge QuoteContext 初始化失败：{type(exc).__name__}: {exc}")
            return None

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = normalize_symbol(symbol)
        market = detect_market(symbol)
        context = self._quote_context()
        if context is None:
            return StockQuote(symbol=symbol, market=market, currency=_currency(market), source=self.source, warnings=list(self.warnings))

        lb_symbol = to_longbridge_symbol(symbol)
        try:
            quotes = context.quote([lb_symbol])
            quote = quotes[0] if quotes else None
            return StockQuote(
                symbol=symbol,
                name=None,
                market=market,
                currency=_currency(market),
                last_price=_to_float(getattr(quote, "last_done", None)),
                prev_close=_to_float(getattr(quote, "prev_close", None)),
                open=_to_float(getattr(quote, "open", None)),
                high=_to_float(getattr(quote, "high", None)),
                low=_to_float(getattr(quote, "low", None)),
                volume=_to_float(getattr(quote, "volume", None)),
                turnover=_to_float(getattr(quote, "turnover", None)),
                trade_status=str(getattr(quote, "trade_status", "")) or None,
                quote_time=datetime.now().astimezone().isoformat(timespec="seconds"),
                source=self.source,
                warnings=list(self.warnings),
            )
        except Exception as exc:
            return StockQuote(symbol=symbol, market=market, currency=_currency(market), source=self.source, warnings=list(self.warnings) + [f"Longbridge 行情读取失败：{type(exc).__name__}: {exc}"])

    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        if period != "day":
            return []
        context = self._quote_context()
        if context is None:
            return []
        try:
            try:
                from longbridge.openapi import AdjustType, Period

                lb_period = Period.Day
                adjust = AdjustType.NoAdjust
            except Exception:
                lb_period = "Day"
                adjust = "NoAdjust"

            lb_symbol = to_longbridge_symbol(symbol)
            candles = context.candlesticks(lb_symbol, lb_period, count, adjust)
            bars: list[StockBar] = []
            for candle in candles or []:
                date_value = getattr(candle, "timestamp", None) or getattr(candle, "date", None) or datetime.now()
                bars.append(
                    StockBar(
                        symbol=symbol,
                        date=pd.to_datetime(date_value).strftime("%Y-%m-%d"),
                        open=_to_float(getattr(candle, "open", None)),
                        high=_to_float(getattr(candle, "high", None)),
                        low=_to_float(getattr(candle, "low", None)),
                        close=_to_float(getattr(candle, "close", None)),
                        volume=_to_float(getattr(candle, "volume", None)),
                        turnover=_to_float(getattr(candle, "turnover", None)),
                        source=self.source,
                    )
                )
            return sorted(bars, key=lambda item: item.date)[-count:]
        except Exception as exc:
            self.warnings.append(f"Longbridge 历史 K 线读取失败：{type(exc).__name__}: {exc}")
            return []

    def search_symbol(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        return [
            item
            for item in [
                {"symbol": "TSLA.US", "name": "Tesla", "market": "US", "source": self.source},
                {"symbol": "NVDA.US", "name": "NVIDIA", "market": "US", "source": self.source},
                {"symbol": "700.HK", "name": "Tencent", "market": "HK", "source": self.source},
                {"symbol": "9988.HK", "name": "Alibaba HK", "market": "HK", "source": self.source},
            ]
            if not keyword or keyword in item["symbol"] or keyword in item["name"].upper()
        ]


def _currency(market: str) -> str | None:
    if market == "US":
        return "USD"
    if market == "HK":
        return "HKD"
    return None
