"""Unit tests for SessionService (Task 2.1)."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app.services.session_service import SessionService


def _make_snapshot(pair_id="Ale:Sofi", **overrides):
    """Build a minimal valid snapshot dict."""
    base = {
        "sibling_pair_id": pair_id,
        "character_profiles": {"c1_name": "Ale", "c2_name": "Sofi"},
        "story_history": [{"narration": "Once upon a time..."}],
        "current_beat": {"beat": 1},
        "session_metadata": {"language": "en", "story_beat_count": 1},
    }
    base.update(overrides)
    return base


class TestSaveSnapshot:
    @pytest.mark.asyncio
    async def test_save_returns_id_and_updated_at(self, session_service):
        result = await session_service.save_snapshot(_make_snapshot())
        assert "id" in result
        assert "updated_at" in result
        assert len(result["id"]) > 0
        assert len(result["updated_at"]) > 0

    @pytest.mark.asyncio
    async def test_save_with_none_current_beat(self, session_service):
        snap = _make_snapshot(current_beat=None)
        result = await session_service.save_snapshot(snap)
        assert "id" in result

    @pytest.mark.asyncio
    async def test_save_with_empty_story_history(self, session_service):
        snap = _make_snapshot(story_history=[])
        result = await session_service.save_snapshot(snap)
        loaded = await session_service.load_snapshot("Ale:Sofi")
        assert loaded["story_history"] == []


class TestLoadSnapshot:
    @pytest.mark.asyncio
    async def test_load_nonexistent_returns_none(self, session_service):
        result = await session_service.load_snapshot("nobody:here")
        assert result is None

    @pytest.mark.asyncio
    async def test_load_returns_parsed_json(self, session_service):
        snap = _make_snapshot()
        await session_service.save_snapshot(snap)
        loaded = await session_service.load_snapshot("Ale:Sofi")
        assert loaded is not None
        assert loaded["character_profiles"] == snap["character_profiles"]
        assert loaded["story_history"] == snap["story_history"]
        assert loaded["current_beat"] == snap["current_beat"]
        assert loaded["session_metadata"] == snap["session_metadata"]

    @pytest.mark.asyncio
    async def test_load_with_none_current_beat(self, session_service):
        await session_service.save_snapshot(_make_snapshot(current_beat=None))
        loaded = await session_service.load_snapshot("Ale:Sofi")
        assert loaded["current_beat"] is None

    @pytest.mark.asyncio
    async def test_corrupted_json_returns_none_and_deletes(self, session_service, db):
        # Insert a row with invalid JSON directly
        await db.execute(
            """INSERT INTO session_snapshots
                (id, sibling_pair_id, character_profiles, story_history,
                 current_beat, session_metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("bad-id", "corrupt:pair", "{not valid json", "[]", None, "{}", "t", "t"),
        )
        result = await session_service.load_snapshot("corrupt:pair")
        assert result is None
        # Row should be deleted
        check = await db.fetch_one(
            "SELECT id FROM session_snapshots WHERE sibling_pair_id = ?",
            ("corrupt:pair",),
        )
        assert check is None


class TestUpsert:
    @pytest.mark.asyncio
    async def test_second_save_overwrites_first(self, session_service):
        snap1 = _make_snapshot(session_metadata={"language": "en", "story_beat_count": 1})
        snap2 = _make_snapshot(session_metadata={"language": "es", "story_beat_count": 5})
        await session_service.save_snapshot(snap1)
        await session_service.save_snapshot(snap2)
        loaded = await session_service.load_snapshot("Ale:Sofi")
        assert loaded["session_metadata"]["language"] == "es"
        assert loaded["session_metadata"]["story_beat_count"] == 5

    @pytest.mark.asyncio
    async def test_upsert_keeps_single_row(self, session_service, db):
        for i in range(3):
            await session_service.save_snapshot(
                _make_snapshot(session_metadata={"language": "en", "story_beat_count": i})
            )
        rows = await db.fetch_all(
            "SELECT id FROM session_snapshots WHERE sibling_pair_id = ?",
            ("Ale:Sofi",),
        )
        assert len(rows) == 1


class TestDeleteSnapshot:
    @pytest.mark.asyncio
    async def test_delete_existing_returns_true(self, session_service):
        await session_service.save_snapshot(_make_snapshot())
        assert await session_service.delete_snapshot("Ale:Sofi") is True

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, session_service):
        assert await session_service.delete_snapshot("nobody:here") is False

    @pytest.mark.asyncio
    async def test_delete_then_load_returns_none(self, session_service):
        await session_service.save_snapshot(_make_snapshot())
        await session_service.delete_snapshot("Ale:Sofi")
        assert await session_service.load_snapshot("Ale:Sofi") is None


class TestCleanupStale:
    @pytest.mark.asyncio
    async def test_cleanup_deletes_old_snapshots(self, session_service, db):
        old_time = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
        await db.execute(
            """INSERT INTO session_snapshots
                (id, sibling_pair_id, character_profiles, story_history,
                 current_beat, session_metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("old-id", "old:pair", '{"a":1}', "[]", None, '{"language":"en"}', old_time, old_time),
        )
        count = await session_service.cleanup_stale(max_age_days=30)
        assert count == 1
        assert await session_service.load_snapshot("old:pair") is None

    @pytest.mark.asyncio
    async def test_cleanup_preserves_recent_snapshots(self, session_service):
        await session_service.save_snapshot(_make_snapshot())
        count = await session_service.cleanup_stale(max_age_days=30)
        assert count == 0
        assert await session_service.load_snapshot("Ale:Sofi") is not None

    @pytest.mark.asyncio
    async def test_cleanup_returns_zero_when_empty(self, session_service):
        count = await session_service.cleanup_stale()
        assert count == 0
