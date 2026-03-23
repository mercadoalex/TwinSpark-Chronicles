"""Unit tests for SessionCoordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agents.coordinators.session_coordinator import SessionCoordinator


class TestCancelSession:
    """cancel_session cancels tracked tasks and returns summary."""

    @pytest.mark.asyncio
    async def test_cancels_tracked_tasks(self):
        sc = SessionCoordinator()
        t1 = asyncio.ensure_future(asyncio.sleep(100))
        t2 = asyncio.ensure_future(asyncio.sleep(100))
        sc._session_tasks["s1"] = {t1, t2}

        result = await sc.cancel_session("s1")

        assert result["cancelled_tasks"] == 2
        assert result["status"] == "stopped"
        assert result["session_saved"] is True
        assert "s1" not in sc._session_tasks

    @pytest.mark.asyncio
    async def test_cancel_empty_session(self):
        sc = SessionCoordinator()
        result = await sc.cancel_session("unknown")
        assert result["cancelled_tasks"] == 0
        assert result["status"] == "stopped"

    @pytest.mark.asyncio
    async def test_ends_time_tracking(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        sc.session_time_enforcer = enforcer
        await sc.cancel_session("s1")
        enforcer.end_session.assert_called_once_with("s1")

    @pytest.mark.asyncio
    async def test_no_crash_when_enforcer_none(self):
        sc = SessionCoordinator()
        sc.session_time_enforcer = None
        result = await sc.cancel_session("s1")
        assert result["status"] == "stopped"


class TestCheckTime:
    """check_time delegates to enforcer or returns None."""

    def test_delegates_to_enforcer(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        enforcer.check_time.return_value = "time_result"
        sc.session_time_enforcer = enforcer
        assert sc.check_time("s1") == "time_result"
        enforcer.check_time.assert_called_once_with("s1")

    def test_returns_none_when_no_enforcer(self):
        sc = SessionCoordinator()
        assert sc.check_time("s1") is None


class TestIsExpired:
    """is_expired checks enforcer or returns False."""

    def test_returns_true_when_expired(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        enforcer.check_time.return_value = MagicMock(is_expired=True)
        sc.session_time_enforcer = enforcer
        assert sc.is_expired("s1") is True

    def test_returns_false_when_not_expired(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        enforcer.check_time.return_value = MagicMock(is_expired=False)
        sc.session_time_enforcer = enforcer
        assert sc.is_expired("s1") is False

    def test_returns_false_when_no_enforcer(self):
        sc = SessionCoordinator()
        assert sc.is_expired("s1") is False


class TestGenerationPause:
    """start/end generation pause delegates to enforcer."""

    def test_start_pause(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        sc.session_time_enforcer = enforcer
        sc.start_generation_pause("s1")
        enforcer.start_generation_pause.assert_called_once_with("s1")

    def test_end_pause(self):
        sc = SessionCoordinator()
        enforcer = MagicMock()
        sc.session_time_enforcer = enforcer
        sc.end_generation_pause("s1")
        enforcer.end_generation_pause.assert_called_once_with("s1")

    def test_no_crash_when_no_enforcer(self):
        sc = SessionCoordinator()
        sc.start_generation_pause("s1")  # should not raise
        sc.end_generation_pause("s1")


class TestNotifications:
    """WS notifications delegate to ws_manager."""

    @pytest.mark.asyncio
    async def test_notify_generation_started(self):
        sc = SessionCoordinator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        sc.ws_manager = ws
        await sc.notify_generation_started("s1")
        ws.send_story.assert_called_once()
        assert ws.send_story.call_args[0][1]["type"] == "GENERATION_STARTED"

    @pytest.mark.asyncio
    async def test_notify_generation_completed(self):
        sc = SessionCoordinator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        sc.ws_manager = ws
        await sc.notify_generation_completed("s1")
        assert ws.send_story.call_args[0][1]["type"] == "GENERATION_COMPLETED"

    @pytest.mark.asyncio
    async def test_notify_session_expired(self):
        sc = SessionCoordinator()
        ws = MagicMock()
        ws.send_story = AsyncMock()
        sc.ws_manager = ws
        await sc.notify_session_expired("s1")
        assert ws.send_story.call_args[0][1]["type"] == "SESSION_TIME_EXPIRED"

    @pytest.mark.asyncio
    async def test_no_crash_when_ws_none(self):
        sc = SessionCoordinator()
        await sc.notify_generation_started("s1")
        await sc.notify_generation_completed("s1")
        await sc.notify_session_expired("s1")


class TestTrackTask:
    """track_task registers tasks and auto-discards on completion."""

    def test_tracks_task(self):
        sc = SessionCoordinator()
        task = MagicMock()
        task.add_done_callback = MagicMock()
        sc.track_task("s1", task)
        assert task in sc._session_tasks["s1"]

    def test_creates_set_for_new_session(self):
        sc = SessionCoordinator()
        task = MagicMock()
        task.add_done_callback = MagicMock()
        sc.track_task("new_session", task)
        assert "new_session" in sc._session_tasks
