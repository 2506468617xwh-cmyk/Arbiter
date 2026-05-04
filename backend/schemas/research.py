from pydantic import BaseModel, Field


class ResearchGenerateRequest(BaseModel):
    target: str = "market_overview"
    index_symbol: str | None = None
    symbol: str | None = None
    report_style: str = "券商研报风"
    use_llm: bool = True
    sections: list[str] = Field(default_factory=lambda: ["market", "news", "macro", "strategy"])
    extra_instruction: str = ""


class ResearchGenerateResponse(BaseModel):
    task_id: str
    status: str
    message: str
