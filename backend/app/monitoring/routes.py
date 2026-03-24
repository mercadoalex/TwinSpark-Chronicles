"""Monitoring API routes — health, metrics, errors, frontend error intake."""

import json
import logging
from datetime import datetime

import aiosqlite
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.monitoring.service import get_monitoring_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


class FrontendErrorReport(BaseModel):
    message: str
    stack: str = ""
    component_stack: str = ""
    component_name: str = "unknown"
    timestamp: str = ""


@router.get("/health")
async def monitoring_health():
    svc = get_monitoring_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    health = svc.health()
    # Check DB connectivity
    try:
        async with aiosqlite.connect(svc.db_path) as db:
            await db.execute("SELECT 1")
        health["db_connected"] = True
    except Exception:
        health["db_connected"] = False
    return health


@router.get("/metrics")
async def monitoring_metrics(since: str | None = Query(default=None)):
    svc = get_monitoring_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")

    result = svc.metrics.get_all()

    if since:
        # Also return historical snapshots from DB
        try:
            async with aiosqlite.connect(svc.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT timestamp, name, type, value FROM metric_snapshots WHERE timestamp > ? ORDER BY timestamp",
                    (since,),
                )
                rows = await cursor.fetchall()
                result["snapshots"] = [
                    {"timestamp": r["timestamp"], "name": r["name"], "type": r["type"], "value": json.loads(r["value"])}
                    for r in rows
                ]
        except Exception as e:
            logger.error("Failed to fetch metric snapshots: %s", e)
            result["snapshots"] = []

    return result


@router.get("/errors")
async def monitoring_errors(limit: int = Query(default=50, ge=1, le=500)):
    svc = get_monitoring_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    return await svc.errors.get_recent(limit=limit)


@router.get("/errors/{fingerprint}")
async def monitoring_error_detail(fingerprint: str):
    svc = get_monitoring_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    record = await svc.errors.get_by_fingerprint(fingerprint)
    if record is None:
        raise HTTPException(status_code=404, detail="Error not found")
    return record


@router.post("/errors/frontend", status_code=201)
async def monitoring_frontend_error(report: FrontendErrorReport):
    svc = get_monitoring_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Monitoring not initialized")
    from app.monitoring.error_tracker import ErrorTracker

    fingerprint_location = report.component_name
    await svc.errors.capture(
        error_type="FrontendError",
        message=report.message,
        traceback=report.stack,
        source="frontend",
        location=fingerprint_location,
        request_path=None,
        trace_id=None,
    )
    return {"status": "captured"}
