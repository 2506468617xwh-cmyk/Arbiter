# src/RAbot/macro/macro_provider.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from RAbot.settings import PROJECT_DIR


@dataclass
class MacroIndicator:
    region: str
    symbol: str
    name: str
    source: str
    category: str
    unit: str = ""
    frequency: str = ""
    direction_note: str = ""
    related_assets: list[str] | None = None

    @classmethod
    def from_config(cls, region: str, symbol: str, raw: dict[str, Any]) -> "MacroIndicator":
        return cls(
            region=region,
            symbol=symbol,
            name=str(raw.get("name", symbol)),
            source=str(raw.get("source", "")),
            category=str(raw.get("category", "")),
            unit=str(raw.get("unit", "")),
            frequency=str(raw.get("frequency", "")),
            direction_note=str(raw.get("direction_note", "")),
            related_assets=list(raw.get("related_assets", []) or []),
        )


def load_macro_config(config_path: str | Path | None = None) -> dict[str, dict[str, Any]]:
    if config_path is None:
        config_path = PROJECT_DIR / "config" / "macro_indicators.yaml"

    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"宏观指标配置文件不存在：{config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    if not isinstance(data, dict):
        raise ValueError("macro_indicators.yaml 格式错误：顶层应该是 dict，例如 US / CN。")

    return data


def iter_macro_indicators(config_path: str | Path | None = None) -> list[MacroIndicator]:
    raw_config = load_macro_config(config_path)
    indicators: list[MacroIndicator] = []

    for region, group in raw_config.items():
        if not isinstance(group, dict):
            continue

        for symbol, raw in group.items():
            if not isinstance(raw, dict):
                continue
            indicators.append(MacroIndicator.from_config(region=region, symbol=symbol, raw=raw))

    return indicators


class MacroProvider:
    source_name = "base"

    def fetch_indicator(
        self,
        indicator: MacroIndicator,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame:
        raise NotImplementedError