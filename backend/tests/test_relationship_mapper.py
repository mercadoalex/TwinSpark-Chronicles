"""Property-based tests for RelationshipMapper (Layer 2).

Tests cover leadership balance shift, conflict detection, emotional synchrony,
cross-session metric decay, and score drop suggestion trigger.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from hypothesis import HealthCheck, given, settings, assume
from hypothesis import strategies as st

from app.models.multimodal import EmotionCategory, EmotionResult, MultimodalInputEvent, TranscriptResult
from app.models.sibling import PersonalityProfile, RelationshipModel
from app.services.relationship_mapper import RelationshipMapper

# Import strategies from conftest via tests package
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from conftest import st_relationship_model

# Reusable primitives
_unit_float = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)


# ---------------------------------------------------------------------------
# Property 8: Leadership balance shift from shared choices
# Feature: sibling-dynamics-engine, Property 8: Leadership balance shift from shared choices
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(
    model=st_relationship_model(),
    n_calls=st.integers(min_value=1, max_value=20),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_leadership_balance_shifts_toward_initiator(sibling_db, model, n_calls):
    """**Validates: Requirements 3.1**

    For any RelationshipModel and any sequence of record_shared_choice calls
    where child A (child1_id) is always the initiator, the leadership_balance
    should shift toward 0.0 (child1's direction).
    """
    mapper = RelationshipMapper(db=sibling_db)

    # Persist the starting model so the mapper can load it
    pair_id = mapper._pair_id(model.child1_id, model.child2_id)
    model.sibling_pair_id = pair_id
    await mapper.persist_model(pair_id, model)

    initial_balance = model.leadership_balance

    # Record N shared choices where child1 is always the initiator
    for _ in range(n_calls):
        updated = await mapper.record_shared_choice(
            initiator_child_id=model.child1_id,
            follower_child_id=model.child2_id,
            cooperative=True,
        )

    # After child1 always initiating, balance should shift toward 0.0
    # i.e. the distance from 0.0 should not increase.
    # EMA: new = alpha*0.0 + (1-alpha)*old = 0.7*old, so balance shrinks.
    # At the float boundary (subnormals) the value may stay the same.
    assert updated.leadership_balance <= initial_balance + 1e-12


# ---------------------------------------------------------------------------
# Property 10: Conflict detection from consecutive disagreements
# Feature: sibling-dynamics-engine, Property 10: Conflict detection from consecutive disagreements
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(model=st_relationship_model())
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_conflict_detection_consecutive_disagreements(sibling_db, model):
    """**Validates: Requirements 3.5**

    Calling record_shared_choice with cooperative=False twice consecutively
    should result in a new ConflictEvent being appended to conflict_events.
    A single disagreement followed by a cooperative choice should NOT produce
    a conflict event.
    """
    mapper = RelationshipMapper(db=sibling_db)

    # Reset consecutive disagreements so we control the sequence
    model.consecutive_disagreements = 0
    pair_id = mapper._pair_id(model.child1_id, model.child2_id)
    model.sibling_pair_id = pair_id
    initial_conflicts = len(model.conflict_events)
    await mapper.persist_model(pair_id, model)

    # --- Part 1: Two consecutive disagreements → conflict event ---
    await mapper.record_shared_choice(
        initiator_child_id=model.child1_id,
        follower_child_id=model.child2_id,
        cooperative=False,
    )
    result = await mapper.record_shared_choice(
        initiator_child_id=model.child1_id,
        follower_child_id=model.child2_id,
        cooperative=False,
    )
    assert len(result.conflict_events) == initial_conflicts + 1

    # --- Part 2: Single disagreement then cooperative → no new conflict ---
    conflicts_after_part1 = len(result.conflict_events)
    await mapper.persist_model(pair_id, result)

    await mapper.record_shared_choice(
        initiator_child_id=model.child1_id,
        follower_child_id=model.child2_id,
        cooperative=False,
    )
    result2 = await mapper.record_shared_choice(
        initiator_child_id=model.child1_id,
        follower_child_id=model.child2_id,
        cooperative=True,
    )
    assert len(result2.conflict_events) == conflicts_after_part1


# ---------------------------------------------------------------------------
# Property 11: Emotional synchrony from emotion pairs
# Feature: sibling-dynamics-engine, Property 11: Emotional synchrony from emotion pairs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(
    model=st_relationship_model(),
    emotion=st.sampled_from(list(EmotionCategory)),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_emotional_synchrony_same_emotion_increases(sibling_db, model, emotion):
    """**Validates: Requirements 3.6**

    If both children exhibit the same emotion, emotional_synchrony should
    increase (or stay at 1.0).
    """
    mapper = RelationshipMapper(db=sibling_db)

    pair_id = mapper._pair_id(model.child1_id, model.child2_id)
    model.sibling_pair_id = pair_id
    await mapper.persist_model(pair_id, model)

    initial_sync = model.emotional_synchrony

    profile_a = PersonalityProfile(child_id=model.child1_id)
    profile_b = PersonalityProfile(child_id=model.child2_id)

    event = MultimodalInputEvent(
        session_id="test-session",
        timestamp="2024-01-01T00:00:00+00:00",
        emotions=[
            EmotionResult(face_id=0, emotion=emotion, confidence=0.9),
            EmotionResult(face_id=1, emotion=emotion, confidence=0.9),
        ],
        face_detected=True,
    )

    result = await mapper.update_from_event(event, (profile_a, profile_b))

    if initial_sync < 1.0 - 1e-9:
        assert result.emotional_synchrony > initial_sync
    else:
        # At or very near 1.0, float precision prevents meaningful increase
        assert result.emotional_synchrony >= initial_sync - 1e-12


@pytest.mark.asyncio
@given(
    model=st_relationship_model(),
    emotion_a=st.sampled_from(list(EmotionCategory)),
    emotion_b=st.sampled_from(list(EmotionCategory)),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_emotional_synchrony_different_emotion_decreases(sibling_db, model, emotion_a, emotion_b):
    """**Validates: Requirements 3.6**

    If children exhibit different emotions, emotional_synchrony should
    decrease (or stay at 0.0).
    """
    assume(emotion_a != emotion_b)

    mapper = RelationshipMapper(db=sibling_db)

    pair_id = mapper._pair_id(model.child1_id, model.child2_id)
    model.sibling_pair_id = pair_id
    await mapper.persist_model(pair_id, model)

    initial_sync = model.emotional_synchrony

    profile_a = PersonalityProfile(child_id=model.child1_id)
    profile_b = PersonalityProfile(child_id=model.child2_id)

    event = MultimodalInputEvent(
        session_id="test-session",
        timestamp="2024-01-01T00:00:00+00:00",
        emotions=[
            EmotionResult(face_id=0, emotion=emotion_a, confidence=0.9),
            EmotionResult(face_id=1, emotion=emotion_b, confidence=0.9),
        ],
        face_detected=True,
    )

    result = await mapper.update_from_event(event, (profile_a, profile_b))

    if initial_sync > 1e-9:
        assert result.emotional_synchrony < initial_sync
    else:
        assert result.emotional_synchrony <= initial_sync


# ---------------------------------------------------------------------------
# Property 20: Cross-session metric decay
# Feature: sibling-dynamics-engine, Property 20: Cross-session metric decay
# ---------------------------------------------------------------------------


@given(
    leadership=_unit_float,
    cooperation=_unit_float,
    synchrony=_unit_float,
)
@settings(max_examples=20)
def test_cross_session_decay_formula(leadership, cooperation, synchrony):
    """**Validates: Requirements 8.3**

    For any RelationshipModel with metrics (l, c, s), applying
    _apply_cross_session_decay with factor 0.9 should produce metrics
    (0.5 + 0.9*(l-0.5), 0.9*c, 0.9*s).
    """
    model = RelationshipModel(
        sibling_pair_id="test_pair",
        child1_id="a",
        child2_id="b",
        leadership_balance=leadership,
        cooperation_score=cooperation,
        emotional_synchrony=synchrony,
    )

    # We need a mapper instance to call the method (it's not static)
    # But _apply_cross_session_decay doesn't use self.db, so we can pass None
    mapper = RelationshipMapper(db=None)  # type: ignore[arg-type]
    result = mapper._apply_cross_session_decay(model, factor=0.9)

    expected_leadership = 0.5 + 0.9 * (leadership - 0.5)
    expected_cooperation = 0.9 * cooperation
    expected_synchrony = 0.9 * synchrony

    assert result.leadership_balance == pytest.approx(expected_leadership, abs=1e-9)
    assert result.cooperation_score == pytest.approx(expected_cooperation, abs=1e-9)
    assert result.emotional_synchrony == pytest.approx(expected_synchrony, abs=1e-9)


# ---------------------------------------------------------------------------
# Property 23: Score drop suggestion trigger
# Feature: sibling-dynamics-engine, Property 23: Score drop suggestion trigger
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(
    prev_score=st.floats(min_value=0.3, max_value=1.0, allow_nan=False),
    drop=st.floats(min_value=0.21, max_value=0.5, allow_nan=False),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_score_drop_triggers_suggestion(sibling_db, prev_score, drop):
    """**Validates: Requirements 9.4**

    For any two consecutive session scores where the current score is more
    than 0.2 below the previous score, the session summary should include
    a suggestion.
    """
    current_score = prev_score - drop
    assume(current_score >= 0.0)

    mapper = RelationshipMapper(db=sibling_db)

    pair_id = "child_a:child_b"

    # Create a model whose sibling_dynamics_score() ≈ current_score.
    # Score = (centered_leadership + cooperation + synchrony) / 3
    # Use leadership_balance=0.5 → centered_leadership=1.0
    # Then cooperation + synchrony = 3*current_score - 1.0
    remainder = 3.0 * current_score - 1.0
    if remainder < 0.0:
        # Use leadership to absorb the deficit
        # centered_leadership = 1 - 2*|lb - 0.5|
        # We need centered_leadership + 0 + 0 = 3*current_score
        # centered_leadership = 3*current_score, need <= 1.0
        centered = max(0.0, min(1.0, 3.0 * current_score))
        lb = 0.5 - (1.0 - centered) / 2.0
        lb = max(0.0, min(1.0, lb))
        coop = 0.0
        sync = 0.0
    else:
        lb = 0.5
        coop = min(1.0, remainder / 2.0)
        sync = min(1.0, remainder - coop)

    model = RelationshipModel(
        sibling_pair_id=pair_id,
        child1_id="child_a",
        child2_id="child_b",
        leadership_balance=lb,
        cooperation_score=coop,
        emotional_synchrony=sync,
    )
    await mapper.persist_model(pair_id, model)

    # Save a previous session summary with the higher score
    await sibling_db.save_session_summary(
        session_id="prev-session",
        pair_id=pair_id,
        score=prev_score,
        summary="Previous session summary.",
    )

    # Generate summary for the current session — should include suggestion
    summary = await mapper.generate_summary(pair_id)
    assert "suggestion" in summary.lower() or "Suggestion" in summary


@pytest.mark.asyncio
@given(
    base_score=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    small_drop=st.floats(min_value=0.0, max_value=0.19, allow_nan=False),
)
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_small_score_drop_no_suggestion(sibling_db, base_score, small_drop):
    """**Validates: Requirements 9.4**

    When the drop is <= 0.2, the summary should NOT include a suggestion.
    """
    prev_score = base_score
    current_score = max(0.0, base_score - small_drop)
    # Ensure the drop is at most 0.2
    assume(prev_score - current_score <= 0.2)

    mapper = RelationshipMapper(db=sibling_db)

    pair_id = "child_x:child_y"

    # Build a model whose score ≈ current_score
    remainder = 3.0 * current_score - 1.0
    if remainder < 0.0:
        centered = max(0.0, min(1.0, 3.0 * current_score))
        lb = 0.5 - (1.0 - centered) / 2.0
        lb = max(0.0, min(1.0, lb))
        coop = 0.0
        sync = 0.0
    else:
        lb = 0.5
        coop = min(1.0, remainder / 2.0)
        sync = min(1.0, remainder - coop)

    model = RelationshipModel(
        sibling_pair_id=pair_id,
        child1_id="child_x",
        child2_id="child_y",
        leadership_balance=lb,
        cooperation_score=coop,
        emotional_synchrony=sync,
    )
    await mapper.persist_model(pair_id, model)

    # Save a previous session with the higher score
    await sibling_db.save_session_summary(
        session_id="prev-session-2",
        pair_id=pair_id,
        score=prev_score,
        summary="Previous session.",
    )

    summary = await mapper.generate_summary(pair_id)
    assert "Suggestion" not in summary


# ===========================================================================
# Unit tests for RelationshipMapper (Task 5.7)
# Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 8.3, 9.1, 9.4
# ===========================================================================


class TestRecordSharedChoice:
    """Unit tests for record_shared_choice — leadership, cooperation, conflict."""

    @pytest.mark.asyncio
    async def test_cooperative_choice_increases_cooperation(self, sibling_db):
        """Req 3.4: cooperative=True should increase cooperation_score."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            cooperation_score=0.5,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("alice", "bob", cooperative=True)
        # EMA: 0.3 * 1.0 + 0.7 * 0.5 = 0.65
        assert result.cooperation_score == pytest.approx(0.65, abs=1e-9)

    @pytest.mark.asyncio
    async def test_non_cooperative_choice_decreases_cooperation(self, sibling_db):
        """Req 3.4: cooperative=False should decrease cooperation_score."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            cooperation_score=0.5,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("alice", "bob", cooperative=False)
        # EMA: 0.3 * 0.0 + 0.7 * 0.5 = 0.35
        assert result.cooperation_score == pytest.approx(0.35, abs=1e-9)

    @pytest.mark.asyncio
    async def test_child1_initiating_shifts_leadership_toward_zero(self, sibling_db):
        """Req 3.1, 3.2: child1 initiating shifts leadership_balance toward 0.0."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("alice", "bob", cooperative=True)
        # EMA: 0.3 * 0.0 + 0.7 * 0.5 = 0.35
        assert result.leadership_balance == pytest.approx(0.35, abs=1e-9)

    @pytest.mark.asyncio
    async def test_child2_initiating_shifts_leadership_toward_one(self, sibling_db):
        """Req 3.1, 3.2: child2 initiating shifts leadership_balance toward 1.0."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("bob", "alice", cooperative=True)
        # EMA: 0.3 * 1.0 + 0.7 * 0.5 = 0.65
        assert result.leadership_balance == pytest.approx(0.65, abs=1e-9)

    @pytest.mark.asyncio
    async def test_disagreement_increments_consecutive_counter(self, sibling_db):
        """Req 3.5: A single disagreement increments consecutive_disagreements."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            consecutive_disagreements=0,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("alice", "bob", cooperative=False)
        assert result.consecutive_disagreements == 1
        assert len(result.conflict_events) == 0

    @pytest.mark.asyncio
    async def test_two_disagreements_create_conflict_event(self, sibling_db):
        """Req 3.5: Two consecutive disagreements create a ConflictEvent and reset counter."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            consecutive_disagreements=0,
        )
        await mapper.persist_model(pair_id, model)

        await mapper.record_shared_choice("alice", "bob", cooperative=False)
        result = await mapper.record_shared_choice("alice", "bob", cooperative=False)

        assert len(result.conflict_events) == 1
        assert "disagreement" in result.conflict_events[0].description.lower()
        assert result.consecutive_disagreements == 0

    @pytest.mark.asyncio
    async def test_cooperative_after_disagreement_resets_counter(self, sibling_db):
        """Req 3.5: A cooperative choice after a disagreement resets consecutive_disagreements."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            consecutive_disagreements=0,
        )
        await mapper.persist_model(pair_id, model)

        await mapper.record_shared_choice("alice", "bob", cooperative=False)
        result = await mapper.record_shared_choice("alice", "bob", cooperative=True)

        assert result.consecutive_disagreements == 0
        assert len(result.conflict_events) == 0

    @pytest.mark.asyncio
    async def test_total_shared_choices_increments(self, sibling_db):
        """Each call to record_shared_choice increments total_shared_choices."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = mapper._pair_id("alice", "bob")
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            total_shared_choices=0,
        )
        await mapper.persist_model(pair_id, model)

        result = await mapper.record_shared_choice("alice", "bob", cooperative=True)
        assert result.total_shared_choices == 1
        result = await mapper.record_shared_choice("alice", "bob", cooperative=False)
        assert result.total_shared_choices == 2


class TestComputeSessionScore:
    """Unit tests for compute_session_score — Req 9.1."""

    @pytest.mark.asyncio
    async def test_balanced_model_score(self, sibling_db):
        """A perfectly balanced model (0.5, 0.5, 0.5) should score ~0.667."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
            cooperation_score=0.5,
            emotional_synchrony=0.5,
        )
        await mapper.persist_model(pair_id, model)

        score = await mapper.compute_session_score(pair_id)
        # centered_leadership = 1.0 - 0 = 1.0
        # score = (1.0 + 0.5 + 0.5) / 3 = 0.6667
        assert score == pytest.approx(2.0 / 3.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_extreme_leadership_lowers_score(self, sibling_db):
        """Leadership at 0.0 (extreme) should lower the score."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.0,
            cooperation_score=1.0,
            emotional_synchrony=1.0,
        )
        await mapper.persist_model(pair_id, model)

        score = await mapper.compute_session_score(pair_id)
        # centered_leadership = 1.0 - 1.0 = 0.0
        # score = (0.0 + 1.0 + 1.0) / 3 = 0.6667
        assert score == pytest.approx(2.0 / 3.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_perfect_score(self, sibling_db):
        """All metrics at ideal values should produce score = 1.0."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
            cooperation_score=1.0,
            emotional_synchrony=1.0,
        )
        await mapper.persist_model(pair_id, model)

        score = await mapper.compute_session_score(pair_id)
        assert score == pytest.approx(1.0, abs=1e-9)

    @pytest.mark.asyncio
    async def test_worst_score(self, sibling_db):
        """All metrics at worst values should produce score = 0.0."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.0,
            cooperation_score=0.0,
            emotional_synchrony=0.0,
        )
        await mapper.persist_model(pair_id, model)

        score = await mapper.compute_session_score(pair_id)
        assert score == pytest.approx(0.0, abs=1e-9)


class TestGenerateSummary:
    """Unit tests for generate_summary — Req 9.2, 9.3, 9.4."""

    @pytest.mark.asyncio
    async def test_summary_returns_string(self, sibling_db):
        """generate_summary should return a non-empty string."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
        )
        await mapper.persist_model(pair_id, model)

        summary = await mapper.generate_summary(pair_id)
        assert isinstance(summary, str)
        assert len(summary) > 0

    @pytest.mark.asyncio
    async def test_summary_includes_suggestion_on_score_drop(self, sibling_db):
        """Req 9.4: Summary includes suggestion when score drops > 0.2."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"

        # Current model with low score
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.0,
            cooperation_score=0.0,
            emotional_synchrony=0.0,
        )
        await mapper.persist_model(pair_id, model)

        # Previous session had a high score
        await sibling_db.save_session_summary(
            session_id="prev-session",
            pair_id=pair_id,
            score=0.8,
            summary="Previous session was great.",
        )

        summary = await mapper.generate_summary(pair_id)
        assert "suggestion" in summary.lower()

    @pytest.mark.asyncio
    async def test_summary_no_suggestion_when_no_drop(self, sibling_db):
        """Req 9.4: No suggestion when score doesn't drop significantly."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"

        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
            cooperation_score=0.8,
            emotional_synchrony=0.8,
        )
        await mapper.persist_model(pair_id, model)

        # Previous session had a similar score
        await sibling_db.save_session_summary(
            session_id="prev-session",
            pair_id=pair_id,
            score=0.85,
            summary="Previous session.",
        )

        summary = await mapper.generate_summary(pair_id)
        assert "Suggestion" not in summary

    @pytest.mark.asyncio
    async def test_high_score_summary_mentions_cooperation(self, sibling_db):
        """A high-scoring session summary should mention cooperation."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.5,
            cooperation_score=1.0,
            emotional_synchrony=1.0,
        )
        await mapper.persist_model(pair_id, model)

        summary = await mapper.generate_summary(pair_id)
        assert "cooperation" in summary.lower()


class TestApplyCrossSessionDecay:
    """Unit tests for _apply_cross_session_decay — Req 8.3."""

    def test_decay_with_known_values(self):
        """leadership=0.8, factor=0.9 → 0.5 + 0.9*(0.8-0.5) = 0.77."""
        model = RelationshipModel(
            sibling_pair_id="test",
            child1_id="a",
            child2_id="b",
            leadership_balance=0.8,
            cooperation_score=0.6,
            emotional_synchrony=0.4,
        )
        mapper = RelationshipMapper(db=None)  # type: ignore[arg-type]
        result = mapper._apply_cross_session_decay(model, factor=0.9)

        assert result.leadership_balance == pytest.approx(0.77, abs=1e-9)
        assert result.cooperation_score == pytest.approx(0.54, abs=1e-9)
        assert result.emotional_synchrony == pytest.approx(0.36, abs=1e-9)

    def test_decay_neutral_leadership_stays_at_half(self):
        """leadership=0.5 should stay at 0.5 after decay."""
        model = RelationshipModel(
            sibling_pair_id="test",
            child1_id="a",
            child2_id="b",
            leadership_balance=0.5,
            cooperation_score=1.0,
            emotional_synchrony=1.0,
        )
        mapper = RelationshipMapper(db=None)  # type: ignore[arg-type]
        result = mapper._apply_cross_session_decay(model, factor=0.9)

        assert result.leadership_balance == pytest.approx(0.5, abs=1e-9)
        assert result.cooperation_score == pytest.approx(0.9, abs=1e-9)
        assert result.emotional_synchrony == pytest.approx(0.9, abs=1e-9)

    def test_decay_zeros_stay_at_zero(self):
        """cooperation=0 and synchrony=0 should stay at 0 after decay."""
        model = RelationshipModel(
            sibling_pair_id="test",
            child1_id="a",
            child2_id="b",
            leadership_balance=0.5,
            cooperation_score=0.0,
            emotional_synchrony=0.0,
        )
        mapper = RelationshipMapper(db=None)  # type: ignore[arg-type]
        result = mapper._apply_cross_session_decay(model, factor=0.9)

        assert result.cooperation_score == pytest.approx(0.0, abs=1e-9)
        assert result.emotional_synchrony == pytest.approx(0.0, abs=1e-9)


class TestLoadModel:
    """Unit tests for load_model — default model behavior."""

    @pytest.mark.asyncio
    async def test_load_nonexistent_returns_default(self, sibling_db):
        """Req 8.3: load_model for non-existent pair returns default with leadership_balance=0.5."""
        mapper = RelationshipMapper(db=sibling_db)
        model = await mapper.load_model("nonexistent:pair")

        assert model.sibling_pair_id == "nonexistent:pair"
        assert model.leadership_balance == 0.5
        assert model.cooperation_score == 0.5
        assert model.emotional_synchrony == 0.5
        assert model.child1_id == ""
        assert model.child2_id == ""
        assert model.total_shared_choices == 0
        assert model.consecutive_disagreements == 0
        assert len(model.conflict_events) == 0

    @pytest.mark.asyncio
    async def test_load_persisted_model_round_trips(self, sibling_db):
        """A persisted model should be loadable with the same values."""
        mapper = RelationshipMapper(db=sibling_db)
        pair_id = "alice:bob"
        model = RelationshipModel(
            sibling_pair_id=pair_id,
            child1_id="alice",
            child2_id="bob",
            leadership_balance=0.3,
            cooperation_score=0.7,
            emotional_synchrony=0.9,
            total_shared_choices=5,
        )
        await mapper.persist_model(pair_id, model)

        loaded = await mapper.load_model(pair_id)
        assert loaded.leadership_balance == pytest.approx(0.3, abs=1e-9)
        assert loaded.cooperation_score == pytest.approx(0.7, abs=1e-9)
        assert loaded.emotional_synchrony == pytest.approx(0.9, abs=1e-9)
        assert loaded.total_shared_choices == 5
