"""Repository for session_snapshots table.

Encapsulates all SQL for session snapshot data access. No JSON
serialization/deserialization — that stays in SessionService.
"""

from __future__ import annotations

from typing import Any

from app.db.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    """Data access for session_snapshots table."""

    async def find_by_id(self, snapshot_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT * FROM session_snapshots WHERE id = ?", (snapshot_id,)
        )

    async def find_all(self, sibling_pair_id: str | None = None, **filters: Any) -> list[dict]:
        if sibling_pair_id is not None:
            return await self._db.fetch_all(
                "SELECT * FROM session_snapshots WHERE sibling_pair_id = ?",
                (sibling_pair_id,),
            )
        return await self._db.fetch_all("SELECT * FROM session_snapshots")

    async def find_by_pair_id(self, sibling_pair_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT id, sibling_pair_id, character_profiles, story_history, "
            "current_beat, session_metadata, created_at, updated_at "
            "FROM session_snapshots WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )

    async def save(self, snapshot: dict) -> None:
        await self._db.execute(
            "INSERT INTO session_snapshots "
            "(id, sibling_pair_id, character_profiles, story_history, "
            "current_beat, session_metadata, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(sibling_pair_id) DO UPDATE SET "
            "character_profiles = excluded.character_profiles, "
            "story_history = excluded.story_history, "
            "current_beat = excluded.current_beat, "
            "session_metadata = excluded.session_metadata, "
            "updated_at = excluded.updated_at",
            (
                snapshot["id"], snapshot["sibling_pair_id"],
                snapshot["character_profiles"], snapshot["story_history"],
                snapshot["current_beat"], snapshot["session_metadata"],
                snapshot["created_at"], snapshot["updated_at"],
            ),
        )

    async def find_id_by_pair(self, sibling_pair_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT id, updated_at FROM session_snapshots WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )

    async def delete(self, snapshot_id: str) -> bool:
        row = await self._db.fetch_one(
            "SELECT id FROM session_snapshots WHERE id = ?", (snapshot_id,)
        )
        if not row:
            return False
        await self._db.execute(
            "DELETE FROM session_snapshots WHERE id = ?", (snapshot_id,)
        )
        return True

    async def delete_by_pair_id(self, sibling_pair_id: str) -> bool:
        row = await self._db.fetch_one(
            "SELECT id FROM session_snapshots WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        if not row:
            return False
        await self._db.execute(
            "DELETE FROM session_snapshots WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        return True

    async def find_stale(self, threshold_iso: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT id FROM session_snapshots WHERE updated_at < ?",
            (threshold_iso,),
        )

    async def delete_stale(self, threshold_iso: str) -> int:
        stale = await self.find_stale(threshold_iso)
        count = len(stale)
        if count > 0:
            await self._db.execute(
                "DELETE FROM session_snapshots WHERE updated_at < ?",
                (threshold_iso,),
            )
        return count
