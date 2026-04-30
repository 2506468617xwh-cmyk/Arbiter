# src/RAbot/llm/research_prompt.py

from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT_RESEARCH_ANALYST = """
你是 RAbot 的研究分析层，不是交易员，也不是财经自媒体。

你的任务：
基于 RAbot 提供的结构化事实包，识别市场或资产的主要矛盾，提出审慎、可验证的研究解释。

硬性约束：
1. 只能使用输入事实包中的信息，不得编造外部事实、新闻、数据、价格或政策。
2. 必须区分“事实”和“推论”。
3. 不得给出买入、卖出、加仓、减仓、目标价、收益承诺等交易建议。
4. 如果事实不足，必须明确说“证据不足”，不能硬编。
5. 观点要像冷静的投研备忘录，不要像喊单，不要夸张。
6. 如果技术面、新闻面、宏观面冲突，要重点解释冲突，而不是强行给单边结论。
7. 所有判断都必须能追溯到输入事实包中的字段。
8. 中文输出。
""".strip()


def build_market_analyst_prompt(context: dict[str, Any]) -> str:
    context_text = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    parts = [
        "请基于下面的 RAbot 市场事实包，写一段“RAbot AI 首席观察”。",
        "",
        "输出结构必须严格使用：",
        "",
        "## RAbot AI 首席观察",
        "",
        "### 1. 当前市场主要矛盾",
        "用一段话说明当前市场最核心的矛盾。不要罗列数据，要归纳。",
        "",
        "### 2. 支撑这一判断的事实",
        "用 3-5 条 bullet，必须来自事实包。",
        "",
        "### 3. 反向证据与不确定性",
        "用 2-4 条 bullet，指出哪些事实可能削弱上述判断。",
        "",
        "### 4. 研究推论",
        "用一段话做谨慎推论。必须明确这是推论，不是事实。",
        "",
        "### 5. 后续观察变量",
        "列出 3-6 个后续最应该跟踪的变量或事件方向。",
        "",
        "### 6. 结论边界",
        "用一句话说明本结论的局限性，并声明不构成投资建议。",
        "",
        "RAbot 市场事实包如下：",
        "",
        "```json",
        context_text,
        "```",
    ]

    return "\n".join(parts).strip()


def build_asset_analyst_prompt(context: dict[str, Any]) -> str:
    context_text = json.dumps(
        context,
        ensure_ascii=False,
        indent=2,
        default=str,
    )

    parts = [
        "请基于下面的 RAbot 单资产事实包，写一段“AI 研究点评”。",
        "",
        "输出结构必须严格使用：",
        "",
        "#### AI 研究点评",
        "",
        "**主要矛盾：**",
        "用 1 段话说明这个资产当前最核心的矛盾。",
        "",
        "**事实依据：**",
        "用 3-5 条 bullet，必须来自事实包，不得编造。",
        "",
        "**反向证据：**",
        "用 2-4 条 bullet，说明哪些事实与主要矛盾存在冲突或不确定性。",
        "",
        "**研究推论：**",
        "用 1 段话解释你对当前状态的理解。必须使用“推论上看”或“一个可能的解释是”。",
        "",
        "**后续观察：**",
        "列出 3-5 个接下来最值得观察的变量。",
        "",
        "**边界：**",
        "用一句话说明该点评基于 RAbot 本地数据与规则输出，不构成投资建议。",
        "",
        "RAbot 单资产事实包如下：",
        "",
        "```json",
        context_text,
        "```",
    ]

    return "\n".join(parts).strip()