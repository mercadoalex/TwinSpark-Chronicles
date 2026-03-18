"""Checkpoint smoke tests — verify Layer 1 and Layer 2 services can be
imported and perform basic operations with an in-memory SiblingDB.

Task 6: Checkpoint - Verify Layer 1 and Layer 2 services
"""

import asyncio

import pytest

from app.models.multimodal import (
    EmotionCategory,
    EmotionResult,
    MultimodalInputEvent,
    TranscriptResult,
)
from app.models.sibling import PersonalityProfile, RelationshipModel
from app.services.personality_engine import PersonalityEngine
from app.services.relationship_mapper import RelationshipMapper
from app.services.sibling_db import SiblingDB
from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner


def _run(coro):
    """Run an async coroutine synchronously."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _make_db():
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    sdb = SiblingDB(conn)
    return sdb


# ── Import verification ──────────────────────────────────────────────


def test_imports():
    """Verify all Layer 1 and Layer 2 classes can be imported."""
    assert PersonalityEngine is not None
    assert RelationshipMapper is not None
    assert SiblingDB is not None
    assert PersonalityProfile is not None
    assert RelationshipModel is not None


# ── SiblingDB smoke tests ────────────────────────────────────────────


def test_sibling_db_initialize():
    """SiblingDB initializes tables without error."""
    async def _test():
        db = await _make_db()
        # calling again is idempotent
        await db.initialize()

    _run(_test())


def test_sibling_db_save_load_profile():
    """Round-trip a profile through SiblingDB."""
    async def _test():
        db = await _make_db()
        profile = PersonalityProfile(child_id="child-a")
        await db.save_profile("child-a", profile.model_dump_json())
        loaded_json = await db.load_profile("child-a")
        assert loaded_json is not None
        loaded = PersonalityProfile.model_validate_json(loaded_json)
        assert loaded.child_id == "child-a"

    _run(_test())


def test_sibling_db_load_missing_returns_none():
    """Loading a non-existent record returns None."""
    async def _test():
        db = await _make_db()
        assert await db.load_profile("nonexistent") is None
        assert await db.load_relationship("nonexistent") is None
        assert await db.load_skill_map("nonexistent") is None

    _run(_test())


# ── PersonalityEngine smoke tests ────────────────────────────────────


def test_personality_engine_load_default():
    """Loading a profile for an unknown child returns an emerging default."""
    async def _test():
        db = await _make_db()
        engine = PersonalityEngine(db)
        profile = await engine.load_profile("new-child")
        assert profile.child_id == "new-child"
        assert profile.is_emerging()
        assert profile.status == "emerging"

    _run(_test())


def test_personality_engine_update_from_event():
    """update_from_event processes emotions and increments interactions."""
    async def _test():
        db = await _make_db()
        engine = PersonalityEngine(db)
        event = MultimodalInputEvent(
            session_id="sess-1",
            timestamp="2024-01-01T00:00:00+00:00",
            transcript=TranscriptResult(
                text="Why is the sky blue?",
                confidence=0.9,
                language="en-US",
                is_empty=False,
            ),
            emotions=[
                EmotionResult(
                    face_id=0,
                    emotion=EmotionCategory.HAPPY,
                    confidence=0.8,
                )
            ],
            face_detected=True,
        )
        profile = await engine.update_from_event("child-a", event)
        assert profile.total_interactions == 1
        assert profile.child_id == "child-a"

    _run(_test())


def test_personality_engine_record_choice():
    """record_choice adds a theme and increments interactions."""
    async def _test():
        db = await _make_db()
        engine = PersonalityEngine(db)
        profile = await engine.record_choice(
            "child-a", "explore the cave", "exploration"
        )
        assert "exploration" in profile.preferred_themes
        assert profile.total_interactions == 1

    _run(_test())


# ── RelationshipMapper smoke tests ───────────────────────────────────


def test_relationship_mapper_load_default():
    """Loading a model for an unknown pair returns a default."""
    async def _test():
        db = await _make_db()
        mapper = RelationshipMapper(db)
        model = await mapper.load_model("pair-1")
        assert model.sibling_pair_id == "pair-1"
        assert model.leadership_balance == 0.5
        assert model.cooperation_score == 0.5

    _run(_test())


def test_relationship_mapper_record_shared_choice():
    """record_shared_choice updates leadership and cooperation."""
    async def _test():
        db = await _make_db()
        mapper = RelationshipMapper(db)
        model = await mapper.record_shared_choice(
            initiator_child_id="child-a",
            follower_child_id="child-b",
            cooperative=True,
        )
        assert model.total_shared_choices == 1
        assert model.cooperation_score > 0.5  # shifted toward 1.0

    _run(_test())


def test_relationship_mapper_update_from_event():
    """update_from_event computes emotional synchrony from paired emotions."""
    async def _test():
        db = await _make_db()
        mapper = RelationshipMapper(db)
        profile_a = PersonalityProfile(child_id="child-a")
        profile_b = PersonalityProfile(child_id="child-b")

        event = MultimodalInputEvent(
            session_id="sess-1",
            timestamp="2024-01-01T00:00:00+00:00",
            transcript=TranscriptResult(
                text="", confidence=0.0, language="en-US", is_empty=True
            ),
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.9),
                EmotionResult(face_id=1, emotion=EmotionCategory.HAPPY, confidence=0.8),
            ],
            face_detected=True,
        )
        model = await mapper.update_from_event(event, (profile_a, profile_b))
        # Both happy → synchrony should increase from default 0.5
        assert model.emotional_synchrony > 0.5

    _run(_test())


def test_relationship_mapper_compute_session_score():
    """compute_session_score returns a value in [0, 1]."""
    async def _test():
        db = await _make_db()
        mapper = RelationshipMapper(db)
        score = await mapper.compute_session_score("pair-1")
        assert 0.0 <= score <= 1.0

    _run(_test())
