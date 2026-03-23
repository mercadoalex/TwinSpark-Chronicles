"""Unit tests for VoiceRecordingRepository — verifies SQL delegation."""

import pytest
from unittest.mock import AsyncMock

from app.db.voice_recording_repository import VoiceRecordingRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    return VoiceRecordingRepository(mock_db)


@pytest.mark.asyncio
async def test_find_by_id(repo, mock_db):
    mock_db.fetch_one.return_value = {"recording_id": "r1"}
    result = await repo.find_by_id("r1")
    assert result == {"recording_id": "r1"}
    sql = mock_db.fetch_one.call_args[0][0]
    assert "voice_recordings" in sql and "recording_id = ?" in sql


@pytest.mark.asyncio
async def test_find_all_with_filters(repo, mock_db):
    await repo.find_all(sibling_pair_id="pair1", message_type="greeting")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "sibling_pair_id = ?" in sql
    assert "message_type = ?" in sql
    assert "ORDER BY recorder_name ASC, created_at ASC" in sql


@pytest.mark.asyncio
async def test_find_all_no_filters(repo, mock_db):
    await repo.find_all()
    sql = mock_db.fetch_all.call_args[0][0]
    assert "WHERE 1=1" in sql
    assert "sibling_pair_id = ?" not in sql


@pytest.mark.asyncio
async def test_save_recording(repo, mock_db):
    rec = {
        "recording_id": "r1", "sibling_pair_id": "pair1",
        "recorder_name": "Mom", "relationship": "parent",
        "message_type": "greeting", "language": "en",
        "duration_seconds": 5.0, "wav_path": "/tmp/r1.wav",
        "mp3_path": "/tmp/r1.mp3", "created_at": "2025-01-01T00:00:00",
    }
    await repo.save(rec)
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO voice_recordings" in sql


@pytest.mark.asyncio
async def test_delete_exists(repo, mock_db):
    mock_db.fetch_one.return_value = {"recording_id": "r1"}
    result = await repo.delete("r1")
    assert result is True


@pytest.mark.asyncio
async def test_delete_not_found(repo, mock_db):
    result = await repo.delete("r1")
    assert result is False


@pytest.mark.asyncio
async def test_count_by_pair(repo, mock_db):
    mock_db.fetch_one.return_value = {"cnt": 7}
    result = await repo.count_by_pair("pair1")
    assert result == 7


@pytest.mark.asyncio
async def test_count_by_type(repo, mock_db):
    mock_db.fetch_one.return_value = {"cnt": 3}
    result = await repo.count_by_type("pair1", "voice_command")
    assert result == 3


@pytest.mark.asyncio
async def test_find_matching_exact(repo, mock_db):
    mock_db.fetch_one.return_value = {"recording_id": "r1"}
    result = await repo.find_matching("pair1", "greeting", "en")
    assert result is not None


@pytest.mark.asyncio
async def test_find_matching_fallback(repo, mock_db):
    mock_db.fetch_one.side_effect = [None, {"recording_id": "r2"}]
    result = await repo.find_matching("pair1", "greeting", "en")
    assert result == {"recording_id": "r2"}


@pytest.mark.asyncio
async def test_get_voice_commands(repo, mock_db):
    await repo.get_voice_commands("pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "message_type = ?" in sql
    assert "command_phrase IS NOT NULL" in sql


@pytest.mark.asyncio
async def test_get_cloning_stats(repo, mock_db):
    await repo.get_cloning_stats("pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "GROUP BY recorder_name" in sql


@pytest.mark.asyncio
async def test_save_event(repo, mock_db):
    event = {
        "event_id": "e1", "sibling_pair_id": "pair1",
        "recording_id": "r1", "event_type": "created",
        "created_at": "2025-01-01T00:00:00",
    }
    await repo.save_event(event)
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO voice_recording_events" in sql


@pytest.mark.asyncio
async def test_delete_all_by_pair(repo, mock_db):
    await repo.delete_all_by_pair("pair1")
    sql = mock_db.execute.call_args[0][0]
    assert "DELETE FROM voice_recordings" in sql
    assert "sibling_pair_id = ?" in sql
