from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import yfinance as yf

from RAbot.settings import get_tushare_token


@dataclass
class IndexConfig:
    symbol: str
    name: str
    source: str
    source_symbol: str
    market: str
    currency: str | None = None


class YFinanceProvider:
    def fetch_daily(
        self,
        config: IndexConfig,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        ticker = yf.Ticker(config.source_symbol)

        raw = ticker.history(
            start=start,
            end=end,
            auto_adjust=False,
            actions=False,
        )

        if raw.empty:
            return pd.DataFrame()

        df = raw.reset_index()

        if "Date" in df.columns:
            df.rename(columns={"Date": "date"}, inplace=True)
        elif "Datetime" in df.columns:
            df.rename(columns={"Datetime": "date"}, inplace=True)

        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        result = pd.DataFrame(
            {
                "date": df["date"],
                "symbol": config.symbol,
                "name": config.name,
                "market": config.market,
                "source": config.source,
                "source_symbol": config.source_symbol,
                "open": df.get("Open"),
                "high": df.get("High"),
                "low": df.get("Low"),
                "close": df.get("Close"),
                "volume": df.get("Volume"),
                "amount": None,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        return result


class TushareProvider:
    def __init__(self) -> None:
        self.token = get_tushare_token()

    def fetch_daily(
        self,
        config: IndexConfig,
        start: str | None = None,
        end: str | None = None,
    ) -> pd.DataFrame:
        if not self.token:
            raise RuntimeError("未配置 TUSHARE_TOKEN。请在 .env 中填写 Tushare Token。")

        import tushare as ts

        pro = ts.pro_api(self.token)

        start_date = pd.to_datetime(start or "2015-01-01").strftime("%Y%m%d")
        end_date = pd.to_datetime(end or datetime.now().strftime("%Y-%m-%d")).strftime("%Y%m%d")

        raw = pro.index_daily(
            ts_code=config.source_symbol,
            start_date=start_date,
            end_date=end_date,
        )

        if raw.empty:
            return pd.DataFrame()

        raw = raw.sort_values("trade_date")

        result = pd.DataFrame(
            {
                "date": pd.to_datetime(raw["trade_date"]).dt.strftime("%Y-%m-%d"),
                "symbol": config.symbol,
                "name": config.name,
                "market": config.market,
                "source": config.source,
                "source_symbol": config.source_symbol,
                "open": raw.get("open"),
                "high": raw.get("high"),
                "low": raw.get("low"),
                "close": raw.get("close"),
                "volume": raw.get("vol"),
                "amount": raw.get("amount"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        return result


class ProviderFactory:
    @staticmethod
    def get_provider(source: str):
        source = source.lower().strip()

        if source == "yfinance":
            return YFinanceProvider()

        if source == "tushare":
            return TushareProvider()

        raise ValueError(f"暂不支持的数据源：{source}")