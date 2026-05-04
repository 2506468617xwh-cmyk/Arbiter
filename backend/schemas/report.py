from pydantic import BaseModel, Field


class ReportMeta(BaseModel):
    filename: str
    title: str
    updated_at: str
    size_bytes: int


class ReportListResponse(BaseModel):
    reports: list[ReportMeta] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class ReportContentResponse(ReportMeta):
    content: str


class ReportDeleteResponse(BaseModel):
    filename: str
    deleted: bool
    message: str
