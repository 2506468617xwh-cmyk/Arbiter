from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class LLMQuickSummaryRequest(BaseModel):
    scope: Literal["market", "single_asset", "multi_asset"] = "market"
    asset_symbol: str | None = None
    symbols: list[str] = Field(default_factory=list)
    use_llm: bool = True


class LLMChatRequest(BaseModel):
    question: str
    scope: Literal["market", "single_asset", "multi_asset"] = "market"
    asset_symbol: str | None = None
    symbols: list[str] = Field(default_factory=list)
    use_llm: bool = True


class PetSummaryRequest(BaseModel):
    page_name: str = "home"
    mode: Literal["market", "page"] = "page"
    context: dict[str, Any] = Field(default_factory=dict)
    use_llm: bool = True


class LLMResponse(BaseModel):
    ok: bool
    text: str
    model: str | None = None
    scope: str
    asset_symbol: str | None = None
    symbols: list[str] = Field(default_factory=list)
    context: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
