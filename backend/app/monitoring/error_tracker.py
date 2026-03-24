"""Error tracking with fingerprint-based deduplication."""

import hashlib
import logging
from datetime import datetime

import aiosqlite

logger = logging.getLogger(__name__)

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS error_events (
    fingerprint  TEXT PRIMARY KEY,
    error_type   TEXT NOT NULL,
    message      TEXT NOT NULL,
    traceback    TEXT NOT NULL DEFAULT '',
    source       TEXT NOT NULL DEFAULT 'backend',
    location     TEXT NOT NULL DEFAULT '',
    request_path TEXT,
    trace_id     TEXT,
    first_seen   TEXT NOT NULL,
    last_seen    TEXT NOT NULL,
    count        INTEGER NOT NULL DEFAULT 1
);
"""

_CREATE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_error_events_last_seen ON error_events(last_seen);",
    "CREATE INDEX IF NOT EXISTS idx_error_events_source ON error_events(source);",
]


class ErrorTracker:
    """Captures, fingerprints, deduplicates, and stores error events."""

    def __init__(self, db_path: str = "monitoring.db"):
        self.db_path = db_path

    @staticmethod
    def compute_fingerprint(error_type: str, location: str) -> str:
        """SHA256 hash of error_type + location, truncated to 16 hex chars."""
        raw = f"{error_type}:{location}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    async def init_db(self) -> None:
        """Create the error_events table if it doesn't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(_CREATE_TABLE)
            for idx in _CREATE_INDEXES:
                await db.execute(idx)
            await db.commit()

    async def capture(
        self,
        error_type: str,
        message: str,
        traceback: str,
        source: str = "backend",
        location: str = "",
        request_path: str | None = None,
        trace_id: str | None = None,
    ) -> None:
        """Capture an error event, deduplicating by fingerprint."""
        fingerprint = self.compute_fingerprint(error_type, location)
        now = datetime.utcnow().isoformat(timespec="milliseconds")
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT count FROM error_events WHERE fingerprint = ?",
                    (fingerprint,),
                )
                existing = await cursor.fetchone()
                if existing:
                    await db.execute(
                        "UPDATE error_events SET count = count + 1, last_seen = ?, trace_id = ? WHERE fingerprint = ?",
                        (now, trace_id, fingerprint),
                    )
                else:
                    await db.execute(
                        "INSERT INTO error_events (fingerprint, error_type, message, traceback, source, location, request_path, trace_id, first_seen, last_seen, count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
                        (fingerprint, error_type, message, traceback, source, location, request_path, trace_id, now, now),
                    )
                await db.commit()
        except Exception as e:
            logger.error("Failed to persist error record: %s", e)

    async def get_recent(self, limit: int = 50) -> list[dict]:
        """Return recent error groups sorted by last_seen desc."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT fingerprint, error_type, message, source, location, request_path, trace_id, first_seen, last_seen, count FROM error_events ORDER BY last_seen DESC LIMIT ?",
                    (limit,),
                )
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error("Failed to fetch recent errors: %s", e)
            return []

    async def get_by_fingerprint(self, fingerprint: str) -> dict | None:
        """Return full details for a single error group."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM error_events WHERE fingerprint = ?",
                    (fingerprint,),
                )
                row = await cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error("Failed to fetch error by fingerprint: %s", e)
            return None
