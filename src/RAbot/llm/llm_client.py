# src/RAbot/llm/llm_client.py

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv


@dataclass
class LLMResult:
    ok: bool
    text: str
    model: str
    error: str = ""


class RAbotLLMClient:
    """
    DeepSeek LLM client for RAbot.

    DeepSeek provides an OpenAI-compatible Chat Completions API.
    This client uses:
    - base_url = https://api.deepseek.com
    - env key  = DEEPSEEK_API_KEY
    - default model = deepseek-v4-flash

    If the key or SDK is missing, it returns a graceful fallback instead of
    crashing the report generator.
    """

    def __init__(
        self,
        model: str | None = None,
        temperature: float = 0.35,
        max_tokens: int = 1600,
        thinking: str | None = None,
        reasoning_effort: str = "high",
    ) -> None:
        load_dotenv()

        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").strip()
        self.model = model or os.getenv("RABOT_LLM_MODEL", "deepseek-v4-flash").strip()
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.thinking = (thinking or os.getenv("RABOT_LLM_THINKING", "disabled")).strip().lower()
        self.reasoning_effort = reasoning_effort

    def is_available(self) -> bool:
        return bool(self.api_key)

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> LLMResult:
        if not self.api_key:
            return LLMResult(
                ok=False,
                text=(
                    "LLM 未启用：当前未检测到 DEEPSEEK_API_KEY。"
                    "请在项目根目录 .env 中配置 DEEPSEEK_API_KEY 后重试。"
                ),
                model=self.model,
                error="missing_deepseek_api_key",
            )

        try:
            from openai import OpenAI
        except Exception as exc:
            return LLMResult(
                ok=False,
                text="LLM 未启用：openai Python 包未正确安装。请运行 pip install -r requirements.txt。",
                model=self.model,
                error=f"{type(exc).__name__}: {exc}",
            )

        try:
            client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            extra_body: dict[str, Any] = {}

            if self.thinking in {"enabled", "disabled"}:
                extra_body["thinking"] = {"type": self.thinking}

            kwargs: dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False,
            }

            if extra_body:
                kwargs["extra_body"] = extra_body

            if self.thinking == "enabled":
                kwargs["reasoning_effort"] = self.reasoning_effort

            response = client.chat.completions.create(**kwargs)

            text = self._extract_output_text(response)

            if not text.strip():
                return LLMResult(
                    ok=False,
                    text="LLM 调用成功，但没有返回可用文本。建议更换模型或稍后重试。",
                    model=self.model,
                    error="empty_output_text",
                )

            return LLMResult(
                ok=True,
                text=text.strip(),
                model=self.model,
                error="",
            )

        except Exception as exc:
            return LLMResult(
                ok=False,
                text=f"LLM 调用失败：{type(exc).__name__}: {exc}",
                model=self.model,
                error=f"{type(exc).__name__}: {exc}",
            )

    @staticmethod
    def _extract_output_text(response: Any) -> str:
        try:
            choice = response.choices[0]
            message = choice.message
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
        except Exception:
            pass

        try:
            data = response.model_dump()
            choices = data.get("choices", [])
            if choices:
                message = choices[0].get("message", {})
                content = message.get("content", "")
                if isinstance(content, str):
                    return content
        except Exception:
            pass

        return ""