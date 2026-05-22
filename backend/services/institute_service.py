"""AI Institute — Five-layer Multi-Agent Debate System.

Layer 1-3: Fundamental, Technical, Sentiment agents (structured analysis)
Layer 4: Bull vs Bear debate
Layer 5: Judge ruling + investment advice
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.services import task_manager
from backend.schemas.task import TaskResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ── Utility ──


def _now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _has_llm() -> bool:
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / ".env")
    except Exception:
        pass
    return bool(os.getenv("DEEPSEEK_API_KEY", "").strip())


def _call_llm(system_prompt: str, user_prompt: str, temperature: float = 0.25, max_tokens: int = 900) -> tuple[bool, str]:
    """Returns (ok, text). If unavailable, returns (False, reason)."""
    if not _has_llm():
        return False, "未配置 DEEPSEEK_API_KEY"
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
            base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip(),
            timeout=90.0,
        )
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip(),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        text = response.choices[0].message.content or ""
        return True, text.strip()
    except Exception as exc:
        return False, f"LLM调用失败：{type(exc).__name__}: {exc}"


def _parse_json_strict(text: str, fallback: dict[str, Any]) -> dict[str, Any]:
    """Extract JSON from LLM output, fallback on failure."""
    if not text:
        return fallback
    # Try to extract JSON from markdown code blocks
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            stripped = part.strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].strip()
            if stripped.startswith("{"):
                cleaned = stripped
                break
    # Find outermost braces
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start:end + 1]
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return fallback


# ── Data Gathering ──


def _gather_fundamental_data(symbol: str | None) -> dict[str, Any]:
    """Gather fundamental data from existing services."""
    data: dict[str, Any] = {"source": "local_db", "warnings": []}

    if symbol:
        # Try stock analysis first
        try:
            from RAbot.stocks.stock_analysis import analyze_stock
            from RAbot.stocks.symbols import detect_market, normalize_symbol
            normalized = normalize_symbol(symbol)
            market = detect_market(normalized)
            if market != "UNKNOWN":
                result = analyze_stock(normalized, use_llm=False, count=250)
                data["stock"] = {
                    "symbol": result.symbol,
                    "name": result.name,
                    "market": result.market,
                    "currency": result.currency,
                    "quote": result.quote.to_dict() if result.quote else None,
                    "indicators": result.indicators,
                    "source": result.source,
                }
                data["warnings"].extend(result.warnings or [])
        except Exception as exc:
            data["warnings"].append(f"个股基本面获取失败：{exc}")

        # Try fund analysis
        try:
            from RAbot.funds.fund_analysis import analyze_fund
            from RAbot.funds.fund_symbols import detect_fund_market, normalize_fund_symbol
            normalized = normalize_fund_symbol(symbol)
            market = detect_fund_market(normalized)
            if market != "UNKNOWN":
                result = analyze_fund(normalized, use_llm=False, count=250)
                data["fund"] = {
                    "symbol": result.symbol,
                    "name": result.name,
                    "market": result.market,
                    "fund_type": result.fund_type,
                    "currency": result.currency,
                    "info": result.info.to_dict() if result.info else None,
                    "quote": result.quote.to_dict() if result.quote else None,
                    "indicators": result.indicators,
                    "source": result.source,
                }
                data["warnings"].extend(result.warnings or [])
        except Exception:
            pass  # Not a fund

    # Macro data
    try:
        from backend.services.macro_service import get_macro_overview
        macro = get_macro_overview(limit=20)
        data["macro"] = {
            "count": getattr(macro, "count", 0),
            "indicators": [
                {
                    "indicator": getattr(item, "indicator", ""),
                    "name": getattr(item, "name", ""),
                    "latest_value": getattr(item, "latest_value", None),
                    "change": getattr(item, "change", None),
                    "trend": getattr(item, "trend", None),
                    "summary": getattr(item, "summary", ""),
                }
                for item in (getattr(macro, "items", []) or [])[:10]
            ],
        }
        data["warnings"].extend(getattr(macro, "warnings", []) or [])
    except Exception as exc:
        data["warnings"].append(f"宏观数据获取失败：{exc}")

    return data


def _gather_technical_data(symbol: str | None) -> dict[str, Any]:
    """Gather technical data using research_engine scoring."""
    data: dict[str, Any] = {"source": "research_engine", "warnings": []}

    if symbol:
        try:
            from RAbot.stocks.symbols import detect_market, normalize_symbol
            normalized = normalize_symbol(symbol)
            market = detect_market(normalized)
            if market != "UNKNOWN":
                # Get bars for the symbol
                from RAbot.stocks.stock_analysis import analyze_stock
                result = analyze_stock(normalized, use_llm=False, count=250)
                indicators = result.indicators or {}
                data["indicators"] = indicators
                data["trend_summary"] = result.trend_summary
                data["risk_summary"] = result.risk_summary
                data["warnings"].extend(result.warnings or [])
        except Exception:
            # Try fund analysis
            try:
                from RAbot.funds.fund_analysis import analyze_fund
                from RAbot.funds.fund_symbols import detect_fund_market, normalize_fund_symbol
                normalized = normalize_fund_symbol(symbol)
                market = detect_fund_market(normalized)
                if market != "UNKNOWN":
                    result = analyze_fund(normalized, use_llm=False, count=250)
                    indicators = result.indicators or {}
                    data["indicators"] = indicators
                    data["performance_summary"] = result.performance_summary
                    data["risk_summary"] = result.risk_summary
                    data["warnings"].extend(result.warnings or [])
            except Exception:
                data["warnings"].append("无法获取标的的技术面数据")
    else:
        # Market overview from research engine
        try:
            from backend.services.market_service import get_market_performance
            perf = get_market_performance()
            items = getattr(perf, "items", []) or []
            data["market_performance"] = {
                "count": len(items),
                "top_performers": [
                    {"symbol": item.symbol, "return_1m": item.return_1m}
                    for item in items[:5]
                ],
            }
            data["warnings"].extend(getattr(perf, "warnings", []) or [])
        except Exception as exc:
            data["warnings"].append(f"市场技术面数据获取失败：{exc}")

    return data


def _gather_sentiment_data(symbol: str | None) -> dict[str, Any]:
    """Gather sentiment from news, split by retail vs institutional sources."""
    data: dict[str, Any] = {"source": "news_db", "warnings": []}

    db_path = PROJECT_ROOT / "data" / "news" / "news_research.db"
    if not db_path.exists():
        data["warnings"].append("新闻数据库不存在，无法分析情绪")
        return data

    try:
        with sqlite3.connect(str(db_path)) as conn:
            conn.row_factory = sqlite3.Row

            # Build WHERE clause
            where_clauses = ["published_at IS NOT NULL"]
            params: list[Any] = []
            if symbol:
                where_clauses.append("symbols_json LIKE ?")
                params.append(f"%{symbol}%")

            where_sql = " AND ".join(where_clauses)

            rows = conn.execute(
                f"""
                SELECT title, summary, source, provider, sentiment_score, importance_score,
                       risk_tags_json, published_at
                FROM news_items
                WHERE {where_sql}
                ORDER BY published_at DESC
                LIMIT 80
                """,
                params,
            ).fetchall()

        items = [dict(r) for r in rows]
    except Exception as exc:
        data["warnings"].append(f"新闻数据查询失败：{exc}")
        return data

    # Split sources: retail vs institutional
    retail_providers = {"sina", "eastmoney", "eastmoney_news", "futu", "akshare", "akshare_news", "rsshub", "sina_finance"}
    inst_providers = {"finnhub", "newsapi", "alphavantage", "alphavantage_news"}

    retail_items = []
    inst_items = []
    for item in items:
        provider = (item.get("provider") or "").lower().strip()
        source = (item.get("source") or "").lower().strip()
        is_inst = False
        for key in inst_providers:
            if key in provider or key in source:
                is_inst = True
                break
        if is_inst:
            inst_items.append(item)
        else:
            retail_items.append(item)

    def _count_sentiment(item_list: list[dict]) -> dict[str, int]:
        positive = 0
        negative = 0
        neutral = 0
        for item in item_list:
            score = item.get("sentiment_score")
            if score is None:
                neutral += 1
            elif score > 0.1:
                positive += 1
            elif score < -0.1:
                negative += 1
            else:
                neutral += 1
        return {"利好": positive, "利空": negative, "中性": neutral}

    def _top_headlines(item_list: list[dict], top_n: int = 5) -> list[str]:
        sorted_items = sorted(item_list, key=lambda x: x.get("importance_score") or 0, reverse=True)
        return [item.get("title", "")[:80] for item in sorted_items[:top_n]]

    # Risk tags summary
    all_tags: dict[str, int] = {}
    for item in items:
        tags_raw = item.get("risk_tags_json") or "[]"
        try:
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else (tags_raw or [])
        except (json.JSONDecodeError, TypeError):
            tags = []
        for tag in tags:
            all_tags[tag] = all_tags.get(tag, 0) + 1

    data["retail"] = {
        "count": len(retail_items),
        "sentiment": _count_sentiment(retail_items),
        "top_headlines": _top_headlines(retail_items),
    }
    data["institutional"] = {
        "count": len(inst_items),
        "sentiment": _count_sentiment(inst_items),
        "top_headlines": _top_headlines(inst_items),
    }
    data["total_count"] = len(items)
    data["risk_tags_summary"] = dict(sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:10])

    return data


# ── Fallback structures ──


def _fundamental_fallback() -> dict[str, Any]:
    return {
        "评级": "中性",
        "核心结论": "数据获取失败，请重试",
        "关键指标": [],
        "风险提示": "无法获取基本面数据",
    }


def _technical_fallback() -> dict[str, Any]:
    return {
        "评级": "中性",
        "核心结论": "数据获取失败，请重试",
        "关键信号": [],
        "关键价位": "暂无数据",
    }


def _sentiment_fallback() -> dict[str, Any]:
    return {
        "整体情绪": "中性",
        "散户情绪": "中性",
        "机构情绪": "中性",
        "情绪分歧": False,
        "核心结论": "数据获取失败，请重试",
        "主要风险标签": [],
        "情绪风险提示": "无法获取情绪数据",
    }


def _bull_fallback() -> dict[str, Any]:
    return {
        "立场": "看多",
        "论据": [],
        "做多信心": "低",
        "最大风险": "数据不足，无法形成有效做多论据",
    }


def _bear_fallback() -> dict[str, Any]:
    return {
        "立场": "看空",
        "论据": [],
        "做空信心": "低",
        "最大阻力": "数据不足，无法形成有效做空论据",
    }


def _judge_fallback() -> dict[str, Any]:
    return {
        "裁决": "中性观望",
        "裁决强度": "谨慎",
        "核心理由": "部分分析数据获取失败，建议重试或更换标的。",
        "胜出论据": [],
        "被否定论据": [],
        "操作建议": {
            "短期（1-4周）": "数据不足，暂不建议操作",
            "中期（1-3月）": "等待更多数据后再评估",
            "风险控制": "建议保持观望",
        },
        "免责声明": "本分析仅供参考，不构成投资建议，市场有风险，投资需谨慎。",
    }


# ── Agent Layers ──


def _run_fundamental_agent(symbol_display: str, fundamental_data: dict[str, Any]) -> dict[str, Any]:
    """Layer 1: Fundamental Analyst Agent."""
    ok, text = _call_llm(
        system_prompt="你是专业的基本面分析师。你只能基于我提供的真实数据进行分析，禁止自行推测或补充任何数据。",
        user_prompt=f"""以下是关于【{symbol_display}】的基本面数据：
{json.dumps(fundamental_data, ensure_ascii=False, indent=2, default=str)}

请基于以上数据，输出基本面分析摘要。格式严格如下（JSON）：
{{
  "评级": "利好|中性|利空",
  "核心结论": "一句话概括，不超过50字",
  "关键指标": [
    {{"指标": "...", "数值": "...", "信号": "正面|中性|负面"}}
  ],
  "风险提示": "一句话，不超过30字"
}}
只输出JSON，不要任何额外说明。""",
    )
    if not ok:
        return _fundamental_fallback()
    return _parse_json_strict(text, _fundamental_fallback())


def _run_technical_agent(symbol_display: str, technical_data: dict[str, Any]) -> dict[str, Any]:
    """Layer 2: Technical Analyst Agent."""
    indicators = technical_data.get("indicators", {}) or {}
    score = indicators.get("score", 0)
    ma_status = []
    close = indicators.get("latest_close")
    for key in ["ma20", "ma60", "ma120"]:
        value = indicators.get(key)
        if close is not None and value is not None:
            ma_status.append(f"{key.upper()}:{'上方' if close > value else '下方'}")
        else:
            ma_status.append(f"{key.upper()}:无数据")

    vol = indicators.get("volatility_20d") or indicators.get("annualized_volatility")
    dd = indicators.get("max_drawdown_120d") or indicators.get("max_drawdown_1y")
    pct_1m = indicators.get("return_20d") or indicators.get("return_1m")

    tech_summary = {
        "当前评分": f"{score}/100",
        "价格vs均线": "，".join(ma_status),
        "20日波动率": f"{vol:.1f}%" if vol is not None else "无数据",
        "当前回撤": f"{dd:.1f}%" if dd is not None else "无数据",
        "近1月涨跌幅": f"{pct_1m:.1f}%" if pct_1m is not None else "无数据",
    }

    ok, text = _call_llm(
        system_prompt="你是专业的技术分析师。只能基于我提供的K线指标数据分析，不得引用基本面信息。",
        user_prompt=f"""以下是【{symbol_display}】的技术面数据：
- 当前评分：{score}/100
- 当前价格 vs MA20/MA60/MA120：{"，".join(ma_status)}
- 20日年化波动率：{tech_summary['20日波动率']}
- 当前回撤：{tech_summary['当前回撤']}
- 近1月涨跌幅：{tech_summary['近1月涨跌幅']}

请输出技术面分析摘要，格式严格如下（JSON）：
{{
  "评级": "利好|中性|利空",
  "核心结论": "一句话概括，不超过50字",
  "关键信号": [
    {{"信号": "...", "含义": "..."}}
  ],
  "关键价位": "支撑/压力位简述，不超过30字"
}}
只输出JSON，不要任何额外说明。""",
    )
    if not ok:
        return _technical_fallback()
    return _parse_json_strict(text, _technical_fallback())


def _run_sentiment_agent(symbol_display: str, sentiment_data: dict[str, Any]) -> dict[str, Any]:
    """Layer 3: Sentiment Analyst Agent."""
    retail = sentiment_data.get("retail", {})
    inst = sentiment_data.get("institutional", {})
    retail_sent = retail.get("sentiment", {})
    inst_sent = inst.get("sentiment", {})

    ok, text = _call_llm(
        system_prompt="你是市场情绪分析师。根据新闻数据分析市场情绪，需区分散户情绪和机构情绪。",
        user_prompt=f"""以下是【{symbol_display}】近期新闻情绪数据：

散户媒体（新浪财经、东方财富）：
- 新闻总数：{retail.get('count', 0)}条
- 利好：{retail_sent.get('利好', 0)}条 / 利空：{retail_sent.get('利空', 0)}条 / 中性：{retail_sent.get('中性', 0)}条
- 高重要性新闻标题摘要：{json.dumps(retail.get('top_headlines', []), ensure_ascii=False)}

机构媒体（Finnhub、NewsAPI、Alpha Vantage）：
- 新闻总数：{inst.get('count', 0)}条
- 利好：{inst_sent.get('利好', 0)}条 / 利空：{inst_sent.get('利空', 0)}条 / 中性：{inst_sent.get('中性', 0)}条
- 高重要性新闻标题摘要：{json.dumps(inst.get('top_headlines', []), ensure_ascii=False)}

风险标签分布：{json.dumps(sentiment_data.get('risk_tags_summary', {}), ensure_ascii=False)}

请输出情绪面分析摘要，格式严格如下（JSON）：
{{
  "整体情绪": "乐观|中性|悲观",
  "散户情绪": "乐观|中性|悲观",
  "机构情绪": "乐观|中性|悲观",
  "情绪分歧": true|false,
  "核心结论": "一句话概括，不超过50字",
  "主要风险标签": ["...", "..."],
  "情绪风险提示": "一句话，不超过30字"
}}
只输出JSON，不要任何额外说明。""",
    )
    if not ok:
        return _sentiment_fallback()
    return _parse_json_strict(text, _sentiment_fallback())


def _run_debate_agents(
    symbol_display: str,
    fundamental: dict[str, Any],
    technical: dict[str, Any],
    sentiment: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Layer 4: Bull vs Bear debate."""
    data_package = json.dumps({
        "基本面Agent输出": fundamental,
        "技术面Agent输出": technical,
        "情绪面Agent输出": sentiment,
    }, ensure_ascii=False, indent=2)

    # Bull agent
    ok_bull, text_bull = _call_llm(
        system_prompt="""你是做多方辩手。你的职责是从以下分析数据中，找出支持做多（看涨）的最强5条论据。
你必须：
1. 每条论据必须来自数据，标注来源（基本面/技术面/情绪面）
2. 如果数据里没有强力做多证据，如实说"证据较弱"，不得捏造
3. 不得超过5条""",
        user_prompt=f"""研究标的：{symbol_display}

{data_package}

请输出做多论据，格式严格如下（JSON）：
{{
  "立场": "看多",
  "论据": [
    {{
      "序号": 1,
      "来源": "基本面|技术面|情绪面",
      "论点": "核心主张，不超过40字",
      "依据": "具体数据支撑，不超过60字"
    }}
  ],
  "做多信心": "高|中|低",
  "最大风险": "一句话，不超过40字"
}}
只输出JSON。""",
        temperature=0.35,
    )

    # Bear agent
    ok_bear, text_bear = _call_llm(
        system_prompt="""你是做空方辩手。你的职责是从以下分析数据中，找出支持做空（看跌）的最强5条论据。
你必须：
1. 每条论据必须来自数据，标注来源（基本面/技术面/情绪面）
2. 如果数据里没有强力做空证据，如实说"证据较弱"，不得捏造
3. 不得超过5条""",
        user_prompt=f"""研究标的：{symbol_display}

{data_package}

请输出做空论据，格式严格如下（JSON）：
{{
  "立场": "看空",
  "论据": [
    {{
      "序号": 1,
      "来源": "基本面|技术面|情绪面",
      "论点": "核心主张，不超过40字",
      "依据": "具体数据支撑，不超过60字"
    }}
  ],
  "做空信心": "高|中|低",
  "最大阻力": "一句话，不超过40字"
}}
只输出JSON。""",
        temperature=0.35,
    )

    bull = _parse_json_strict(text_bull, _bull_fallback()) if ok_bull else _bull_fallback()
    bear = _parse_json_strict(text_bear, _bear_fallback()) if ok_bear else _bear_fallback()

    return bull, bear


def _run_judge_agent(
    symbol_display: str,
    fundamental: dict[str, Any],
    technical: dict[str, Any],
    sentiment: dict[str, Any],
    bull: dict[str, Any],
    bear: dict[str, Any],
) -> dict[str, Any]:
    """Layer 5: Judge Agent."""
    ok, text = _call_llm(
        system_prompt="""你是独立的投资研究裁判。你的职责是综合多空双方论据，给出客观的最终裁决和操作建议。

裁决权重规则（必须遵守）：
1. 基本面论据权重 > 情绪面论据权重
2. 技术面趋势信号（MA体系）权重 > 短期K线信号
3. 机构情绪 > 散户情绪
4. 论据质量（有具体数据）> 论据数量
5. 多空信心均为"低"时，裁决为"中性观望" """,
        user_prompt=f"""研究标的：{symbol_display}
分析时间：{_now_iso()}

【看多方论据】
{json.dumps(bull, ensure_ascii=False, indent=2)}

【看空方论据】
{json.dumps(bear, ensure_ascii=False, indent=2)}

【基本面评级】{fundamental.get('评级', '未知')} 【技术面评级】{technical.get('评级', '未知')} 【情绪面评级】{sentiment.get('整体情绪', '未知')}

请给出最终裁决，格式严格如下（JSON）：
{{
  "裁决": "看多|看空|中性观望",
  "裁决强度": "强烈|适度|谨慎",
  "核心理由": "3句话以内，说明为何倾向此裁决",
  "胜出论据": [
    {{"来源": "看多|看空", "论点": "..."}}
  ],
  "被否定论据": [
    {{"来源": "看多|看空", "论点": "...", "否定理由": "..."}}
  ],
  "操作建议": {{
    "短期（1-4周）": "...",
    "中期（1-3月）": "...",
    "风险控制": "止损或仓位建议，不超过40字"
  }},
  "免责声明": "本分析仅供参考，不构成投资建议，市场有风险，投资需谨慎。"
}}
只输出JSON。""",
        temperature=0.2,
        max_tokens=1200,
    )
    if not ok:
        return _judge_fallback()
    return _parse_json_strict(text, _judge_fallback())


# ── Main Orchestrator ──


def _update(task_id: str, progress: int, step: str, message: str) -> None:
    task_manager.update_task(
        task_id,
        status="running",
        progress=progress,
        current_step=step,
        message=message,
    )


def run_institute_analysis(task_id: str, symbol: str | None) -> dict[str, Any]:
    """Main orchestrator for the five-layer AI Institute analysis.

    Called by task_manager.run_task_in_background.
    """
    try:
        task_manager.update_task(task_id, status="running", progress=0, current_step="初始化", message="AI研究所启动", mark_started=True)
    except Exception:
        pass

    symbol_display = symbol or "全市场"

    # ── Step 1: Gather Data ──
    _update(task_id, 5, "正在采集基本面数据", f"从本地数据库和市场服务获取{symbol_display}的基本面信息")
    fundamental_data = _gather_fundamental_data(symbol)

    _update(task_id, 10, "正在采集技术面数据", f"获取{symbol_display}的技术指标与评分")
    technical_data = _gather_technical_data(symbol)

    _update(task_id, 15, "正在采集情绪面数据", f"获取{symbol_display}的新闻情绪分布")
    sentiment_data = _gather_sentiment_data(symbol)

    all_warnings = (
        fundamental_data.get("warnings", []) +
        technical_data.get("warnings", []) +
        sentiment_data.get("warnings", [])
    )

    # ── Step 2: Layer 1 — Fundamental ──
    _update(task_id, 20, "第一层：基本面Agent分析中", f"LLM分析{symbol_display}的基本面")
    fundamental = _run_fundamental_agent(symbol_display, fundamental_data)

    # ── Step 3: Layer 2 — Technical ──
    _update(task_id, 35, "第二层：技术面Agent分析中", f"LLM分析{symbol_display}的技术面")
    technical = _run_technical_agent(symbol_display, technical_data)

    # ── Step 4: Layer 3 — Sentiment ──
    _update(task_id, 50, "第三层：情绪面Agent分析中", f"LLM分析{symbol_display}的市场情绪")
    sentiment = _run_sentiment_agent(symbol_display, sentiment_data)

    # ── Step 5: Layer 4 — Debate ──
    _update(task_id, 65, "第四层：多空辩论中", f"看多/看空Agent各自从数据中提取论据")
    bull, bear = _run_debate_agents(symbol_display, fundamental, technical, sentiment)

    # ── Step 6: Layer 5 — Judge ──
    _update(task_id, 80, "第五层：法官Agent裁决中", "综合多空论据给出最终裁决")
    judge = _run_judge_agent(symbol_display, fundamental, technical, sentiment, bull, bear)

    # ── Build Final Result ──
    _update(task_id, 95, "正在组装最终结果", "整理五层分析结果")

    result: dict[str, Any] = {
        "symbol": symbol,
        "analyzed_at": _now_iso(),
        "fundamental": fundamental,
        "technical": technical,
        "sentiment": sentiment,
        "bull": bull,
        "bear": bear,
        "judge": judge,
        "data_summary": {
            "market": "connected" if fundamental_data else "no_data",
            "fundamental": "connected" if fundamental_data.get("stock") or fundamental_data.get("fund") else "no_data",
            "technical_indicators": "connected" if technical_data.get("indicators") else "no_data",
            "news_count": sentiment_data.get("total_count", 0),
        },
        "warnings": all_warnings,
    }

    _update(task_id, 100, "分析完成", "五层分析已全部完成")
    return result


# ── Public API helper ──


def create_institute_task(symbol: str | None) -> TaskResponse:
    """Create an async institute analysis task."""
    task = task_manager.create_task(
        task_type="institute_analysis",
        message=f"AI研究所分析：{symbol or '全市场'}",
    )
    task_manager.run_task_in_background(task.task_id, run_institute_analysis, symbol)
    return task


# ── Q&A Mode ──


# ── Asset detection from free-text ──

_ASSET_KEYWORD_MAP = {
    "NASDAQ": ["纳斯达克", "nasdaq", "纳指", "科技股"],
    "NASDAQ100": ["纳指100", "nasdaq100", "ndx"],
    "SP500": ["标普500", "s&p500", "sp500", "标普", "美股大盘"],
    "DOW": ["道琼斯", "dow", "道指"],
    "CSI300": ["沪深300", "csi300"],
    "SSE": ["上证指数", "上证", "沪指", "sse"],
    "HSI": ["恒生指数", "恒指", "恒生", "hsi", "港股大盘"],
    "GOLD": ["黄金", "gold", "贵金属"],
    "WTI": ["原油", "石油", "wti", "oil"],
    "DXY": ["美元指数", "美元", "dxy"],
    "VIX": ["恐慌指数", "vix", "波动率"],
    "NIKKEI225": ["日经", "日经225", "nikkei"],
    "CHINEXT": ["创业板", "chinext"],
    "STAR50": ["科创50", "科创", "star50"],
    "CSI500": ["中证500", "csi500"],
    "CSI1000": ["中证1000", "csi1000"],
    "DAX": ["德国dax", "dax"],
    "FTSE100": ["富时100", "ftse", "英国"],
    "RUSSELL2000": ["罗素2000", "russell"],
}

_STOCK_CODE_PATTERN = r'\b([A-Za-z0-9]{1,10}\.(SH|SZ|US|HK|OF))\b'


def _detect_symbols(text: str) -> list[str]:
    """Extract known index symbols and stock codes from a free-text question."""
    text_lower = text.lower()
    found = set()
    # Check stock code patterns first
    import re
    for match in re.finditer(_STOCK_CODE_PATTERN, text, re.IGNORECASE):
        found.add(match.group(1).upper())
    # Check keyword mappings
    for symbol, keywords in _ASSET_KEYWORD_MAP.items():
        for kw in keywords:
            if kw in text_lower:
                found.add(symbol)
                break
    return list(found)


def run_institute_question(task_id: str, question: str) -> dict[str, Any]:
    """Run investment research Q&A — detects assets and runs full 5-layer analysis."""
    try:
        task_manager.update_task(task_id, status="running", progress=0, current_step="初始化", message="解析问题中的资产…", mark_started=True)
    except Exception:
        pass

    # Detect symbols from the question
    symbols = _detect_symbols(question)
    primary_symbol = symbols[0] if symbols else None

    if primary_symbol:
        _update(task_id, 5, f"检测到资产：{primary_symbol}", f"为 {primary_symbol} 拉取数据并启动五层分析")
        # Run the FULL 5-layer analysis with real data
        result = run_institute_analysis(task_id, primary_symbol)
        # Inject the user's question for the judge
        if result.get("judge"):
            result["judge"]["用户提问"] = question
            result["question"] = question
            result["mode"] = "qa_with_data"
        return result

    # Fallback: no specific asset detected — do market-level analysis
    _update(task_id, 5, "未检测到特定资产", "以全市场视角进行分析…")
    result = run_institute_analysis(task_id, None)

    # Add a Q&A wrapper with guardrails
    _update(task_id, 82, "综合回答用户问题", "结合市场数据生成回答")

    # Check if question is investment-related via LLM guardrail
    ok_guard, guard_text = _call_llm(
        system_prompt="判断用户问题是否与投资研究相关。只回答 YES 或 NO。",
        user_prompt=f"用户问题：{question}\n\n这个问题与投资、金融、股票、基金、宏观经济学相关吗？只回答YES或NO。",
        temperature=0,
        max_tokens=5,
    )
    if ok_guard and guard_text.strip().upper().startswith("N"):
        result["judge"]["核心理由"] = "抱歉，我是投资研究助手，只能回答与投资、金融市场、宏观经济相关的问题。请提出投研相关问题。"
        result["judge"]["裁决"] = "中性观望"
        result["question"] = question
        result["mode"] = "qa_guardrail"
        return result

    # If investment-related, use the market data + LLM to answer the question
    if result.get("judge"):
        market_context = json.dumps({
            "fundamental_rating": result.get("fundamental", {}).get("评级"),
            "technical_rating": result.get("technical", {}).get("评级"),
            "sentiment_overall": result.get("sentiment", {}).get("整体情绪"),
            "bull_confidence": result.get("bull", {}).get("做多信心"),
            "bear_confidence": result.get("bear", {}).get("做空信心"),
            "judge_verdict": result.get("judge", {}).get("裁决"),
            "judge_reason": result.get("judge", {}).get("核心理由", "")[:300],
        }, ensure_ascii=False)

        ok_qa, qa_text = _call_llm(
            system_prompt="""你是 ArbiterX 投资研究助手。根据五层Agent分析系统的真实数据来回答用户问题。

规则：
1. 以五层分析数据为依据回答，标注哪些来自数据分析、哪些是一般性知识
2. 如果问题与投研完全无关，礼貌拒绝
3. 不给出具体买卖建议，不承诺收益
4. 中文回答，300-500字""",
            user_prompt=f"""用户问题：{question}

以下是 ArbiterX 五层分析系统基于真实市场数据生成的结论：
{market_context}

请基于以上数据回答用户问题。如果数据不足以回答，坦诚说明。""",
            temperature=0.3,
            max_tokens=900,
        )

        if ok_qa and qa_text.strip():
            result["judge"]["核心理由"] = qa_text.strip()

    result["question"] = question
    result["mode"] = "qa"
    return result


def create_institute_question_task(question: str) -> TaskResponse:
    """Create an async Q&A task."""
    task = task_manager.create_task(
        task_type="institute_question",
        message=f"投研问答：{question[:50]}",
    )
    task_manager.run_task_in_background(task.task_id, run_institute_question, question)
    return task
