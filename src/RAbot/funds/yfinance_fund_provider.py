from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.funds.fund_models import FundBar, FundInfo, FundQuote
from RAbot.funds.fund_provider import BaseFundProvider
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol, to_yahoo_fund_symbol


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class YFinanceFundProvider(BaseFundProvider):
    source = "yfinance_fallback"

    def _ticker(self, symbol: str):
        import yfinance as yf

        return yf.Ticker(to_yahoo_fund_symbol(symbol))

    def get_info(self, symbol: str) -> FundInfo:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings = ["当前使用 yfinance fallback 数据源，仅作研究参考。"]
        try:
            ticker = self._ticker(symbol)
            info = getattr(ticker, "info", {}) or {}
            return FundInfo(
                symbol=symbol,
                name=info.get("longName") or info.get("shortName"),
                market=market,
                fund_type=fund_type,
                asset_class=info.get("category") or info.get("quoteType"),
                currency=info.get("currency") or _currency(market),
                benchmark=info.get("fundBenchmark"),
                fund_company=info.get("fundFamily"),
                expense_ratio=_to_float(info.get("annualReportExpenseRatio") or info.get("netExpenseRatio")),
                aum=_to_float(info.get("totalAssets")),
                source=self.source,
                warnings=warnings,
            )
        except Exception as exc:
            return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency=_currency(market), source=self.source, warnings=warnings + [f"yfinance 基础信息读取失败：{type(exc).__name__}: {exc}"])

    def get_quote(self, symbol: str) -> FundQuote:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings = ["当前使用 yfinance fallback 数据源，仅作研究参考。"]
        try:
            ticker = self._ticker(symbol)
            info = getattr(ticker, "fast_info", {}) or {}
            hist = ticker.history(period="5d", auto_adjust=False, actions=False)
            latest = hist.iloc[-1] if hist is not None and not hist.empty else {}
            previous = hist.iloc[-2] if hist is not None and len(hist) >= 2 else {}
            return FundQuote(
                symbol=symbol,
                name=None,
                market=market,
                fund_type=fund_type,
                currency=_currency(market),
                last_price=_to_float(info.get("last_price")) or _to_float(latest.get("Close")),
                prev_close=_to_float(info.get("previous_close")) or _to_float(previous.get("Close")),
                volume=_to_float(latest.get("Volume")),
                turnover=None,
                quote_time=datetime.now().astimezone().isoformat(timespec="seconds"),
                source=self.source,
                warnings=warnings,
            )
        except Exception as exc:
            return FundQuote(symbol=symbol, market=market, fund_type=fund_type, currency=_currency(market), source=self.source, warnings=warnings + [f"yfinance 行情读取失败：{type(exc).__name__}: {exc}"])

    def get_history(self, symbol: str, period: str = "day", count: int = 500) -> list[FundBar]:
        symbol = normalize_fund_symbol(symbol)
        if period != "day":
            return []
        try:
            ticker = self._ticker(symbol)
            raw = ticker.history(period=f"{max(count + 20, 90)}d", auto_adjust=False, actions=False)
            if raw is None or raw.empty:
                return []
            df = raw.reset_index().tail(count)
            date_col = "Date" if "Date" in df.columns else "Datetime"
            bars: list[FundBar] = []
            for _, row in df.iterrows():
                bars.append(
                    FundBar(
                        symbol=symbol,
                        date=pd.to_datetime(row[date_col]).strftime("%Y-%m-%d"),
                        open=_to_float(row.get("Open")),
                        high=_to_float(row.get("High")),
                        low=_to_float(row.get("Low")),
                        close=_to_float(row.get("Close")),
                        volume=_to_float(row.get("Volume")),
                        source=self.source,
                    )
                )
            return bars
        except Exception:
            return []

    def search_fund(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        examples = [
            {"symbol": "SPY.US", "name": "SPDR S&P 500 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "VOO.US", "name": "Vanguard S&P 500 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "IVV.US", "name": "iShares Core S&P 500 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "QQQ.US", "name": "Invesco QQQ Trust", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "TQQQ.US", "name": "ProShares UltraPro QQQ", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "TLT.US", "name": "iShares 20+ Year Treasury Bond ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "GLD.US", "name": "SPDR Gold Shares", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "IWM.US", "name": "iShares Russell 2000 ETF", "market": "US", "fund_type": "US_ETF", "source": self.source},
            {"symbol": "2800.HK", "name": "Tracker Fund of Hong Kong", "market": "HK", "fund_type": "HK_ETF", "source": self.source},
        ]
        return [item for item in examples if not keyword or keyword in item["symbol"] or keyword in item["name"].upper()]


def _currency(market: str) -> str | None:
    if market == "US":
        return "USD"
    if market == "HK":
        return "HKD"
    if market == "CN":
        return "CNY"
    return None
