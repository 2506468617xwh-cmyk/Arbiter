from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from RAbot.data.pipeline import update_all_indexes


def main() -> None:
    parser = argparse.ArgumentParser(description="更新指数行情数据")

    parser.add_argument(
        "--symbols",
        nargs="*",
        default=None,
        help="只更新指定指数，例如：--symbols NASDAQ SP500 CSI300 SSE",
    )

    parser.add_argument(
        "--start",
        default="2020-01-01",
        help="开始日期，例如：2020-01-01",
    )

    parser.add_argument(
        "--end",
        default=None,
        help="结束日期，例如：2024-12-31；不填则默认到最近可用日期",
    )

    args = parser.parse_args()

    result = update_all_indexes(
        symbols=args.symbols,
        start=args.start,
        end=args.end,
    )

    print("\n指数数据更新结果：")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()