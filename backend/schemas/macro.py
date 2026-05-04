from typing import Optional

from pydantic import BaseModel, Field


class MacroIndicatorItem(BaseModel):
    indicator: str
    name: Optional[str] = None
    latest_value: Optional[float] = None
    latest_date: Optional[str] = None
    previous_value: Optional[float] = None
    change: Optional[float] = None
    trend: Optional[str] = None
    summary: str


class MacroOverviewResponse(BaseModel):
    items: list[MacroIndicatorItem] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MacroSnapshotItem(BaseModel):
    symbol: str
    name: str | None = None
    region: str | None = None
    category: str | None = None
    source: str | None = None
    unit: str | None = None
    latest_date: str | None = None
    latest_value: float | None = None
    change_1m: float | None = None
    change_3m: float | None = None
    change_6m: float | None = None
    change_1y: float | None = None
    trend_label: str | None = None
    risk_label: str | None = None
    interpretation: str | None = None
    direction_note: str | None = None
    related_assets: str | None = None


class MacroSnapshotResponse(BaseModel):
    items: list[MacroSnapshotItem] = Field(default_factory=list)
    count: int = 0
    regions: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MacroSeriesPoint(BaseModel):
    symbol: str
    name: str | None = None
    region: str | None = None
    category: str | None = None
    date: str
    value: float | None = None
    unit: str | None = None


class MacroSeriesResponse(BaseModel):
    items: list[MacroSeriesPoint] = Field(default_factory=list)
    symbols: list[str] = Field(default_factory=list)
    count: int = 0
    last_update: str
    warnings: list[str] = Field(default_factory=list)


class MacroAnalysisRequest(BaseModel):
    question: str
    symbols: list[str] = Field(default_factory=list)
    use_llm: bool = True


class MacroAnalysisResponse(BaseModel):
    ok: bool = False
    text: str
    model: str | None = None
    warnings: list[str] = Field(default_factory=list)
