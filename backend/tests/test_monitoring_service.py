"""Unit tests for MonitoringService."""

import pytest
import pytest_asyncio
import aiosqlite
from datetime import datetime, timedelta
from app.monitoring.service import MonitoringService


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_monitoring.db")


@pytest_asyncio.fixture
async def service(tmp_db):
    svc = MonitoringService(db_path=tmp_db, retention_days=7, flush_interval=9999, cleanup_interval=9999)
    await svc.errors.init_db()
    await svc.metrics.init_db()
    yield svc
    # Ensure cleanup task is stopped
    if svc._cleanup_task is not None:
        svc._cleanup_task.cancel()
        try:
            await svc._cleanup_task
        except Exception:
            pass


@pytest.mark.asyncio
async def test_cleanup_deletes_old_records(service, tmp_db):
    old_ts = (datetime.utcnow() - timedelta(days=10)).isoformat(timespec="milliseconds")
    async with aiosqlite.connect(tmp_db) as db:
        await db.execute(
            "INSERT INTO error_events (fingerprint, error_type, message, traceback, source, location, first_seen, last_seen, count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("fp_old", "E", "old error", "", "backend", "loc", old_ts, old_ts, 1),
        )
        await db.execute(
            "INSERT INTO metric_snapshots (timestamp, name, type, value) VALUES (?, ?, ?, ?)",
            (old_ts, "old_metric", "counter", "5"),
        )
        await db.commit()

    await service.cleanup()

    async with aiosqlite.connect(tmp_db) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM error_events WHERE fingerprint = 'fp_old'")
        row = await cursor.fetchone()
        assert row[0] == 0
        cursor = await db.execute("SELECT COUNT(*) FROM metric_snapshots WHERE name = 'old_metric'")
        row = await cursor.fetchone()
        assert row[0] == 0


@pytest.mark.asyncio
async def test_cleanup_preserves_recent_records(service, tmp_db):
    recent_ts = datetime.utcnow().isoformat(timespec="milliseconds")
    async with aiosqlite.connect(tmp_db) as db:
        await db.execute(
            "INSERT INTO error_events (fingerprint, error_type, message, traceback, source, location, first_seen, last_seen, count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("fp_new", "E", "new error", "", "backend", "loc", recent_ts, recent_ts, 1),
        )
        await db.execute(
            "INSERT INTO metric_snapshots (timestamp, name, type, value) VALUES (?, ?, ?, ?)",
            (recent_ts, "new_metric", "counter", "3"),
        )
        await db.commit()

    await service.cleanup()

    async with aiosqlite.connect(tmp_db) as db:
        cursor = await db.execute("SELECT COUNT(*) FROM error_events WHERE fingerprint = 'fp_new'")
        row = await cursor.fetchone()
        assert row[0] == 1
        cursor = await db.execute("SELECT COUNT(*) FROM metric_snapshots WHERE name = 'new_metric'")
        row = await cursor.fetchone()
        assert row[0] == 1


@pytest.mark.asyncio
async def test_cleanup_failure_logged_without_crash(tmp_path):
    bad_path = str(tmp_path / "no" / "such" / "dir" / "monitoring.db")
    svc = MonitoringService(db_path=bad_path)
    # Should not raise
    await svc.cleanup()


def test_health_returns_expected_fields(tmp_db):
    svc = MonitoringService(db_path=tmp_db)
    h = svc.health()
    assert "status" in h
    assert "uptime_seconds" in h
    assert "python_version" in h
    assert "total_request_count" in h
    assert "total_error_count" in h
    assert h["status"] == "healthy"
