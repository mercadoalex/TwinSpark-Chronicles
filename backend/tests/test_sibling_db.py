"""Unit tests for SiblingDB persistence layer.

Validates: Requirements 10.1, 10.2, 10.3, 10.4
"""

import json

import pytest

from app.models.sibling import PersonalityProfile, RelationshipModel, SkillMap


pytestmark = pytest.mark.asyncio


# ── initialize() ─────────────────────────────────────────────────


async def test_initialize_is_idempotent(sibling_db):
    """Calling initialize() multiple times should not raise."""
    await sibling_db.initialize()
    await sibling_db.initialize()


# ── Personality Profiles ─────────────────────────────────────────


async def test_save_load_profile_round_trip(sibling_db):
    profile = PersonalityProfile(child_id="child1")
    profile_json = profile.model_dump_json()
    await sibling_db.save_profile("child1", profile_json)

    loaded = await sibling_db.load_profile("child1")
    assert loaded is not None
    restored = PersonalityProfile.model_validate_json(loaded)
    assert restored.child_id == "child1"


async def test_save_profile_upserts(sibling_db):
    """Saving the same child_id twice should overwrite."""
    p1 = PersonalityProfile(child_id="child1", status="emerging")
    await sibling_db.save_profile("child1", p1.model_dump_json())

    p2 = PersonalityProfile(child_id="child1", status="established", total_interactions=10)
    await sibling_db.save_profile("child1", p2.model_dump_json())

    loaded = await sibling_db.load_profile("child1")
    restored = PersonalityProfile.model_validate_json(loaded)
    assert restored.status == "established"
    assert restored.total_interactions == 10


async def test_load_profile_nonexistent_returns_none(sibling_db):
    result = await sibling_db.load_profile("no_such_child")
    assert result is None


# ── Relationship Models ──────────────────────────────────────────


async def test_save_load_relationship_round_trip(sibling_db):
    model = RelationshipModel(
        sibling_pair_id="a_b", child1_id="a", child2_id="b",
        cooperation_score=0.8,
    )
    model_json = model.model_dump_json()
    await sibling_db.save_relationship("a_b", model_json)

    loaded = await sibling_db.load_relationship("a_b")
    assert loaded is not None
    restored = RelationshipModel.model_validate_json(loaded)
    assert restored.sibling_pair_id == "a_b"
    assert restored.cooperation_score == pytest.approx(0.8)


async def test_save_relationship_upserts(sibling_db):
    m1 = RelationshipModel(
        sibling_pair_id="a_b", child1_id="a", child2_id="b",
        cooperation_score=0.3,
    )
    await sibling_db.save_relationship("a_b", m1.model_dump_json())

    m2 = RelationshipModel(
        sibling_pair_id="a_b", child1_id="a", child2_id="b",
        cooperation_score=0.9,
    )
    await sibling_db.save_relationship("a_b", m2.model_dump_json())

    loaded = await sibling_db.load_relationship("a_b")
    restored = RelationshipModel.model_validate_json(loaded)
    assert restored.cooperation_score == pytest.approx(0.9)


async def test_load_relationship_nonexistent_returns_none(sibling_db):
    result = await sibling_db.load_relationship("no_pair")
    assert result is None


# ── Skill Maps ───────────────────────────────────────────────────


async def test_save_load_skill_map_round_trip(sibling_db):
    sm = SkillMap(sibling_pair_id="a_b", interaction_count_at_evaluation=20)
    await sibling_db.save_skill_map("a_b", sm.model_dump_json())

    loaded = await sibling_db.load_skill_map("a_b")
    assert loaded is not None
    restored = SkillMap.model_validate_json(loaded)
    assert restored.sibling_pair_id == "a_b"
    assert restored.interaction_count_at_evaluation == 20


async def test_save_skill_map_upserts(sibling_db):
    sm1 = SkillMap(sibling_pair_id="a_b", interaction_count_at_evaluation=10)
    await sibling_db.save_skill_map("a_b", sm1.model_dump_json())

    sm2 = SkillMap(sibling_pair_id="a_b", interaction_count_at_evaluation=30)
    await sibling_db.save_skill_map("a_b", sm2.model_dump_json())

    loaded = await sibling_db.load_skill_map("a_b")
    restored = SkillMap.model_validate_json(loaded)
    assert restored.interaction_count_at_evaluation == 30


async def test_load_skill_map_nonexistent_returns_none(sibling_db):
    result = await sibling_db.load_skill_map("no_pair")
    assert result is None


# ── Session Summaries ────────────────────────────────────────────


async def test_save_load_session_summary_round_trip(sibling_db):
    await sibling_db.save_session_summary(
        session_id="sess1",
        pair_id="a_b",
        score=0.75,
        summary="Great cooperation today.",
        suggestion=None,
    )

    row = await sibling_db.load_session_summary("sess1")
    assert row is not None
    assert row["session_id"] == "sess1"
    assert row["score"] == pytest.approx(0.75)
    assert row["summary"] == "Great cooperation today."
    assert row["suggestion"] is None


async def test_save_session_summary_with_suggestion(sibling_db):
    await sibling_db.save_session_summary(
        session_id="sess2",
        pair_id="a_b",
        score=0.4,
        summary="Some tension observed.",
        suggestion="Try a cooperative game before the next session.",
    )

    row = await sibling_db.load_session_summary("sess2")
    assert row["suggestion"] == "Try a cooperative game before the next session."


async def test_load_session_summaries_returns_list(sibling_db):
    for i in range(3):
        await sibling_db.save_session_summary(
            session_id=f"sess{i}",
            pair_id="a_b",
            score=0.5 + i * 0.1,
            summary=f"Session {i}",
        )

    rows = await sibling_db.load_session_summaries("a_b", limit=10)
    assert len(rows) == 3
    # Should be ordered by created_at DESC (most recent first)
    assert all("session_id" in r for r in rows)


async def test_load_session_summaries_respects_limit(sibling_db):
    for i in range(5):
        await sibling_db.save_session_summary(
            session_id=f"s{i}", pair_id="a_b", score=0.5, summary=f"S{i}",
        )

    rows = await sibling_db.load_session_summaries("a_b", limit=2)
    assert len(rows) == 2


async def test_load_session_summaries_empty_for_unknown_pair(sibling_db):
    rows = await sibling_db.load_session_summaries("unknown_pair")
    assert rows == []


async def test_load_session_summary_nonexistent_returns_none(sibling_db):
    result = await sibling_db.load_session_summary("no_such_session")
    assert result is None


async def test_save_session_summary_upserts(sibling_db):
    await sibling_db.save_session_summary(
        session_id="sess1", pair_id="a_b", score=0.5, summary="First",
    )
    await sibling_db.save_session_summary(
        session_id="sess1", pair_id="a_b", score=0.9, summary="Updated",
    )

    row = await sibling_db.load_session_summary("sess1")
    assert row["score"] == pytest.approx(0.9)
    assert row["summary"] == "Updated"


# ── Initial Profiles ─────────────────────────────────────────────


async def test_save_load_initial_profile_round_trip(sibling_db):
    profile = PersonalityProfile(child_id="child1")
    await sibling_db.save_initial_profile("child1", profile.model_dump_json())

    loaded = await sibling_db.load_initial_profile("child1")
    assert loaded is not None
    restored = PersonalityProfile.model_validate_json(loaded)
    assert restored.child_id == "child1"


async def test_save_initial_profile_ignores_duplicate(sibling_db):
    """INSERT OR IGNORE means the first write wins."""
    p1 = PersonalityProfile(child_id="child1", status="emerging")
    await sibling_db.save_initial_profile("child1", p1.model_dump_json())

    p2 = PersonalityProfile(child_id="child1", status="established", total_interactions=99)
    await sibling_db.save_initial_profile("child1", p2.model_dump_json())

    loaded = await sibling_db.load_initial_profile("child1")
    restored = PersonalityProfile.model_validate_json(loaded)
    # First write should win
    assert restored.status == "emerging"
    assert restored.total_interactions == 0


async def test_load_initial_profile_nonexistent_returns_none(sibling_db):
    result = await sibling_db.load_initial_profile("no_child")
    assert result is None
