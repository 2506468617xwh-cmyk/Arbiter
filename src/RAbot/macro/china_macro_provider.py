# src/RAbot/macro/china_macro_provider.py

from __future__ import annotations

import os
from typing import Any, Callable

import pandas as pd

from RAbot.macro.macro_provider import MacroIndicator, MacroProvider


class ChinaTushareMacroProvider(MacroProvider):
    """
    China macro provider based on Tushare Pro.

    Notes:
    1. Tushare macro APIs may vary by account permissions, API version, and points.
    2. This provider uses multiple candidate APIs and candidate fields.
    3. If an indicator cannot be fetched, it returns an empty DataFrame instead of crashing RAbot.
    """

    source_name = "tushare"

    API_CANDIDATES: dict[str, list[str]] = {
        "CN_CPI": ["cn_cpi"],
        "CN_PPI": ["cn_ppi"],
        "CN_PMI": ["cn_pmi"],
        "CN_M2": ["cn_m"],
        "CN_SOCIAL_FINANCING": ["sf_month", "cn_sf"],
        "CN_LPR_1Y": ["loan_lpr"],
        "CN_LPR_5Y": ["loan_lpr"],
    }

    DATE_CANDIDATES = [
        "date",
        "month",
        "m",
        "stat_month",
        "ann_date",
        "trade_date",
        "end_date",
    ]

    VALUE_CANDIDATES: dict[str, list[str]] = {
        "CN_CPI": [
            "nt_val",
            "town_val",
            "cnt_val",
            "cpi",
            "yoy",
            "value",
        ],
        "CN_PPI": [
            "ppi_yoy",
            "yoy",
            "all_yoy",
            "value",
        ],
        "CN_PMI": [
            "pmi010000",
            "pmi",
            "manufacturing_pmi",
            "value",
        ],
        "CN_M2": [
            "m2_yoy",
            "m2",
            "m2同比",
            "value",
        ],
        "CN_SOCIAL_FINANCING": [
            "inc_month",
            "sf_month",
            "social_financing",
            "value",
        ],
        "CN_LPR_1Y": [
            "one_year",
            "lpr1y",
            "1y",
            "value",
        ],
        "CN_LPR_5Y": [
            "five_year",
            "lpr5y",
            "5y",
            "value",
        ],
    }

    def __init__(self, token: str | None = None) -> None:
        self.token = token or os.getenv("TUSHARE_TOKEN") or os.getenv("TS_TOKEN")
        self.pro = None

        if self.token:
            try:
                import tushare as ts

                ts.set_token(self.token)
                self.pro = ts.pro_api(self.token)
            except Exception:
                self.pro = None

    def fetch_indicator(
        self,
        indicator: MacroIndicator,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        if self.pro is None:
            return self._empty(indicator)

        api_names = self.API_CANDIDATES.get(indicator.symbol, [])
        if not api_names:
            return self._empty(indicator)

        raw_df = pd.DataFrame()

        for api_name in api_names:
            raw_df = self._try_fetch(
                api_name=api_name,
                start_date=start_date,
                end_date=end_date,
            )
            if not raw_df.empty:
                break

        if raw_df.empty:
            return self._empty(indicator)

        parsed = self._parse_raw(indicator, raw_df)
        if parsed.empty:
            return self._empty(indicator)

        if start_date:
            start_dt = pd.to_datetime(start_date, errors="coerce")
            if pd.notna(start_dt):
                parsed = parsed[parsed["date"] >= start_dt]

        if end_date:
            end_dt = pd.to_datetime(end_date, errors="coerce")
            if pd.notna(end_dt):
                parsed = parsed[parsed["date"] <= end_dt]

        parsed = parsed.sort_values("date").reset_index(drop=True)

        parsed["symbol"] = indicator.symbol
        parsed["name"] = indicator.name
        parsed["region"] = indicator.region
        parsed["category"] = indicator.category
        parsed["source"] = indicator.source
        parsed["unit"] = indicator.unit
        parsed["frequency"] = indicator.frequency
        parsed["direction_note"] = indicator.direction_note
        parsed["related_assets"] = ",".join(indicator.related_assets or [])

        return parsed[
            [
                "symbol",
                "date",
                "value",
                "name",
                "region",
                "category",
                "source",
                "unit",
                "frequency",
                "direction_note",
                "related_assets",
            ]
        ]

    def _try_fetch(
        self,
        api_name: str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        candidates: list[Callable[[], pd.DataFrame]] = []

        start_compact = self._to_compact_date(start_date)
        end_compact = self._to_compact_date(end_date)

        start_month = start_compact[:6] if start_compact else None
        end_month = end_compact[:6] if end_compact else None

        if hasattr(self.pro, api_name):
            fn = getattr(self.pro, api_name)

            candidates.extend(
                [
                    lambda: fn(),
                    lambda: fn(start_date=start_compact, end_date=end_compact),
                    lambda: fn(start_m=start_month, end_m=end_month),
                    lambda: fn(m=start_month),
                ]
            )

        candidates.extend(
            [
                lambda: self.pro.query(api_name),
                lambda: self.pro.query(
                    api_name,
                    start_date=start_compact,
                    end_date=end_compact,
                ),
                lambda: self.pro.query(
                    api_name,
                    start_m=start_month,
                    end_m=end_month,
                ),
            ]
        )

        for candidate in candidates:
            try:
                df = candidate()
                if isinstance(df, pd.DataFrame) and not df.empty:
                    return df
            except Exception:
                continue

        return pd.DataFrame()

    def _parse_raw(self, indicator: MacroIndicator, raw_df: pd.DataFrame) -> pd.DataFrame:
        df = raw_df.copy()

        date_col = self._find_first_existing(df, self.DATE_CANDIDATES)
        value_col = self._find_first_existing(
            df,
            self.VALUE_CANDIDATES.get(indicator.symbol, []) + ["value"],
        )

        if date_col is None:
            date_col = self._guess_date_col(df)

        if value_col is None:
            exclude = {date_col} if date_col else set()
            value_col = self._guess_value_col(df, exclude=exclude)

        if date_col is None or value_col is None:
            return pd.DataFrame(columns=["date", "value"])

        out = df[[date_col, value_col]].copy()
        out.columns = ["date", "value"]

        out["date"] = out["date"].apply(self._parse_date)
        out["value"] = pd.to_numeric(out["value"], errors="coerce")

        out = out.dropna(subset=["date", "value"])
        out = out.drop_duplicates(subset=["date"], keep="last")

        return out

    @staticmethod
    def _find_first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
        columns = list(df.columns)
        lower_map = {str(c).lower(): c for c in columns}

        for c in candidates:
            if c in columns:
                return c

            lower_c = str(c).lower()
            if lower_c in lower_map:
                return lower_map[lower_c]

        return None

    @staticmethod
    def _guess_date_col(df: pd.DataFrame) -> str | None:
        for col in df.columns:
            name = str(col).lower()
            if "date" in name or "month" in name or name in {"m", "ym"}:
                return col

        return None

    @staticmethod
    def _guess_value_col(df: pd.DataFrame, exclude: set[str] | None = None) -> str | None:
        exclude = exclude or set()

        numeric_cols = []

        for col in df.columns:
            if col in exclude:
                continue

            series = pd.to_numeric(df[col], errors="coerce")
            if series.notna().sum() > 0:
                numeric_cols.append(col)

        if not numeric_cols:
            return None

        return numeric_cols[-1]

    @staticmethod
    def _to_compact_date(date_str: str | None) -> str | None:
        if not date_str:
            return None

        dt = pd.to_datetime(date_str, errors="coerce")
        if pd.isna(dt):
            return None

        return dt.strftime("%Y%m%d")

    @staticmethod
    def _parse_date(value: Any) -> pd.Timestamp | None:
        if pd.isna(value):
            return None

        s = str(value).strip()

        if not s:
            return None

        if len(s) == 6 and s.isdigit():
            dt = pd.to_datetime(s + "01", format="%Y%m%d", errors="coerce")
            return None if pd.isna(dt) else dt

        if len(s) == 8 and s.isdigit():
            dt = pd.to_datetime(s, format="%Y%m%d", errors="coerce")
            return None if pd.isna(dt) else dt

        dt = pd.to_datetime(s, errors="coerce")
        return None if pd.isna(dt) else dt

    @staticmethod
    def _empty(indicator: MacroIndicator) -> pd.DataFrame:
        return pd.DataFrame(
            columns=[
                "symbol",
                "date",
                "value",
                "name",
                "region",
                "category",
                "source",
                "unit",
                "frequency",
                "direction_note",
                "related_assets",
            ]
        )