from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.funds.fund_models import FundBar, FundInfo, FundQuote
from RAbot.funds.fund_provider import BaseFundProvider
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol
from RAbot.settings import get_tushare_token


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


class TushareFundProvider(BaseFundProvider):
    source = "tushare"

    def __init__(self) -> None:
        self.token = get_tushare_token()
        self._pro = None
        self.warnings: list[str] = []

    def _client(self):
        if not self.token:
            self.warnings.append("未配置 TUSHARE_TOKEN，A 股基金/ETF 的 Tushare 数据不可用。")
            return None
        if self._pro is None:
            try:
                import tushare as ts

                self._pro = ts.pro_api(self.token)
            except Exception as exc:
                self.warnings.append(f"Tushare 初始化失败：{type(exc).__name__}: {exc}")
                return None
        return self._pro

    def get_info(self, symbol: str) -> FundInfo:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings: list[str] = []
        pro = self._client()
        if pro is None:
            return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency="CNY", source=self.source, warnings=list(self.warnings))
        try:
            raw = pro.fund_basic(ts_code=symbol, fields="ts_code,name,management,custodian,fund_type,found_date,benchmark,invest_type,type")
            if raw is None or raw.empty:
                warnings.append("Tushare fund_basic 未返回基金基础信息。")
                return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency="CNY", source=self.source, warnings=warnings)
            row = raw.iloc[0]
            return FundInfo(
                symbol=symbol,
                name=str(row.get("name") or "") or None,
                market=market,
                fund_type=fund_type,
                asset_class=str(row.get("fund_type") or row.get("invest_type") or row.get("type") or "") or None,
                currency="CNY",
                benchmark=str(row.get("benchmark") or "") or None,
                fund_company=str(row.get("management") or "") or None,
                inception_date=_date(row.get("found_date")),
                source=self.source,
                warnings=warnings,
            )
        except Exception as exc:
            warnings.append(f"Tushare fund_basic 读取失败：{type(exc).__name__}: {exc}")
            return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency="CNY", source=self.source, warnings=warnings)

    def get_quote(self, symbol: str) -> FundQuote:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings: list[str] = []
        bars = self.get_history(symbol, count=2)
        if not bars:
            warnings.extend(self.warnings)
            warnings.append("Tushare 未读取到最近基金行情/净值，无法构造最新 quote。")
        latest = bars[-1] if bars else None
        previous = bars[-2] if len(bars) >= 2 else None
        info = self.get_info(symbol)
        warnings.extend(info.warnings)
        price = latest.close if latest else None
        nav = latest.nav if latest else None
        premium = ((price / nav - 1) * 100) if price is not None and nav not in (None, 0) else None
        return FundQuote(
            symbol=symbol,
            name=info.name,
            market=market,
            fund_type=fund_type,
            currency="CNY",
            last_price=price,
            nav=nav,
            prev_close=previous.close if previous else None,
            premium_discount=_to_float(premium),
            volume=latest.volume if latest else None,
            turnover=latest.turnover if latest else None,
            quote_time=latest.date if latest else None,
            source=self.source,
            warnings=_dedupe(warnings),
        )

    def get_history(self, symbol: str, period: str = "day", count: int = 500) -> list[FundBar]:
        symbol = normalize_fund_symbol(symbol)
        if period != "day":
            return []
        pro = self._client()
        if pro is None:
            return []
        fund_type = detect_fund_type(symbol)
        try:
            end_date = datetime.now().strftime("%Y%m%d")
            if fund_type == "CN_ETF":
                raw = pro.fund_daily(ts_code=symbol, end_date=end_date)
                return _bars_from_fund_daily(symbol, raw, count, self.source)
            if fund_type == "CN_MUTUAL_FUND":
                raw = pro.fund_nav(ts_code=symbol, end_date=end_date)
                return _bars_from_fund_nav(symbol, raw, count, self.source)
        except Exception as exc:
            self.warnings.append(f"Tushare 基金历史数据读取失败：{type(exc).__name__}: {exc}")
        return []

    def search_fund(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        if not keyword:
            return []
        pro = self._client()
        if pro is None:
            return []
        try:
            df = pro.fund_basic(fields="ts_code,name,market,fund_type,type")
            if df is None or df.empty:
                return []
            mask = (
                df["ts_code"].astype(str).str.upper().str.contains(keyword, regex=False)
                | df["name"].astype(str).str.upper().str.contains(keyword, regex=False)
            )
            return [
                {"symbol": row["ts_code"], "name": row["name"], "market": "CN", "fund_type": detect_fund_type(row["ts_code"]), "source": self.source}
                for _, row in df[mask].head(20).iterrows()
            ]
        except Exception as exc:
            self.warnings.append(f"Tushare 基金搜索失败：{type(exc).__name__}: {exc}")
            return []


def _bars_from_fund_daily(symbol: str, raw: Any, count: int, source: str) -> list[FundBar]:
    if raw is None or raw.empty:
        return []
    raw = raw.sort_values("trade_date").tail(count)
    bars: list[FundBar] = []
    for _, row in raw.iterrows():
        bars.append(
            FundBar(
                symbol=symbol,
                date=_date(row.get("trade_date")) or "",
                open=_to_float(row.get("open")),
                high=_to_float(row.get("high")),
                low=_to_float(row.get("low")),
                close=_to_float(row.get("close")),
                volume=_to_float(row.get("vol")),
                turnover=_to_float(row.get("amount")),
                source=source,
            )
        )
    return [bar for bar in bars if bar.date]


def _bars_from_fund_nav(symbol: str, raw: Any, count: int, source: str) -> list[FundBar]:
    if raw is None or raw.empty:
        return []
    date_col = "end_date" if "end_date" in raw.columns else "nav_date" if "nav_date" in raw.columns else "ann_date"
    nav_col = "unit_nav" if "unit_nav" in raw.columns else "nav" if "nav" in raw.columns else "adj_nav"
    raw = raw.sort_values(date_col).tail(count)
    bars: list[FundBar] = []
    for _, row in raw.iterrows():
        nav = _to_float(row.get(nav_col))
        bars.append(FundBar(symbol=symbol, date=_date(row.get(date_col)) or "", close=nav, nav=nav, source=source))
    return [bar for bar in bars if bar.date]


def _date(value: Any) -> str | None:
    try:
        if value is None or str(value).strip() == "":
            return None
        return pd.to_datetime(str(value)).strftime("%Y-%m-%d")
    except Exception:
        return None


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result

