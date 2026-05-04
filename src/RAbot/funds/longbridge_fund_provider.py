from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.funds.fund_models import FundBar, FundInfo, FundQuote
from RAbot.funds.fund_provider import BaseFundProvider
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol, to_longbridge_fund_symbol
from RAbot.stocks.longbridge_stock_provider import LongbridgeStockProvider


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class LongbridgeFundProvider(BaseFundProvider):
    source = "longbridge"

    def __init__(self) -> None:
        self._stock_provider = LongbridgeStockProvider()
        self.warnings: list[str] = []

    def get_info(self, symbol: str) -> FundInfo:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency=_currency(market), source=self.source, warnings=list(self.warnings))

    def get_quote(self, symbol: str) -> FundQuote:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        stock_quote = self._stock_provider.get_quote(symbol)
        warnings = list(getattr(stock_quote, "warnings", []) or []) + list(getattr(self._stock_provider, "warnings", []) or [])
        return FundQuote(
            symbol=symbol,
            name=stock_quote.name,
            market=market,
            fund_type=fund_type,
            currency=_currency(market),
            last_price=stock_quote.last_price,
            prev_close=stock_quote.prev_close,
            volume=stock_quote.volume,
            turnover=stock_quote.turnover,
            quote_time=stock_quote.quote_time,
            source=self.source,
            warnings=_dedupe(warnings),
        )

    def get_history(self, symbol: str, period: str = "day", count: int = 500) -> list[FundBar]:
        symbol = normalize_fund_symbol(symbol)
        if period != "day":
            return []
        context = self._stock_provider._quote_context()
        if context is None:
            self.warnings.extend(getattr(self._stock_provider, "warnings", []) or [])
            return []
        try:
            try:
                from longbridge.openapi import AdjustType, Period

                lb_period = Period.Day
                adjust = AdjustType.NoAdjust
            except Exception:
                lb_period = "Day"
                adjust = "NoAdjust"
            candles = context.candlesticks(to_longbridge_fund_symbol(symbol), lb_period, count, adjust)
            bars: list[FundBar] = []
            for candle in candles or []:
                date_value = getattr(candle, "timestamp", None) or getattr(candle, "date", None) or datetime.now()
                bars.append(
                    FundBar(
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
            self.warnings.append(f"Longbridge ETF 历史 K 线读取失败：{type(exc).__name__}: {exc}")
            return []

    def search_fund(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        examples = [
            {"symbol": "SPY.US", "name": "SPDR S&P 500 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "VOO.US", "name": "Vanguard S&P 500 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "QQQ.US", "name": "Invesco QQQ Trust", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "2800.HK", "name": "Tracker Fund of Hong Kong", "market": "HK", "fund_type": "HK_ETF", "source": self.source},
            {"symbol": "3067.HK", "name": "iShares Hang Seng TECH ETF", "market": "HK", "fund_type": "HK_ETF", "source": self.source},
        ]
        return [item for item in examples if not keyword or keyword in item["symbol"] or keyword in str(item["name"]).upper()]


def _currency(market: str) -> str | None:
    if market == "US":
        return "USD"
    if market == "HK":
        return "HKD"
    return None


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result

