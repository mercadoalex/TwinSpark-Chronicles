"""Server-side session time enforcement.

Tracks per-session elapsed time using monotonic clock and enforces
time limits independently of the frontend timer. Pauses during AI
generation are excluded from elapsed time calculations.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.4, 2.5, 7.7
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class TimeCheckResult:
    """Result of checking a session's time status."""

    is_expired: bool
    elapsed_seconds: float
    remaining_seconds: float
    total_limit_seconds: float


@dataclass
class _SessionTimeState:
    """Internal per-session tracking state."""

    session_id: str
    start_time: float  # time.monotonic()
    time_limit_seconds: float
    generation_pause_start: float | None = None
    total_paused_seconds: float = 0.0
    ended: bool = False
    end_time: float | None = None
    previous_duration_seconds: float = 0.0


class SessionTimeEnforcer:
    """Tracks per-session elapsed time and enforces time limits server-side."""

    def __init__(self) -> None:
        self._sessions: dict[str, _SessionTimeState] = {}

    def start_session(self, session_id: str, time_limit_minutes: int) -> None:
        """Record session start timestamp and configured time limit."""
        self._sessions[session_id] = _SessionTimeState(
            session_id=session_id,
            start_time=time.monotonic(),
            time_limit_seconds=time_limit_minutes * 60,
        )

    def _get_effective_elapsed(self, state: _SessionTimeState) -> float:
        """Compute elapsed seconds excluding generation pauses."""
        now = time.monotonic()
        end = state.end_time if state.ended and state.end_time is not None else now
        wall_clock = end - state.start_time

        paused = state.total_paused_seconds
        if state.generation_pause_start is not None and not state.ended:
            paused += now - state.generation_pause_start

        return max(0.0, wall_clock - paused + state.previous_duration_seconds)

    def check_time(self, session_id: str) -> TimeCheckResult:
        """Check if session has exceeded its time limit.

        Returns a safe default (not expired) for unknown sessions.
        """
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("check_time called for unknown session %s", session_id)
            return TimeCheckResult(
                is_expired=False,
                elapsed_seconds=0.0,
                remaining_seconds=0.0,
                total_limit_seconds=0.0,
            )

        elapsed = self._get_effective_elapsed(state)
        remaining = max(0.0, state.time_limit_seconds - elapsed)
        is_expired = elapsed >= state.time_limit_seconds

        return TimeCheckResult(
            is_expired=is_expired,
            elapsed_seconds=elapsed,
            remaining_seconds=remaining,
            total_limit_seconds=state.time_limit_seconds,
        )

    def extend_time(self, session_id: str, additional_minutes: int) -> int:
        """Add minutes to session time limit. Returns new total limit in minutes."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("extend_time called for unknown session %s", session_id)
            return 0

        state.time_limit_seconds += additional_minutes * 60
        return int(state.time_limit_seconds / 60)

    def start_generation_pause(self, session_id: str) -> None:
        """Record start of a generation pause period."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("start_generation_pause called for unknown session %s", session_id)
            return

        if state.ended:
            logger.warning("start_generation_pause called on ended session %s", session_id)
            return

        if state.generation_pause_start is not None:
            logger.warning("start_generation_pause called while already paused for session %s", session_id)
            return

        state.generation_pause_start = time.monotonic()

    def end_generation_pause(self, session_id: str) -> None:
        """Record end of a generation pause period."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("end_generation_pause called for unknown session %s", session_id)
            return

        if state.generation_pause_start is None:
            logger.warning("end_generation_pause called without active pause for session %s", session_id)
            return

        pause_duration = time.monotonic() - state.generation_pause_start
        state.total_paused_seconds += pause_duration
        state.generation_pause_start = None

    def get_session_duration(self, session_id: str) -> float:
        """Compute total wall-clock duration in seconds (start to now/end)."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("get_session_duration called for unknown session %s", session_id)
            return 0.0

        end = state.end_time if state.ended and state.end_time is not None else time.monotonic()
        return (end - state.start_time) + state.previous_duration_seconds

    def end_session(self, session_id: str) -> float:
        """Mark session ended, return total duration in seconds."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("end_session called for unknown session %s", session_id)
            return 0.0

        if state.ended:
            logger.warning("end_session called on already ended session %s", session_id)
            return self.get_session_duration(session_id)

        state.end_time = time.monotonic()
        state.ended = True

        # Finalize any active pause
        if state.generation_pause_start is not None:
            state.total_paused_seconds += state.end_time - state.generation_pause_start
            state.generation_pause_start = None

        return self.get_session_duration(session_id)

    def resume_session(self, session_id: str, previous_duration_seconds: float) -> None:
        """Resume tracking from a previously recorded duration (snapshot restore)."""
        state = self._sessions.get(session_id)
        if state is None:
            logger.warning("resume_session called for unknown session %s", session_id)
            return

        state.previous_duration_seconds = previous_duration_seconds

    def remove_session(self, session_id: str) -> None:
        """Clean up tracking data for a session."""
        removed = self._sessions.pop(session_id, None)
        if removed is None:
            logger.warning("remove_session called for unknown session %s", session_id)
