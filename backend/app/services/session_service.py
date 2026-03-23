"""Async persistence for session snapshots.

Stores and retrieves session snapshots per sibling pair so that
siblings can resume their story where they left off. Delegates all
SQL to SessionRepository.

Requirements: 1.1-1.5, 8.1-8.4
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.db.connection import DatabaseConnection
from app.db.session_repository import SessionRepository

logger = logging.getLogger(__name__)


class SessionService:
    """CRUD for session snapshots using SessionRepository."""

    def __init__(self, db: DatabaseConnection, session_repo: SessionRepository | None = None) -> None:
        self._db = db
        self._repo = session_repo or SessionRepository(db)

    async def save_snapshot(self, snapshot: dict) -> dict:
        """Upsert a session snapshot. Returns ``{id, updated_at}``."""
        now = datetime.now(timezone.utc).isoformat()
        snap_id = str(uuid4())

        character_profiles = json.dumps(snapshot["character_profiles"])
        story_history = json.dumps(snapshot["story_history"])
        current_beat = json.dumps(snapshot["current_beat"]) if snapshot.get("current_beat") is not None else None
        session_metadata = json.dumps(snapshot["session_metadata"])
        sibling_pair_id = snapshot["sibling_pair_id"]

        await self._repo.save({
            "id": snap_id,
            "sibling_pair_id": sibling_pair_id,
            "character_profiles": character_profiles,
            "story_history": story_history,
            "current_beat": current_beat,
            "session_metadata": session_metadata,
            "created_at": now,
            "updated_at": now,
        })

        row = await self._repo.find_id_by_pair(sibling_pair_id)
        return {"id": row["id"], "updated_at": row["updated_at"]} if row else {"id": snap_id, "updated_at": now}

    async def load_snapshot(self, sibling_pair_id: str) -> dict | None:
        """Load the active snapshot for a sibling pair, or ``None``."""
        row = await self._repo.find_by_pair_id(sibling_pair_id)
        if row is None:
            return None

        try:
            return {
                "id": row["id"],
                "sibling_pair_id": row["sibling_pair_id"],
                "character_profiles": json.loads(row["character_profiles"]),
                "story_history": json.loads(row["story_history"]),
                "current_beat": json.loads(row["current_beat"]) if row["current_beat"] is not None else None,
                "session_metadata": json.loads(row["session_metadata"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        except json.JSONDecodeError:
            logger.warning(
                "Corrupted JSON in session snapshot for pair %s — deleting row",
                sibling_pair_id,
            )
            await self._repo.delete_by_pair_id(sibling_pair_id)
            return None

    async def delete_snapshot(self, sibling_pair_id: str) -> bool:
        """Delete the active snapshot. Returns ``True`` if a row was deleted."""
        return await self._repo.delete_by_pair_id(sibling_pair_id)

    async def cleanup_stale(self, max_age_days: int = 30) -> int:
        """Delete snapshots older than *max_age_days*. Returns count deleted."""
        threshold = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        count = await self._repo.delete_stale(threshold)
        if count > 0:
            logger.info("Cleaned up %d stale session snapshot(s) older than %d days", count, max_age_days)
        return count
