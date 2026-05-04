from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any

import pandas as pd

from RAbot.analysis.indicators import build_asset_performance_table
from RAbot.macro.macro_store import MacroStore
from RAbot.news.news_store import NewsResearchStore, news_items_to_dataframe
from RAbot.settings import get_db_path
from RAbot.storage.sqlite_store import SQLiteStore


@dataclass
class ResearchAlert:
    alert_type: str
    level: str
    title: str
    message: str
    symbols: list[str]
    evidence: dict
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AlertsEngine:
    def __init__(self) -> None:
        self.store = SQLiteStore(get_db_path())
        self.macro_store = MacroStore(get_db_path())
        self._news_research_store = NewsResearchStore()

    def _now(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _alert(
        self,
        alert_type: str,
        level: str,
        title: str,
        message: str,
        symbols: list[str] | None = None,
        evidence: dict | None = None,
    ) -> ResearchAlert:
        return ResearchAlert(
            alert_type=alert_type,
            level=level,
            title=title,
            message=message,
            symbols=symbols or [],
            evidence=evidence or {},
            created_at=self._now(),
        )

    def generate_alerts(
        self,
        watchlist_symbols: list[str] | None = None,
        max_alerts: int = 30,
    ) -> list[ResearchAlert]:
        watchlist_symbols = [str(x) for x in (watchlist_symbols or []) if str(x).strip()]

        try:
            all_data = self.store.read_index_daily()
        except Exception:
            all_data = pd.DataFrame()

        try:
            news_items = self._news_research_store.list_latest(limit=500)
            all_news = news_items_to_dataframe(news_items)
        except Exception:
            all_news = pd.DataFrame()

        try:
            all_macro = self.macro_store.read_macro_series()
        except Exception:
            all_macro = pd.DataFrame()

        try:
            perf_df = build_asset_performance_table(all_data) if not all_data.empty else pd.DataFrame()
        except Exception:
            perf_df = pd.DataFrame()

        alerts: list[ResearchAlert] = []
        alerts.extend(self.generate_data_alerts(all_data, all_news, all_macro, watchlist_symbols))
        alerts.extend(self.generate_trend_alerts(perf_df, all_data, watchlist_symbols))
        alerts.extend(self.generate_risk_alerts(perf_df, all_data, watchlist_symbols))
        alerts.extend(self.generate_macro_alerts(perf_df, all_macro, watchlist_symbols))
        alerts.extend(self.generate_news_alerts(all_news, watchlist_symbols))
        alerts.extend(self.generate_cross_asset_alerts(perf_df, all_data, watchlist_symbols))

        priority = {"critical": 0, "warning": 1, "watch": 2, "info": 3}
        alerts = sorted(alerts, key=lambda x: priority.get(x.level, 9))
        return alerts[: int(max_alerts or 30)]

    def _scoped_perf(self, perf_df: pd.DataFrame, watchlist_symbols: list[str] | None) -> pd.DataFrame:
        if perf_df.empty or not watchlist_symbols or "symbol" not in perf_df.columns:
            return perf_df
        return perf_df[perf_df["symbol"].astype(str).isin(watchlist_symbols)].copy()

    def _num(self, row: pd.Series, col: str) -> float | None:
        if col not in row.index:
            return None
        try:
            value = pd.to_numeric(pd.Series([row.get(col)]), errors="coerce").iloc[0]
            return None if pd.isna(value) else float(value)
        except Exception:
            return None

    def _row_by_symbol(self, perf_df: pd.DataFrame, symbol: str) -> pd.Series | None:
        if perf_df.empty or "symbol" not in perf_df.columns:
            return None
        found = perf_df[perf_df["symbol"].astype(str) == symbol]
        return None if found.empty else found.iloc[0]

    def generate_trend_alerts(self, perf_df, all_data, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        data = self._scoped_perf(perf_df, watchlist_symbols)
        needed = {"symbol", "近1周收益率%", "近1月收益率%", "当前回撤%", "20日年化波动率%"}
        if data.empty or not needed.intersection(set(data.columns)):
            return alerts

        for _, row in data.iterrows():
            symbol = str(row.get("symbol", ""))
            r1w = self._num(row, "近1周收益率%")
            r1m = self._num(row, "近1月收益率%")
            dd = self._num(row, "当前回撤%")
            vol = self._num(row, "20日年化波动率%")
            evidence = {"近1周收益率%": r1w, "近1月收益率%": r1m, "当前回撤%": dd, "20日年化波动率%": vol}

            if r1m is not None and dd is not None and r1m > 8 and dd < -5:
                alerts.append(self._alert("trend_alert", "watch", f"{symbol} 强趋势中出现回撤扩大", "该资产近1月表现较强，但当前回撤已扩大，提示趋势可能进入震荡或拥挤交易阶段。", [symbol], evidence))
            if r1m is not None and r1w is not None and r1m < -5 and r1w > 2:
                alerts.append(self._alert("trend_alert", "watch", f"{symbol} 弱势资产出现短期修复", "该资产近1月仍偏弱，但近1周有所改善，后续需要观察修复是否持续。", [symbol], evidence))
            if r1m is not None and vol is not None and r1m > 10 and vol > 30:
                alerts.append(self._alert("trend_alert", "warning", f"{symbol} 强势伴随高波动", "收益强势与高波动并存，提示短期分歧和回撤风险上升。", [symbol], evidence))

        return alerts

    def generate_risk_alerts(self, perf_df, all_data, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        data = self._scoped_perf(perf_df, watchlist_symbols)
        if not data.empty:
            for _, row in data.iterrows():
                symbol = str(row.get("symbol", ""))
                dd = self._num(row, "当前回撤%")
                if dd is not None and dd < -10:
                    alerts.append(self._alert("risk_alert", "warning", f"{symbol} 当前回撤较深", "当前回撤已经较深，需要关注风险暴露是否继续扩大。", [symbol], {"当前回撤%": dd}))

        vix = self._row_by_symbol(perf_df, "VIX")
        if vix is not None and (self._num(vix, "近1周收益率%") or 0) > 10:
            for symbol in ["NASDAQ", "SP500"]:
                row = self._row_by_symbol(perf_df, symbol)
                if row is not None and (self._num(row, "近1周收益率%") or 0) > 0:
                    alerts.append(self._alert("risk_alert", "watch", "美股上涨与 VIX 上行并存", "风险资产上涨但波动率同步上行，提示市场风险偏好可能存在分歧。", ["VIX", symbol], {"VIX近1周收益率%": self._num(vix, "近1周收益率%"), f"{symbol}近1周收益率%": self._num(row, "近1周收益率%")}))
                    break

        return alerts

    def generate_macro_alerts(self, perf_df, all_macro, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        dxy = self._row_by_symbol(perf_df, "DXY")
        gold = self._row_by_symbol(perf_df, "GOLD")
        hsi = self._row_by_symbol(perf_df, "HSI")
        wti = self._row_by_symbol(perf_df, "WTI")

        dxy_m = self._num(dxy, "近1月收益率%") if dxy is not None else None
        gold_m = self._num(gold, "近1月收益率%") if gold is not None else None
        hsi_m = self._num(hsi, "近1月收益率%") if hsi is not None else None
        wti_m = self._num(wti, "近1月收益率%") if wti is not None else None

        if dxy_m is not None and gold_m is not None and dxy_m > 2 and gold_m > 2:
            alerts.append(self._alert("macro_alert", "watch", "美元与黄金同步走强", "美元和黄金同步走强可能意味着避险需求与流动性定价并存，需要关注风险资产承压可能。", ["DXY", "GOLD"], {"DXY近1月收益率%": dxy_m, "GOLD近1月收益率%": gold_m}))
        if dxy_m is not None and hsi_m is not None and dxy_m > 2 and hsi_m < -5:
            alerts.append(self._alert("macro_alert", "warning", "美元走强与港股弱势并存", "美元偏强叠加港股弱势，可能反映外部流动性或风险偏好压力。", ["DXY", "HSI"], {"DXY近1月收益率%": dxy_m, "HSI近1月收益率%": hsi_m}))
        if wti_m is not None and wti_m > 8:
            alerts.append(self._alert("macro_alert", "watch", "油价阶段性走强", "油价阶段性走强可能影响通胀预期和利率定价，需要关注宏观再定价风险。", ["WTI"], {"WTI近1月收益率%": wti_m}))

        return alerts

    def generate_news_alerts(self, all_news, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        if all_news is None or all_news.empty:
            return alerts

        news = all_news.copy()
        if "published_at" in news.columns:
            news["published_dt"] = pd.to_datetime(news["published_at"], errors="coerce")
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=7)
            news = news[(news["published_dt"].isna()) | (news["published_dt"] >= cutoff)].copy()

        for col in ["importance_score", "quality_score"]:
            if col in news.columns:
                news[col] = pd.to_numeric(news[col], errors="coerce").fillna(0)

        symbols = watchlist_symbols or []
        if "related_assets" in news.columns:
            for symbol in symbols:
                related = news[news["related_assets"].fillna("").astype(str).str.contains(symbol, case=False, regex=False)].copy()
                if related.empty:
                    continue
                high = related[related.get("importance_score", 0) >= 70] if "importance_score" in related.columns else pd.DataFrame()
                if len(high) >= 3:
                    alerts.append(self._alert("news_alert", "watch", f"{symbol} 高重要性新闻集中出现", "近7天该资产相关高重要性新闻较多，建议跟踪事件演化。", [symbol], {"high_importance_count": int(len(high))}))
                if "sentiment_label" in related.columns and "importance_score" in related.columns:
                    neg = related[(related["sentiment_label"] == "偏利空") & (related["importance_score"] >= 60)]
                    if len(neg) >= 2:
                        alerts.append(self._alert("news_alert", "warning", f"{symbol} 负面新闻压力上升", "近7天该资产相关偏利空且较重要的新闻增加，提示新闻面压力上升。", [symbol], {"negative_news_count": int(len(neg))}))

        policy_words = ["政策", "监管", "刺激", "会议", "降息", "加息", "关税"]
        if "title" in news.columns:
            title_hit = news["title"].fillna("").astype(str).apply(lambda x: any(word in x for word in policy_words))
            event_hit = news["event_type"].fillna("").astype(str).str.contains("政策", regex=False) if "event_type" in news.columns else False
            quality = news["quality_score"] >= 60 if "quality_score" in news.columns else True
            policy_news = news[(title_hit | event_hit) & quality]
            if len(policy_news) >= 2:
                alerts.append(self._alert("news_alert", "watch", "政策相关新闻集中出现", "政策、监管、利率或关税相关高质量新闻增多，提示政策预期可能变化。", [], {"policy_news_count": int(len(policy_news)), "sample_titles": policy_news["title"].head(3).tolist()}))

        return alerts

    def generate_cross_asset_alerts(self, perf_df, all_data, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        values = {}
        for symbol in ["NASDAQ", "GOLD", "DXY", "HSI", "CSI300"]:
            row = self._row_by_symbol(perf_df, symbol)
            values[symbol] = self._num(row, "近1月收益率%") if row is not None else None

        if values["NASDAQ"] is not None and values["GOLD"] is not None and values["NASDAQ"] > 8 and values["GOLD"] > 5:
            alerts.append(self._alert("cross_asset_alert", "watch", "成长资产与避险资产同步走强", "纳指与黄金同步走强，说明市场主线可能并不单一，需要同时关注 AI/成长交易与避险/利率交易。", ["NASDAQ", "GOLD"], values))
        if values["DXY"] is not None and values["GOLD"] is not None and values["HSI"] is not None and values["DXY"] > 2 and values["GOLD"] > 2 and values["HSI"] < -5:
            alerts.append(self._alert("cross_asset_alert", "warning", "美元、黄金、港股形成风险偏好压力组合", "美元与黄金走强、港股走弱，可能提示全球资金偏谨慎。", ["DXY", "GOLD", "HSI"], values))
        if values["CSI300"] is not None and values["HSI"] is not None and values["CSI300"] < -5 and values["HSI"] < -5:
            alerts.append(self._alert("cross_asset_alert", "warning", "中国相关资产同步承压", "A股核心指数与港股同步偏弱，需要关注中国增长预期、政策预期和外部流动性压力。", ["CSI300", "HSI"], values))

        return alerts

    def generate_data_alerts(self, all_data, all_news, all_macro, watchlist_symbols) -> list[ResearchAlert]:
        alerts: list[ResearchAlert] = []
        if all_data is None or all_data.empty:
            alerts.append(self._alert("data_alert", "critical", "行情数据库为空", "当前本地行情数据库为空，请先更新行情数据。", [], {}))
            return alerts

        if "symbol" in all_data.columns:
            available = set(all_data["symbol"].dropna().astype(str).unique().tolist())
            for symbol in watchlist_symbols or []:
                if symbol not in available:
                    alerts.append(self._alert("data_alert", "warning", f"{symbol} 缺少行情数据", "自选资产在本地行情库中没有数据。", [symbol], {}))

            if "date" in all_data.columns:
                now = pd.Timestamp.now().normalize()
                for symbol in watchlist_symbols or list(available):
                    df = all_data[all_data["symbol"].astype(str) == symbol]
                    latest = pd.to_datetime(df["date"], errors="coerce").max()
                    if pd.notna(latest) and (now - latest.normalize()).days > 5:
                        alerts.append(self._alert("data_alert", "watch", f"{symbol} 行情数据可能未更新", "该资产最新行情日期距离当前日期超过 5 天，请检查数据源或更新任务。", [symbol], {"latest_date": latest.strftime("%Y-%m-%d"), "days_lag": int((now - latest.normalize()).days)}))

        if all_news is None or all_news.empty:
            alerts.append(self._alert("data_alert", "watch", "新闻数据库为空", "当前本地新闻数据为空，请先更新新闻。", [], {}))
        elif len(all_news) < 10:
            alerts.append(self._alert("data_alert", "info", "新闻数据数量较少", "新闻库记录较少，新闻面观察可能不充分。", [], {"news_count": int(len(all_news))}))

        if all_macro is None or all_macro.empty:
            alerts.append(self._alert("data_alert", "info", "宏观数据库为空", "当前本地宏观数据为空，宏观预警覆盖有限。", [], {}))

        return alerts

    def generate_alert_explanation(self, alert: ResearchAlert) -> str:
        return f"{alert.title}：{alert.message}"
