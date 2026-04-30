from __future__ import annotations

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from RAbot.news.news_provider import fetch_all_news
from RAbot.news.news_store import NewsStore
from RAbot.settings import get_db_path


def main() -> None:
    store = NewsStore(get_db_path())

    print("正在更新新闻...")
    df = fetch_all_news()

    rows = store.upsert_news(df)

    print(f"新闻更新完成，写入/更新 {rows} 条。")

    if not df.empty:
        show_cols = [
            "source_id",
            "source_name",
            "title",
            "event_type",
            "related_assets",
            "sentiment_label",
            "importance_score",
            "source_tier",
            "freshness_score",
            "quality_score",
        ]
        show_cols = [col for col in show_cols if col in df.columns]
        print(df[show_cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()