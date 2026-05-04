from datetime import datetime
from pathlib import Path

from fastapi import HTTPException

from backend.schemas.report import ReportContentResponse, ReportDeleteResponse, ReportListResponse, ReportMeta


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"
REPORT_ASSETS_DIR = REPORTS_DIR / "assets"


def _format_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(timespec="seconds")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8-sig")


def _extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                return title
    return fallback


def _safe_report_path(filename: str) -> Path:
    if not filename.lower().endswith(".md"):
        raise HTTPException(status_code=400, detail="Only Markdown .md reports are allowed.")

    base = REPORTS_DIR.resolve()
    candidate = (base / filename).resolve()

    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report path.") from exc

    if candidate.name != filename:
        raise HTTPException(status_code=400, detail="Nested report paths are not allowed.")

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report not found.")

    return candidate


def _safe_write_path(filename: str) -> Path:
    if not filename.lower().endswith(".md"):
        raise ValueError("Only Markdown .md reports are allowed.")

    base = REPORTS_DIR.resolve()
    base.mkdir(parents=True, exist_ok=True)
    candidate = (base / filename).resolve()

    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError("Invalid report path.") from exc

    if candidate.name != filename:
        raise ValueError("Nested report paths are not allowed.")

    return candidate


def get_report_asset(asset_path: str) -> Path:
    allowed_suffixes = {".svg", ".png", ".jpg", ".jpeg", ".webp"}
    base = REPORT_ASSETS_DIR.resolve()
    candidate = (base / asset_path).resolve()

    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid report asset path.") from exc

    if candidate.suffix.lower() not in allowed_suffixes:
        raise HTTPException(status_code=400, detail="Unsupported report asset type.")

    if not candidate.exists() or not candidate.is_file():
        raise HTTPException(status_code=404, detail="Report asset not found.")

    return candidate


def _to_meta(path: Path) -> ReportMeta:
    content = _read_text(path)
    stat = path.stat()
    return ReportMeta(
        filename=path.name,
        title=_extract_title(content, path.name),
        updated_at=_format_mtime(path),
        size_bytes=stat.st_size,
    )


def list_reports() -> ReportListResponse:
    warnings: list[str] = []
    if not REPORTS_DIR.exists():
        warnings.append(f"报告目录不存在：{REPORTS_DIR}")
        return ReportListResponse(reports=[], warnings=warnings)

    if not REPORTS_DIR.is_dir():
        warnings.append(f"报告路径不是目录：{REPORTS_DIR}")
        return ReportListResponse(reports=[], warnings=warnings)

    report_paths = sorted(
        (path for path in REPORTS_DIR.iterdir() if path.is_file() and path.suffix.lower() == ".md"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    reports: list[ReportMeta] = []
    for path in report_paths:
        try:
            reports.append(_to_meta(path))
        except OSError as exc:
            warnings.append(f"读取报告失败：{path.name}（{exc}）")

    return ReportListResponse(reports=reports, warnings=warnings)


def get_report(filename: str) -> ReportContentResponse:
    path = _safe_report_path(filename)
    content = _read_text(path)
    stat = path.stat()
    return ReportContentResponse(
        filename=path.name,
        title=_extract_title(content, path.name),
        content=content,
        updated_at=_format_mtime(path),
        size_bytes=stat.st_size,
    )


def get_latest_report() -> ReportContentResponse:
    reports = list_reports()
    if not reports.reports:
        raise HTTPException(status_code=404, detail="No Markdown reports found.")
    return get_report(reports.reports[0].filename)


def delete_report(filename: str) -> ReportDeleteResponse:
    path = _safe_report_path(filename)
    try:
        path.unlink()
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Failed to delete report: {exc}") from exc

    return ReportDeleteResponse(
        filename=filename,
        deleted=True,
        message="Report deleted.",
    )


def save_report_content(filename: str, content: str) -> ReportMeta:
    path = _safe_write_path(filename)
    path.write_text(content, encoding="utf-8")
    return _to_meta(path)
