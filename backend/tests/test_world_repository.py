"""Unit tests for WorldRepository — verifies SQL delegation."""

import pytest
from unittest.mock import AsyncMock

from app.db.world_repository import WorldRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    return WorldRepository(mock_db)


# ── locations ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_by_id(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "loc1"}
    result = await repo.find_by_id("loc1")
    assert result == {"id": "loc1"}


@pytest.mark.asyncio
async def test_find_all_with_pair(repo, mock_db):
    await repo.find_all(sibling_pair_id="pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "world_locations" in sql and "sibling_pair_id = ?" in sql


@pytest.mark.asyncio
async def test_save_location(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "loc1"}
    loc_id = await repo.save_location("pair1", "Forest", "A dark forest")
    assert loc_id == "loc1"
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO world_locations" in sql


@pytest.mark.asyncio
async def test_update_location_state(repo, mock_db):
    mock_db.fetch_one.return_value = {"state": "discovered", "description": "old"}
    await repo.update_location_state("loc1", "explored", "new desc")
    # Should have inserted history + updated location
    assert mock_db.execute.call_count == 2


@pytest.mark.asyncio
async def test_delete_location_exists(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "loc1"}
    result = await repo.delete("loc1")
    assert result is True


@pytest.mark.asyncio
async def test_delete_location_not_found(repo, mock_db):
    result = await repo.delete("loc1")
    assert result is False


# ── NPCs ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_npc(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "npc1"}
    npc_id = await repo.save_npc("pair1", "Wizard", "A wise wizard")
    assert npc_id == "npc1"
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO world_npcs" in sql


@pytest.mark.asyncio
async def test_load_npcs(repo, mock_db):
    await repo.load_npcs("pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "world_npcs" in sql


@pytest.mark.asyncio
async def test_update_npc_relationship(repo, mock_db):
    await repo.update_npc_relationship("npc1", 5)
    sql = mock_db.execute.call_args[0][0]
    assert "UPDATE world_npcs SET relationship_level" in sql


# ── items ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_save_item(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "item1"}
    item_id = await repo.save_item("pair1", "Sword", "A magic sword", "sess1")
    assert item_id == "item1"


@pytest.mark.asyncio
async def test_load_items(repo, mock_db):
    await repo.load_items("pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "world_items" in sql


# ── aggregate ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_load_world_state(repo, mock_db):
    result = await repo.load_world_state("pair1")
    assert "locations" in result
    assert "npcs" in result
    assert "items" in result
