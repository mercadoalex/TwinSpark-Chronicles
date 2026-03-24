"""MonitoringService facade — owns MetricsCollector, ErrorTracker, and cleanup."""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta

import aiosqlite

from app.monitoring.error_tracker import ErrorTracker
from app.monitoring.metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

# Module-level singleton
_monitoring_service: "MonitoringService | None" = None


def get_monitoring_service() -> "MonitoringService | None":
    """Return the global MonitoringService instance (set during app startup)."""
    return _monitoring_service


class MonitoringService:
    """Facade that owns metrics collection, error tracking, and cleanup."""

    def __init__(
        self,
        db_path: str = "monitoring.db",
        retention_days: int = 7,
        flush_interval: int = 60,
        cleanup_interval: int = 3600,
    ):
        self.db_path = db_path
        self.retention_days = retention_days
        self.cleanup_interval = cleanup_interval
        self.metrics = MetricsCollector(db_path, flush_interval)
        self.errors = ErrorTracker(db_path)
        self._cleanup_task: asyncio.Task | None = None
        self._start_time = time.time()

    async def start(self) -> None:
        """Initialize DB tables, start flush and cleanup loops."""
        global _monitoring_service
        await self.errors.init_db()
        await self.metrics.init_db()
        await self.metrics.start_flush_loop()
        self._start_cleanup_loop()
        self._start_time = time.time()
        _monitoring_service = self
        logger.info("MonitoringService started")

    async def stop(self) -> None:
        """Stop loops, flush pending data."""
        global _monitoring_service
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
        await self.metrics.stop_flush_loop()
        _monitoring_service = None
        logger.info("MonitoringService stopped")

    async def cleanup(self) -> None:
        """Delete records older than retention_days."""
        cutoff = (datetime.utcnow() - timedelta(days=self.retention_days)).isoformat(
            timespec="milliseconds"
        )
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM error_events WHERE last_seen < ?", (cutoff,)
                )
                await db.execute(
                    "DELETE FROM metric_snapshots WHERE timestamp < ?", (cutoff,)
                )
                await db.commit()
            logger.info("Monitoring cleanup completed (cutoff=%s)", cutoff)
        except Exception as e:
            logger.error("Monitoring cleanup failed: %s", e)

    def health(self) -> dict:
        """Return system health summary."""
        all_metrics = self.metrics.get_all()
        return {
            "status": "healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "python_version": sys.version,
            "total_request_count": all_metrics["counters"].get("request_count", 0),
            "total_error_count": all_metrics["counters"].get("error_count", 0),
            "db_path": self.db_path,
        }

    def _start_cleanup_loop(self) -> None:
        async def _loop():
            while True:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup()

        self._cleanup_task = asyncio.create_task(_loop())
