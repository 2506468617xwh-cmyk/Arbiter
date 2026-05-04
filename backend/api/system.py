from fastapi import APIRouter

from backend.services.update_service import update_service


router = APIRouter(tags=["system"])


@router.get("/system/update/status")
def get_update_status() -> dict:
    return update_service.status()


@router.post("/system/update/run")
def run_update() -> dict:
    return update_service.run_background(reason="manual_api")
