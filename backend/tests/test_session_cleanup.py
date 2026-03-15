"""Unit tests for session task tracking and cleanup (Task 7.1)."""
import asyncio
from unittest.mock import AsyncMock, patch
import pytest


class TestSessionTaskTracking:
    """Tests for background task tracking and session cleanup."""

    def test_session_tasks_initialized_on_connect(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        assert "s1" in m._session_tasks
        assert len(m._session_tasks["s1"]) == 0

    def test_track_task_adds_to_set(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        async def noop():
            pass
        loop = asyncio.get_event_loop()
        task = loop.create_task(noop())
        m.track_task("s1", task)
        assert task in m._session_tasks["s1"]
        loop.run_until_complete(task)

    def test_track_task_ignored_for_unknown_session(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        async def noop():
            pass
        loop = asyncio.get_event_loop()
        task = loop.create_task(noop())
        m.track_task("unknown", task)
        loop.run_until_complete(task)

    def test_done_task_auto_removed(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        async def noop():
            pass
        loop = asyncio.get_event_loop()
        task = loop.create_task(noop())
        m.track_task("s1", task)
        loop.run_until_complete(task)
        loop.run_until_complete(asyncio.sleep(0))
        assert task not in m._session_tasks["s1"]

    def test_disconnect_cancels_pending_tasks(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        async def hang():
            await asyncio.sleep(999)
        loop = asyncio.get_event_loop()
        task = loop.create_task(hang())
        m.track_task("s1", task)
        m.disconnect("s1")
        # Task is in cancelling state; run loop to let CancelledError propagate
        loop.run_until_complete(asyncio.sleep(0))
        assert task.cancelled()

    def test_disconnect_clears_session_tasks(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        m.disconnect("s1")
        assert "s1" not in m._session_tasks


class TestCleanupSession:
    """Tests for _cleanup_session with timeout-bounded cleanup."""

    def test_cleanup_disconnects_session(self):
        import app.main as mod
        m = mod.ConnectionManager()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(m.connect(AsyncMock(), "s1"))
        with patch.object(mod, "manager", m):
            loop.run_until_complete(mod._cleanup_session("s1"))
        assert m.get_input_manager("s1") is None

    def test_cleanup_cancels_pending_tasks(self):
        import app.main as mod
        m = mod.ConnectionManager()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(m.connect(AsyncMock(), "s1"))
        async def hang():
            await asyncio.sleep(999)
        task = loop.create_task(hang())
        m.track_task("s1", task)
        with patch.object(mod, "manager", m):
            loop.run_until_complete(mod._cleanup_session("s1", timeout=0.1))
        assert task.cancelled()

    def test_cleanup_no_tasks_safe(self):
        import app.main as mod
        m = mod.ConnectionManager()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(m.connect(AsyncMock(), "s1"))
        with patch.object(mod, "manager", m):
            loop.run_until_complete(mod._cleanup_session("s1"))
