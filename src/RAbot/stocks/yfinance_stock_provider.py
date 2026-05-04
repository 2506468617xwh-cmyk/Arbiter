from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.stocks.stock_models import StockBar, StockQuote
from RAbot.stocks.stock_provider import BaseStockProvider
from RAbot.stocks.symbols import detect_market, normalize_symbol, to_yahoo_symbol


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class YFinanceStockProvider(BaseStockProvider):
    source = "yfinance_fallback"

    def _ticker(self, symbol: str):
        import yfinance as yf

        return yf.Ticker(to_yahoo_symbol(symbol))

    def get_quote(self, symbol: str) -> StockQuote:
        symbol = normalize_symbol(symbol)
        market = detect_market(symbol)
        warnings = ["当前使用 yfinance fallback 数据源，仅作为研究参考。"]
        try:
            ticker = self._ticker(symbol)
            info = getattr(ticker, "fast_info", {}) or {}
            hist = ticker.history(period="5d", auto_adjust=False, actions=False)
            latest = hist.iloc[-1] if hist is not None and not hist.empty else {}
            previous = hist.iloc[-2] if hist is not None and len(hist) >= 2 else {}
            return StockQuote(
                symbol=symbol,
                name=None,
                market=market,
                currency="USD" if market == "US" else "HKD" if market == "HK" else None,
                last_price=_to_float(info.get("last_price")) or _to_float(latest.get("Close")),
                prev_close=_to_float(info.get("previous_close")) or _to_float(previous.get("Close")),
                open=_to_float(latest.get("Open")),
                high=_to_float(latest.get("High")),
                low=_to_float(latest.get("Low")),
                volume=_to_float(latest.get("Volume")),
                turnover=None,
                trade_status="fallback",
                quote_time=datetime.now().astimezone().isoformat(timespec="seconds"),
                source=self.source,
                warnings=warnings,
            )
        except Exception as exc:
            return StockQuote(symbol=symbol, market=market, source=self.source, warnings=warnings + [f"yfinance 行情读取失败：{type(exc).__name__}: {exc}"])

    def get_history(self, symbol: str, period: str = "day", count: int = 250) -> list[StockBar]:
        symbol = normalize_symbol(symbol)
        return self.get_history_by_yahoo_symbol(symbol, display_symbol=symbol, count=count)

    def get_history_by_yahoo_symbol(self, yahoo_symbol: str, display_symbol: str | None = None, count: int = 250) -> list[StockBar]:
        display_symbol = normalize_symbol(display_symbol or yahoo_symbol)
        try:
            import yfinance as yf

            ticker = yf.Ticker(to_yahoo_symbol(yahoo_symbol))
            raw = ticker.history(period=f"{max(count + 20, 60)}d", auto_adjust=False, actions=False)
            if raw is None or raw.empty:
                return []
            df = raw.reset_index().tail(count)
            date_col = "Date" if "Date" in df.columns else "Datetime"
            bars = []
            for _, row in df.iterrows():
                bars.append(
                    StockBar(
                        symbol=display_symbol,
                        date=pd.to_datetime(row[date_col]).strftime("%Y-%m-%d"),
                        open=_to_float(row.get("Open")),
                        high=_to_float(row.get("High")),
                        low=_to_float(row.get("Low")),
                        close=_to_float(row.get("Close")),
                        volume=_to_float(row.get("Volume")),
                        turnover=None,
                        source=self.source,
                    )
                )
            return bars
        except Exception:
            return []

    def search_symbol(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        examples = [
            {"symbol": "TSLA.US", "name": "Tesla", "market": "US", "source": self.source},
            {"symbol": "NVDA.US", "name": "NVIDIA", "market": "US", "source": self.source},
            {"symbol": "AAPL.US", "name": "Apple", "market": "US", "source": self.source},
            {"symbol": "MSFT.US", "name": "Microsoft", "market": "US", "source": self.source},
            {"symbol": "700.HK", "name": "Tencent", "market": "HK", "source": self.source},
            {"symbol": "9988.HK", "name": "Alibaba HK", "market": "HK", "source": self.source},
            {"symbol": "3690.HK", "name": "Meituan", "market": "HK", "source": self.source},
        ]
        if not keyword:
            return examples
        return [item for item in examples if keyword in item["symbol"] or keyword in item["name"].upper()]
