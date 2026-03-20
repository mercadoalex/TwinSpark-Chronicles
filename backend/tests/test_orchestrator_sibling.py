"""Property-based tests for the AgentOrchestrator sibling event pipeline.

Tests verify that the orchestrator correctly skips personality and relationship
updates when events contain no usable data (empty transcript + no emotions).
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.models.multimodal import (
    MultimodalInputEvent,
    TranscriptResult,
)


# ── Hypothesis strategy: empty events (is_empty=True, no emotions) ────────

@st.composite
def st_empty_event(draw):
    """Generate a MultimodalInputEvent with is_empty=True transcript and no emotions."""
    session_id = draw(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=12)
    )
    timestamp = draw(
        st.datetimes(
            min_value=__import__("datetime").datetime(2020, 1, 1),
            max_value=__import__("datetime").datetime(2030, 1, 1),
            timezones=st.just(__import__("datetime").timezone.utc),
        ).map(lambda dt: dt.isoformat())
    )
    return MultimodalInputEvent(
        session_id=session_id,
        timestamp=timestamp,
        transcript=TranscriptResult(text="", confidence=0.0, language="en-US", is_empty=True),
        emotions=[],
        face_detected=False,
        speech_id=None,
    )


# Feature: sibling-dynamics-engine, Property 25: Empty event skips pipeline
@pytest.mark.asyncio
@given(event=st_empty_event())
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
async def test_empty_event_skips_personality_and_relationship_updates(event):
    """Property 25: For any MultimodalInputEvent where transcript.is_empty is True
    AND emotions is empty, the orchestrator should NOT call
    PersonalityEngine.update_from_event or RelationshipMapper.update_from_event.

    **Validates: Requirements 11.4**
    """
    # Patch the __init__ to avoid importing real agents and services
    with patch.object(
        __import__("app.agents.orchestrator", fromlist=["AgentOrchestrator"]).AgentOrchestrator,
        "__init__",
        lambda self: None,
    ):
        from app.agents.orchestrator import AgentOrchestrator

        orchestrator = AgentOrchestrator()

        # Wire up mocked dependencies
        orchestrator._db_initialized = True
        orchestrator._protagonist_history = []

        orchestrator.personality_engine = AsyncMock()
        orchestrator.relationship_mapper = AsyncMock()
        orchestrator.skills_discoverer = AsyncMock()
        orchestrator.storyteller = AsyncMock()

        # Make storyteller return a minimal result
        orchestrator.storyteller.generate_story_segment = AsyncMock(return_value={"text": "story"})

        # personality_engine.load_profile returns a default profile for Layer 4 context building
        from app.models.sibling import PersonalityProfile, RelationshipModel

        default_profile = PersonalityProfile(child_id="child1")
        orchestrator.personality_engine.load_profile = AsyncMock(return_value=default_profile)

        default_relationship = RelationshipModel(
            sibling_pair_id="child1:child2", child1_id="child1", child2_id="child2"
        )
        orchestrator.relationship_mapper.load_model = AsyncMock(return_value=default_relationship)

        # Call process_sibling_event with the empty event
        await orchestrator.process_sibling_event(
            event=event,
            child1_id="child1",
            child2_id="child2",
            characters={"hero": "dragon"},
            language="en",
        )

        # Assert: personality_engine.update_from_event should NOT have been called
        orchestrator.personality_engine.update_from_event.assert_not_called()

        # Assert: relationship_mapper.update_from_event should NOT have been called
        orchestrator.relationship_mapper.update_from_event.assert_not_called()


# ── Unit tests for orchestrator sibling integration (Task 10.3) ───────────


def _make_orchestrator():
    """Create an AgentOrchestrator with __init__ patched out and mocked deps."""
    with patch.object(
        __import__("app.agents.orchestrator", fromlist=["AgentOrchestrator"]).AgentOrchestrator,
        "__init__",
        lambda self: None,
    ):
        from app.agents.orchestrator import AgentOrchestrator
        from app.models.sibling import PersonalityProfile, RelationshipModel

        orch = AgentOrchestrator()
        orch._db_initialized = True
        orch._protagonist_history = []
        orch._ensure_db_initialized = AsyncMock()

        # Layer 1
        orch.personality_engine = AsyncMock()
        default_profile = PersonalityProfile(child_id="child1")
        orch.personality_engine.update_from_event = AsyncMock(return_value=default_profile)
        orch.personality_engine.load_profile = AsyncMock(return_value=default_profile)

        # Layer 2
        orch.relationship_mapper = AsyncMock()
        default_rel = RelationshipModel(
            sibling_pair_id="child1:child2", child1_id="child1", child2_id="child2"
        )
        orch.relationship_mapper.update_from_event = AsyncMock(return_value=default_rel)
        orch.relationship_mapper.load_model = AsyncMock(return_value=default_rel)
        orch.relationship_mapper.compute_session_score = AsyncMock(return_value=0.75)
        orch.relationship_mapper.generate_summary = AsyncMock(
            return_value="The siblings cooperated well."
        )

        # Layer 3
        orch.skills_discoverer = AsyncMock()
        orch.skills_discoverer.evaluate = AsyncMock(return_value=None)

        # Layer 4 / storyteller
        orch.storyteller = AsyncMock()
        orch.storyteller.generate_story_segment = AsyncMock(return_value={"text": "story"})

        # DB / memory stubs needed by end_session
        orch._sibling_db = AsyncMock()
        orch._sibling_db.save_session_summary = AsyncMock()
        orch.memory = MagicMock(enabled=False)
        orch._world_extractor = MagicMock()
        orch._world_db = AsyncMock()
        orch._world_state_cache = {}

        return orch


def _non_empty_event():
    """Return a MultimodalInputEvent with usable data (non-empty transcript)."""
    return MultimodalInputEvent(
        session_id="sess1",
        timestamp="2024-01-01T00:00:00+00:00",
        transcript=TranscriptResult(
            text="I want to explore the cave",
            confidence=0.9,
            language="en-US",
            is_empty=False,
        ),
        emotions=[],
        face_detected=False,
        speech_id=None,
    )


def _empty_event():
    """Return a MultimodalInputEvent with no usable data."""
    return MultimodalInputEvent(
        session_id="sess1",
        timestamp="2024-01-01T00:00:00+00:00",
        transcript=TranscriptResult(
            text="", confidence=0.0, language="en-US", is_empty=True
        ),
        emotions=[],
        face_detected=False,
        speech_id=None,
    )


# ── 1. process_sibling_event calls layers in correct order ────────────────


@pytest.mark.asyncio
async def test_process_sibling_event_calls_all_layers():
    """Non-empty event triggers personality, relationship, skills, and storyteller.

    Validates: Requirements 11.1
    """
    orch = _make_orchestrator()
    event = _non_empty_event()

    await orch.process_sibling_event(
        event=event,
        child1_id="child1",
        child2_id="child2",
        characters={"hero": "dragon"},
        language="en",
    )

    # Layer 1: personality updated for BOTH children
    assert orch.personality_engine.update_from_event.call_count == 2
    calls = orch.personality_engine.update_from_event.call_args_list
    assert calls[0][0][0] == "child1"
    assert calls[1][0][0] == "child2"

    # Layer 2: relationship updated
    orch.relationship_mapper.update_from_event.assert_called_once()

    # Layer 3: skills evaluated
    orch.skills_discoverer.evaluate.assert_called_once()

    # Layer 4: storyteller called
    orch.storyteller.generate_story_segment.assert_called_once()


# ── 2. Empty event skips personality and relationship updates ─────────────


@pytest.mark.asyncio
async def test_process_sibling_event_empty_skips_layers_1_to_3():
    """Empty event (no transcript, no emotions) skips Layers 1-3.

    Validates: Requirements 11.4
    """
    orch = _make_orchestrator()
    event = _empty_event()

    await orch.process_sibling_event(
        event=event,
        child1_id="child1",
        child2_id="child2",
        characters={"hero": "dragon"},
        language="en",
    )

    orch.personality_engine.update_from_event.assert_not_called()
    orch.relationship_mapper.update_from_event.assert_not_called()
    orch.skills_discoverer.evaluate.assert_not_called()

    # Storyteller still called (Layer 4 always runs)
    orch.storyteller.generate_story_segment.assert_called_once()


# ── 3. end_session persists data and returns score + summary ──────────────


@pytest.mark.asyncio
async def test_end_session_returns_score_and_summary():
    """end_session computes score, generates summary, persists, and returns result.

    Validates: Requirements 8.1, 9.2
    """
    orch = _make_orchestrator()

    result = await orch.end_session(
        session_id="sess1", sibling_pair_id="child1:child2"
    )

    # Score computed
    orch.relationship_mapper.compute_session_score.assert_called_once_with(
        "child1:child2"
    )

    # Summary generated
    orch.relationship_mapper.generate_summary.assert_called_once_with(
        "child1:child2"
    )

    # Persisted to DB
    orch._sibling_db.save_session_summary.assert_called_once()

    # Return dict has required keys
    assert result["session_id"] == "sess1"
    assert result["sibling_pair_id"] == "child1:child2"
    assert result["sibling_dynamics_score"] == 0.75
    assert "cooperated" in result["summary"]


@pytest.mark.asyncio
async def test_end_session_extracts_suggestion():
    """end_session splits suggestion from summary when present.

    Validates: Requirements 9.2
    """
    orch = _make_orchestrator()
    orch.relationship_mapper.generate_summary = AsyncMock(
        return_value="Good session. Suggestion: Try cooperative games."
    )

    result = await orch.end_session(
        session_id="sess2", sibling_pair_id="child1:child2"
    )

    assert result["summary"] == "Good session."
    assert result["suggestion"] is not None
    assert "cooperative games" in result["suggestion"]


# ── 4. Resilience: one layer failure doesn't block others ─────────────────


@pytest.mark.asyncio
async def test_resilience_personality_failure_does_not_block_relationship():
    """If personality_engine.update_from_event raises, relationship still runs.

    Validates: Requirements 11.5
    """
    orch = _make_orchestrator()
    event = _non_empty_event()

    # Make Layer 1 fail for both children
    orch.personality_engine.update_from_event = AsyncMock(
        side_effect=RuntimeError("personality boom")
    )

    await orch.process_sibling_event(
        event=event,
        child1_id="child1",
        child2_id="child2",
        characters={"hero": "dragon"},
        language="en",
    )

    # Layer 2 still called despite Layer 1 failure
    orch.relationship_mapper.update_from_event.assert_called_once()

    # Storyteller still called
    orch.storyteller.generate_story_segment.assert_called_once()


@pytest.mark.asyncio
async def test_resilience_relationship_failure_does_not_block_skills():
    """If relationship_mapper.update_from_event raises, skills still runs.

    Validates: Requirements 11.5
    """
    orch = _make_orchestrator()
    event = _non_empty_event()

    # Make Layer 2 fail
    orch.relationship_mapper.update_from_event = AsyncMock(
        side_effect=RuntimeError("relationship boom")
    )

    await orch.process_sibling_event(
        event=event,
        child1_id="child1",
        child2_id="child2",
        characters={"hero": "dragon"},
        language="en",
    )

    # Layer 3 still called despite Layer 2 failure
    orch.skills_discoverer.evaluate.assert_called_once()

    # Storyteller still called
    orch.storyteller.generate_story_segment.assert_called_once()
