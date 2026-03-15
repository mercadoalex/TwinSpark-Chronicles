"""Unit tests for sibling dynamics REST endpoints and WebSocket routing (Tasks 11.1, 11.2)."""
import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException


def _b64(data=b"fake"):
    return base64.b64encode(data).decode()


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


TS = "2024-06-01T12:00:00Z"

SIBLING_CHARACTERS = {
    "child1": {"name": "Ale", "spirit_animal": "dragon"},
    "child2": {"name": "Sofi", "spirit_animal": "phoenix"},
}

SIBLING_CONTEXT = {
    "characters": SIBLING_CHARACTERS,
    "language": "en",
}

SINGLE_CHARACTERS = {
    "child1": {"name": "Ale", "spirit_animal": "dragon"},
    "child2": {},
}


# ============================================
# Task 11.1: REST endpoint tests
# ============================================

class TestGetSiblingSummary:
    """Tests for GET /api/sessions/{session_id}/sibling-summary."""

    def test_returns_summary_when_found(self):
        import app.main as mod

        row = {
            "session_id": "s1",
            "sibling_pair_id": "Ale:Sofi",
            "score": 0.75,
            "summary": "Great cooperation today.",
            "suggestion": None,
        }
        mock_db = MagicMock()
        mock_db.load_session_summary = AsyncMock(return_value=row)

        with patch.object(mod.orchestrator, "_ensure_db_initialized", new_callable=AsyncMock), \
             patch.object(mod.orchestrator, "_sibling_db", mock_db):
            result = _run(mod.get_sibling_summary("s1"))

        assert result["sibling_dynamics_score"] == 0.75
        assert result["summary"] == "Great cooperation today."
        assert result["session_id"] == "s1"

    def test_returns_404_when_not_found(self):
        import app.main as mod

        mock_db = MagicMock()
        mock_db.load_session_summary = AsyncMock(return_value=None)

        with patch.object(mod.orchestrator, "_ensure_db_initialized", new_callable=AsyncMock), \
             patch.object(mod.orchestrator, "_sibling_db", mock_db):
            with pytest.raises(HTTPException) as exc_info:
                _run(mod.get_sibling_summary("s1"))
        assert exc_info.value.status_code == 404

    def test_includes_suggestion_when_present(self):
        import app.main as mod

        row = {
            "session_id": "s1",
            "sibling_pair_id": "Ale:Sofi",
            "score": 0.3,
            "summary": "Some tension observed.",
            "suggestion": "Try cooperative games.",
        }
        mock_db = MagicMock()
        mock_db.load_session_summary = AsyncMock(return_value=row)

        with patch.object(mod.orchestrator, "_ensure_db_initialized", new_callable=AsyncMock), \
             patch.object(mod.orchestrator, "_sibling_db", mock_db):
            result = _run(mod.get_sibling_summary("s1"))

        assert result["suggestion"] == "Try cooperative games."


class TestEndSession:
    """Tests for POST /api/sessions/{session_id}/end."""

    def setup_method(self):
        import app.main as mod
        mod._ended_sessions.clear()

    def test_triggers_end_session(self):
        import app.main as mod

        result = {
            "session_id": "s1",
            "sibling_pair_id": "Ale:Sofi",
            "sibling_dynamics_score": 0.8,
            "summary": "Good session.",
            "suggestion": None,
        }
        with patch.object(mod.orchestrator, "end_session", new_callable=AsyncMock, return_value=result):
            resp = _run(mod.end_session("s1", {"characters": SIBLING_CHARACTERS}))

        assert resp["sibling_dynamics_score"] == 0.8
        assert resp["sibling_pair_id"] == "Ale:Sofi"

    def test_idempotent_second_call(self):
        import app.main as mod

        result = {
            "session_id": "s1",
            "sibling_pair_id": "Ale:Sofi",
            "sibling_dynamics_score": 0.8,
            "summary": "Good session.",
            "suggestion": None,
        }
        mock_end = AsyncMock(return_value=result)
        with patch.object(mod.orchestrator, "end_session", mock_end):
            resp1 = _run(mod.end_session("s1", {"characters": SIBLING_CHARACTERS}))
            resp2 = _run(mod.end_session("s1", {"characters": SIBLING_CHARACTERS}))

        assert resp1 == resp2
        # end_session should only be called once (idempotent)
        mock_end.assert_called_once()

    def test_derives_pair_id_sorted(self):
        import app.main as mod

        result = {
            "session_id": "s1",
            "sibling_pair_id": "Ale:Sofi",
            "sibling_dynamics_score": 0.5,
            "summary": "",
            "suggestion": None,
        }
        mock_end = AsyncMock(return_value=result)
        with patch.object(mod.orchestrator, "end_session", mock_end):
            _run(mod.end_session("s1", {"characters": SIBLING_CHARACTERS}))

        # Pair ID should be sorted: "Ale" < "Sofi"
        mock_end.assert_called_once_with("s1", "Ale:Sofi")

    def test_defaults_child_ids_when_no_body(self):
        import app.main as mod

        result = {
            "session_id": "s1",
            "sibling_pair_id": "child1:child2",
            "sibling_dynamics_score": 0.5,
            "summary": "",
            "suggestion": None,
        }
        mock_end = AsyncMock(return_value=result)
        with patch.object(mod.orchestrator, "end_session", mock_end):
            _run(mod.end_session("s1", None))

        mock_end.assert_called_once_with("s1", "child1:child2")


# ============================================
# Task 11.2: WebSocket sibling mode routing tests
# ============================================

class TestSiblingModeDetection:
    """Tests for _is_sibling_mode and _get_sibling_ids helpers."""

    def test_sibling_mode_true_when_both_children_named(self):
        import app.main as mod
        m = mod.ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        m.set_session_context("s1", SIBLING_CONTEXT)
        with patch.object(mod, "manager", m):
            assert mod._is_sibling_mode("s1") is True

    def test_sibling_mode_false_when_child2_empty(self):
        import app.main as mod
        m = mod.ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        m.set_session_context("s1", {"characters": SINGLE_CHARACTERS})
        with patch.object(mod, "manager", m):
            assert mod._is_sibling_mode("s1") is False

    def test_sibling_mode_false_when_no_context(self):
        import app.main as mod
        m = mod.ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        with patch.object(mod, "manager", m):
            assert mod._is_sibling_mode("s1") is False

    def test_get_sibling_ids_returns_names(self):
        import app.main as mod
        m = mod.ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        m.set_session_context("s1", SIBLING_CONTEXT)
        with patch.object(mod, "manager", m):
            c1, c2 = mod._get_sibling_ids("s1")
        assert c1 == "Ale"
        assert c2 == "Sofi"

    def test_get_sibling_ids_defaults_when_no_context(self):
        import app.main as mod
        m = mod.ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        with patch.object(mod, "manager", m):
            c1, c2 = mod._get_sibling_ids("s1")
        assert c1 == "child1"
        assert c2 == "child2"


class TestSessionContextTracking:
    """Tests for session context storage in ConnectionManager."""

    def test_set_and_get_context(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        m.set_session_context("s1", SIBLING_CONTEXT)
        assert m.get_session_context("s1") == SIBLING_CONTEXT

    def test_context_cleared_on_disconnect(self):
        from app.main import ConnectionManager
        m = ConnectionManager()
        _run(m.connect(AsyncMock(), "s1"))
        m.set_session_context("s1", SIBLING_CONTEXT)
        m.disconnect("s1")
        assert m.get_session_context("s1") is None

    def test_get_context_returns_none_for_unknown(self):
        from app.main import ConnectionManager
        assert ConnectionManager().get_session_context("x") is None


class TestCameraFrameSiblingRouting:
    """Tests that _process_camera_frame routes to process_sibling_event in sibling mode."""

    @pytest.fixture(autouse=True)
    def setup(self):
        import app.main as mod
        from app.models.multimodal import (
            EmotionCategory, EmotionResult, FaceBBox,
        )
        self.mod = mod
        self.ws = AsyncMock()
        self.mgr = mod.ConnectionManager()
        _run(self.mgr.connect(self.ws, "s1"))

        faces = [FaceBBox(x=0.1, y=0.1, width=0.3, height=0.3, confidence=0.9)]
        emotions = [EmotionResult(face_id=0, emotion=EmotionCategory.HAPPY, confidence=0.85)]

        self.fd = MagicMock(detect=MagicMock(return_value=list(faces)))
        self.ed = MagicMock(classify_all=MagicMock(return_value=list(emotions)))
        self.orch = MagicMock(
            generate_rich_story_moment=AsyncMock(return_value={"text": "story"}),
            process_sibling_event=AsyncMock(return_value={"text": "sibling story"}),
        )
        self._ps = [
            patch.object(mod, "manager", self.mgr),
            patch.object(mod, "face_detector", self.fd),
            patch.object(mod, "emotion_detector", self.ed),
            patch.object(mod, "orchestrator", self.orch),
        ]
        for p in self._ps:
            p.start()
        yield
        for p in self._ps:
            p.stop()

    def _run_frame(self):
        _run(self.mod._process_camera_frame("s1", {"data": _b64(), "timestamp": TS}))

    def test_routes_to_sibling_event_when_sibling_mode(self):
        self.mgr.set_session_context("s1", SIBLING_CONTEXT)
        self._run_frame()
        self.orch.process_sibling_event.assert_called_once()
        self.orch.generate_rich_story_moment.assert_not_called()

    def test_routes_to_regular_when_not_sibling_mode(self):
        self._run_frame()
        self.orch.generate_rich_story_moment.assert_called_once()
        self.orch.process_sibling_event.assert_not_called()

    def test_passes_child_ids_from_context(self):
        self.mgr.set_session_context("s1", SIBLING_CONTEXT)
        self._run_frame()
        kw = self.orch.process_sibling_event.call_args.kwargs
        assert kw["child1_id"] == "Ale"
        assert kw["child2_id"] == "Sofi"


class TestAudioSegmentSiblingRouting:
    """Tests that _process_audio_segment routes to process_sibling_event in sibling mode."""

    @pytest.fixture(autouse=True)
    def setup(self):
        import app.main as mod
        from app.models.multimodal import TranscriptResult
        self.mod = mod
        self.ws = AsyncMock()
        self.mgr = mod.ConnectionManager()
        _run(self.mgr.connect(self.ws, "s1"))

        transcript = TranscriptResult(text="hello", confidence=0.9, is_empty=False)
        self.stt = MagicMock(transcribe=AsyncMock(return_value=transcript))
        self.orch = MagicMock(
            generate_rich_story_moment=AsyncMock(return_value={"text": "story"}),
            process_sibling_event=AsyncMock(return_value={"text": "sibling story"}),
        )
        self._ps = [
            patch.object(mod, "manager", self.mgr),
            patch.object(mod, "stt_service", self.stt),
            patch.object(mod, "orchestrator", self.orch),
        ]
        for p in self._ps:
            p.start()
        yield
        for p in self._ps:
            p.stop()

    def _run_audio(self):
        _run(self.mod._process_audio_segment("s1", {"data": _b64(), "timestamp": TS}))

    def test_routes_to_sibling_event_when_sibling_mode(self):
        self.mgr.set_session_context("s1", SIBLING_CONTEXT)
        self._run_audio()
        self.orch.process_sibling_event.assert_called_once()
        self.orch.generate_rich_story_moment.assert_not_called()

    def test_routes_to_regular_when_not_sibling_mode(self):
        self._run_audio()
        self.orch.generate_rich_story_moment.assert_called_once()
        self.orch.process_sibling_event.assert_not_called()

    def test_passes_child_ids_from_context(self):
        self.mgr.set_session_context("s1", SIBLING_CONTEXT)
        self._run_audio()
        kw = self.orch.process_sibling_event.call_args.kwargs
        assert kw["child1_id"] == "Ale"
        assert kw["child2_id"] == "Sofi"

    def test_passes_language_from_context(self):
        ctx = dict(SIBLING_CONTEXT)
        ctx["language"] = "es"
        self.mgr.set_session_context("s1", ctx)
        self._run_audio()
        kw = self.orch.process_sibling_event.call_args.kwargs
        assert kw["language"] == "es"
