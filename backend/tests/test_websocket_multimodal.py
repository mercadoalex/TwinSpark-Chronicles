"""Unit tests for WebSocket multimodal handling (Tasks 7.1 & 7.2)."""
import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.multimodal import (
    EmotionCategory, EmotionResult, FaceBBox, TranscriptResult,
)

def _b64(data=b"fake"):
    return base64.b64encode(data).decode()

FACES = [FaceBBox(x=0.1, y=0.1, width=0.3, height=0.3, confidence=0.9)]
EMOTIONS = [EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.85)]
TRANSCRIPT = TranscriptResult(text="fight the dragon", confidence=0.92, is_empty=False)
EMPTY_TR = TranscriptResult()
STORY = {"text": "The dragon appeared!", "image": None, "audio": {}}
TS = "2024-06-01T12:00:00Z"

class TestConnectionManager:
    def test_creates_input_manager(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        assert m.get_input_manager("s1") is not None

    def test_cleans_up_on_disconnect(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        asyncio.get_event_loop().run_until_complete(m.connect(AsyncMock(), "s1"))
        m.disconnect("s1")
        assert m.get_input_manager("s1") is None

    def test_disconnect_unknown_safe(self):
        from app.main import ConnectionManager
        ConnectionManager().disconnect("nope")

    def test_unknown_returns_none(self):
        from app.main import ConnectionManager
        assert ConnectionManager().get_input_manager("x") is None

def _env():
    import app.main as mod
    ws = AsyncMock()
    mgr = mod.ConnectionManager()
    asyncio.get_event_loop().run_until_complete(mgr.connect(ws, "s1"))
    fd = MagicMock(detect=MagicMock(return_value=list(FACES)))
    ed = MagicMock(classify_all=MagicMock(return_value=list(EMOTIONS)))
    stt = MagicMock(transcribe=AsyncMock(return_value=TRANSCRIPT))
    orch = MagicMock(generate_rich_story_moment=AsyncMock(return_value=STORY))
    return mod, ws, mgr, fd, ed, stt, orch

class TestCameraFrame:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mod, self.ws, self.mgr, self.fd, self.ed, self.stt, self.orch = _env()
        self._ps = [
            patch.object(self.mod, "manager", self.mgr),
            patch.object(self.mod, "face_detector", self.fd),
            patch.object(self.mod, "emotion_detector", self.ed),
            patch.object(self.mod, "orchestrator", self.orch),
        ]
        for p in self._ps: p.start()
        yield
        for p in self._ps: p.stop()

    def _run(self, d=None):
        asyncio.get_event_loop().run_until_complete(
            self.mod._process_camera_frame("s1", d or {"data": _b64(), "timestamp": TS}))

    def _msgs(self, t):
        return [c for c in self.ws.send_json.call_args_list if c[0][0].get("type") == t]

    def test_face_detector_called(self):
        self._run(); self.fd.detect.assert_called_once()

    def test_emotion_detector_called(self):
        self._run(); self.ed.classify_all.assert_called_once()

    def test_emotion_feedback_sent(self):
        self._run()
        msgs = self._msgs("emotion_feedback")
        assert len(msgs) == 1
        assert msgs[0][0][0]["emotions"][0]["emotion"] == "happy"

    def test_no_feedback_no_faces(self):
        self.fd.detect.return_value = []
        self.ed.classify_all.return_value = []
        self._run()
        assert len(self._msgs("emotion_feedback")) == 0

    def test_orchestrator_called(self):
        self._run(); self.orch.generate_rich_story_moment.assert_called_once()

    def test_story_segment_sent(self):
        self._run(); assert len(self._msgs("story_segment")) == 1

    def test_missing_session_safe(self):
        self.mgr.disconnect("s1"); self._run()

class TestAudioSegment:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mod, self.ws, self.mgr, self.fd, self.ed, self.stt, self.orch = _env()
        self._ps = [
            patch.object(self.mod, "manager", self.mgr),
            patch.object(self.mod, "stt_service", self.stt),
            patch.object(self.mod, "orchestrator", self.orch),
        ]
        for p in self._ps: p.start()
        yield
        for p in self._ps: p.stop()

    def _run(self, d=None):
        asyncio.get_event_loop().run_until_complete(
            self.mod._process_audio_segment("s1", d or {"data": _b64(), "timestamp": TS}))

    def _msgs(self, t):
        return [c for c in self.ws.send_json.call_args_list if c[0][0].get("type") == t]

    def test_stt_called(self):
        self._run(); self.stt.transcribe.assert_called_once()

    def test_transcript_feedback_sent(self):
        self._run()
        msgs = self._msgs("transcript_feedback")
        assert len(msgs) == 1
        assert msgs[0][0][0]["text"] == "fight the dragon"

    def test_no_feedback_empty(self):
        self.stt.transcribe = AsyncMock(return_value=EMPTY_TR)
        self._run()
        assert len(self._msgs("transcript_feedback")) == 0

    def test_orchestrator_called(self):
        self._run(); self.orch.generate_rich_story_moment.assert_called_once()

    def test_story_segment_sent(self):
        self._run(); assert len(self._msgs("story_segment")) == 1

    def test_language_forwarded(self):
        self._run({"data": _b64(), "timestamp": TS, "language": "es-ES"})
        assert self.stt.transcribe.call_args[1]["language"] == "es-ES"

    def test_dedup(self):
        d = {"data": _b64(), "timestamp": TS, "speech_id": "sp1"}
        self._run(d); self._run(d)
        assert self.orch.generate_rich_story_moment.call_count == 1

    def test_missing_session_safe(self):
        self.mgr.disconnect("s1"); self._run()

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

