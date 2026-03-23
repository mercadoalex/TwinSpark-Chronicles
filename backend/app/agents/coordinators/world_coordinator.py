"""WorldCoordinator — persistent world state management."""

import logging
from typing import Dict, Callable

logger = logging.getLogger(__name__)


class WorldCoordinator:
    """Manages world state: loading, caching, formatting, extracting, persisting."""

    def __init__(self, world_db, world_extractor, world_context_formatter) -> None:
        self._world_db = world_db
        self._world_extractor = world_extractor
        self._world_context_formatter = world_context_formatter
        self._world_state_cache: Dict[str, dict] = {}

    @property
    def world_db(self):
        return self._world_db

    async def get_world_context(
        self,
        sibling_pair_id: str,
        user_input: str,
        db_initializer: Callable,
    ) -> str:
        """Load world state (with caching) and format context for storyteller."""
        try:
            if sibling_pair_id not in self._world_state_cache:
                await db_initializer()
                self._world_state_cache[sibling_pair_id] = (
                    await self._world_db.load_world_state(sibling_pair_id)
                )

            world_state = self._world_state_cache.get(sibling_pair_id, {})
            context_str = self._world_context_formatter.format_beat_context(
                world_state, user_input,
            )
            if context_str:
                locs = len(world_state.get("locations", []))
                npcs = len(world_state.get("npcs", []))
                items = len(world_state.get("items", []))
                print(f"🗺️  World context injected ({locs} locations, {npcs} NPCs, {items} items)")
            return context_str
        except Exception as e:
            logger.warning("World context injection failed: %s", e)
            return ""

    async def extract_and_persist_world_state(
        self,
        session_id: str,
        sibling_pair_id: str,
        memory_agent,
    ) -> None:
        """Extract new world entities from session moments and persist them."""
        try:
            session_moments: list[dict] = []
            if memory_agent.enabled:
                results = memory_agent.story_memories.get(
                    where={"session_id": session_id}
                )
                if results and results.get("metadatas"):
                    session_moments = results["metadatas"]

            if not session_moments:
                return

            changes = await self._world_extractor.extract(session_moments)

            for loc in changes.get("new_locations", []):
                await self._world_db.save_location(
                    sibling_pair_id,
                    loc.get("name", "Unknown"),
                    loc.get("description", ""),
                    loc.get("state", "discovered"),
                )

            for npc in changes.get("new_npcs", []):
                await self._world_db.save_npc(
                    sibling_pair_id,
                    npc.get("name", "Unknown"),
                    npc.get("description", ""),
                    npc.get("relationship_level", 1),
                )

            for item in changes.get("new_items", []):
                await self._world_db.save_item(
                    sibling_pair_id,
                    item.get("name", "Unknown"),
                    item.get("description", ""),
                    session_id,
                )

            for upd in changes.get("location_updates", []):
                loc_name = upd.get("name", "")
                if loc_name:
                    locs = await self._world_db.load_locations(sibling_pair_id)
                    for loc in locs:
                        if loc["name"] == loc_name:
                            await self._world_db.update_location_state(
                                loc["id"],
                                upd.get("new_state", loc["state"]),
                                upd.get("new_description", loc["description"]),
                            )
                            break

            for upd in changes.get("npc_updates", []):
                npc_name = upd.get("name", "")
                if npc_name:
                    npcs = await self._world_db.load_npcs(sibling_pair_id)
                    for npc in npcs:
                        if npc["name"] == npc_name:
                            await self._world_db.update_npc_relationship(
                                npc["id"],
                                upd.get("relationship_level", npc["relationship_level"]),
                            )
                            break

            self.invalidate_cache(sibling_pair_id)

            logger.info(
                "World state persisted for %s — %d locs, %d npcs, %d items, %d loc_upd, %d npc_upd",
                sibling_pair_id,
                len(changes.get("new_locations", [])),
                len(changes.get("new_npcs", [])),
                len(changes.get("new_items", [])),
                len(changes.get("location_updates", [])),
                len(changes.get("npc_updates", [])),
            )
        except Exception as e:
            logger.error("World state extraction failed: %s", e)

    def invalidate_cache(self, sibling_pair_id: str) -> None:
        """Remove cached world state for a sibling pair."""
        self._world_state_cache.pop(sibling_pair_id, None)
