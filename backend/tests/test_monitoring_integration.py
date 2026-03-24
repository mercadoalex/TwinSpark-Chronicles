"""Integration tests for the full monitoring pipeline."""

import json
import logging
import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.monitoring.service import MonitoringService
from app.monitoring.middleware import TraceIDMiddleware, MonitoringMiddleware
from app.monitoring.routes import router as monitoring_router
from app.monitoring.log_formatter import StructuredLogFormatter


@pytest_asyncio.fixture
async def integrated_app(tmp_path):
    """Build a minimal FastAPI app with full monitoring stack."""
    db_path = str(tmp_path / "integration.db")
    svc = MonitoringService(db_path=db_path, flush_interval=9999, cleanup_interval=9999)
    await svc.errors.init_db()
    await svc.metrics.init_db()

    app = FastAPI()
    app.add_middleware(MonitoringMiddleware, monitoring_service=svc)
    app.add_middleware(TraceIDMiddleware)
    app.include_router(monitoring_router)

    @app.get("/test/ok")
    async def ok():
        return {"result": "ok"}

    @app.get("/test/fail")
    async def fail():
        raise ValueError("integration test error")

    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        yield app, svc


@pytest.mark.asyncio
async def test_full_request_records_metrics(integrated_app):
    app, svc = integrated_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/test/ok")
    assert svc.metrics._counters.get("request_count", 0) >= 1
    assert "request_duration_ms" in svc.metrics._histograms


@pytest.mark.asyncio
async def test_trace_id_in_response(integrated_app):
    app, svc = integrated_app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/test/ok")
    tid = resp.headers.get("x-trace-id")
    assert tid is not None
    uuid.UUID(tid, version=4)  # validates format


@pytest.mark.asyncio
async def test_exception_appears_in_error_list(integrated_app):
    app, svc = integrated_app
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/test/fail")
    assert resp.status_code == 500
    errors = await svc.errors.get_recent()
    assert any(e["error_type"] == "ValueError" for e in errors)


@pytest.mark.asyncio
async def test_structured_log_output_is_valid_json():
    formatter = StructuredLogFormatter()
    test_logger = logging.getLogger("integration.test")
    record = test_logger.makeRecord(
        name="integration.test",
        level=logging.INFO,
        fn="test.py",
        lno=1,
        msg="integration log message",
        args=(),
        exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["message"] == "integration log message"
    assert "timestamp" in parsed
    assert "level" in parsed
