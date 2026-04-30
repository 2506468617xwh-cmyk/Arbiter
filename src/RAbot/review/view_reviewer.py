from __future__ import annotations

from typing import Any

import pandas as pd

from RAbot.settings import get_db_path
from RAbot.storage.sqlite_store import SQLiteStore
from RAbot.review.view_store import ViewStore


class ViewReviewer:
    positive_words = ["强", "支撑", "上行", "改善", "偏强", "利多", "反弹", "修复"]
    negative_words = ["弱", "压力", "下行", "风险", "偏弱", "利空", "回撤", "承压"]

    def __init__(self) -> None:
        self.view_store = ViewStore()
        self.market_store = SQLiteStore(get_db_path())

    def _infer_view_direction(self, text: str) -> str:
        value = str(text or "")
        pos = any(word in value for word in self.positive_words)
        neg = any(word in value for word in self.negative_words)

        if pos and not neg:
            return "positive"
        if neg and not pos:
            return "negative"
        return "unknown"

    def calculate_forward_returns(self, view: dict[str, Any]) -> dict[str, Any]:
        result = {
            "forward_return_1d": None,
            "forward_return_5d": None,
            "forward_return_20d": None,
            "review_result": "仅支持单标的观点的后续收益复盘。",
        }

        if not view or view.get("scope") != "single_asset" or not view.get("symbol"):
            return result

        symbol = str(view.get("symbol") or "").split(",")[0].strip()
        base_date = view.get("base_date")
        base_price = view.get("base_price")

        try:
            base_price = float(base_price) if base_price is not None and not pd.isna(base_price) else None
        except Exception:
            base_price = None

        if not symbol or not base_date:
            result["review_result"] = "缺少标的或基准日期，暂无法复盘。"
            return result

        df = self.market_store.read_index_daily(symbol=symbol)
        if df.empty or "date" not in df.columns or "close" not in df.columns:
            result["review_result"] = "暂无该标的行情数据，暂无法复盘。"
            return result

        data = df.copy()
        data["date_dt"] = pd.to_datetime(data["date"], errors="coerce")
        data["close"] = pd.to_numeric(data["close"], errors="coerce")
        data = data.dropna(subset=["date_dt", "close"]).sort_values("date_dt").reset_index(drop=True)

        if data.empty:
            result["review_result"] = "行情数据为空，暂无法复盘。"
            return result

        base_dt = pd.to_datetime(base_date, errors="coerce")
        if pd.isna(base_dt):
            result["review_result"] = "基准日期格式无效，暂无法复盘。"
            return result

        base_candidates = data[data["date_dt"] <= base_dt]
        if base_candidates.empty:
            base_candidates = data[data["date_dt"] >= base_dt]

        if base_candidates.empty:
            result["review_result"] = "找不到基准日期附近的行情，暂无法复盘。"
            return result

        base_idx = int(base_candidates.index[-1])
        if base_price is None:
            base_price = float(data.loc[base_idx, "close"])

        if not base_price:
            result["review_result"] = "缺少有效基准价格，暂无法复盘。"
            return result

        for days, key in [
            (1, "forward_return_1d"),
            (5, "forward_return_5d"),
            (20, "forward_return_20d"),
        ]:
            target_idx = base_idx + days
            if target_idx < len(data):
                target_price = float(data.loc[target_idx, "close"])
                result[key] = round((target_price / base_price - 1) * 100, 2)

        text = f"{view.get('title', '')}\n{view.get('view_text', '')}\n{view.get('thesis', '')}"
        direction = self._infer_view_direction(text)
        r5 = result["forward_return_5d"]
        r20 = result["forward_return_20d"]

        if r5 is None and r20 is None:
            result["review_result"] = "继续观察：后续行情数据不足。"
        elif direction == "positive":
            result["review_result"] = "初步验证：观点偏正向，后续 5 日表现为正。" if r5 is not None and r5 > 0 else "需要复盘：观点偏正向，但后续表现未同步。"
        elif direction == "negative":
            result["review_result"] = "初步验证：观点偏谨慎，后续 5 日表现为负。" if r5 is not None and r5 < 0 else "需要复盘：观点偏谨慎，但后续表现未同步。"
        else:
            visible = []
            if result["forward_return_1d"] is not None:
                visible.append(f"1日 {result['forward_return_1d']:.2f}%")
            if r5 is not None:
                visible.append(f"5日 {r5:.2f}%")
            if r20 is not None:
                visible.append(f"20日 {r20:.2f}%")
            result["review_result"] = "仅展示后续收益：" + "，".join(visible) if visible else "继续观察：暂无足够后续收益。"

        return result

    def refresh_all_observing_views(self) -> pd.DataFrame:
        views = self.view_store.list_views(limit=1000, status="observing")
        records = []

        if views.empty:
            return pd.DataFrame(records)

        for _, row in views.iterrows():
            view = row.to_dict()
            metrics = self.calculate_forward_returns(view)
            ok = self.view_store.update_review_metrics(int(view["id"]), metrics)
            records.append(
                {
                    "id": view.get("id"),
                    "symbol": view.get("symbol"),
                    "updated": ok,
                    **metrics,
                }
            )

        return pd.DataFrame(records)
