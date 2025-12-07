# app/api/admin.py
from fastapi import APIRouter
from ..core.metrics import METRICS

router = APIRouter()

@router.get("/healthz", tags=["admin"])
def healthz():
    return {"status":"ok"}

@router.get("/metrics", tags=["admin"])
def metrics():
    return METRICS.get_snapshot()
