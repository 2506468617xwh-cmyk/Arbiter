# src/RAbot/llm/research_chat.py

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from RAbot.llm.context_builder import (
    ContextBuildResult,
    build_asset_context,
    build_market_context,
    build_multi_asset_context,
)


@dataclass
class ResearchChatResult:
    ok: bool
    text: str
    model: str = ""
    context: dict[str, Any] | None = None


class RAbotResearchChat:
    """
    RAbot 轻量级 LLM Research Analyst。

    用途：
    1. 单资产 AI 快评；
    2. 全市场问答；
    3. 单标的问答；
    4. 多标的组合问答。

    注意：
    - 不裸聊；
    - 每次回答都基于 context_builder 构造的 RAbot 本地事实包；
    - 如果没有 DEEPSEEK_API_KEY，前端不会崩，而是返回友好提示。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
        self.model = model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat").strip()
        self.timeout = timeout

    def _is_ready(self) -> bool:
        return bool(self.api_key)

    def _client(self) -> OpenAI:
        return OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.25,
        max_tokens: int = 900,
    ) -> ResearchChatResult:
        if not self._is_ready():
            return ResearchChatResult(
                ok=False,
                text=(
                    "当前尚未配置 DEEPSEEK_API_KEY，因此 RAbot 不能调用 LLM 研究层。\n\n"
                    "你可以在项目 `.env` 或系统环境变量中加入：\n\n"
                    "`DEEPSEEK_API_KEY=你的 key`\n\n"
                    "配置后重启 Streamlit，再使用 AI 快评或研究对话。"
                ),
                model=self.model,
            )

        try:
            client = self._client()

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )

            text = response.choices[0].message.content or ""

            return ResearchChatResult(
                ok=True,
                text=text.strip(),
                model=self.model,
            )

        except Exception as e:
            return ResearchChatResult(
                ok=False,
                text=(
                    "RAbot 调用 LLM 研究层失败。\n\n"
                    f"错误类型：{type(e).__name__}\n\n"
                    f"错误信息：{e}"
                ),
                model=self.model,
            )

    def _system_prompt(self) -> str:
        return """
你是 RAbot 的 LLM Research Analyst，是一个面向个人研究与市场复盘的金融研究助手。

你的回答必须遵守以下规则：
1. 只能基于用户提供的 RAbot 结构化事实包进行分析。
2. 不得编造实时行情、新闻、宏观数据或不存在的指标。
3. 如果事实包不足以支持判断，要明确说“数据不足”或“只能做有限判断”。
4. 不给具体买卖指令，不承诺收益，不输出“必涨”“必跌”等绝对化判断。
5. 回答使用中文，风格像研究员口头简报：简洁、直接、低废话。
6. 明确区分：趋势判断、支撑因素、压力因素、观察变量、不确定性。
7. 不要复述大段数据表，只提炼关键含义。
""".strip()

    def _context_to_text(self, context: dict[str, Any]) -> str:
        return json.dumps(context, ensure_ascii=False, indent=2, default=str)

    def _build_quick_view_prompt(self, context: dict[str, Any]) -> str:
        return f"""
下面是 RAbot 为单一资产构造的结构化事实包：

{self._context_to_text(context)}

请基于上述事实包，输出一段“AI 快评”。

要求：
1. 中文。
2. 总长度控制在 300-500 字。
3. 不要写成完整研报，写成研究员口头快评。
4. 必须包含：
   - 一句话结论
   - 当前主要支撑因素
   - 当前主要压力因素
   - 未来 1-2 周重点观察变量
   - 不确定性提示
5. 不要给具体买卖建议。
6. 不要编造事实包之外的数据。
""".strip()

    def generate_asset_quick_view(self, asset_symbol: str) -> ResearchChatResult:
        context_result: ContextBuildResult = build_asset_context(asset_symbol)

        if not context_result.ok:
            return ResearchChatResult(
                ok=False,
                text=context_result.message,
                model=self.model,
                context=context_result.context,
            )

        result = self._call_llm(
            system_prompt=self._system_prompt(),
            user_prompt=self._build_quick_view_prompt(context_result.context),
            temperature=0.25,
            max_tokens=900,
        )

        result.context = context_result.context
        return result

    def _build_answer_prompt(
        self,
        question: str,
        context: dict[str, Any],
    ) -> str:
        return f"""
用户问题：

{question}

下面是 RAbot 根据本地数据库和规则层研究模块构造的结构化事实包：

{self._context_to_text(context)}

请基于事实包回答用户问题。

回答要求：
1. 中文。
2. 先给核心结论，再展开理由。
3. 不要超过 800 字，除非用户问题需要更长分析。
4. 明确说明哪些判断来自数据支持，哪些属于不确定性。
5. 如果事实包无法支持某个判断，直接说数据不足。
6. 不要编造实时数据、新闻或宏观指标。
7. 不要给具体买卖指令。
""".strip()

    def answer_question(
        self,
        question: str,
        scope: str = "market",
        asset_symbol: str | None = None,
        symbols: list[str] | None = None,
    ) -> ResearchChatResult:
        question = str(question or "").strip()

        if not question:
            return ResearchChatResult(
                ok=False,
                text="你还没有输入问题。",
                model=self.model,
            )

        scope = str(scope or "market").strip()

        if scope == "single_asset":
            if not asset_symbol:
                return ResearchChatResult(
                    ok=False,
                    text="你选择了单标的研究范围，但没有指定标的。",
                    model=self.model,
                )
            context_result = build_asset_context(asset_symbol)

        elif scope == "multi_asset":
            if not symbols:
                return ResearchChatResult(
                    ok=False,
                    text="你选择了多标的组合研究范围，但没有选择标的。",
                    model=self.model,
                )
            context_result = build_multi_asset_context(symbols)

        else:
            context_result = build_market_context()

        if not context_result.ok:
            return ResearchChatResult(
                ok=False,
                text=context_result.message,
                model=self.model,
                context=context_result.context,
            )

        result = self._call_llm(
            system_prompt=self._system_prompt(),
            user_prompt=self._build_answer_prompt(question, context_result.context),
            temperature=0.25,
            max_tokens=1100,
        )

        result.context = context_result.context
        return result