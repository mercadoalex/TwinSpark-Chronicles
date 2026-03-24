"""Unit tests for monitoring API routes."""

import pytest
import pytest_asyncio
from unittest.mock import patch
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.monitoring.service import MonitoringService
from app.monitoring.routes import router


@pytest_asyncio.fixture
async def app_and_service(tmp_path):
    db_path = str(tmp_path / "test_routes.db")
    svc = MonitoringService(db_path=db_path, flush_interval=9999, cleanup_interval=9999)
    await svc.errors.init_db()
    await svc.metrics.init_db()

    app = FastAPI()
    app.include_router(router)

    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        yield app, svc


@pytest.mark.asyncio
async def test_health_returns_expected_fields(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/monitoring/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "uptime_seconds" in data
    assert "python_version" in data
    assert "total_request_count" in data
    assert "total_error_count" in data
    assert "db_connected" in data


@pytest.mark.asyncio
async def test_metrics_returns_grouped_data(app_and_service):
    app, svc = app_and_service
    svc.metrics.increment("test_counter")
    svc.metrics.set_gauge("test_gauge", 42.0)
    svc.metrics.record("test_hist", 10.0)
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/monitoring/metrics")
    data = resp.json()
    assert data["counters"]["test_counter"] == 1
    assert data["gauges"]["test_gauge"] == 42.0
    assert data["histograms"]["test_hist"]["count"] == 1


@pytest.mark.asyncio
async def test_metrics_filters_by_since(app_and_service):
    app, svc = app_and_service
    # Flush some data first
    svc.metrics.increment("snap_counter", 5)
    await svc.metrics.flush()
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/monitoring/metrics", params={"since": "2000-01-01T00:00:00"})
    data = resp.json()
    assert "snapshots" in data
    assert len(data["snapshots"]) >= 1


@pytest.mark.asyncio
async def test_errors_returns_sorted_list(app_and_service):
    app, svc = app_and_service
    await svc.errors.capture(error_type="A", message="a", traceback="", location="loc1")
    await svc.errors.capture(error_type="B", message="b", traceback="", location="loc2")
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/monitoring/errors")
    data = resp.json()
    assert len(data) == 2
    # Most recent first
    assert data[0]["error_type"] == "B"


@pytest.mark.asyncio
async def test_error_detail_returns_or_404(app_and_service):
    app, svc = app_and_service
    await svc.errors.capture(error_type="X", message="x", traceback="tb", location="loc")
    from app.monitoring.error_tracker import ErrorTracker
    fp = ErrorTracker.compute_fingerprint("X", "loc")
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/monitoring/errors/{fp}")
            assert resp.status_code == 200
            assert resp.json()["traceback"] == "tb"

            resp404 = await client.get("/api/monitoring/errors/nonexistent12345")
            assert resp404.status_code == 404


@pytest.mark.asyncio
async def test_frontend_error_post_creates_record(app_and_service):
    app, svc = app_and_service
    transport = ASGITransport(app=app)
    with patch("app.monitoring.routes.get_monitoring_service", return_value=svc):
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post("/api/monitoring/errors/frontend", json={
                "message": "Uncaught TypeError",
                "stack": "at Component.render",
                "component_stack": "in MyComponent",
                "component_name": "MyComponent",
                "timestamp": "2024-01-15T10:00:00.000",
            })
    assert resp.status_code == 201
    errors = await svc.errors.get_recent()
    assert any(e["source"] == "frontend" and e["message"] == "Uncaught TypeError" for e in errors)
