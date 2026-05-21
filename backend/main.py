import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

HERE = Path(__file__).resolve().parent
PROJECT_DIR = HERE.parent
FRONTEND_DIST = PROJECT_DIR / "frontend" / "dist"

# Make src/RAbot importable regardless of PYTHONPATH / cwd
sys.path.insert(0, str(PROJECT_DIR / "src"))

from backend.api.funds import router as funds_router
from backend.api.institute import router as institute_router
from backend.api.llm import router as llm_router
from backend.api.macro import router as macro_router
from backend.api.market import router as market_router
from backend.api.news import router as news_router
from backend.api.news_intelligence import router as news_intelligence_router
from backend.api.overview import router as overview_router
from backend.api.research import router as research_router
from backend.api.reports import router as reports_router
from backend.api.stocks import router as stocks_router
from backend.api.system import router as system_router
from backend.api.tasks import router as tasks_router
from backend.services.update_service import update_service
from RAbot.settings import get_data_dir


class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"


@asynccontextmanager
async def lifespan(app: FastAPI):
    enabled = os.getenv("RABOT_AUTO_UPDATE_ON_START", "true").strip().lower()
    if enabled not in {"0", "false", "no", "off", "disabled"}:
        update_service.run_background(reason="startup")
    yield


app = FastAPI(title="RAbot API", version="0.1.0", lifespan=lifespan, default_response_class=UTF8JSONResponse)

# CORS — configurable via FRONTEND_ORIGINS env var
_cors = os.getenv("FRONTEND_ORIGINS", "").strip()
if _cors:
    origins = [o.strip() for o in _cors.split(",") if o.strip()]
else:
    origins = [
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, object]:
    import traceback
    data_dir_exists = False
    reports_dir_exists = False
    try:
        data_dir = get_data_dir()
        data_dir_exists = data_dir.is_dir()
        reports_dir_exists = (data_dir / "reports").is_dir()
    except Exception:
        pass
    return {
        "status": "ok",
        "app": "RAbot API",
        "version": "0.1.0",
        "environment": os.getenv("APP_ENV", "development"),
        "data_dir_exists": data_dir_exists,
        "reports_dir_exists": reports_dir_exists,
        "cwd": str(Path.cwd()),
        "project_dir": str(PROJECT_DIR),
        "pythonpath": os.getenv("PYTHONPATH", ""),
        "sys_path_src": [p for p in sys.path if "src" in p],
        "frontend_dist_exists": FRONTEND_DIST.is_dir(),
    }


@app.get("/api/debug/routes")
def debug_routes() -> dict[str, object]:
    routes = []
    for route in app.routes:
        routes.append({
            "path": getattr(route, "path", ""),
            "name": getattr(route, "name", ""),
            "methods": list(getattr(route, "methods", set())),
        })
    return {"count": len(routes), "routes": [r for r in routes if r["path"].startswith("/api")]}


app.include_router(overview_router, prefix="/api")
app.include_router(llm_router, prefix="/api")
app.include_router(market_router, prefix="/api")
app.include_router(news_intelligence_router, prefix="/api")
app.include_router(news_router, prefix="/api")
app.include_router(macro_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(stocks_router, prefix="/api")
app.include_router(funds_router, prefix="/api")
app.include_router(institute_router, prefix="/api")
app.include_router(tasks_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(system_router, prefix="/api")


# ── Production: serve built frontend ──────────────────────────────
if FRONTEND_DIST.is_dir():
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="frontend_assets",
    )

    @app.exception_handler(404)
    async def _spa_fallback(request, exc):
        index = FRONTEND_DIST / "index.html"
        if not index.exists():
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return FileResponse(str(index))

    @app.get("/")
    async def _serve_index():
        index = FRONTEND_DIST / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"status": "ok", "message": "RAbot API running. Build the frontend to serve the UI."}
