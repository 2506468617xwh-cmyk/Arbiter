from __future__ import annotations

from pathlib import Path

import pandas as pd
import yaml

from RAbot.analysis.indicators import add_technical_indicators
from RAbot.data.providers import IndexConfig, ProviderFactory
from RAbot.settings import get_config_path, get_db_path
from RAbot.storage.sqlite_store import SQLiteStore


def load_index_configs(config_path: Path | None = None) -> list[IndexConfig]:
    path = config_path or get_config_path()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    indexes = raw.get("indexes", [])

    configs: list[IndexConfig] = []

    for item in indexes:
        configs.append(
            IndexConfig(
                symbol=item["symbol"],
                name=item["name"],
                source=item["source"],
                source_symbol=item["source_symbol"],
                market=item["market"],
                currency=item.get("currency"),
            )
        )

    return configs


def update_one_index(
    config: IndexConfig,
    start: str | None = None,
    end: str | None = None,
) -> tuple[bool, str, int]:
    store = SQLiteStore(get_db_path())

    try:
        provider = ProviderFactory.get_provider(config.source)
        raw = provider.fetch_daily(config=config, start=start, end=end)

        if raw.empty:
            message = f"{config.symbol} 没有拉取到数据。"
            store.log_update(config.symbol, "EMPTY", message, 0)
            return False, message, 0

        enriched = add_technical_indicators(raw)
        store.upsert_index_daily(enriched)

        message = f"{config.symbol} 更新成功，写入 {len(enriched)} 行。"
        store.log_update(config.symbol, "SUCCESS", message, len(enriched))
        return True, message, len(enriched)

    except Exception as e:
        message = f"{config.symbol} 更新失败：{e}"
        store.log_update(config.symbol, "FAILED", message, 0)
        return False, message, 0


def update_all_indexes(
    symbols: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    configs = load_index_configs()

    if symbols:
        symbols_upper = {s.upper() for s in symbols}
        configs = [cfg for cfg in configs if cfg.symbol.upper() in symbols_upper]

    records = []

    for config in configs:
        ok, message, rows = update_one_index(config=config, start=start, end=end)

        records.append(
            {
                "symbol": config.symbol,
                "name": config.name,
                "source": config.source,
                "success": ok,
                "rows": rows,
                "message": message,
            }
        )

    return pd.DataFrame(records)