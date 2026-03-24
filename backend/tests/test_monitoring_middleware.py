"""Unit tests for TraceID and Monitoring middleware."""

import uuid
import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.monitoring.middleware import TraceIDMiddleware, MonitoringMiddleware
from app.monitoring.service import MonitoringService


@pytest_asyncio.fixture
async def app_and_service(tmp_path):
    db_path = str(tmp_path / "test_mw.db")
    svc = MonitoringService(db_path=db_path, flush_interval=9999, cleanup_interval=9999)
    await svc.errors.init_db()
    await svc.metrics.init_db()

    app = FastAPI()
    app.add_middleware(MonitoringMiddleware, monitoring_service=svc)
    app.add_middleware(TraceIDMiddleware)

    @app.get("/ok")
    async def ok_route():
        return {"status": "ok"}

    @app.get("/fail")
    async def fail_route():
        raise RuntimeError("test error")

    yield app, svc


@pytest.mark.asyncio
async def test_trace_id_in_response_header(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ok")
    assert "x-trace-id" in resp.headers


@pytest.mark.asyncio
async def test_trace_id_is_valid_uuid4(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/ok")
    tid = resp.headers["x-trace-id"]
    parsed = uuid.UUID(tid, version=4)
    assert str(parsed) == tid


@pytest.mark.asyncio
async def test_request_count_incremented(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/ok")
        await client.get("/ok")
    assert svc.metrics._counters.get("request_count", 0) == 2


@pytest.mark.asyncio
async def test_request_duration_ms_recorded(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.get("/ok")
    h = svc.metrics._histograms.get("request_duration_ms")
    assert h is not None
    assert h.count == 1
    assert h.min_val >= 0


@pytest.mark.asyncio
async def test_error_count_incremented_on_exception(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/fail")
    assert resp.status_code == 500
    assert svc.metrics._counters.get("error_count", 0) == 1


@pytest.mark.asyncio
async def test_error_captured_with_trace_id(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/fail")
    errors = await svc.errors.get_recent(limit=10)
    assert len(errors) >= 1
    err = errors[0]
    assert err["error_type"] == "RuntimeError"
    assert err["trace_id"] is not None
