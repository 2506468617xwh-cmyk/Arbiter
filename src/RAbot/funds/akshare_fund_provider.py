from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.funds.fund_models import FundBar, FundInfo, FundQuote
from RAbot.funds.fund_provider import BaseFundProvider
from RAbot.funds.fund_symbols import detect_fund_market, detect_fund_type, normalize_fund_symbol


def _to_float(value: Any) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        text = str(value).replace(",", "").replace("%", "").strip()
        return float(text)
    except Exception:
        return None


class AKShareFundProvider(BaseFundProvider):
    source = "akshare"

    def __init__(self) -> None:
        self.warnings: list[str] = []

    def _ak(self):
        try:
            import akshare as ak

            return ak
        except Exception as exc:
            self.warnings.append(f"未安装或无法导入 akshare：{type(exc).__name__}: {exc}")
            return None

    def get_info(self, symbol: str) -> FundInfo:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings: list[str] = []
        name = None
        asset_class = None
        ak = self._ak()
        if ak is None:
            return FundInfo(symbol=symbol, market=market, fund_type=fund_type, currency="CNY", source=self.source, warnings=list(self.warnings))
        code = symbol.split(".")[0]
        try:
            names = ak.fund_name_em()
            if names is not None and not names.empty:
                code_col = _find_col(names, ["基金代码", "基金简称", "代码"])
                name_col = _find_col(names, ["基金简称", "基金名称", "名称"])
                type_col = _find_col(names, ["基金类型", "类型"])
                if code_col:
                    row = names[names[code_col].astype(str).str.zfill(6) == code.zfill(6)]
                    if not row.empty:
                        first = row.iloc[0]
                        name = str(first.get(name_col) or "") if name_col else None
                        asset_class = str(first.get(type_col) or "") if type_col else None
        except Exception as exc:
            warnings.append(f"AKShare fund_name_em 读取失败：{type(exc).__name__}: {exc}")
        return FundInfo(
            symbol=symbol,
            name=name,
            market=market,
            fund_type=fund_type,
            asset_class=asset_class,
            currency="CNY",
            source=self.source,
            warnings=_dedupe(warnings + self.warnings),
        )

    def get_quote(self, symbol: str) -> FundQuote:
        symbol = normalize_fund_symbol(symbol)
        market = detect_fund_market(symbol)
        fund_type = detect_fund_type(symbol)
        warnings: list[str] = []
        info = self.get_info(symbol)
        bars = self.get_history(symbol, count=2)
        latest = bars[-1] if bars else None
        previous = bars[-2] if len(bars) >= 2 else None
        if not latest:
            warnings.append("AKShare 未读取到基金最近行情/净值。")
        return FundQuote(
            symbol=symbol,
            name=info.name,
            market=market,
            fund_type=fund_type,
            currency="CNY",
            last_price=latest.close if latest else None,
            nav=latest.nav if latest else None,
            prev_close=previous.close if previous else None,
            volume=latest.volume if latest else None,
            turnover=latest.turnover if latest else None,
            quote_time=latest.date if latest else None,
            source=self.source,
            warnings=_dedupe(info.warnings + warnings + self.warnings),
        )

    def get_history(self, symbol: str, period: str = "day", count: int = 500) -> list[FundBar]:
        symbol = normalize_fund_symbol(symbol)
        if period != "day":
            return []
        ak = self._ak()
        if ak is None:
            return []
        code = symbol.split(".")[0]
        fund_type = detect_fund_type(symbol)
        errors: list[str] = []
        if fund_type == "CN_MUTUAL_FUND":
            for func_name in ["fund_open_fund_info_em", "fund_money_fund_info_em"]:
                try:
                    func = getattr(ak, func_name)
                    raw = func(symbol=code, indicator="单位净值走势")
                    bars = _bars_from_nav_frame(symbol, raw, count, self.source)
                    if bars:
                        return bars
                except Exception as exc:
                    errors.append(f"{func_name}: {type(exc).__name__}: {exc}")
        for func_name in ["fund_etf_hist_em", "fund_etf_fund_info_em", "stock_zh_a_hist"]:
            try:
                func = getattr(ak, func_name)
                if func_name == "stock_zh_a_hist":
                    raw = func(symbol=code, period="daily", start_date="20000101", end_date=datetime.now().strftime("%Y%m%d"), adjust="")
                else:
                    raw = func(symbol=code)
                bars = _bars_from_price_frame(symbol, raw, count, self.source)
                if bars:
                    return bars
            except Exception as exc:
                errors.append(f"{func_name}: {type(exc).__name__}: {exc}")
        if errors:
            self.warnings.append("AKShare 基金历史接口均未返回可用数据：" + "；".join(errors[:3]))
        return []

    def search_fund(self, keyword: str) -> list[dict]:
        keyword = str(keyword or "").strip().upper()
        ak = self._ak()
        if ak is None or not keyword:
            return []
        try:
            df = ak.fund_name_em()
            if df is None or df.empty:
                return []
            code_col = _find_col(df, ["基金代码", "代码"])
            name_col = _find_col(df, ["基金简称", "基金名称", "名称"])
            type_col = _find_col(df, ["基金类型", "类型"])
            if not code_col:
                return []
            mask = df[code_col].astype(str).str.upper().str.contains(keyword, regex=False)
            if name_col:
                mask = mask | df[name_col].astype(str).str.upper().str.contains(keyword, regex=False)
            items = []
            for _, row in df[mask].head(30).iterrows():
                code = str(row.get(code_col)).zfill(6)
                suffix = "OF"
                type_text = str(row.get(type_col) or "") if type_col else ""
                if "ETF" in type_text.upper() or "场内" in type_text:
                    suffix = "SH" if code.startswith(("5", "6")) else "SZ"
                symbol = f"{code}.{suffix}"
                items.append({"symbol": symbol, "name": row.get(name_col) if name_col else None, "market": "CN", "fund_type": detect_fund_type(symbol), "source": self.source})
            return items
        except Exception as exc:
            self.warnings.append(f"AKShare 基金搜索失败：{type(exc).__name__}: {exc}")
            return []


def _bars_from_price_frame(symbol: str, raw: Any, count: int, source: str) -> list[FundBar]:
    if raw is None or raw.empty:
        return []
    date_col = _find_col(raw, ["日期", "date", "交易日期"])
    close_col = _find_col(raw, ["收盘", "close", "单位净值"])
    open_col = _find_col(raw, ["开盘", "open"])
    high_col = _find_col(raw, ["最高", "high"])
    low_col = _find_col(raw, ["最低", "low"])
    volume_col = _find_col(raw, ["成交量", "volume"])
    turnover_col = _find_col(raw, ["成交额", "turnover", "成交额(元)"])
    if not date_col or not close_col:
        return []
    df = raw.sort_values(date_col).tail(count)
    return [
        FundBar(
            symbol=symbol,
            date=pd.to_datetime(row.get(date_col)).strftime("%Y-%m-%d"),
            open=_to_float(row.get(open_col)) if open_col else None,
            high=_to_float(row.get(high_col)) if high_col else None,
            low=_to_float(row.get(low_col)) if low_col else None,
            close=_to_float(row.get(close_col)),
            volume=_to_float(row.get(volume_col)) if volume_col else None,
            turnover=_to_float(row.get(turnover_col)) if turnover_col else None,
            source=source,
        )
        for _, row in df.iterrows()
    ]


def _bars_from_nav_frame(symbol: str, raw: Any, count: int, source: str) -> list[FundBar]:
    if raw is None or raw.empty:
        return []
    date_col = _find_col(raw, ["净值日期", "日期", "date", "x"])
    nav_col = _find_col(raw, ["单位净值", "净值", "y"])
    if not date_col or not nav_col:
        return []
    df = raw.sort_values(date_col).tail(count)
    bars = []
    for _, row in df.iterrows():
        nav = _to_float(row.get(nav_col))
        bars.append(FundBar(symbol=symbol, date=pd.to_datetime(row.get(date_col)).strftime("%Y-%m-%d"), close=nav, nav=nav, source=source))
    return bars


def _find_col(df: Any, candidates: list[str]) -> str | None:
    cols = list(getattr(df, "columns", []))
    lowered = {str(col).lower(): col for col in cols}
    for candidate in candidates:
        if candidate in cols:
            return candidate
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return None


def _dedupe(items: list[str]) -> list[str]:
    result = []
    seen = set()
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result

