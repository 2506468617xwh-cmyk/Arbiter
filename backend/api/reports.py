from fastapi import APIRouter
from fastapi.responses import FileResponse

from backend.schemas.report import ReportContentResponse, ReportDeleteResponse, ReportListResponse
from backend.services.report_service import delete_report, get_latest_report, get_report, get_report_asset, list_reports


router = APIRouter(tags=["reports"])


@router.get("/reports", response_model=ReportListResponse)
def get_reports() -> ReportListResponse:
    return list_reports()


@router.get("/reports/latest", response_model=ReportContentResponse)
def get_latest_report_content() -> ReportContentResponse:
    return get_latest_report()


@router.get("/reports/assets/{asset_path:path}")
def get_report_asset_file(asset_path: str) -> FileResponse:
    path = get_report_asset(asset_path)
    return FileResponse(path)


@router.get("/reports/{filename}", response_model=ReportContentResponse)
def get_report_content(filename: str) -> ReportContentResponse:
    return get_report(filename)


@router.delete("/reports/{filename}", response_model=ReportDeleteResponse)
def delete_report_content(filename: str) -> ReportDeleteResponse:
    return delete_report(filename)
