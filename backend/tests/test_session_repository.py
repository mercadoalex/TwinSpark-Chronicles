"""Unit tests for SessionRepository — verifies SQL delegation."""

import pytest
from unittest.mock import AsyncMock

from app.db.session_repository import SessionRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    return SessionRepository(mock_db)


@pytest.mark.asyncio
async def test_find_by_id(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "s1"}
    result = await repo.find_by_id("s1")
    assert result == {"id": "s1"}


@pytest.mark.asyncio
async def test_find_by_pair_id(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "s1", "sibling_pair_id": "pair1"}
    result = await repo.find_by_pair_id("pair1")
    assert result is not None
    sql = mock_db.fetch_one.call_args[0][0]
    assert "sibling_pair_id = ?" in sql


@pytest.mark.asyncio
async def test_find_all_with_pair(repo, mock_db):
    await repo.find_all(sibling_pair_id="pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "sibling_pair_id = ?" in sql


@pytest.mark.asyncio
async def test_save_snapshot(repo, mock_db):
    snap = {
        "id": "s1", "sibling_pair_id": "pair1",
        "character_profiles": "{}", "story_history": "[]",
        "current_beat": None, "session_metadata": "{}",
        "created_at": "2025-01-01T00:00:00", "updated_at": "2025-01-01T00:00:00",
    }
    await repo.save(snap)
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO session_snapshots" in sql
    assert "ON CONFLICT(sibling_pair_id)" in sql


@pytest.mark.asyncio
async def test_find_id_by_pair(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "s1", "updated_at": "2025-01-01"}
    result = await repo.find_id_by_pair("pair1")
    assert result == {"id": "s1", "updated_at": "2025-01-01"}


@pytest.mark.asyncio
async def test_delete_exists(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "s1"}
    result = await repo.delete("s1")
    assert result is True


@pytest.mark.asyncio
async def test_delete_not_found(repo, mock_db):
    result = await repo.delete("s1")
    assert result is False


@pytest.mark.asyncio
async def test_delete_by_pair_id_exists(repo, mock_db):
    mock_db.fetch_one.return_value = {"id": "s1"}
    result = await repo.delete_by_pair_id("pair1")
    assert result is True


@pytest.mark.asyncio
async def test_delete_by_pair_id_not_found(repo, mock_db):
    result = await repo.delete_by_pair_id("pair1")
    assert result is False


@pytest.mark.asyncio
async def test_find_stale(repo, mock_db):
    await repo.find_stale("2025-01-01T00:00:00")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "updated_at < ?" in sql


@pytest.mark.asyncio
async def test_delete_stale(repo, mock_db):
    mock_db.fetch_all.return_value = [{"id": "s1"}, {"id": "s2"}]
    count = await repo.delete_stale("2025-01-01T00:00:00")
    assert count == 2
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_stale_none(repo, mock_db):
    count = await repo.delete_stale("2025-01-01T00:00:00")
    assert count == 0
    mock_db.execute.assert_not_called()
