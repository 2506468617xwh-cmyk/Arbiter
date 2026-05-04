from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import pandas as pd

from RAbot.settings import get_tushare_token
from RAbot.stocks.stock_models import StockBar, StockQuote
from RAbot.stocks.stock_provider import BaseStockProvider
from RAbot.stocks.symbols import normalize_symbol


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class TushareStockProvider(BaseStockProvider):
    source = "tushare"

    def __init__(self) -> None:
        self.token = get_tushare_token()
        self._pro = None

    def _client(self):
        if not self.token:
            return None
        if self._pro is None:
            import tushare as ts

            self._pro = ts.pro_api(self.token)
        return self._pro

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = normalize_symbol(symbol)
        warnings: list[str] = []
        bars = self.get_history(symbol, count=2)
        warnings.extend([] if bars else ["未读取到 A 股最近日线，无法构造最新行情。"])
        if not self.token:
            warnings.append("未配置 TUSHARE_TOKEN，请在项目根目录 .env 中填写。")
        latest = bars[-1] if bars else None
        previous = bars[-2] if len(bars) >= 2 else None
        return StockQuote(
            symbol=symbol,
            name=self._find_name(symbol),
            market="CN",
            currency="CNY",
            last_price=latest.close if latest else None,
            prev_close=previous.close if previous else None,
            open=latest.open if latest else None,
            high=latest.high if latest else None,
            low=latest.low if latest else None,
            volume=latest.volume if latest else None,
            turnover=latest.turnover if latest else None,
            trade_status="daily_close" if latest else None,
            quote_time=latest.date if latest else None,
            source=self.source,
            warnings=warnings,
        )

    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        if period != "day":
            return []
        if not self.token:
            return []
        try:
            pro = self._client()
            if pro is None:
                return []
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
            raw = pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            if raw is None or raw.empty:
                return []
            raw = raw.sort_values("trade_date").tail(count)
            bars: list[StockBar] = []
            for _, row in raw.iterrows():
                bars.append(
                    StockBar(
                        symbol=symbol,
                        date=pd.to_datetime(str(row.get("trade_date"))).strftime("%Y-%m-%d"),
                        open=_to_float(row.get("open")),
                        high=_to_float(row.get("high")),
                        low=_to_float(row.get("low")),
                        close=_to_float(row.get("close")),
                        volume=_to_float(row.get("vol")),
                        turnover=_to_float(row.get("amount")),
                        source=self.source,
                    )
                )
            return bars
        except Exception:
            return []

    def get_index_history(self, symbol: str, count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        if not self.token:
            return []
        try:
            pro = self._client()
            if pro is None:
                return []
            end_date = datetime.now().strftime("%Y%m%d")
            start_date = (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
            raw = pro.index_daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            if raw is None or raw.empty:
                return []
            raw = raw.sort_values("trade_date").tail(count)
            bars: list[StockBar] = []
            for _, row in raw.iterrows():
                bars.append(
                    StockBar(
                        symbol=symbol,
                        date=pd.to_datetime(str(row.get("trade_date"))).strftime("%Y-%m-%d"),
                        open=_to_float(row.get("open")),
                        high=_to_float(row.get("high")),
                        low=_to_float(row.get("low")),
                        close=_to_float(row.get("close")),
                        volume=_to_float(row.get("vol")),
                        turnover=_to_float(row.get("amount")),
                        source=self.source,
                    )
                )
            return bars
        except Exception:
            return []

    def search_symbol(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        if not keyword or not self.token:
            return []
        try:
            pro = self._client()
            if pro is None:
                return []
            df = pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,market")
            if df is None or df.empty:
                return []
            mask = (
                df["ts_code"].astype(str).str.upper().str.contains(keyword, regex=False)
                | df["symbol"].astype(str).str.upper().str.contains(keyword, regex=False)
                | df["name"].astype(str).str.upper().str.contains(keyword, regex=False)
            )
            return [
                {"symbol": row["ts_code"], "name": row["name"], "market": "CN", "source": self.source}
                for _, row in df[mask].head(20).iterrows()
            ]
        except Exception:
            return []

    def _find_name(self, symbol: str) -> str | None:
        if not self.token:
            return None
        try:
            pro = self._client()
            if pro is None:
                return None
            df = pro.stock_basic(ts_code=symbol, fields="ts_code,name")
            if df is not None and not df.empty:
                return str(df.iloc[0]["name"])
        except Exception:
            return None
        return None
