"""Property-based tests for PersonalityEngine (Layer 1).

Tests cover temporal decay weighting, profile independence, personality
update from events, and transcript analysis using Hypothesis strategies
from conftest.py.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from app.models.multimodal import (
    EmotionCategory,
    EmotionResult,
    MultimodalInputEvent,
    TranscriptResult,
)
from app.models.sibling import PersonalityProfile, TraitScore
from app.services.personality_engine import PersonalityEngine
from app.services.sibling_db import SiblingDB

from tests.conftest import st_multimodal_event, st_personality_profile


# ---------------------------------------------------------------------------
# Property 5: Temporal decay weighting
# Feature: sibling-dynamics-engine, Property 5: Temporal decay weighting
# ---------------------------------------------------------------------------


@given(
    current=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    new_signal=st.floats(min_value=0.0, max_value=1.0, allow_nan=False),
    alpha=st.floats(min_value=0.01, max_value=0.99, allow_nan=False),
)
@settings(max_examples=20)
def test_temporal_decay_weighting(current: float, new_signal: float, alpha: float):
    """For any EMA update, result = alpha * new_signal + (1 - alpha) * current
    and the result is always between current and new_signal (inclusive).

    **Validates: Requirements 1.5**
    """
    # We need a SiblingDB to construct PersonalityEngine, but _apply_temporal_decay
    # is a pure method that doesn't touch the DB. Use None as a placeholder.
    engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
    result = engine._apply_temporal_decay(current, new_signal, alpha)

    # Verify the EMA formula
    expected = alpha * new_signal + (1.0 - alpha) * current
    assert abs(result - expected) < 1e-9, (
        f"EMA formula mismatch: got {result}, expected {expected}"
    )

    # Result must be between current and new_signal (inclusive)
    lo = min(current, new_signal)
    hi = max(current, new_signal)
    assert lo - 1e-9 <= result <= hi + 1e-9, (
        f"Result {result} not between {lo} and {hi}"
    )


# ---------------------------------------------------------------------------
# Property 6: Profile independence
# Feature: sibling-dynamics-engine, Property 6: Profile independence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(event=st_multimodal_event())
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_profile_independence(sibling_db: SiblingDB, event: MultimodalInputEvent):
    """Updating child A's profile must not change child B's profile.

    **Validates: Requirements 1.3**
    """
    child_a = "child_a_test"
    child_b = "child_b_test"

    engine = PersonalityEngine(db=sibling_db)

    # Ensure both profiles exist with known initial state
    profile_a_init = PersonalityProfile(child_id=child_a)
    profile_b_init = PersonalityProfile(child_id=child_b)
    await engine.persist_profile(child_a, profile_a_init)
    await engine.persist_profile(child_b, profile_b_init)

    # Snapshot child B's profile before updating child A
    profile_b_before = await engine.load_profile(child_b)
    b_before_json = profile_b_before.model_dump_json()

    # Update child A only
    await engine.update_from_event(child_a, event)

    # Reload child B and verify it is unchanged
    profile_b_after = await engine.load_profile(child_b)
    b_after_json = profile_b_after.model_dump_json()

    assert b_before_json == b_after_json, (
        "Child B's profile changed after updating child A"
    )


# ---------------------------------------------------------------------------
# Property 7: Personality update from events
# Feature: sibling-dynamics-engine, Property 7: Personality update from events
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(event=st_multimodal_event())
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_personality_update_increments_interactions(
    sibling_db: SiblingDB, event: MultimodalInputEvent
):
    """For any MultimodalInputEvent, calling update_from_event should
    increase total_interactions by 1.

    **Validates: Requirements 1.1, 1.2, 11.2**
    """
    # Ensure the event has at least some emotion data so the update is meaningful
    assume(len(event.emotions) > 0)
    # Ensure at least one emotion has confidence >= 0.1 (otherwise all are discarded)
    assume(any(e.confidence >= 0.1 for e in event.emotions))

    child_id = "test_child_update"
    engine = PersonalityEngine(db=sibling_db)

    # Start with a fresh profile
    initial_profile = PersonalityProfile(child_id=child_id)
    await engine.persist_profile(child_id, initial_profile)

    before = await engine.load_profile(child_id)
    interactions_before = before.total_interactions

    await engine.update_from_event(child_id, event)

    after = await engine.load_profile(child_id)
    assert after.total_interactions == interactions_before + 1, (
        f"Expected total_interactions to increase by 1: "
        f"before={interactions_before}, after={after.total_interactions}"
    )


# ---------------------------------------------------------------------------
# Property 24: Transcript analysis produces signals
# Feature: sibling-dynamics-engine, Property 24: Transcript analysis produces signals
# ---------------------------------------------------------------------------

# Keywords that _analyze_transcript recognises
_KEYWORDS = [
    "why", "how", "what if", "let me", "please", "imagine",
    "wait", "haha", "?",
]

TRAIT_DIMENSIONS = {"curiosity", "boldness", "empathy", "creativity", "patience", "humor"}


@given(
    keyword=st.sampled_from(_KEYWORDS),
    padding=st.text(
        alphabet=st.characters(whitelist_categories=("L", "Zs")),
        min_size=0,
        max_size=30,
    ),
)
@settings(max_examples=20)
def test_transcript_analysis_produces_signals(keyword: str, padding: str):
    """For any non-empty transcript containing at least one recognised keyword,
    _analyze_transcript should return a dict with at least one key from the
    trait dimensions.

    **Validates: Requirements 11.3**
    """
    # Build a transcript that definitely contains the keyword
    transcript = f"{padding} {keyword} {padding}".strip()
    assume(len(transcript) > 0)

    engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
    signals = engine._analyze_transcript(transcript)

    assert isinstance(signals, dict)
    assert len(signals) > 0, (
        f"Expected at least one signal for transcript containing '{keyword}', got empty dict"
    )
    assert all(k in TRAIT_DIMENSIONS for k in signals), (
        f"Signal keys {set(signals.keys())} not subset of {TRAIT_DIMENSIONS}"
    )


# ===========================================================================
# Unit tests for PersonalityEngine
# Requirements: 1.1, 1.2, 1.5, 2.2, 2.3, 2.5
# ===========================================================================


class TestUpdateFromEvent:
    """Tests for PersonalityEngine.update_from_event."""

    @pytest.mark.asyncio
    async def test_emotion_updates_correct_traits(self, sibling_db: SiblingDB):
        """A HAPPY emotion should update humor and boldness traits.

        Validates: Requirements 1.1, 1.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_1"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.9)
            ],
            face_detected=True,
        )

        profile = await engine.update_from_event(child_id, event)

        # HAPPY maps to humor(0.8) and boldness(0.6) — both should shift from default 0.5
        assert profile.humor.value != 0.5, "humor trait should be updated"
        assert profile.boldness.value != 0.5, "boldness trait should be updated"
        assert profile.humor.observation_count >= 1
        assert profile.boldness.observation_count >= 1

    @pytest.mark.asyncio
    async def test_sad_emotion_updates_empathy_and_patience(self, sibling_db: SiblingDB):
        """A SAD emotion should update empathy and patience traits.

        Validates: Requirements 1.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_sad"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.SAD, confidence=0.8)
            ],
            face_detected=True,
        )

        profile = await engine.update_from_event(child_id, event)

        assert profile.empathy.value != 0.5
        assert profile.patience.value != 0.5
        assert profile.empathy.observation_count >= 1

    @pytest.mark.asyncio
    async def test_interaction_count_increments(self, sibling_db: SiblingDB):
        """Each update_from_event call should increment total_interactions by 1.

        Validates: Requirements 1.1
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_count"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.NEUTRAL, confidence=0.5)
            ],
            face_detected=True,
        )

        await engine.update_from_event(child_id, event)
        profile = await engine.load_profile(child_id)
        assert profile.total_interactions == 1

        await engine.update_from_event(child_id, event)
        profile = await engine.load_profile(child_id)
        assert profile.total_interactions == 2

    @pytest.mark.asyncio
    async def test_transcript_signals_update_traits(self, sibling_db: SiblingDB):
        """A transcript with 'why' should boost curiosity.

        Validates: Requirements 1.1
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_transcript"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            transcript=TranscriptResult(
                text="why is the sky blue?",
                confidence=0.9,
                is_empty=False,
            ),
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.NEUTRAL, confidence=0.5)
            ],
            face_detected=True,
        )

        profile = await engine.update_from_event(child_id, event)

        # "why" and "?" both map to curiosity
        assert profile.curiosity.value != 0.5, "curiosity should be updated from transcript"
        assert profile.curiosity.observation_count >= 1


class TestLowConfidenceDiscarded:
    """Tests that low-confidence emotion signals are discarded."""

    @pytest.mark.asyncio
    async def test_confidence_below_threshold_discarded(self, sibling_db: SiblingDB):
        """Emotions with confidence < 0.1 should not affect traits.

        Validates: Requirements 1.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_low_conf"

        # Persist a known initial profile
        from app.models.sibling import PersonalityProfile
        initial = PersonalityProfile(child_id=child_id)
        await engine.persist_profile(child_id, initial)

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            transcript=TranscriptResult(text="", confidence=0.0, is_empty=True),
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.05)
            ],
            face_detected=True,
        )

        profile = await engine.update_from_event(child_id, event)

        # HAPPY maps to humor and boldness, but confidence 0.05 < 0.1 → discarded
        assert profile.humor.value == 0.5, "humor should remain at default"
        assert profile.boldness.value == 0.5, "boldness should remain at default"
        assert profile.humor.observation_count == 0
        assert profile.boldness.observation_count == 0

    @pytest.mark.asyncio
    async def test_confidence_at_threshold_not_discarded(self, sibling_db: SiblingDB):
        """Emotions with confidence exactly 0.1 should NOT be discarded (< 0.1 is the cutoff).

        Validates: Requirements 1.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_at_threshold"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.1)
            ],
            face_detected=True,
        )

        profile = await engine.update_from_event(child_id, event)

        # confidence 0.1 is NOT < 0.1, so it should be processed
        assert profile.humor.observation_count >= 1, "emotion at threshold should be processed"


class TestRecordChoice:
    """Tests for PersonalityEngine.record_choice."""

    @pytest.mark.asyncio
    async def test_adds_new_theme(self, sibling_db: SiblingDB):
        """record_choice should add a new theme to preferred_themes.

        Validates: Requirements 2.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_choice"

        profile = await engine.record_choice(child_id, "go explore", "exploration")

        assert "exploration" in profile.preferred_themes

    @pytest.mark.asyncio
    async def test_does_not_duplicate_theme(self, sibling_db: SiblingDB):
        """record_choice should not add a theme that already exists.

        Validates: Requirements 2.2
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_dup"

        await engine.record_choice(child_id, "go explore", "exploration")
        profile = await engine.record_choice(child_id, "explore more", "exploration")

        assert profile.preferred_themes.count("exploration") == 1

    @pytest.mark.asyncio
    async def test_increments_interactions(self, sibling_db: SiblingDB):
        """record_choice should increment total_interactions.

        Validates: Requirements 1.1
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_choice_count"

        await engine.record_choice(child_id, "pick A", "action")
        profile = await engine.load_profile(child_id)
        assert profile.total_interactions == 1


class TestEmergingProfile:
    """Tests for emerging profile defaults and status transitions."""

    @pytest.mark.asyncio
    async def test_fresh_profile_is_emerging(self, sibling_db: SiblingDB):
        """A newly loaded profile should have status='emerging' and total_interactions=0.

        Validates: Requirements 2.5
        """
        engine = PersonalityEngine(db=sibling_db)
        profile = await engine.load_profile("brand_new_child")

        assert profile.status == "emerging"
        assert profile.total_interactions == 0
        assert profile.child_id == "brand_new_child"

    @pytest.mark.asyncio
    async def test_status_becomes_established_after_5_interactions(self, sibling_db: SiblingDB):
        """After 5 interactions, status should change to 'established'.

        Validates: Requirements 2.5
        """
        engine = PersonalityEngine(db=sibling_db)
        child_id = "unit_child_establish"

        event = MultimodalInputEvent(
            session_id="s1",
            timestamp="2024-01-01T00:00:00+00:00",
            emotions=[
                EmotionResult(face_id=0, emotion=EmotionCategory.NEUTRAL, confidence=0.5)
            ],
            face_detected=True,
        )

        for _ in range(4):
            profile = await engine.update_from_event(child_id, event)
        assert profile.status == "emerging"

        # 5th interaction should flip to established
        profile = await engine.update_from_event(child_id, event)
        assert profile.status == "established"
        assert profile.total_interactions == 5

    @pytest.mark.asyncio
    async def test_default_trait_values(self, sibling_db: SiblingDB):
        """A fresh profile should have all traits at default value 0.5 with confidence 0.0.

        Validates: Requirements 2.5
        """
        engine = PersonalityEngine(db=sibling_db)
        profile = await engine.load_profile("default_child")

        for trait_name, trait in profile.trait_dict().items():
            assert trait.value == 0.5, f"{trait_name} value should default to 0.5"
            assert trait.confidence == 0.0, f"{trait_name} confidence should default to 0.0"
            assert trait.observation_count == 0, f"{trait_name} observation_count should default to 0"


class TestAnalyzeTranscript:
    """Tests for PersonalityEngine._analyze_transcript."""

    def test_why_triggers_curiosity(self):
        """'why' keyword should produce a curiosity signal.

        Validates: Requirements 1.1
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("why do birds fly?")

        assert "curiosity" in signals
        assert signals["curiosity"] > 0

    def test_please_triggers_empathy(self):
        """'please' keyword should produce an empathy signal.

        Validates: Requirements 2.3
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("please help me")

        assert "empathy" in signals

    def test_imagine_triggers_creativity(self):
        """'imagine' keyword should produce a creativity signal.

        Validates: Requirements 2.3
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("imagine a dragon")

        assert "creativity" in signals

    def test_haha_triggers_humor(self):
        """'haha' keyword should produce a humor signal.

        Validates: Requirements 2.3
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("haha that was funny")

        assert "humor" in signals

    def test_wait_triggers_patience(self):
        """'wait' keyword should produce a patience signal.

        Validates: Requirements 2.3
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("wait for me")

        assert "patience" in signals

    def test_let_me_triggers_boldness(self):
        """'let me' keyword should produce a boldness signal.

        Validates: Requirements 2.3
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("let me try that")

        assert "boldness" in signals

    def test_question_mark_triggers_curiosity(self):
        """A question mark alone should produce a curiosity signal.

        Validates: Requirements 1.1
        """
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("really?")

        assert "curiosity" in signals

    def test_empty_text_returns_empty(self):
        """Empty text should return no signals."""
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("")

        assert signals == {}

    def test_no_keywords_returns_empty(self):
        """Text with no recognized keywords should return empty dict."""
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("the cat sat on the mat")

        assert signals == {}

    def test_multiple_keywords_produce_multiple_signals(self):
        """Text with multiple keywords should produce signals for each matched trait."""
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        signals = engine._analyze_transcript("why not imagine something funny haha?")

        assert "curiosity" in signals
        assert "creativity" in signals
        assert "humor" in signals

    def test_keeps_strongest_signal_per_trait(self):
        """When multiple patterns match the same trait, the strongest signal wins."""
        engine = PersonalityEngine(db=None)  # type: ignore[arg-type]
        # "why" → curiosity 0.7, "?" → curiosity 0.5 — should keep 0.7
        signals = engine._analyze_transcript("why?")

        assert signals["curiosity"] == 0.7
