"""Async persistence for cross-session world state.

Stores discovered locations, befriended NPCs, and collected items
per sibling pair. Uses the DatabaseConnection abstraction so the same
code works with SQLite (dev) and PostgreSQL (production).

Requirements: 1.1-1.6, 4.2, 4.4, 5.1-5.5, 6.2, 6.3, 6.5, 9.4
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class WorldDB:
    """CRUD for world state entities using DatabaseConnection."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    async def initialize(self) -> None:
        """No-op — schema is managed by the migration runner."""
        pass

    # ── Locations ─────────────────────────────────────────────────

    async def save_location(
        self, sibling_pair_id: str, name: str, description: str, state: str = "discovered"
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        loc_id = str(uuid4())
        await self._db.execute(
            """INSERT INTO world_locations
                (id, sibling_pair_id, name, description, state, discovered_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sibling_pair_id, name) DO UPDATE SET
                description = excluded.description,
                state = excluded.state,
                updated_at = excluded.updated_at""",
            (loc_id, sibling_pair_id, name, description, state, now, now),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_locations WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else loc_id

    async def load_locations(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._db.fetch_all(
            """SELECT id, sibling_pair_id, name, description, state, discovered_at, updated_at
            FROM world_locations WHERE sibling_pair_id = ?
            ORDER BY discovered_at DESC LIMIT ?""",
            (sibling_pair_id, limit),
        )

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
                """INSERT INTO world_location_history
                    (id, location_id, previous_state, previous_description, changed_at)
                VALUES (?, ?, ?, ?, ?)""",
                (str(uuid4()), location_id, row["state"], row["description"], now),
            )
        await self._db.execute(
            """UPDATE world_locations SET state = ?, description = ?, updated_at = ?
            WHERE id = ?""",
            (new_state, new_description, now, location_id),
        )

    # ── NPCs ──────────────────────────────────────────────────────

    async def save_npc(
        self, sibling_pair_id: str, name: str, description: str, relationship_level: int = 1
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        npc_id = str(uuid4())
        await self._db.execute(
            """INSERT INTO world_npcs
                (id, sibling_pair_id, name, description, relationship_level, met_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(sibling_pair_id, name) DO UPDATE SET
                description = excluded.description,
                relationship_level = excluded.relationship_level,
                updated_at = excluded.updated_at""",
            (npc_id, sibling_pair_id, name, description, relationship_level, now, now),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_npcs WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else npc_id

    async def load_npcs(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._db.fetch_all(
            """SELECT id, sibling_pair_id, name, description, relationship_level, met_at, updated_at
            FROM world_npcs WHERE sibling_pair_id = ?
            ORDER BY met_at DESC LIMIT ?""",
            (sibling_pair_id, limit),
        )

    async def update_npc_relationship(self, npc_id: str, relationship_level: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            "UPDATE world_npcs SET relationship_level = ?, updated_at = ? WHERE id = ?",
            (relationship_level, now, npc_id),
        )

    # ── Items ─────────────────────────────────────────────────────

    async def save_item(
        self, sibling_pair_id: str, name: str, description: str, session_id: str
    ) -> str:
        now = datetime.now(timezone.utc).isoformat()
        item_id = str(uuid4())
        await self._db.execute(
            """INSERT INTO world_items
                (id, sibling_pair_id, name, description, collected_at, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(sibling_pair_id, name) DO UPDATE SET
                description = excluded.description,
                collected_at = excluded.collected_at,
                session_id = excluded.session_id""",
            (item_id, sibling_pair_id, name, description, now, session_id),
        )
        row = await self._db.fetch_one(
            "SELECT id FROM world_items WHERE sibling_pair_id = ? AND name = ?",
            (sibling_pair_id, name),
        )
        return row["id"] if row else item_id

    async def load_items(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._db.fetch_all(
            """SELECT id, sibling_pair_id, name, description, collected_at, session_id
            FROM world_items WHERE sibling_pair_id = ?
            ORDER BY collected_at DESC LIMIT ?""",
            (sibling_pair_id, limit),
        )

    # ── Aggregate ─────────────────────────────────────────────────

    async def load_world_state(self, sibling_pair_id: str) -> dict:
        locations = await self.load_locations(sibling_pair_id)
        npcs = await self.load_npcs(sibling_pair_id)
        items = await self.load_items(sibling_pair_id)
        return {"locations": locations, "npcs": npcs, "items": items}
