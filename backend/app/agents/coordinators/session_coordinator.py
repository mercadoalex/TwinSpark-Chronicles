"""SessionCoordinator — session lifecycle, emergency stop, time enforcement."""

import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SessionCoordinator:
    """Manages session lifecycle: cancel, time checks, generation pause, WS notifications."""

    def __init__(self) -> None:
        self.session_time_enforcer = None  # SessionTimeEnforcer, set from main.py
        self.ws_manager = None  # ConnectionManager, set from main.py
        self._session_tasks: Dict[str, set[asyncio.Task]] = {}

    async def cancel_session(self, session_id: str) -> Dict:
        """Cancel all in-flight tasks for a session and return state summary."""
        if self.session_time_enforcer is not None:
            self.session_time_enforcer.end_session(session_id)

        tasks = self._session_tasks.pop(session_id, set())
        cancelled_count = 0
        for task in tasks:
            if not task.done():
                task.cancel()
                cancelled_count += 1

        if tasks:
            await asyncio.wait(tasks, timeout=2.0)

        logger.info(
            "Emergency stop: session=%s cancelled=%d total=%d",
            session_id, cancelled_count, len(tasks),
        )

        return {
            "session_id": session_id,
            "cancelled_tasks": cancelled_count,
            "session_saved": True,
            "status": "stopped",
        }

    def check_time(self, session_id: str):
        """Delegate time check to session_time_enforcer. Returns None if no enforcer."""
        if self.session_time_enforcer is None:
            return None
        return self.session_time_enforcer.check_time(session_id)

    def is_expired(self, session_id: str) -> bool:
        """Return True if the session time has expired."""
        if self.session_time_enforcer is None:
            return False
        time_check = self.session_time_enforcer.check_time(session_id)
        return time_check.is_expired

    def start_generation_pause(self, session_id: str) -> None:
        """Signal generation pause start to the time enforcer."""
        if self.session_time_enforcer is not None:
            self.session_time_enforcer.start_generation_pause(session_id)

    def end_generation_pause(self, session_id: str) -> None:
        """Signal generation pause end to the time enforcer."""
        if self.session_time_enforcer is not None:
            self.session_time_enforcer.end_generation_pause(session_id)

    async def notify_generation_started(self, session_id: str) -> None:
        """Send GENERATION_STARTED via WebSocket."""
        if self.ws_manager is not None:
            await self.ws_manager.send_story(session_id, {
                "type": "GENERATION_STARTED",
                "session_id": session_id,
            })

    async def notify_generation_completed(self, session_id: str) -> None:
        """Send GENERATION_COMPLETED via WebSocket."""
        if self.ws_manager is not None:
            await self.ws_manager.send_story(session_id, {
                "type": "GENERATION_COMPLETED",
                "session_id": session_id,
            })

    async def notify_session_expired(self, session_id: str) -> None:
        """Send SESSION_TIME_EXPIRED via WebSocket."""
        if self.ws_manager is not None:
            await self.ws_manager.send_story(session_id, {
                "type": "SESSION_TIME_EXPIRED",
                "session_id": session_id,
            })

    def track_task(self, session_id: str, task: asyncio.Task) -> None:
        """Register a background processing task for a session."""
        if session_id not in self._session_tasks:
            self._session_tasks[session_id] = set()
        self._session_tasks[session_id].add(task)
        task.add_done_callback(
            lambda t: self._session_tasks.get(session_id, set()).discard(t)
        )
