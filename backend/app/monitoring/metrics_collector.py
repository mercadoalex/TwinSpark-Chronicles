"""In-memory metrics collection with periodic SQLite persistence."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import aiosqlite

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS metric_snapshots (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    name      TEXT NOT NULL,
    type      TEXT NOT NULL,
    value     TEXT NOT NULL
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_metric_snapshots_timestamp ON metric_snapshots(timestamp);",
    "CREATE INDEX IF NOT EXISTS idx_metric_snapshots_name ON metric_snapshots(name);",
]


@dataclass
class HistogramStats:
    count: int = 0
    total: float = 0.0
    min_val: float = float("inf")
    max_val: float = float("-inf")
    values: list[float] = field(default_factory=list)
    max_values: int = 1000

    @property
    def mean(self) -> float:
        return self.total / self.count if self.count > 0 else 0.0

    @property
    def p95(self) -> float:
        if not self.values:
            return 0.0
        sorted_vals = sorted(self.values)
        idx = int(len(sorted_vals) * 0.95)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]


class MetricsCollector:
    """Collects counters, gauges, and histograms in memory with SQLite flush."""

    def __init__(self, db_path: str = "monitoring.db", flush_interval: int = 60):
        self.db_path = db_path
        self.flush_interval = flush_interval
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}
        self._histograms: dict[str, HistogramStats] = {}
        self._flush_task: asyncio.Task | None = None

    def increment(self, name: str, value: int = 1) -> None:
        """Increment a counter metric."""
        self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float) -> None:
        """Set a gauge metric to a specific value."""
        self._gauges[name] = value

    def record(self, name: str, value: float) -> None:
        """Record a value in a histogram metric."""
        if name not in self._histograms:
            self._histograms[name] = HistogramStats()
        h = self._histograms[name]
        h.count += 1
        h.total += value
        h.min_val = min(h.min_val, value)
        h.max_val = max(h.max_val, value)
        if len(h.values) < h.max_values:
            h.values.append(value)

    def get_all(self) -> dict:
        """Return all current metrics grouped by type."""
        histograms = {}
        for name, h in self._histograms.items():
            histograms[name] = {
                "count": h.count,
                "total": h.total,
                "min": h.min_val if h.count > 0 else 0,
                "max": h.max_val if h.count > 0 else 0,
                "mean": h.mean,
                "p95": h.p95,
            }
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": histograms,
        }

    async def init_db(self) -> None:
        """Create the metric_snapshots table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(_CREATE_TABLE)
            for idx in _CREATE_INDEXES:
                await db.execute(idx)
            await db.commit()

    async def flush(self) -> None:
        """Persist current metric snapshot to SQLite."""
        now = datetime.utcnow().isoformat(timespec="milliseconds")
        rows = []
        for name, val in self._counters.items():
            rows.append((now, name, "counter", json.dumps(val)))
        for name, val in self._gauges.items():
            rows.append((now, name, "gauge", json.dumps(val)))
        for name, h in self._histograms.items():
            rows.append((now, name, "histogram", json.dumps({
                "count": h.count, "total": h.total,
                "min": h.min_val if h.count > 0 else 0,
                "max": h.max_val if h.count > 0 else 0,
                "mean": h.mean, "p95": h.p95,
            })))
        if not rows:
            return
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.executemany(
                    "INSERT INTO metric_snapshots (timestamp, name, type, value) VALUES (?, ?, ?, ?)",
                    rows,
                )
                await db.commit()
        except Exception as e:
            logger.error("Failed to flush metrics: %s", e)

    async def start_flush_loop(self) -> None:
        """Start periodic flush task."""
        async def _loop():
            while True:
                await asyncio.sleep(self.flush_interval)
                await self.flush()
        self._flush_task = asyncio.create_task(_loop())

    async def stop_flush_loop(self) -> None:
        """Stop periodic flush and do a final flush."""
        if self._flush_task is not None:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
            self._flush_task = None
        await self.flush()
