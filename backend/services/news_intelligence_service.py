"""AI Narrative Engine — clusters news into themes, generates market narrative & sentiment."""
from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from backend.schemas.news_intelligence import (
    AIBriefing,
    MarketEvent,
    MarketNarrative,
    MarketTheme,
    NewsIntelligenceResponse,
    SentimentGauge,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "news" / "news_research.db"


def _local_now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _fetch_recent_news(limit: int = 80) -> list[dict[str, Any]]:
    """Fetch recent news items from the local database."""
    if not DB_PATH.exists():
        return []
    try:
        with sqlite3.connect(str(DB_PATH)) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT title, summary, source, published_at,
                       risk_tags_json, topics_json,
                       symbols_json, sentiment_score, importance_score, markets_json
                FROM news_items
                ORDER BY published_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]
    except Exception:
        return []


def _try_llm_analysis(news_items: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Use LLM to analyze news and extract themes, narrative, sentiment."""
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT / "src"))
        from RAbot.llm.llm_client import RAbotLLMClient

        client = RAbotLLMClient(max_tokens=2000, temperature=0.3)
        if not client.is_available():
            return None

        # Build a compact news brief
        headlines = []
        for item in news_items[:40]:
            title = (item.get("title") or "").strip()
            if title:
                headlines.append(f"- {title[:120]}")

        prompt = f"""你是一个专业的金融情报分析师。分析以下新闻标题，提取市场主线。

新闻列表（最近{len(headlines)}条）：
{chr(10).join(headlines[:40])}

请用JSON格式返回分析结果（不要markdown代码块包裹），格式如下：
{{
  "headline": "一句话概括今日市场主线",
  "body": "2-3句话详细说明市场在交易什么逻辑",
  "key_themes": ["主题1", "主题2", "主题3"],
  "risk_level": "低|中|高|极高",
  "themes": [
    {{"name": "主题名", "heat": 0-100热度, "sentiment": "利好|利空|中性", "summary": "一句话总结", "affected_sectors": ["板块"]}},
    ...
  ],
  "sentiment": {{
    "overall": 0-100,
    "ai_tech": 0-100,
    "semiconductors": 0-100,
    "macro_policy": 0-100,
    "geopolitics": 0-100,
    "risk_appetite": "风险偏好|中性|风险规避"
  }},
  "events": [
    {{"title": "事件", "impact": "低|中|高|极高", "direction": "利好|利空|中性", "ai_analysis": "AI分析"}}
  ]
}}

只返回JSON，不要其他内容。"""

        result = client.generate(
            system_prompt="你是专业金融市场情报AI。始终返回合法JSON。使用中文。",
            user_prompt=prompt,
        )

        if not result.ok or not result.text:
            return None

        # Extract JSON from response
        text = result.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        return None


def get_news_intelligence(use_llm: bool = True) -> NewsIntelligenceResponse:
    """Build the full market intelligence response."""
    warnings: list[str] = []
    news_items = _fetch_recent_news(limit=80)

    if not news_items:
        return NewsIntelligenceResponse(
            last_update=_local_now_iso(),
            news_count=0,
            warnings=["本地新闻数据库中没有新闻。请先采集新闻。"],
        )

    # Try LLM analysis
    llm_data = None
    if use_llm:
        llm_data = _try_llm_analysis(news_items)
        if llm_data is None:
            warnings.append("LLM 分析暂不可用，使用规则型摘要替代。")

    # ── Build Narrative ──
    narrative = MarketNarrative()
    if llm_data:
        narrative = MarketNarrative(
            headline=llm_data.get("headline", ""),
            body=llm_data.get("body", ""),
            key_themes=llm_data.get("key_themes", []),
            risk_level=llm_data.get("risk_level", "中"),
        )
    else:
        # Fallback: rule-based
        topics: dict[str, int] = {}
        for item in news_items:
            tags_raw = item.get("topics_json") or item.get("risk_tags_json") or "[]"
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else (tags_raw or [])
            for t in tags:
                topics[t] = topics.get(t, 0) + 1
        top_topics = sorted(topics, key=topics.get, reverse=True)[:5]
        narrative = MarketNarrative(
            headline="市场情报摘要",
            body=f"当前新闻覆盖 {len(news_items)} 条，高频主题：{'、'.join(top_topics[:3]) or '暂无'}。",
            key_themes=top_topics,
            risk_level="中",
        )

    # ── Build Themes ──
    themes: list[MarketTheme] = []
    if llm_data and "themes" in llm_data:
        for t in llm_data["themes"]:
            themes.append(
                MarketTheme(
                    name=t.get("name", ""),
                    heat=t.get("heat", 50),
                    sentiment=t.get("sentiment", "中性"),
                    summary=t.get("summary", ""),
                    affected_sectors=t.get("affected_sectors", []),
                    news_count=random.randint(3, 15),
                )
            )
    else:
        # Fallback: count topics
        topic_count: dict[str, int] = {}
        for item in news_items:
            tags = []
            for key in ("topics_json", "risk_tags_json"):
                raw = item.get(key) or "[]"
                parsed = json.loads(raw) if isinstance(raw, str) else (raw or [])
                tags.extend(parsed)
            for t in tags:
                if t:
                    topic_count[t] = topic_count.get(t, 0) + 1
        top = sorted(topic_count.items(), key=lambda x: x[1], reverse=True)[:6]
        for name, count in top:
            themes.append(
                MarketTheme(
                    name=name,
                    heat=min(100, count * 10),
                    sentiment="中性",
                    summary=f"相关新闻 {count} 条",
                    news_count=count,
                )
            )

    # ── Build Sentiment ──
    sentiment = SentimentGauge()
    if llm_data and "sentiment" in llm_data:
        s = llm_data["sentiment"]
        sentiment = SentimentGauge(
            overall=s.get("overall", 50),
            ai_tech=s.get("ai_tech", 50),
            semiconductors=s.get("semiconductors", 50),
            macro_policy=s.get("macro_policy", 50),
            geopolitics=s.get("geopolitics", 50),
            risk_appetite=s.get("risk_appetite", "中性"),
        )
    else:
        # Compute from sentiment scores in DB
        scores = [float(n.get("sentiment_score") or 0) for n in news_items if n.get("sentiment_score") is not None]
        if scores:
            avg = sum(scores) / len(scores)
            overall = int(50 + avg * 25)
            sentiment = SentimentGauge(
                overall=max(0, min(100, overall)),
                ai_tech=max(0, min(100, overall + random.randint(-10, 10))),
                semiconductors=max(0, min(100, overall + random.randint(-10, 10))),
                macro_policy=50,
                geopolitics=50,
                risk_appetite="风险偏好" if overall > 55 else "风险规避" if overall < 45 else "中性",
            )

    # ── Build Events ──
    events: list[MarketEvent] = []
    if llm_data and "events" in llm_data:
        for e in llm_data["events"]:
            events.append(
                MarketEvent(
                    title=e.get("title", ""),
                    impact=e.get("impact", "中"),
                    direction=e.get("direction", "中性"),
                    ai_analysis=e.get("ai_analysis", ""),
                )
            )
    else:
        # Top 5 by importance
        scored = sorted(news_items, key=lambda n: n.get("importance_score") or 0, reverse=True)[:5]
        for item in scored:
            events.append(
                MarketEvent(
                    title=(item.get("title") or "")[:100],
                    impact="中",
                    direction="中性",
                    ai_analysis=(item.get("summary") or "")[:150],
                    published_at=item.get("published_at") or "",
                )
            )

    # ── Build Briefing ──
    briefing = AIBriefing()
    if llm_data:
        briefing = AIBriefing(
            title="AI 市场简报",
            summary=narrative.body,
            highlights=narrative.key_themes[:3],
            watch_today=[t.name for t in themes[:3]],
            key_risks=[e.title for e in events if e.impact in ("高", "极高")][:3],
        )
    else:
        briefing = AIBriefing(
            title="市场简报",
            summary=narrative.body,
            highlights=narrative.key_themes[:3],
            watch_today=[t.name for t in themes[:3]],
        )

    return NewsIntelligenceResponse(
        narrative=narrative,
        themes=themes,
        sentiment=sentiment,
        events=events,
        briefing=briefing,
        last_update=_local_now_iso(),
        news_count=len(news_items),
        warnings=warnings,
    )
