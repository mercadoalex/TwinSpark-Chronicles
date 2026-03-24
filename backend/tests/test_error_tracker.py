"""Unit tests for ErrorTracker."""

import asyncio
import pytest
import pytest_asyncio
from app.monitoring.error_tracker import ErrorTracker


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_monitoring.db")


@pytest_asyncio.fixture
async def tracker(tmp_db):
    t = ErrorTracker(db_path=tmp_db)
    await t.init_db()
    return t


def test_fingerprint_determinism():
    fp1 = ErrorTracker.compute_fingerprint("ValueError", "main.py:func:10")
    fp2 = ErrorTracker.compute_fingerprint("ValueError", "main.py:func:10")
    assert fp1 == fp2
    assert len(fp1) == 16
    assert all(c in "0123456789abcdef" for c in fp1)


def test_fingerprint_differs_for_different_inputs():
    fp1 = ErrorTracker.compute_fingerprint("ValueError", "main.py:func:10")
    fp2 = ErrorTracker.compute_fingerprint("TypeError", "main.py:func:10")
    assert fp1 != fp2


@pytest.mark.asyncio
async def test_capture_creates_new_record(tracker):
    await tracker.capture(
        error_type="ValueError",
        message="bad value",
        traceback="Traceback...",
        source="backend",
        location="main.py:func:10",
    )
    records = await tracker.get_recent()
    assert len(records) == 1
    assert records[0]["error_type"] == "ValueError"
    assert records[0]["count"] == 1


@pytest.mark.asyncio
async def test_capture_deduplicates_by_fingerprint(tracker):
    for _ in range(3):
        await tracker.capture(
            error_type="ValueError",
            message="bad value",
            traceback="Traceback...",
            source="backend",
            location="main.py:func:10",
        )
    records = await tracker.get_recent()
    assert len(records) == 1
    assert records[0]["count"] == 3


@pytest.mark.asyncio
async def test_capture_updates_last_seen(tracker):
    await tracker.capture(
        error_type="ValueError", message="m", traceback="", location="a:b:1"
    )
    first = await tracker.get_recent()
    first_seen = first[0]["first_seen"]
    last_seen_1 = first[0]["last_seen"]

    # Small delay to ensure timestamp differs
    await asyncio.sleep(0.01)
    await tracker.capture(
        error_type="ValueError", message="m", traceback="", location="a:b:1"
    )
    second = await tracker.get_recent()
    assert second[0]["first_seen"] == first_seen
    assert second[0]["last_seen"] >= last_seen_1


@pytest.mark.asyncio
async def test_get_recent_sorted_by_last_seen(tracker):
    await tracker.capture(error_type="A", message="a", traceback="", location="loc1")
    await asyncio.sleep(0.01)
    await tracker.capture(error_type="B", message="b", traceback="", location="loc2")
    records = await tracker.get_recent()
    assert records[0]["error_type"] == "B"
    assert records[1]["error_type"] == "A"


@pytest.mark.asyncio
async def test_get_by_fingerprint_returns_details(tracker):
    await tracker.capture(
        error_type="KeyError",
        message="missing key",
        traceback="full traceback here",
        source="backend",
        location="svc.py:handle:5",
        request_path="/api/test",
        trace_id="trace-123",
    )
    fp = ErrorTracker.compute_fingerprint("KeyError", "svc.py:handle:5")
    record = await tracker.get_by_fingerprint(fp)
    assert record is not None
    assert record["traceback"] == "full traceback here"
    assert record["request_path"] == "/api/test"
    assert record["trace_id"] == "trace-123"


@pytest.mark.asyncio
async def test_get_by_fingerprint_returns_none_for_missing(tracker):
    result = await tracker.get_by_fingerprint("nonexistent1234")
    assert result is None


@pytest.mark.asyncio
async def test_db_failure_logged_without_crash(tmp_path):
    bad_path = str(tmp_path / "nonexistent_dir" / "sub" / "monitoring.db")
    t = ErrorTracker(db_path=bad_path)
    # capture should not raise even with bad DB path
    await t.capture(error_type="E", message="m", traceback="", location="l")
