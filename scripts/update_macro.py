# scripts/update_macro.py

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from RAbot.macro.china_macro_provider import ChinaTushareMacroProvider
from RAbot.macro.fred_provider import FredGraphProvider
from RAbot.macro.macro_provider import MacroIndicator, iter_macro_indicators
from RAbot.macro.macro_store import MacroStore


def get_provider(indicator: MacroIndicator):
    if indicator.source == "fred":
        return FredGraphProvider()

    if indicator.source == "tushare":
        return ChinaTushareMacroProvider()

    raise ValueError(f"暂不支持的宏观数据源：{indicator.source}")


def update_macro(
    symbols: list[str] | None = None,
    regions: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> None:
    store = MacroStore()
    indicators = iter_macro_indicators()

    if symbols:
        wanted = {x.upper() for x in symbols}
        indicators = [x for x in indicators if x.symbol.upper() in wanted]

    if regions:
        wanted_regions = {x.upper() for x in regions}
        indicators = [x for x in indicators if x.region.upper() in wanted_regions]

    if not indicators:
        print("没有匹配到需要更新的宏观指标。")
        return

    print(f"准备更新宏观指标数量：{len(indicators)}")
    print(f"数据库：{store.db_path}")

    for indicator in indicators:
        print(f"\n[{indicator.region}] {indicator.symbol} - {indicator.name} / {indicator.source}")

        try:
            provider = get_provider(indicator)
            df = provider.fetch_indicator(
                indicator=indicator,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                msg = "未获取到数据，可能是接口权限、接口字段或数据源暂不可用。"
                print(f"  跳过：{msg}")
                store.log_update(
                    symbol=indicator.symbol,
                    name=indicator.name,
                    region=indicator.region,
                    source=indicator.source,
                    status="empty",
                    rows=0,
                    message=msg,
                )
                continue

            inserted = store.upsert_macro_series(df)

            min_date = pd.to_datetime(df["date"], errors="coerce").min()
            max_date = pd.to_datetime(df["date"], errors="coerce").max()

            msg = f"更新成功：{inserted} 行，区间 {min_date.date()} 至 {max_date.date()}"
            print(f"  {msg}")

            store.log_update(
                symbol=indicator.symbol,
                name=indicator.name,
                region=indicator.region,
                source=indicator.source,
                status="success",
                rows=inserted,
                message=msg,
            )

        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            print(f"  失败：{msg}")

            store.log_update(
                symbol=indicator.symbol,
                name=indicator.name,
                region=indicator.region,
                source=indicator.source,
                status="failed",
                rows=0,
                message=msg,
            )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update RAbot macro data.")

    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="指定宏观指标代码，例如 DGS10 CPIAUCSL CN_CPI",
    )

    parser.add_argument(
        "--regions",
        nargs="*",
        default=None,
        help="指定地区，例如 US CN",
    )

    parser.add_argument(
        "--start",
        default="2015-01-01",
        help="开始日期，默认 2015-01-01",
    )

    parser.add_argument(
        "--end",
        default=None,
        help="结束日期，默认拉到最新",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    update_macro(
        symbols=args.symbols,
        regions=args.regions,
        start_date=args.start,
        end_date=args.end,
    )