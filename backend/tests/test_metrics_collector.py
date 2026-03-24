"""Unit tests for MetricsCollector."""

import json
import pytest
import pytest_asyncio
import aiosqlite
from app.monitoring.metrics_collector import MetricsCollector, HistogramStats


@pytest.fixture
def tmp_db(tmp_path):
    return str(tmp_path / "test_metrics.db")


@pytest_asyncio.fixture
async def collector(tmp_db):
    mc = MetricsCollector(db_path=tmp_db, flush_interval=60)
    await mc.init_db()
    return mc


def test_counter_increment():
    mc = MetricsCollector()
    mc.increment("req_count")
    mc.increment("req_count")
    mc.increment("req_count", 3)
    assert mc._counters["req_count"] == 5


def test_gauge_set():
    mc = MetricsCollector()
    mc.set_gauge("cpu", 45.2)
    mc.set_gauge("cpu", 60.1)
    assert mc._gauges["cpu"] == 60.1


def test_histogram_record():
    mc = MetricsCollector()
    mc.record("duration", 10.0)
    mc.record("duration", 20.0)
    mc.record("duration", 30.0)
    h = mc._histograms["duration"]
    assert h.count == 3
    assert h.min_val == 10.0
    assert h.max_val == 30.0
    assert h.mean == 20.0


def test_histogram_p95():
    mc = MetricsCollector()
    for i in range(100):
        mc.record("latency", float(i))
    h = mc._histograms["latency"]
    assert h.p95 == 95.0


def test_histogram_bounded_values():
    mc = MetricsCollector()
    h = HistogramStats(max_values=5)
    mc._histograms["test"] = h
    for i in range(10):
        mc.record("test", float(i))
    assert len(h.values) == 5
    assert h.count == 10


def test_get_all_grouping():
    mc = MetricsCollector()
    mc.increment("requests")
    mc.set_gauge("memory", 512.0)
    mc.record("duration", 100.0)
    result = mc.get_all()
    assert "counters" in result
    assert "gauges" in result
    assert "histograms" in result
    assert result["counters"]["requests"] == 1
    assert result["gauges"]["memory"] == 512.0
    assert result["histograms"]["duration"]["count"] == 1


@pytest.mark.asyncio
async def test_flush_persists_to_sqlite(collector, tmp_db):
    collector.increment("req_count", 5)
    collector.set_gauge("cpu", 42.0)
    collector.record("latency", 15.5)
    await collector.flush()

    async with aiosqlite.connect(tmp_db) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM metric_snapshots")
        rows = await cursor.fetchall()
    assert len(rows) == 3
    names = {r["name"] for r in rows}
    assert names == {"req_count", "cpu", "latency"}


@pytest.mark.asyncio
async def test_stop_flush_loop_triggers_final_flush(collector, tmp_db):
    collector.increment("final_count", 1)
    await collector.start_flush_loop()
    await collector.stop_flush_loop()

    async with aiosqlite.connect(tmp_db) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM metric_snapshots WHERE name = 'final_count'"
        )
        rows = await cursor.fetchall()
    assert len(rows) == 1
