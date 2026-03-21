"""Unit tests for SessionTimeEnforcer.

Validates core functionality: session lifecycle, time checking,
pause tracking, extensions, resume, and graceful handling of
missing/invalid sessions.
"""

from __future__ import annotations

import time
from unittest.mock import patch

from app.services.session_time_enforcer import SessionTimeEnforcer, TimeCheckResult


class TestSessionTimeEnforcer:
    """Tests for SessionTimeEnforcer."""

    def test_start_session_records_state(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        state = enforcer._sessions["s1"]
        assert state.time_limit_seconds == 1800
        assert state.total_paused_seconds == 0.0
        assert state.ended is False
        assert state.generation_pause_start is None
        assert state.previous_duration_seconds == 0.0

    def test_check_time_not_expired(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        result = enforcer.check_time("s1")
        assert result.is_expired is False
        assert result.total_limit_seconds == 1800
        assert result.elapsed_seconds >= 0
        assert result.remaining_seconds > 0

    def test_check_time_expired(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 1)

        # Simulate time passing by adjusting start_time
        enforcer._sessions["s1"].start_time = time.monotonic() - 120

        result = enforcer.check_time("s1")
        assert result.is_expired is True
        assert result.remaining_seconds == 0.0

    def test_check_time_unknown_session(self) -> None:
        enforcer = SessionTimeEnforcer()
        result = enforcer.check_time("unknown")
        assert result.is_expired is False
        assert result.elapsed_seconds == 0.0
        assert result.remaining_seconds == 0.0
        assert result.total_limit_seconds == 0.0

    def test_extend_time(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        new_total = enforcer.extend_time("s1", 15)
        assert new_total == 45
        assert enforcer._sessions["s1"].time_limit_seconds == 2700

    def test_extend_time_unknown_session(self) -> None:
        enforcer = SessionTimeEnforcer()
        assert enforcer.extend_time("unknown", 10) == 0

    def test_generation_pause_tracking(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        enforcer.start_generation_pause("s1")
        assert enforcer._sessions["s1"].generation_pause_start is not None

        enforcer.end_generation_pause("s1")
        assert enforcer._sessions["s1"].generation_pause_start is None
        assert enforcer._sessions["s1"].total_paused_seconds >= 0

    def test_double_pause_ignored(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        enforcer.start_generation_pause("s1")
        first_start = enforcer._sessions["s1"].generation_pause_start

        # Second pause call should be ignored
        enforcer.start_generation_pause("s1")
        assert enforcer._sessions["s1"].generation_pause_start == first_start

    def test_end_pause_without_start_ignored(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        # Should not raise
        enforcer.end_generation_pause("s1")
        assert enforcer._sessions["s1"].total_paused_seconds == 0.0

    def test_pause_on_ended_session_ignored(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)
        enforcer.end_session("s1")

        # Should not raise
        enforcer.start_generation_pause("s1")
        assert enforcer._sessions["s1"].generation_pause_start is None

    def test_end_session(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        duration = enforcer.end_session("s1")
        assert duration >= 0
        assert enforcer._sessions["s1"].ended is True
        assert enforcer._sessions["s1"].end_time is not None

    def test_end_session_double_call(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        d1 = enforcer.end_session("s1")
        d2 = enforcer.end_session("s1")
        assert d2 >= d1  # Should return same/similar duration

    def test_end_session_finalizes_active_pause(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        enforcer.start_generation_pause("s1")
        enforcer.end_session("s1")

        state = enforcer._sessions["s1"]
        assert state.generation_pause_start is None
        assert state.total_paused_seconds >= 0

    def test_get_session_duration(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        duration = enforcer.get_session_duration("s1")
        assert duration >= 0

    def test_get_session_duration_unknown(self) -> None:
        enforcer = SessionTimeEnforcer()
        assert enforcer.get_session_duration("unknown") == 0.0

    def test_resume_session(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        enforcer.resume_session("s1", 300.0)
        assert enforcer._sessions["s1"].previous_duration_seconds == 300.0

        duration = enforcer.get_session_duration("s1")
        assert duration >= 300.0

    def test_resume_session_unknown(self) -> None:
        enforcer = SessionTimeEnforcer()
        # Should not raise
        enforcer.resume_session("unknown", 100.0)

    def test_remove_session(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        enforcer.remove_session("s1")
        assert "s1" not in enforcer._sessions

    def test_remove_session_unknown(self) -> None:
        enforcer = SessionTimeEnforcer()
        # Should not raise
        enforcer.remove_session("unknown")

    def test_elapsed_excludes_pauses(self) -> None:
        enforcer = SessionTimeEnforcer()
        enforcer.start_session("s1", 30)

        # Simulate: 100s wall-clock, 20s paused
        state = enforcer._sessions["s1"]
        now = time.monotonic()
        state.start_time = now - 100
        state.total_paused_seconds = 20.0

        result = enforcer.check_time("s1")
        # elapsed should be ~80s (100 wall - 20 paused)
        assert 79.0 <= result.elapsed_seconds <= 81.0
        assert result.remaining_seconds == pytest.approx(1800 - result.elapsed_seconds, abs=0.1)


# Need pytest for approx
import pytest
