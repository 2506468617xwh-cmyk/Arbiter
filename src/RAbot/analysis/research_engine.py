from __future__ import annotations

import pandas as pd

from RAbot.analysis.indicators import add_technical_indicators


def _safe_float(value) -> float | None:
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except Exception:
        return None


def _fmt_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f}%"


def _calc_period_return(df: pd.DataFrame, months: int = 1) -> float | None:
    if df.empty:
        return None

    data = df.copy()
    data["date_dt"] = pd.to_datetime(data["date"])
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    data = data.dropna(subset=["close"]).sort_values("date_dt")

    if len(data) < 2:
        return None

    end_date = data["date_dt"].max()
    start_date = end_date - pd.DateOffset(months=months)

    sub = data[data["date_dt"] >= start_date].copy()

    if len(sub) < 2:
        return None

    first = sub["close"].iloc[0]
    last = sub["close"].iloc[-1]

    if first == 0 or pd.isna(first) or pd.isna(last):
        return None

    return (last / first - 1) * 100


def _score_to_grade(score: int) -> tuple[str, str]:
    if score >= 82:
        return "强势趋势", "资产处于较强趋势区间，价格结构、动量与风险状态整体较优。"
    if score >= 68:
        return "偏强震荡", "资产整体偏强，但可能存在一定震荡或短期消化压力。"
    if score >= 52:
        return "中性观察", "资产处于中性区间，趋势和风险信号尚未形成明显共振。"
    if score >= 36:
        return "弱势修复", "资产仍在修复阶段，趋势结构尚不稳固，需要观察能否站稳关键均线。"
    return "风险释放", "资产处于偏弱或高风险状态，回撤、趋势或波动指标需要重点警惕。"


def build_single_asset_research(df: pd.DataFrame) -> dict:
    """
    单资产研究判断引擎。

    输入：某一个 symbol 的行情数据。
    输出：趋势判断、风险判断、波动判断、动量判断、综合评分、行动提示。
    """
    if df.empty:
        return {
            "score": 0,
            "grade": "无数据",
            "grade_comment": "当前资产没有可用行情数据。",
            "trend_label": "无数据",
            "risk_label": "无数据",
            "volatility_label": "无数据",
            "momentum_label": "无数据",
            "summary": "当前资产没有可用行情数据，暂时无法生成研究判断。",
            "action_hint": "请先更新行情数据。",
            "watch_points": [],
            "metrics": {},
        }

    data = add_technical_indicators(df).dropna(subset=["close"]).sort_values("date")

    if data.empty:
        return {
            "score": 0,
            "grade": "无数据",
            "grade_comment": "当前行情数据不足以计算研究指标。",
            "trend_label": "无数据",
            "risk_label": "无数据",
            "volatility_label": "无数据",
            "momentum_label": "无数据",
            "summary": "当前行情数据不足以形成可靠判断。",
            "action_hint": "请扩大时间区间或更新更多历史数据。",
            "watch_points": [],
            "metrics": {},
        }

    latest = data.iloc[-1]

    close = _safe_float(latest.get("close"))
    ma20 = _safe_float(latest.get("ma20"))
    ma60 = _safe_float(latest.get("ma60"))
    ma120 = _safe_float(latest.get("ma120"))
    drawdown = _safe_float(latest.get("drawdown"))
    volatility = _safe_float(latest.get("volatility_20d"))
    pct_change = _safe_float(latest.get("pct_change"))
    ret_1m = _calc_period_return(data, months=1)
    ret_3m = _calc_period_return(data, months=3)

    score = 0
    watch_points: list[str] = []

    # 1. 趋势评分，最高 40 分
    trend_count = 0

    if close is not None and ma20 is not None and close > ma20:
        trend_count += 1

    if close is not None and ma60 is not None and close > ma60:
        trend_count += 1

    if close is not None and ma120 is not None and close > ma120:
        trend_count += 1

    if trend_count == 3:
        trend_score = 40
        trend_label = "强趋势"
        trend_text = "收盘价同时位于 MA20、MA60、MA120 上方，趋势结构较强。"
    elif trend_count == 2:
        trend_score = 30
        trend_label = "偏强趋势"
        trend_text = "收盘价位于多数关键均线上方，整体趋势偏强，但仍需观察持续性。"
    elif trend_count == 1:
        trend_score = 18
        trend_label = "修复趋势"
        trend_text = "收盘价仅站上一条关键均线，可能处于修复早期或震荡阶段。"
    else:
        trend_score = 6
        trend_label = "弱趋势"
        trend_text = "收盘价低于主要均线，趋势结构偏弱。"
        watch_points.append("观察价格能否重新站上 MA20 与 MA60。")

    score += trend_score

    # 2. 回撤风险评分，最高 25 分
    if drawdown is None:
        risk_score = 10
        risk_label = "回撤未知"
        risk_text = "当前回撤数据不足，暂时无法评估回撤风险。"
    elif drawdown >= -5:
        risk_score = 25
        risk_label = "低回撤"
        risk_text = "当前距离区间高点较近，回撤压力较小。"
    elif drawdown >= -10:
        risk_score = 20
        risk_label = "温和回撤"
        risk_text = "当前存在一定回撤，但尚未进入明显风险释放区间。"
        watch_points.append("观察回撤是否继续扩大至 10% 以上。")
    elif drawdown >= -20:
        risk_score = 12
        risk_label = "中等回撤"
        risk_text = "当前回撤已经比较明显，说明市场仍在修复或风险释放过程中。"
        watch_points.append("关注前高修复速度，以及是否出现二次下探。")
    else:
        risk_score = 4
        risk_label = "深度回撤"
        risk_text = "当前处于较深回撤区间，需要重点评估基本面、流动性与风险偏好是否恶化。"
        watch_points.append("警惕趋势性下跌或系统性风险继续发酵。")

    score += risk_score

    # 3. 波动评分，最高 20 分
    if volatility is None:
        vol_score = 8
        volatility_label = "波动未知"
        volatility_text = "当前波动率数据不足。"
    elif volatility < 15:
        vol_score = 20
        volatility_label = "低波动"
        volatility_text = "20日年化波动率较低，短期运行相对平稳。"
    elif volatility < 25:
        vol_score = 15
        volatility_label = "中等波动"
        volatility_text = "波动率处于中等区间，市场风险偏好相对正常。"
    elif volatility < 35:
        vol_score = 9
        volatility_label = "高波动"
        volatility_text = "波动率偏高，短期情绪和价格扰动可能加大。"
        watch_points.append("观察波动率是否继续上行，避免在情绪剧烈波动时追涨杀跌。")
    else:
        vol_score = 4
        volatility_label = "极高波动"
        volatility_text = "波动率显著偏高，市场可能处于剧烈分歧或风险释放阶段。"
        watch_points.append("高波动环境下更适合降低交易频率，等待趋势重新清晰。")

    score += vol_score

    # 4. 动量评分，最高 15 分
    if ret_1m is None:
        momentum_score = 6
        momentum_label = "动量未知"
        momentum_text = "近1月收益率数据不足。"
    elif ret_1m >= 8:
        momentum_score = 15
        momentum_label = "强动量"
        momentum_text = "近1月涨幅较强，短期风险偏好积极。"
        watch_points.append("若短期涨幅过快，需警惕追涨后的波动回撤。")
    elif ret_1m >= 2:
        momentum_score = 12
        momentum_label = "偏强动量"
        momentum_text = "近1月收益为正，短期动量偏强。"
    elif ret_1m >= -3:
        momentum_score = 8
        momentum_label = "中性动量"
        momentum_text = "近1月涨跌幅不大，市场可能处于震荡状态。"
    elif ret_1m >= -8:
        momentum_score = 5
        momentum_label = "偏弱动量"
        momentum_text = "近1月表现偏弱，短期修复力度不足。"
        watch_points.append("观察近1月收益率能否重新转正。")
    else:
        momentum_score = 2
        momentum_label = "弱动量"
        momentum_text = "近1月跌幅较大，短期风险偏好明显偏弱。"
        watch_points.append("关注是否出现放量下跌或破位。")

    score += momentum_score
    score = max(0, min(100, int(round(score))))

    grade, grade_comment = _score_to_grade(score)

    if score >= 75:
        action_hint = "长期配置视角下，可以维持跟踪或定投节奏；短期不宜在急涨后盲目加速。"
    elif score >= 55:
        action_hint = "适合保持观察和常规定投，等待趋势、回撤与波动率进一步确认。"
    elif score >= 35:
        action_hint = "更适合谨慎观察，若用于定投可考虑降低节奏，等待价格重新站稳关键均线。"
    else:
        action_hint = "当前风险信号较多，不适合激进加仓，优先等待趋势修复和波动回落。"

    if not watch_points:
        watch_points = [
            "观察 MA20、MA60、MA120 的排列是否继续改善。",
            "观察回撤是否继续收窄，或是否再次扩大。",
            "观察波动率是否维持在可控区间。",
        ]

    summary = (
        f"{trend_text}{risk_text}{volatility_text}{momentum_text}"
        f" 综合来看，当前资产状态被归类为“{grade}”，状态分数为 {score}/100。"
    )

    return {
        "score": score,
        "grade": grade,
        "grade_comment": grade_comment,
        "trend_label": trend_label,
        "risk_label": risk_label,
        "volatility_label": volatility_label,
        "momentum_label": momentum_label,
        "summary": summary,
        "action_hint": action_hint,
        "watch_points": watch_points,
        "metrics": {
            "close": close,
            "ma20": ma20,
            "ma60": ma60,
            "ma120": ma120,
            "drawdown": drawdown,
            "volatility_20d": volatility,
            "pct_change": pct_change,
            "ret_1m": ret_1m,
            "ret_3m": ret_3m,
        },
    }


def build_market_overview(perf_df: pd.DataFrame) -> dict:
    """
    多资产总览判断。

    输入：build_asset_performance_table 生成的表现表。
    输出：市场强弱、风险、波动、概括性研究语言。
    """
    if perf_df.empty:
        return {
            "headline": "暂无市场总览",
            "summary": "当前没有足够的多资产数据生成市场总览。",
            "strong_assets": [],
            "weak_assets": [],
            "high_vol_assets": [],
            "risk_assets": [],
        }

    data = perf_df.copy()

    strong_assets = []
    weak_assets = []
    high_vol_assets = []
    risk_assets = []

    if "近1月收益率%" in data.columns:
        strong = data.dropna(subset=["近1月收益率%"]).sort_values("近1月收益率%", ascending=False).head(3)
        weak = data.dropna(subset=["近1月收益率%"]).sort_values("近1月收益率%", ascending=True).head(3)

        strong_assets = [
            {
                "symbol": row["symbol"],
                "name": row.get("name", row["symbol"]),
                "value": row["近1月收益率%"],
            }
            for _, row in strong.iterrows()
        ]

        weak_assets = [
            {
                "symbol": row["symbol"],
                "name": row.get("name", row["symbol"]),
                "value": row["近1月收益率%"],
            }
            for _, row in weak.iterrows()
        ]

    if "20日年化波动率%" in data.columns:
        high_vol = data.dropna(subset=["20日年化波动率%"]).sort_values("20日年化波动率%", ascending=False).head(3)
        high_vol_assets = [
            {
                "symbol": row["symbol"],
                "name": row.get("name", row["symbol"]),
                "value": row["20日年化波动率%"],
            }
            for _, row in high_vol.iterrows()
        ]

    if "当前回撤%" in data.columns:
        risk = data.dropna(subset=["当前回撤%"]).sort_values("当前回撤%", ascending=True).head(3)
        risk_assets = [
            {
                "symbol": row["symbol"],
                "name": row.get("name", row["symbol"]),
                "value": row["当前回撤%"],
            }
            for _, row in risk.iterrows()
        ]

    if strong_assets:
        strong_text = "、".join([f"{x['symbol']}（{_fmt_pct(x['value'])}）" for x in strong_assets])
    else:
        strong_text = "暂无明显强势资产"

    if weak_assets:
        weak_text = "、".join([f"{x['symbol']}（{_fmt_pct(x['value'])}）" for x in weak_assets])
    else:
        weak_text = "暂无明显弱势资产"

    if high_vol_assets:
        vol_text = "、".join([f"{x['symbol']}（{_fmt_pct(x['value'])}）" for x in high_vol_assets])
    else:
        vol_text = "暂无明显高波动资产"

    headline = "市场分化观察"

    summary = (
        f"从近1月表现看，当前相对强势资产为：{strong_text}；"
        f"相对弱势资产为：{weak_text}。"
        f"波动率维度上，需要重点关注：{vol_text}。"
        "这说明当前市场并非单一方向行情，更适合结合趋势、回撤和波动率进行分层观察。"
    )

    return {
        "headline": headline,
        "summary": summary,
        "strong_assets": strong_assets,
        "weak_assets": weak_assets,
        "high_vol_assets": high_vol_assets,
        "risk_assets": risk_assets,
    }