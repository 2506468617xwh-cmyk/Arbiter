from __future__ import annotations

import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from RAbot.reporting.markdown_report import save_index_markdown_report


def main() -> None:
    path = save_index_markdown_report()
    print(f"指数研究简报已生成：{path}")


if __name__ == "__main__":
    main()