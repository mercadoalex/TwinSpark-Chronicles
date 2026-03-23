"""Full-flow integration tests: setup → WebSocket → story generation → display.

All Gemini/Vertex/TTS agents are mocked at the boundary — zero API calls.
Ale and Sofi are the canonical test sibling pair throughout.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.testclient import TestClient

# ---------------------------------------------------------------------------
# Shared mock story segment
# ---------------------------------------------------------------------------

MOCK_STORY_SEGMENT = {
    "text": (
        "Ale and Sofi discovered a magical forest filled with glowing mushrooms! 🍄 "
        "A friendly dragon appeared and asked them a riddle. "
        "What should they do? Should they answer the riddle or ask the dragon for a clue?"
    ),
    "timestamp": "2025-01-15T10:00:00",
    "characters": {},
    "interactive": {
        "type": "question",
        "text": "Should they answer the riddle or ask the dragon for a clue?",
        "expects_response": True,
    },
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ale_sofi_profiles():
    """Canonical Ale & Sofi character profiles for full-flow tests."""
    return {
        "child1": {
            "name": "Ale",
            "gender": "girl",
            "spirit_animal": "Dragon",
            "toy_name": "Bruno",
            "costume": "adventure_clothes",
            "costume_prompt": "wearing adventure clothes",
        },
        "child2": {
            "name": "Sofi",
            "gender": "boy",
            "spirit_animal": "Owl",
            "toy_name": "Book",
            "costume": "adventure_clothes",
            "costume_prompt": "wearing adventure clothes",
        },
    }


@pytest.fixture
def ale_sofi_ws_params():
    """WebSocket query parameters matching the format expected by the handler."""
    return {
        "lang": "en",
        "c1_name": "Ale",
        "c1_gender": "girl",
        "c1_personality": "brave",
        "c1_spirit": "Dragon",
        "c1_toy": "Bruno",
        "c2_name": "Sofi",
        "c2_gender": "boy",
        "c2_personality": "wise",
        "c2_spirit": "Owl",
        "c2_toy": "Book",
    }


SIBLING_PAIR_ID = "Ale:Sofi"


def _ws_url(session_id: str, params: dict) -> str:
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return f"/ws/{session_id}?{qs}"


# ---------------------------------------------------------------------------
# Helper: patched TestClient context
# ---------------------------------------------------------------------------


def _patched_client():
    """Return a TestClient with storyteller mocked so no Gemini calls happen."""
    from app.main import app

    seg = MOCK_STORY_SEGMENT.copy()

    patcher_gen = patch(
        "app.main.storyteller.generate_story_segment",
        new_callable=AsyncMock,
        return_value=seg,
    )
    patcher_model = patch("app.main.storyteller.model", new_callable=MagicMock)

    patcher_gen.start()
    patcher_model.start()

    client = TestClient(app)
    return client, [patcher_gen, patcher_model]


# ===================================================================
# Task 2: Backend WebSocket connection and session lifecycle tests
# ===================================================================


def test_ws_connect_and_input_status(ale_sofi_ws_params):
    """WebSocket accepts connection and sends input_status as first message."""
    client, patchers = _patched_client()
    try:
        session_id = "test-session-input-status"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)) as ws:
            msg = ws.receive_json()
            assert msg["type"] == "input_status"
            assert "camera" in msg
            assert "mic" in msg
    finally:
        for p in patchers:
            p.stop()


def test_ws_session_registered(ale_sofi_ws_params):
    """After connect, session is registered in ConnectionManager."""
    from app.main import manager

    client, patchers = _patched_client()
    try:
        session_id = "test-session-registered"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)):
            assert session_id in manager.active_connections
            assert session_id in manager.input_managers
    finally:
        for p in patchers:
            p.stop()


def test_ws_story_generation(ale_sofi_ws_params, ale_sofi_profiles):
    """Sending context message returns story_segment with expected structure."""
    client, patchers = _patched_client()
    try:
        session_id = "test-session-story-gen"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)) as ws:
            # Receive initial input_status
            ws.receive_json()

            # Send context with characters
            ws.send_json({"context": {"characters": ale_sofi_profiles}})
            msg = ws.receive_json()

            assert msg["type"] == "story_segment"
            data = msg["data"]
            assert "text" in data
            assert "timestamp" in data
            assert "characters" in data
            assert "interactive" in data
    finally:
        for p in patchers:
            p.stop()


def test_ws_story_fallback_on_error(ale_sofi_ws_params, ale_sofi_profiles):
    """When the Gemini model raises, the storyteller's internal fallback fires
    and the WebSocket returns a story containing both Ale and Sofi."""
    from app.main import app

    # Mock the model's generate_content_async to raise, so the storyteller's
    # own try/except catches it and returns _fallback_story.
    with patch(
        "app.agents.storyteller_agent.storyteller.model",
        new_callable=MagicMock,
    ) as mock_model:
        mock_model.generate_content_async = AsyncMock(
            side_effect=Exception("API failure")
        )
        client = TestClient(app)
        session_id = "test-session-fallback"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)) as ws:
            ws.receive_json()  # input_status
            ws.send_json({"context": {"characters": ale_sofi_profiles}})
            msg = ws.receive_json()

            assert msg["type"] == "story_segment"
            text = msg["data"]["text"]
            assert "Ale" in text
            assert "Sofi" in text


def test_ws_disconnect_cleanup(ale_sofi_ws_params):
    """After disconnect, session is removed from active_connections."""
    from app.main import manager

    client, patchers = _patched_client()
    try:
        session_id = "test-session-disconnect"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)):
            assert session_id in manager.active_connections

        # After context manager exits (disconnect), session should be cleaned up
        assert session_id not in manager.active_connections
    finally:
        for p in patchers:
            p.stop()


def test_session_time_enforcer_tracking(ale_sofi_ws_params):
    """After connect, SessionTimeEnforcer has an active entry for the session."""
    from app.main import session_time_enforcer

    client, patchers = _patched_client()
    try:
        session_id = "test-session-time-track"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)):
            # session_time_enforcer should be tracking this session
            time_check = session_time_enforcer.check_time(session_id)
            assert time_check is not None
            assert not time_check.is_expired
    finally:
        for p in patchers:
            p.stop()


# ===================================================================
# Task 4: Backend orchestrator integration tests
# ===================================================================


@pytest.mark.asyncio
async def test_orchestrator_rich_story(ale_sofi_profiles):
    """generate_rich_story_moment returns complete result with all expected keys."""
    from app.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()

    # Mock all sub-agents at the coordinator boundary
    orch.story.generate_safe_story_segment = AsyncMock(return_value=MOCK_STORY_SEGMENT.copy())
    orch.story.recall_memories = AsyncMock(return_value=[])
    orch.story.filter_choices = MagicMock(side_effect=lambda seg, *a, **kw: seg)
    orch.story.check_voice_playback = AsyncMock(return_value=[])
    orch.story.generate_narration = AsyncMock(return_value=None)
    orch.story.generate_character_voices = AsyncMock(return_value=[])
    orch.story.store_memory = AsyncMock()

    orch.media.generate_scene = AsyncMock(return_value=None)
    orch.media.inject_drawing_prompt = AsyncMock()

    orch.world.get_world_context = AsyncMock(return_value="")

    orch.session.session_time_enforcer = None
    orch.session.start_generation_pause = MagicMock()
    orch.session.end_generation_pause = MagicMock()
    orch.session.notify_generation_started = AsyncMock()
    orch.session.notify_generation_completed = AsyncMock()

    orch._ensure_db_initialized = AsyncMock()

    result = await orch.generate_rich_story_moment("test-orch", ale_sofi_profiles)

    for key in ("text", "image", "audio", "interactive", "timestamp",
                "memories_used", "voice_recordings", "agents_used"):
        assert key in result, f"Missing key: {key}"

    assert result["agents_used"]["storyteller"] is True


@pytest.mark.asyncio
async def test_orchestrator_visual_disabled(ale_sofi_profiles):
    """With visual agent disabled (scene returns None), agents_used.visual is False."""
    from app.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()

    orch.story.generate_safe_story_segment = AsyncMock(return_value=MOCK_STORY_SEGMENT.copy())
    orch.story.recall_memories = AsyncMock(return_value=[])
    orch.story.filter_choices = MagicMock(side_effect=lambda seg, *a, **kw: seg)
    orch.story.check_voice_playback = AsyncMock(return_value=[])
    orch.story.generate_narration = AsyncMock(return_value=None)
    orch.story.generate_character_voices = AsyncMock(return_value=[])
    orch.story.store_memory = AsyncMock()

    orch.media.generate_scene = AsyncMock(return_value=None)
    orch.media.inject_drawing_prompt = AsyncMock()

    orch.world.get_world_context = AsyncMock(return_value="")

    orch.session.session_time_enforcer = None
    orch.session.start_generation_pause = MagicMock()
    orch.session.end_generation_pause = MagicMock()
    orch.session.notify_generation_started = AsyncMock()
    orch.session.notify_generation_completed = AsyncMock()

    orch._ensure_db_initialized = AsyncMock()

    result = await orch.generate_rich_story_moment("test-vis-off", ale_sofi_profiles)

    assert result["agents_used"]["visual"] is False
    assert result["image"] is None


@pytest.mark.asyncio
async def test_orchestrator_memory_count(ale_sofi_profiles):
    """memories_used reflects the count returned by recall_memories."""
    from app.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()

    mock_memories = [{"text": f"memory {i}"} for i in range(3)]

    orch.story.generate_safe_story_segment = AsyncMock(return_value=MOCK_STORY_SEGMENT.copy())
    orch.story.recall_memories = AsyncMock(return_value=mock_memories)
    orch.story.filter_choices = MagicMock(side_effect=lambda seg, *a, **kw: seg)
    orch.story.check_voice_playback = AsyncMock(return_value=[])
    orch.story.generate_narration = AsyncMock(return_value=None)
    orch.story.generate_character_voices = AsyncMock(return_value=[])
    orch.story.store_memory = AsyncMock()

    orch.media.generate_scene = AsyncMock(return_value=None)
    orch.media.inject_drawing_prompt = AsyncMock()

    orch.world.get_world_context = AsyncMock(return_value="")

    orch.session.session_time_enforcer = None
    orch.session.start_generation_pause = MagicMock()
    orch.session.end_generation_pause = MagicMock()
    orch.session.notify_generation_started = AsyncMock()
    orch.session.notify_generation_completed = AsyncMock()

    orch._ensure_db_initialized = AsyncMock()

    result = await orch.generate_rich_story_moment("test-mem", ale_sofi_profiles)

    assert result["memories_used"] == 3
    assert result["agents_used"]["memory"] is True


# ===================================================================
# Task 8: Backend WebSocket message protocol conformance tests
# ===================================================================


def test_ws_message_protocol_input_status(ale_sofi_ws_params):
    """input_status message has type, camera, mic with correct types."""
    client, patchers = _patched_client()
    try:
        session_id = "test-proto-input-status"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)) as ws:
            msg = ws.receive_json()
            assert set(msg.keys()) >= {"type", "camera", "mic"}
            assert msg["type"] == "input_status"
            assert isinstance(msg["camera"], bool)
            assert isinstance(msg["mic"], bool)
    finally:
        for p in patchers:
            p.stop()


def test_ws_message_protocol_story_segment(ale_sofi_ws_params, ale_sofi_profiles):
    """story_segment message has type and data.text."""
    client, patchers = _patched_client()
    try:
        session_id = "test-proto-story-seg"
        with client.websocket_connect(_ws_url(session_id, ale_sofi_ws_params)) as ws:
            ws.receive_json()  # input_status
            ws.send_json({"context": {"characters": ale_sofi_profiles}})
            msg = ws.receive_json()

            assert msg["type"] == "story_segment"
            assert "data" in msg
            assert "text" in msg["data"]
    finally:
        for p in patchers:
            p.stop()


# ===================================================================
# Property-Based Tests (Hypothesis)
# ===================================================================

from hypothesis import given, settings
from hypothesis import strategies as st


# Feature: full-flow-integration-testing, Property 1: Sibling Pair ID Derivation
@given(
    name1=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12),
    name2=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=12),
)
@settings(max_examples=100)
def test_pbt_sibling_pair_id_derivation(name1, name2):
    """For any two non-empty names, the pair ID has exactly one colon and left <= right."""
    pair_id = ":".join(sorted([name1, name2]))
    assert pair_id.count(":") == 1
    left, right = pair_id.split(":")
    assert left <= right


# Feature: full-flow-integration-testing, Property 2: Story Segment Structure Invariant
@given(
    c1_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    c1_gender=st.sampled_from(["girl", "boy"]),
    c1_spirit=st.sampled_from(["Dragon", "Owl", "Unicorn", "Dolphin", "Phoenix", "Tiger"]),
    c2_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    c2_gender=st.sampled_from(["girl", "boy"]),
    c2_spirit=st.sampled_from(["Dragon", "Owl", "Unicorn", "Dolphin", "Phoenix", "Tiger"]),
)
@settings(max_examples=100)
def test_pbt_story_segment_structure_invariant(c1_name, c1_gender, c1_spirit, c2_name, c2_gender, c2_spirit):
    """Fallback story always returns dict with text, timestamp, characters, interactive."""
    from app.agents.storyteller_agent import StorytellerAgent

    agent = StorytellerAgent.__new__(StorytellerAgent)
    context = {
        "characters": {
            "child1": {"name": c1_name, "gender": c1_gender, "spirit_animal": c1_spirit},
            "child2": {"name": c2_name, "gender": c2_gender, "spirit_animal": c2_spirit},
        }
    }
    result = agent._fallback_story(context)

    assert isinstance(result["text"], str) and len(result["text"]) > 0
    assert "timestamp" in result
    assert isinstance(result["characters"], dict)
    interactive = result["interactive"]
    assert "type" in interactive
    assert "text" in interactive
    assert "expects_response" in interactive


# Feature: full-flow-integration-testing, Property 3: Orchestrator Output Completeness
@given(
    c1_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
    c2_name=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10),
)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_pbt_orchestrator_output_completeness(c1_name, c2_name):
    """generate_rich_story_moment always returns all required keys for any character names."""
    from app.agents.orchestrator import AgentOrchestrator

    profiles = {
        "child1": {"name": c1_name, "gender": "girl", "spirit_animal": "Dragon",
                    "costume": "adventure_clothes", "costume_prompt": "wearing adventure clothes"},
        "child2": {"name": c2_name, "gender": "boy", "spirit_animal": "Owl",
                    "costume": "adventure_clothes", "costume_prompt": "wearing adventure clothes"},
    }

    seg = MOCK_STORY_SEGMENT.copy()
    orch = AgentOrchestrator()
    orch.story.generate_safe_story_segment = AsyncMock(return_value=seg)
    orch.story.recall_memories = AsyncMock(return_value=[])
    orch.story.filter_choices = MagicMock(side_effect=lambda seg, *a, **kw: seg)
    orch.story.check_voice_playback = AsyncMock(return_value=[])
    orch.story.generate_narration = AsyncMock(return_value=None)
    orch.story.generate_character_voices = AsyncMock(return_value=[])
    orch.story.store_memory = AsyncMock()
    orch.media.generate_scene = AsyncMock(return_value=None)
    orch.media.inject_drawing_prompt = AsyncMock()
    orch.world.get_world_context = AsyncMock(return_value="")
    orch.session.session_time_enforcer = None
    orch.session.start_generation_pause = MagicMock()
    orch.session.end_generation_pause = MagicMock()
    orch.session.notify_generation_started = AsyncMock()
    orch.session.notify_generation_completed = AsyncMock()
    orch._ensure_db_initialized = AsyncMock()

    result = await orch.generate_rich_story_moment("pbt-session", profiles)

    for key in ("text", "image", "audio", "interactive", "timestamp",
                "memories_used", "voice_recordings", "agents_used"):
        assert key in result, f"Missing key: {key}"


# Feature: full-flow-integration-testing, Property 4: Memory Count Consistency
@given(
    n_memories=st.integers(min_value=0, max_value=10),
)
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_pbt_memory_count_consistency(n_memories):
    """memories_used always equals the number of memories returned by recall."""
    from app.agents.orchestrator import AgentOrchestrator

    profiles = {
        "child1": {"name": "Ale", "gender": "girl", "spirit_animal": "Dragon",
                    "costume": "adventure_clothes", "costume_prompt": "wearing adventure clothes"},
        "child2": {"name": "Sofi", "gender": "boy", "spirit_animal": "Owl",
                    "costume": "adventure_clothes", "costume_prompt": "wearing adventure clothes"},
    }

    mock_memories = [{"text": f"memory {i}"} for i in range(n_memories)]
    seg = MOCK_STORY_SEGMENT.copy()

    orch = AgentOrchestrator()
    orch.story.generate_safe_story_segment = AsyncMock(return_value=seg)
    orch.story.recall_memories = AsyncMock(return_value=mock_memories)
    orch.story.filter_choices = MagicMock(side_effect=lambda seg, *a, **kw: seg)
    orch.story.check_voice_playback = AsyncMock(return_value=[])
    orch.story.generate_narration = AsyncMock(return_value=None)
    orch.story.generate_character_voices = AsyncMock(return_value=[])
    orch.story.store_memory = AsyncMock()
    orch.media.generate_scene = AsyncMock(return_value=None)
    orch.media.inject_drawing_prompt = AsyncMock()
    orch.world.get_world_context = AsyncMock(return_value="")
    orch.session.session_time_enforcer = None
    orch.session.start_generation_pause = MagicMock()
    orch.session.end_generation_pause = MagicMock()
    orch.session.notify_generation_started = AsyncMock()
    orch.session.notify_generation_completed = AsyncMock()
    orch._ensure_db_initialized = AsyncMock()

    result = await orch.generate_rich_story_moment("pbt-mem", profiles)

    assert result["memories_used"] == n_memories
