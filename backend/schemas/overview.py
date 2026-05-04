from pydantic import BaseModel, Field


class OverviewSection(BaseModel):
    count: int = 0
    highlights: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class OverviewReports(BaseModel):
    count: int = 0
    latest_title: str | None = None
    latest_filename: str | None = None


class OverviewResponse(BaseModel):
    market_status: str
    market_summary: str
    news_summary: str
    macro_summary: str
    report_summary: str
    last_update: str
    warnings: list[str] = Field(default_factory=list)
    market: OverviewSection = Field(default_factory=OverviewSection)
    news: OverviewSection = Field(default_factory=OverviewSection)
    macro: OverviewSection = Field(default_factory=OverviewSection)
    reports: OverviewReports = Field(default_factory=OverviewReports)
