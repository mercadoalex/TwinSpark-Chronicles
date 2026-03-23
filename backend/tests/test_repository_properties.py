"""Property-based tests for the Repository Pattern.

Covers:
- 1.3: BaseRepository subclass instantiation
- 2.3: PhotoRepository round-trip (save → find_by_id)
- 3.3: VoiceRecordingRepository filter consistency
- 4.3: WorldRepository location round-trip (save_location → find_all)
- 5.3: SessionRepository delete_by_pair_id idempotency
"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from hypothesis import given, settings, strategies as st

from app.db.base_repository import BaseRepository
from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.db.photo_repository import PhotoRepository
from app.db.voice_recording_repository import VoiceRecordingRepository
from app.db.world_repository import WorldRepository
from app.db.session_repository import SessionRepository


# ── helpers ───────────────────────────────────────────────────

_safe_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-",
    min_size=1,
    max_size=20,
)

_iso_ts = st.builds(
    lambda dt: dt.isoformat(),
    st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
        timezones=st.just(timezone.utc),
    ),
)


async def _fresh_db() -> DatabaseConnection:
    """Create an in-memory SQLite DB with all migrations applied."""
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    return conn


# ── 1.3  BaseRepository: any complete subclass can be instantiated ─

# Strategy: generate a random set of 4 method names (the abstract ones)
# and dynamically build a subclass that implements them all.

_METHOD_NAMES = ["find_by_id", "find_all", "save", "delete"]


@settings(max_examples=20)
@given(extra_attr=_safe_text)
def test_any_complete_subclass_instantiates(extra_attr):
    """Any subclass implementing all 4 abstract methods can be instantiated."""

    # Dynamically create a concrete subclass with an extra attribute
    ns = {
        "find_by_id": lambda self, entity_id: None,
        "find_all": lambda self, **filters: [],
        "save": lambda self, entity: None,
        "delete": lambda self, entity_id: False,
        extra_attr: "custom",
    }
    ConcreteRepo = type("ConcreteRepo", (BaseRepository,), ns)
    repo = ConcreteRepo(db=AsyncMock())
    assert repo._db is not None
    assert getattr(repo, extra_attr) == "custom"


# ── 2.3  PhotoRepository: save → find_by_id round-trip ────────

@st.composite
def st_photo(draw):
    return {
        "photo_id": draw(_safe_text),
        "sibling_pair_id": draw(_safe_text),
        "filename": draw(_safe_text) + ".jpg",
        "file_path": "/tmp/" + draw(_safe_text),
        "file_size_bytes": draw(st.integers(min_value=1, max_value=10_000_000)),
        "width": draw(st.integers(min_value=1, max_value=4096)),
        "height": draw(st.integers(min_value=1, max_value=4096)),
        "status": draw(st.sampled_from(["pending", "safe", "rejected"])),
        "uploaded_at": draw(_iso_ts),
        "content_hash": draw(_safe_text),
    }


@settings(max_examples=20)
@given(photo=st_photo())
@pytest.mark.asyncio
async def test_photo_round_trip(photo):
    """save(photo) then find_by_id returns equivalent data."""
    db = await _fresh_db()
    try:
        repo = PhotoRepository(db)
        await repo.save(photo)
        row = await repo.find_by_id(photo["photo_id"])
        assert row is not None
        assert row["photo_id"] == photo["photo_id"]
        assert row["sibling_pair_id"] == photo["sibling_pair_id"]
        assert row["filename"] == photo["filename"]
        assert row["file_path"] == photo["file_path"]
        assert row["file_size_bytes"] == photo["file_size_bytes"]
        assert row["width"] == photo["width"]
        assert row["height"] == photo["height"]
        assert row["status"] == photo["status"]
        assert row["content_hash"] == photo["content_hash"]
    finally:
        await db.close()


# ── 3.3  VoiceRecordingRepository: filter consistency ─────────

_message_types = st.sampled_from(["greeting", "farewell", "encouragement", "voice_command"])


@st.composite
def st_voice_recording(draw, sibling_pair_id=None, message_type=None):
    return {
        "recording_id": str(uuid4()),
        "sibling_pair_id": sibling_pair_id or draw(_safe_text),
        "recorder_name": draw(st.sampled_from(["Mom", "Dad", "Grandma"])),
        "relationship": draw(st.sampled_from(["parent", "grandparent"])),
        "message_type": message_type or draw(_message_types),
        "language": draw(st.sampled_from(["en", "es", "fr"])),
        "duration_seconds": draw(st.floats(min_value=0.5, max_value=30.0)),
        "wav_path": "/tmp/" + draw(_safe_text) + ".wav",
        "mp3_path": "/tmp/" + draw(_safe_text) + ".mp3",
        "created_at": draw(_iso_ts),
    }


@settings(max_examples=20)
@given(
    target_type=_message_types,
    data=st.data(),
)
@pytest.mark.asyncio
async def test_voice_filter_consistency(target_type, data):
    """find_all(message_type=t) results all have message_type == t."""
    db = await _fresh_db()
    try:
        repo = VoiceRecordingRepository(db)
        pair_id = "test-pair"

        # Insert a mix of recordings: some matching, some not
        num_matching = data.draw(st.integers(min_value=1, max_value=4))
        num_other = data.draw(st.integers(min_value=0, max_value=3))

        for _ in range(num_matching):
            rec = data.draw(st_voice_recording(sibling_pair_id=pair_id, message_type=target_type))
            await repo.save(rec)

        other_types = [t for t in ["greeting", "farewell", "encouragement", "voice_command"] if t != target_type]
        for _ in range(num_other):
            other_type = data.draw(st.sampled_from(other_types))
            rec = data.draw(st_voice_recording(sibling_pair_id=pair_id, message_type=other_type))
            await repo.save(rec)

        results = await repo.find_all(sibling_pair_id=pair_id, message_type=target_type)
        assert len(results) == num_matching
        for row in results:
            assert row["message_type"] == target_type
    finally:
        await db.close()


# ── 4.3  WorldRepository: save_location → find_all round-trip ─


@settings(max_examples=20)
@given(
    name=_safe_text,
    description=st.text(min_size=1, max_size=50),
    state=st.sampled_from(["discovered", "explored", "conquered"]),
)
@pytest.mark.asyncio
async def test_world_location_round_trip(name, description, state):
    """save_location then find_all includes the saved location."""
    db = await _fresh_db()
    try:
        repo = WorldRepository(db)
        pair_id = "test-pair"

        loc_id = await repo.save_location(pair_id, name, description, state)
        assert loc_id is not None

        locations = await repo.find_all(sibling_pair_id=pair_id)
        names = [loc["name"] for loc in locations]
        assert name in names

        # Verify the matching location has correct data
        match = next(loc for loc in locations if loc["name"] == name)
        assert match["description"] == description
        assert match["state"] == state
    finally:
        await db.close()


# ── 5.3  SessionRepository: delete_by_pair_id idempotency ────


@settings(max_examples=20)
@given(pair_id=_safe_text)
@pytest.mark.asyncio
async def test_session_delete_idempotency(pair_id):
    """delete_by_pair_id twice: second call returns False."""
    db = await _fresh_db()
    try:
        repo = SessionRepository(db)
        snap_id = str(uuid4())
        now = datetime.now(timezone.utc).isoformat()

        await repo.save({
            "id": snap_id,
            "sibling_pair_id": pair_id,
            "character_profiles": "{}",
            "story_history": "[]",
            "current_beat": None,
            "session_metadata": "{}",
            "created_at": now,
            "updated_at": now,
        })

        first = await repo.delete_by_pair_id(pair_id)
        assert first is True

        second = await repo.delete_by_pair_id(pair_id)
        assert second is False
    finally:
        await db.close()
