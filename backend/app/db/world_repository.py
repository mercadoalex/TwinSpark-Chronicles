"""Repository for world_locations, world_location_history, world_npcs, world_items tables.

Encapsulates all SQL for world state data access. No game logic — just
database operations.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.db.base_repository import BaseRepository


class WorldRepository(BaseRepository):
    """Data access for world_locations, world_npcs, world_items."""

    # ── world_locations ───────────────────────────────────────────

    async def find_by_id(self, location_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT * FROM world_locations WHERE id = ?", (location_id,)
        )

    async def find_all(self, sibling_pair_id: str | None = None, limit: int = 100, **filters: Any) -> list[dict]:
        if sibling_pair_id is not None:
            return await self._db.fetch_all(
                "SELECT id, sibling_pair_id, name, description, state, discovered_at, updated_at "
                "FROM world_locations WHERE sibling_pair_id = ? "
                "ORDER BY discovered_at DESC LIMIT ?",
                (sibling_pair_id, limit),
            )
        return await self._db.fetch_all(
            "SELECT * FROM world_locations ORDER BY discovered_at DESC LIMIT ?",
            (limit,),
        )

    async def save(self, location: dict) -> None:
        await self._db.execute(
            "INSERT INTO world_locations "
            "(id, sibling_pair_id, name, description, state, discovered_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(sibling_pair_id, name) DO UPDATE SET "
            "description = excluded.description, state = excluded.state, "
            "updated_at = excluded.updated_at",
            (
                location["id"], location["sibling_pair_id"], location["name"],
                location["description"], location["state"],
                location["discovered_at"], location["updated_at"],
            ),
        )

    async def delete(self, location_id: str) -> bool:
        row = await self._db.fetch_one(
            "SELECT id FROM world_locations WHERE id = ?", (location_id,)
        )
        if not row:
            return False
        await self._db.execute("DELETE FROM world_locations WHERE id = ?", (location_id,))
        return True

    async def save_location(
        self, sibling_pair_id: str, name: str, description: str, state: str = "discovered"
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        loc_id = str(uuid4())
        await self._db.execute(
            "INSERT INTO world_locations "
            "(id, sibling_pair_id, name, description, state, discovered_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(sibling_pair_id, name) DO UPDATE SET "
            "description = excluded.description, state = excluded.state, "
            "updated_at = excluded.updated_at",
            (loc_id, sibling_pair_id, name, description, state, now, now),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_locations WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else loc_id

    async def update_location_state(
        self, location_id: str, new_state: str, new_description: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        row = await self._db.fetch_one(
            "SELECT state, description FROM world_locations WHERE id = ?",
            (location_id,),
        )
        if row:
            await self._db.execute(
                "INSERT INTO world_location_history "
                "(id, location_id, previous_state, previous_description, changed_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (str(uuid4()), location_id, row["state"], row["description"], now),
            )
        await self._db.execute(
            "UPDATE world_locations SET state = ?, description = ?, updated_at = ? WHERE id = ?",
            (new_state, new_description, now, location_id),
        )

    # ── world_npcs ────────────────────────────────────────────────

    async def save_npc(
        self, sibling_pair_id: str, name: str, description: str, relationship_level: int = 1
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        npc_id = str(uuid4())
        await self._db.execute(
            "INSERT INTO world_npcs "
            "(id, sibling_pair_id, name, description, relationship_level, met_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(sibling_pair_id, name) DO UPDATE SET "
            "description = excluded.description, relationship_level = excluded.relationship_level, "
            "updated_at = excluded.updated_at",
            (npc_id, sibling_pair_id, name, description, relationship_level, now, now),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_npcs WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else npc_id

    async def load_npcs(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT id, sibling_pair_id, name, description, relationship_level, met_at, updated_at "
            "FROM world_npcs WHERE sibling_pair_id = ? "
            "ORDER BY met_at DESC LIMIT ?",
            (sibling_pair_id, limit),
        )

    async def update_npc_relationship(self, npc_id: str, relationship_level: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE world_npcs SET relationship_level = ?, updated_at = ? WHERE id = ?",
            (relationship_level, now, npc_id),
        )

    # ── world_items ───────────────────────────────────────────────

    async def save_item(
        self, sibling_pair_id: str, name: str, description: str, session_id: str
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        item_id = str(uuid4())
        await self._db.execute(
            "INSERT INTO world_items "
            "(id, sibling_pair_id, name, description, collected_at, session_id) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(sibling_pair_id, name) DO UPDATE SET "
            "description = excluded.description, collected_at = excluded.collected_at, "
            "session_id = excluded.session_id",
            (item_id, sibling_pair_id, name, description, now, session_id),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_items WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else item_id

    async def load_items(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT id, sibling_pair_id, name, description, collected_at, session_id "
            "FROM world_items WHERE sibling_pair_id = ? "
            "ORDER BY collected_at DESC LIMIT ?",
            (sibling_pair_id, limit),
        )

    # ── aggregate ─────────────────────────────────────────────────

    async def load_world_state(self, sibling_pair_id: str) -> dict:
        locations = await self.find_all(sibling_pair_id=sibling_pair_id)
        npcs = await self.load_npcs(sibling_pair_id)
        items = await self.load_items(sibling_pair_id)
        return {"locations": locations, "npcs": npcs, "items": items}
