"""Unit tests for WorldCoordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agents.coordinators.world_coordinator import WorldCoordinator


def _make_wc():
    """Create a WorldCoordinator with mocked dependencies."""
    world_db = MagicMock()
    world_db.load_world_state = AsyncMock(return_value={
        "locations": [{"name": "Forest"}],
        "npcs": [],
        "items": [],
    })
    world_db.save_location = AsyncMock()
    world_db.save_npc = AsyncMock()
    world_db.save_item = AsyncMock()
    world_db.load_locations = AsyncMock(return_value=[])
    world_db.load_npcs = AsyncMock(return_value=[])
    world_db.update_location_state = AsyncMock()
    world_db.update_npc_relationship = AsyncMock()

    extractor = MagicMock()
    extractor.extract = AsyncMock(return_value={
        "new_locations": [], "new_npcs": [], "new_items": [],
        "location_updates": [], "npc_updates": [],
    })

    formatter = MagicMock()
    formatter.format_beat_context = MagicMock(return_value="world context")

    return WorldCoordinator(world_db, extractor, formatter)


class TestGetWorldContext:
    """get_world_context loads, caches, and formats world state."""

    @pytest.mark.asyncio
    async def test_cache_miss_loads_from_db(self):
        wc = _make_wc()
        db_init = AsyncMock()
        result = await wc.get_world_context("pair1", "explore", db_init)
        assert result == "world context"
        db_init.assert_called_once()
        wc._world_db.load_world_state.assert_called_once_with("pair1")

    @pytest.mark.asyncio
    async def test_cache_hit_skips_db(self):
        wc = _make_wc()
        wc._world_state_cache["pair1"] = {"locations": [], "npcs": [], "items": []}
        db_init = AsyncMock()
        await wc.get_world_context("pair1", "explore", db_init)
        db_init.assert_not_called()
        wc._world_db.load_world_state.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_on_error(self):
        wc = _make_wc()
        wc._world_db.load_world_state = AsyncMock(side_effect=Exception("db error"))
        result = await wc.get_world_context("pair1", "go", AsyncMock())
        assert result == ""


class TestExtractAndPersist:
    """extract_and_persist_world_state extracts and saves world changes."""

    @pytest.mark.asyncio
    async def test_persists_new_entities(self):
        wc = _make_wc()
        wc._world_extractor.extract = AsyncMock(return_value={
            "new_locations": [{"name": "Cave", "description": "Dark cave", "state": "discovered"}],
            "new_npcs": [{"name": "Wizard", "description": "Old wizard", "relationship_level": 2}],
            "new_items": [{"name": "Sword", "description": "Magic sword"}],
            "location_updates": [],
            "npc_updates": [],
        })
        memory = MagicMock(enabled=True)
        memory.story_memories.get.return_value = {"metadatas": [{"session_id": "s1"}]}

        await wc.extract_and_persist_world_state("s1", "pair1", memory)

        wc._world_db.save_location.assert_called_once()
        wc._world_db.save_npc.assert_called_once()
        wc._world_db.save_item.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidates_cache_after_extract(self):
        wc = _make_wc()
        wc._world_state_cache["pair1"] = {"locations": []}
        memory = MagicMock(enabled=True)
        memory.story_memories.get.return_value = {"metadatas": [{"session_id": "s1"}]}

        await wc.extract_and_persist_world_state("s1", "pair1", memory)
        assert "pair1" not in wc._world_state_cache

    @pytest.mark.asyncio
    async def test_no_op_when_no_moments(self):
        wc = _make_wc()
        memory = MagicMock(enabled=True)
        memory.story_memories.get.return_value = {"metadatas": []}
        await wc.extract_and_persist_world_state("s1", "pair1", memory)
        wc._world_extractor.extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_resilient_to_errors(self):
        wc = _make_wc()
        wc._world_extractor.extract = AsyncMock(side_effect=Exception("boom"))
        memory = MagicMock(enabled=True)
        memory.story_memories.get.return_value = {"metadatas": [{"session_id": "s1"}]}
        await wc.extract_and_persist_world_state("s1", "pair1", memory)  # no raise


class TestWorldDbProperty:
    """world_db property exposes the underlying WorldDB."""

    def test_world_db_property(self):
        wc = _make_wc()
        assert wc.world_db is wc._world_db


class TestInvalidateCache:
    """invalidate_cache removes cached state."""

    def test_removes_cached_entry(self):
        wc = _make_wc()
        wc._world_state_cache["pair1"] = {"locations": []}
        wc.invalidate_cache("pair1")
        assert "pair1" not in wc._world_state_cache

    def test_no_error_on_missing_key(self):
        wc = _make_wc()
        wc.invalidate_cache("nonexistent")  # no raise
