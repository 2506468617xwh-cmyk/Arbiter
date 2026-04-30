from __future__ import annotations

import numpy as np
import pandas as pd


def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    给指数行情数据添加常用研究指标：
    - 日涨跌幅
    - MA20 / MA60 / MA120
    - 20日年化波动率
    - 历史回撤序列
    """
    if df.empty:
        return df

    data = df.copy()
    data = data.sort_values("date")

    data["date"] = pd.to_datetime(data["date"]).dt.strftime("%Y-%m-%d")
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["close"])

    data["pct_change"] = data["close"].pct_change() * 100

    data["ma20"] = data["close"].rolling(window=20, min_periods=5).mean()
    data["ma60"] = data["close"].rolling(window=60, min_periods=10).mean()
    data["ma120"] = data["close"].rolling(window=120, min_periods=20).mean()

    daily_ret = data["close"].pct_change()
    data["volatility_20d"] = daily_ret.rolling(window=20, min_periods=10).std() * np.sqrt(252) * 100

    running_max = data["close"].cummax()
    data["drawdown"] = (data["close"] / running_max - 1) * 100

    return data


def summarize_latest_status(df: pd.DataFrame) -> dict:
    """
    根据最新行情生成一个简单状态判断。
    """
    if df.empty:
        return {
            "status": "无数据",
            "comment": "当前数据库中没有可用行情数据。",
        }

    data = add_technical_indicators(df).dropna(subset=["close"])

    if data.empty:
        return {
            "status": "无数据",
            "comment": "当前行情数据不足以计算指标。",
        }

    latest = data.iloc[-1]

    close = latest.get("close")
    ma20 = latest.get("ma20")
    ma60 = latest.get("ma60")
    ma120 = latest.get("ma120")
    drawdown = latest.get("drawdown")
    volatility = latest.get("volatility_20d")
    pct_change = latest.get("pct_change")

    trend_score = 0

    if pd.notna(ma20) and close > ma20:
        trend_score += 1

    if pd.notna(ma60) and close > ma60:
        trend_score += 1

    if pd.notna(ma120) and close > ma120:
        trend_score += 1

    if trend_score == 3:
        status = "强势区间"
        comment = "指数收盘价同时位于 MA20、MA60、MA120 上方，中短期趋势较强。"
    elif trend_score == 2:
        status = "偏强震荡"
        comment = "指数大体位于主要均线之上，但趋势强度尚未完全确认。"
    elif trend_score == 1:
        status = "弱势修复"
        comment = "指数仅站上一部分均线，可能处于修复或震荡阶段。"
    else:
        status = "弱势区间"
        comment = "指数收盘价低于主要均线，趋势偏弱，需要警惕进一步回撤。"

    return {
        "status": status,
        "comment": comment,
        "close": round(float(close), 2) if pd.notna(close) else None,
        "pct_change": round(float(pct_change), 2) if pd.notna(pct_change) else None,
        "ma20": round(float(ma20), 2) if pd.notna(ma20) else None,
        "ma60": round(float(ma60), 2) if pd.notna(ma60) else None,
        "ma120": round(float(ma120), 2) if pd.notna(ma120) else None,
        "drawdown": round(float(drawdown), 2) if pd.notna(drawdown) else None,
        "volatility_20d": round(float(volatility), 2) if pd.notna(volatility) else None,
    }


def calculate_return_between(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> float | None:
    """
    计算某段时间内收益率。
    """
    if df.empty:
        return None

    data = df.copy()
    data["date_dt"] = pd.to_datetime(data["date"])
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["close"])
    data = data[(data["date_dt"] >= start_date) & (data["date_dt"] <= end_date)]
    data = data.sort_values("date_dt")

    if len(data) < 2:
        return None

    first = data["close"].iloc[0]
    last = data["close"].iloc[-1]

    if first == 0 or pd.isna(first) or pd.isna(last):
        return None

    return (last / first - 1) * 100


def calculate_max_drawdown(df: pd.DataFrame) -> float | None:
    """
    计算区间最大回撤。
    """
    if df.empty:
        return None

    data = df.copy()
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["close"])

    if data.empty:
        return None

    running_max = data["close"].cummax()
    drawdown = data["close"] / running_max - 1

    return float(drawdown.min() * 100)


def build_asset_performance_table(all_data: pd.DataFrame) -> pd.DataFrame:
    """
    构建多资产表现表：
    - 最新收盘价
    - 1周 / 1月 / 3月 / 6月 / YTD / 1年收益
    - 20日波动率
    - 当前回撤
    - 区间最大回撤
    """
    if all_data.empty:
        return pd.DataFrame()

    rows = []
    today = pd.to_datetime(all_data["date"]).max()
    year_start = pd.Timestamp(year=today.year, month=1, day=1)

    windows = {
        "近1周收益率%": today - pd.DateOffset(days=7),
        "近1月收益率%": today - pd.DateOffset(months=1),
        "近3月收益率%": today - pd.DateOffset(months=3),
        "近6月收益率%": today - pd.DateOffset(months=6),
        "近1年收益率%": today - pd.DateOffset(years=1),
    }

    for symbol, df in all_data.groupby("symbol"):
        df = df.sort_values("date")
        enriched = add_technical_indicators(df)

        if enriched.empty:
            continue

        latest = enriched.iloc[-1]
        name = latest.get("name", symbol)
        market = latest.get("market", "")
        source = latest.get("source", "")

        row = {
            "symbol": symbol,
            "name": name,
            "market": market,
            "source": source,
            "最新日期": latest.get("date"),
            "最新收盘价": round(float(latest["close"]), 2) if pd.notna(latest.get("close")) else None,
            "最新涨跌幅%": round(float(latest["pct_change"]), 2) if pd.notna(latest.get("pct_change")) else None,
            "YTD收益率%": None,
            "20日年化波动率%": round(float(latest["volatility_20d"]), 2) if pd.notna(latest.get("volatility_20d")) else None,
            "当前回撤%": round(float(latest["drawdown"]), 2) if pd.notna(latest.get("drawdown")) else None,
            "区间最大回撤%": None,
        }

        for col_name, start_date in windows.items():
            value = calculate_return_between(enriched, start_date, today)
            row[col_name] = round(value, 2) if value is not None else None

        ytd = calculate_return_between(enriched, year_start, today)
        row["YTD收益率%"] = round(ytd, 2) if ytd is not None else None

        max_dd = calculate_max_drawdown(enriched)
        row["区间最大回撤%"] = round(max_dd, 2) if max_dd is not None else None

        rows.append(row)

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    preferred_cols = [
        "symbol",
        "name",
        "market",
        "source",
        "最新日期",
        "最新收盘价",
        "最新涨跌幅%",
        "近1周收益率%",
        "近1月收益率%",
        "近3月收益率%",
        "近6月收益率%",
        "YTD收益率%",
        "近1年收益率%",
        "20日年化波动率%",
        "当前回撤%",
        "区间最大回撤%",
    ]

    result = result[[col for col in preferred_cols if col in result.columns]]

    return result


def build_correlation_matrix(all_data: pd.DataFrame, symbols: list[str] | None = None) -> pd.DataFrame:
    """
    基于日收益率构建相关性矩阵。
    """
    if all_data.empty:
        return pd.DataFrame()

    data = all_data.copy()

    if symbols:
        data = data[data["symbol"].isin(symbols)]

    if data.empty:
        return pd.DataFrame()

    frames = []

    for symbol, df in data.groupby("symbol"):
        df = df.sort_values("date")
        df["date_dt"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])
        df[symbol] = df["close"].pct_change()
        frames.append(df[["date_dt", symbol]])

    if not frames:
        return pd.DataFrame()

    merged = frames[0]

    for frame in frames[1:]:
        merged = pd.merge(merged, frame, on="date_dt", how="outer")

    merged = merged.sort_values("date_dt")
    corr = merged.drop(columns=["date_dt"]).corr()

    return corr.round(3)


def build_normalized_price_table(all_data: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """
    构建多资产归一化净值表，起点=100。
    """
    if all_data.empty or not symbols:
        return pd.DataFrame()

    frames = []

    for symbol in symbols:
        df = all_data[all_data["symbol"] == symbol].copy()
        df = df.sort_values("date")

        if df.empty:
            continue

        df["date_dt"] = pd.to_datetime(df["date"])
        df["close"] = pd.to_numeric(df["close"], errors="coerce")
        df = df.dropna(subset=["close"])

        if df.empty:
            continue

        base = df["close"].iloc[0]

        if base == 0 or pd.isna(base):
            continue

        df[symbol] = df["close"] / base * 100
        frames.append(df[["date_dt", symbol]])

    if not frames:
        return pd.DataFrame()

    merged = frames[0]

    for frame in frames[1:]:
        merged = pd.merge(merged, frame, on="date_dt", how="outer")

    merged = merged.sort_values("date_dt")

    return merged