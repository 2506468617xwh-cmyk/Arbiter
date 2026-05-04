from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from dotenv import load_dotenv

from RAbot.news.news_engine import collect_all_news


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="更新 RAbot 新闻雷达数据")
    parser.add_argument("--limit-per-source", type=int, default=50)
    parser.add_argument("--markets", nargs="*", default=["CN", "US", "HK", "GLOBAL"])
    parser.add_argument("--symbols", nargs="*", default=[])
    parser.add_argument(
        "--keywords",
        nargs="*",
        default=["Federal Reserve", "AI chips", "中国经济"],
    )
    return parser.parse_args()


def main() -> None:
    load_dotenv(PROJECT_DIR / ".env", override=False)
    args = parse_args()
    result = collect_all_news(
        limit_per_source=args.limit_per_source,
        markets=args.markets,
        symbols=args.symbols,
        keywords=args.keywords,
    )

    print("新闻雷达更新完成")
    print(f"写入/更新：{result.get('saved_count', 0)} 条")
    print(f"更新时间：{result.get('last_update')}")

    print("\n来源统计：")
    for provider, stats in (result.get("provider_stats") or {}).items():
        print(f"- {provider}: fetched={stats.get('fetched', 0)}, saved={stats.get('saved', 0)}")
        for warning in stats.get("warnings", [])[:3]:
            print(f"  warning: {warning}")

    warnings = result.get("warnings") or []
    if warnings:
        print("\nWarnings:")
        for warning in warnings[:20]:
            print(f"- {warning}")


if __name__ == "__main__":
    main()
