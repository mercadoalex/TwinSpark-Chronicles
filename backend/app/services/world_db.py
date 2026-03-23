"""Async persistence for cross-session world state.

Stores discovered locations, befriended NPCs, and collected items
per sibling pair. Delegates all SQL to WorldRepository.

Requirements: 1.1-1.6, 4.2, 4.4, 5.1-5.5, 6.2, 6.3, 6.5, 9.4
"""

from __future__ import annotations

import logging

from app.db.connection import DatabaseConnection
from app.db.world_repository import WorldRepository

logger = logging.getLogger(__name__)


class WorldDB:
    """CRUD for world state entities — thin facade over WorldRepository."""

    def __init__(self, db: DatabaseConnection, world_repo: WorldRepository | None = None) -> None:
        self._db = db
        self._repo = world_repo or WorldRepository(db)

    async def initialize(self) -> None:
        """No-op — schema is managed by the migration runner."""
        pass

    # ── Locations ─────────────────────────────────────────────────

    async def save_location(
        self, sibling_pair_id: str, name: str, description: str, state: str = "discovered"
    ) -> str:
        return await self._repo.save_location(sibling_pair_id, name, description, state)

    async def load_locations(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._repo.find_all(sibling_pair_id=sibling_pair_id, limit=limit)

    async def update_location_state(
        self, location_id: str, new_state: str, new_description: str
    ) -> None:
        await self._repo.update_location_state(location_id, new_state, new_description)

    # ── NPCs ──────────────────────────────────────────────────────

    async def save_npc(
        self, sibling_pair_id: str, name: str, description: str, relationship_level: int = 1
    ) -> str:
        return await self._repo.save_npc(sibling_pair_id, name, description, relationship_level)

    async def load_npcs(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._repo.load_npcs(sibling_pair_id, limit)

    async def update_npc_relationship(self, npc_id: str, relationship_level: int) -> None:
        await self._repo.update_npc_relationship(npc_id, relationship_level)

    # ── Items ─────────────────────────────────────────────────────

    async def save_item(
        self, sibling_pair_id: str, name: str, description: str, session_id: str
    ) -> str:
        return await self._repo.save_item(sibling_pair_id, name, description, session_id)

    async def load_items(self, sibling_pair_id: str, limit: int = 100) -> list[dict]:
        return await self._repo.load_items(sibling_pair_id, limit)

    # ── Aggregate ─────────────────────────────────────────────────

    async def load_world_state(self, sibling_pair_id: str) -> dict:
        return await self._repo.load_world_state(sibling_pair_id)
