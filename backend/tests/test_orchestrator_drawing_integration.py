"""Unit tests for Orchestrator drawing prompt injection (Task 4.2).

Tests cover:
- Drawing prompt detection and DRAWING_PROMPT message sent via ws_manager
- Duration clamping using DrawingSyncService.clamp_duration with remaining session time
- Session expiry during drawing sends DRAWING_END with reason "session_expired"
- drawing_context passed through to story_context for post-drawing beats
- No crash when story_segment has no drawing_prompt field
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.services.content_filter import ContentRating
from app.services.session_time_enforcer import TimeCheckResult


STORY_BASE = {
    "text": "The twins entered the enchanted forest.",
    "image": None,
    "audio": {},
    "interactive": {},
    "timestamp": "2024-06-01T12:00:00Z",
}

CHARACTERS = {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}}


def _make_orchestrator():
    """Create an AgentOrchestrator with all agents mocked out."""
    from app.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()
    orch.storyteller = MagicMock()
    orch.storyteller.generate_story_segment = AsyncMock(return_value=dict(STORY_BASE))
    orch.storyteller._fallback_story = MagicMock(return_value=dict(STORY_BASE))
    orch.visual = MagicMock(enabled=False)
    orch.voice = MagicMock(enabled=False)
    orch.memory = MagicMock(enabled=False)
    orch.content_filter = MagicMock()
    orch.content_filter.scan = MagicMock(
        return_value=MagicMock(rating=ContentRating.SAFE, reason=None, matched_terms=[])
    )
    orch._db_initialized = True
    orch._db_conn = MagicMock()
    orch._db_conn.fetch_all = AsyncMock(return_value=[])
    orch._playback_integrator = None
    orch._world_db = MagicMock()
    orch._world_db.load_world_state = AsyncMock(return_value={})
    orch._world_state_cache = {}
    return orch


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Drawing prompt detection and DRAWING_PROMPT message
# ---------------------------------------------------------------------------

class TestDrawingPromptInjection:
    """Task 4.2: Drawing prompt injection into orchestrator."""

    def test_drawing_prompt_sent_when_present(self):
        """When story_segment contains drawing_prompt, DRAWING_PROMPT is sent."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw the magic door!"
        story_with_prompt["drawing_duration"] = 60
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        # No time enforcer — should still send prompt
        orch.session_time_enforcer = None

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS, user_input="open the door",
        ))

        # Find the DRAWING_PROMPT call
        drawing_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_calls) == 1
        msg = drawing_calls[0][0][1]
        assert msg["prompt"] == "Draw the magic door!"
        assert msg["duration"] == 60
        assert msg["session_id"] == "s1"

    def test_no_drawing_prompt_when_absent(self):
        """When story_segment has no drawing_prompt, no DRAWING_PROMPT is sent."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS, user_input="walk forward",
        ))

        drawing_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_calls) == 0

    def test_no_crash_when_ws_manager_is_none(self):
        """When ws_manager is None, drawing prompt is silently skipped."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw a castle!"
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)
        orch.ws_manager = None
        orch.session_time_enforcer = None

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
        ))
        assert "text" in result  # Story still returned


# ---------------------------------------------------------------------------
# Duration clamping with remaining session time
# ---------------------------------------------------------------------------

class TestDrawingDurationClamping:
    """Duration is clamped via DrawingSyncService.clamp_duration with remaining time."""

    def test_duration_clamped_to_remaining_time(self):
        """When remaining time < requested duration, duration is clamped."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw a rainbow!"
        story_with_prompt["drawing_duration"] = 90
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        enforcer = MagicMock()
        enforcer.check_time = MagicMock(return_value=TimeCheckResult(
            is_expired=False,
            elapsed_seconds=500.0,
            remaining_seconds=45.0,
            total_limit_seconds=600.0,
        ))
        enforcer.start_generation_pause = MagicMock()
        enforcer.end_generation_pause = MagicMock()
        orch.session_time_enforcer = enforcer

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS, user_input="paint",
        ))

        drawing_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_calls) == 1
        # 45 seconds remaining, requested 90 → clamped to 45
        assert drawing_calls[0][0][1]["duration"] == 45

    def test_duration_clamped_to_range(self):
        """Duration below 30 is clamped to 30, above 120 to 120."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw a star!"
        story_with_prompt["drawing_duration"] = 10  # below minimum
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        enforcer = MagicMock()
        enforcer.check_time = MagicMock(return_value=TimeCheckResult(
            is_expired=False,
            elapsed_seconds=100.0,
            remaining_seconds=500.0,
            total_limit_seconds=600.0,
        ))
        enforcer.start_generation_pause = MagicMock()
        enforcer.end_generation_pause = MagicMock()
        orch.session_time_enforcer = enforcer

        _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
        ))

        drawing_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_calls) == 1
        # 10 → clamped to 30 (minimum)
        assert drawing_calls[0][0][1]["duration"] == 30

    def test_default_duration_when_not_specified(self):
        """When drawing_duration is absent, defaults to 60."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw something!"
        # No drawing_duration key
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
        ))

        drawing_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_calls) == 1
        assert drawing_calls[0][0][1]["duration"] == 60


# ---------------------------------------------------------------------------
# Session expiry during drawing
# ---------------------------------------------------------------------------

class TestSessionExpiryDuringDrawing:
    """If session time expires when drawing prompt is triggered, send DRAWING_END."""

    def test_expired_session_sends_drawing_end(self):
        """When session is expired at drawing time, DRAWING_END is sent instead."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw a tree!"
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        # First check_time call (in generate_rich_story_moment) returns not expired
        # Second check_time call (in _do_generate for drawing) returns expired
        enforcer = MagicMock()
        enforcer.check_time = MagicMock(side_effect=[
            TimeCheckResult(is_expired=False, elapsed_seconds=590.0,
                            remaining_seconds=10.0, total_limit_seconds=600.0),
            TimeCheckResult(is_expired=True, elapsed_seconds=601.0,
                            remaining_seconds=0.0, total_limit_seconds=600.0),
        ])
        enforcer.start_generation_pause = MagicMock()
        enforcer.end_generation_pause = MagicMock()
        orch.session_time_enforcer = enforcer

        _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
        ))

        drawing_end_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_END"
        ]
        assert len(drawing_end_calls) == 1
        assert drawing_end_calls[0][0][1]["reason"] == "session_expired"

        # No DRAWING_PROMPT should have been sent
        drawing_prompt_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_PROMPT"
        ]
        assert len(drawing_prompt_calls) == 0


# ---------------------------------------------------------------------------
# Drawing context passed to story generation
# ---------------------------------------------------------------------------

class TestDrawingContextInjection:
    """drawing_context kwarg is forwarded into story_context for post-drawing beats."""

    def test_drawing_context_in_story_context(self):
        """When drawing_context is passed, it appears in the story_context."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        drawing_ctx = {"prompt": "Draw the magic door!", "sibling_names": ["Ale", "Sofi"]}

        _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
            user_input="continue", drawing_context=drawing_ctx,
        ))

        # Verify the storyteller received drawing_context in the context
        call_args = orch.storyteller.generate_story_segment.call_args
        context = call_args.kwargs.get("context") or call_args[1].get("context") or call_args[0][0]
        assert context.get("drawing_context") == drawing_ctx

    def test_drawing_image_path_in_result(self):
        """When drawing_context includes image_path, result contains drawing_image_path."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        drawing_ctx = {
            "prompt": "Draw the magic door!",
            "sibling_names": ["Ale", "Sofi"],
            "image_path": "assets/generated_images/drawing_1700000000.png",
        }

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
            user_input="continue", drawing_context=drawing_ctx,
        ))

        assert result["drawing_image_path"] == "assets/generated_images/drawing_1700000000.png"

    def test_no_drawing_image_path_without_context(self):
        """When no drawing_context is passed, result has no drawing_image_path."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
            user_input="walk forward",
        ))

        assert "drawing_image_path" not in result

    def test_drawing_context_with_empty_image_path(self):
        """When drawing_context has empty image_path (render failure), it is still included."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        drawing_ctx = {
            "prompt": "Draw a castle!",
            "sibling_names": ["Ale", "Sofi"],
            "image_path": "",
        }

        result = _run(orch.generate_rich_story_moment(
            session_id="s1", characters=CHARACTERS,
            user_input="continue", drawing_context=drawing_ctx,
        ))

        assert result["drawing_image_path"] == ""


# ---------------------------------------------------------------------------
# Drawing time watchdog (Task 9.1)
# ---------------------------------------------------------------------------

class TestDrawingTimeWatchdog:
    """Task 9.1: Background watchdog expires drawing when session time runs out."""

    def test_watchdog_sends_drawing_end_on_expiry(self):
        """Watchdog sends DRAWING_END with reason session_expired when time runs out."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        # Simulate expiry on first check
        enforcer = MagicMock()
        enforcer.check_time = MagicMock(return_value=TimeCheckResult(
            is_expired=True,
            elapsed_seconds=600.0,
            remaining_seconds=0.0,
            total_limit_seconds=600.0,
        ))
        orch.session_time_enforcer = enforcer

        _run(orch._drawing_time_watchdog("s1", 60))

        drawing_end_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_END"
        ]
        assert len(drawing_end_calls) == 1
        assert drawing_end_calls[0][0][1]["reason"] == "session_expired"
        assert drawing_end_calls[0][0][1]["session_id"] == "s1"

    def test_watchdog_no_message_when_not_expired(self):
        """Watchdog completes silently when session does not expire during drawing."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        enforcer = MagicMock()
        enforcer.check_time = MagicMock(return_value=TimeCheckResult(
            is_expired=False,
            elapsed_seconds=100.0,
            remaining_seconds=500.0,
            total_limit_seconds=600.0,
        ))
        orch.session_time_enforcer = enforcer

        # Use a very short duration so the loop finishes quickly
        _run(orch._drawing_time_watchdog("s1", 1))

        drawing_end_calls = [
            c for c in ws.send_story.call_args_list
            if c[0][1].get("type") == "DRAWING_END"
        ]
        assert len(drawing_end_calls) == 0

    def test_watchdog_exits_when_no_enforcer(self):
        """Watchdog exits gracefully when session_time_enforcer is None."""
        orch = _make_orchestrator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws
        orch.session_time_enforcer = None

        # Should not raise
        _run(orch._drawing_time_watchdog("s1", 1))

        assert ws.send_story.call_count == 0

    def test_watchdog_started_when_drawing_prompt_sent(self):
        """When a drawing prompt is sent with time enforcer, watchdog task is created."""
        orch = _make_orchestrator()
        story_with_prompt = dict(STORY_BASE)
        story_with_prompt["drawing_prompt"] = "Draw a dragon!"
        story_with_prompt["drawing_duration"] = 60
        orch.storyteller.generate_story_segment = AsyncMock(return_value=story_with_prompt)

        ws = MagicMock()
        ws.send_story = AsyncMock()
        orch.ws_manager = ws

        enforcer = MagicMock()
        enforcer.check_time = MagicMock(return_value=TimeCheckResult(
            is_expired=False,
            elapsed_seconds=100.0,
            remaining_seconds=500.0,
            total_limit_seconds=600.0,
        ))
        enforcer.start_generation_pause = MagicMock()
        enforcer.end_generation_pause = MagicMock()
        orch.session_time_enforcer = enforcer

        with patch("asyncio.create_task") as mock_create_task:
            mock_create_task.return_value = MagicMock()
            _run(orch.generate_rich_story_moment(
                session_id="s1", characters=CHARACTERS, user_input="draw",
            ))

            # Verify create_task was called with the watchdog coroutine
            watchdog_calls = [
                c for c in mock_create_task.call_args_list
                if "drawing_time_watchdog" in str(c)
            ]
            assert len(watchdog_calls) >= 1
