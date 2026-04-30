# src/RAbot/macro/fred_provider.py

from __future__ import annotations

from io import StringIO
from urllib.parse import urlencode

import pandas as pd
import requests

from RAbot.macro.macro_provider import MacroIndicator, MacroProvider


class FredGraphProvider(MacroProvider):
    """
    Lightweight FRED provider.

    Uses FRED's public graph CSV endpoint:
    https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10

    This endpoint usually does not require an API key and is enough for RAbot's
    first macro layer.
    """

    source_name = "fred"

    BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

    def fetch_indicator(
        self,
        indicator: MacroIndicator,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        params = urlencode({"id": indicator.symbol})
        url = f"{self.BASE_URL}?{params}"

        resp = requests.get(url, timeout=30)
        resp.raise_for_status()

        df = pd.read_csv(StringIO(resp.text))

        if df.empty:
            return self._empty(indicator)

        date_col = df.columns[0]
        value_col = indicator.symbol if indicator.symbol in df.columns else df.columns[-1]

        out = df[[date_col, value_col]].copy()
        out.columns = ["date", "value"]

        out["date"] = pd.to_datetime(out["date"], errors="coerce")
        out["value"] = pd.to_numeric(out["value"], errors="coerce")
        out = out.dropna(subset=["date", "value"])

        if start_date:
            out = out[out["date"] >= pd.to_datetime(start_date)]

        if end_date:
            out = out[out["date"] <= pd.to_datetime(end_date)]

        out = out.sort_values("date").reset_index(drop=True)

        out["symbol"] = indicator.symbol
        out["name"] = indicator.name
        out["region"] = indicator.region
        out["category"] = indicator.category
        out["source"] = indicator.source
        out["unit"] = indicator.unit
        out["frequency"] = indicator.frequency
        out["direction_note"] = indicator.direction_note
        out["related_assets"] = ",".join(indicator.related_assets or [])

        return out[
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