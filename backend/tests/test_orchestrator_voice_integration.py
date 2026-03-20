"""Unit tests for Orchestrator voice recording integration (Task 6).

Tests cover:
- 6.1: PlaybackIntegrator initialization in _ensure_db_initialized
- 6.2: Voice recording step in generate_rich_story_moment
- 6.3: Voice command matching in WebSocket audio_segment handler
- 6.4: voice_recordings key in rich story moment response
"""
import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
import pytest

from app.models.voice_recording import PlaybackResult, VoiceCommandMatch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _b64(data=b"fake"):
    return base64.b64encode(data).decode()


STORY = {
    "text": "The brave dragon appeared!",
    "image": None,
    "audio": {},
    "interactive": {},
    "timestamp": "2024-06-01T12:00:00Z",
}

PLAYBACK_RESULT = PlaybackResult(
    source="recording",
    audio_base64="dGVzdA==",
    recorder_name="Abuela",
    recording_id="rec-123",
)


# ---------------------------------------------------------------------------
# 6.1 — PlaybackIntegrator initialization
# ---------------------------------------------------------------------------

class TestPlaybackIntegratorInit:
    """Task 6.1: PlaybackIntegrator is initialized in _ensure_db_initialized."""

    def test_playback_integrator_none_before_init(self):
        """Before DB init, _playback_integrator should be None."""
        from app.agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()
        assert orch._playback_integrator is None

    def test_playback_integrator_set_after_init(self):
        """After _ensure_db_initialized, _playback_integrator should be set."""
        from app.agents.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator()

        # Mock DB connect and migration runner
        orch._db_conn = MagicMock()
        orch._db_conn.connect = AsyncMock()

        with patch("app.db.migration_runner.MigrationRunner", autospec=True) as MockRunner:
            runner_inst = MockRunner.return_value
            runner_inst.ensure_migration_table = AsyncMock()
            runner_inst.get_pending_migrations = AsyncMock(return_value=[])
            runner_inst.apply_all = AsyncMock(return_value=[])

            asyncio.get_event_loop().run_until_complete(orch._ensure_db_initialized())

        from app.services.playback_integrator import PlaybackIntegrator
        assert isinstance(orch._playback_integrator, PlaybackIntegrator)


# ---------------------------------------------------------------------------
# 6.2 — Voice recording step in generate_rich_story_moment
# ---------------------------------------------------------------------------

class TestVoiceRecordingStep:
    """Task 6.2: Voice recording triggers in generate_rich_story_moment."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.agents.orchestrator import AgentOrchestrator
        self.orch = AgentOrchestrator()
        # Disable agents to keep tests fast
        self.orch.storyteller = MagicMock()
        self.orch.storyteller.generate_story_segment = AsyncMock(return_value=dict(STORY))
        self.orch.storyteller._fallback_story = MagicMock(return_value=dict(STORY))
        self.orch.visual = MagicMock(enabled=False)
        self.orch.voice = MagicMock(enabled=False)
        self.orch.memory = MagicMock(enabled=False)
        self.orch.content_filter = MagicMock()
        self.orch.content_filter.scan = MagicMock(
            return_value=MagicMock(rating=MagicMock(value="safe"), reason=None, matched_terms=[])
        )
        # Make content_filter.scan return SAFE rating
        from app.services.content_filter import ContentRating
        self.orch.content_filter.scan.return_value.rating = ContentRating.SAFE

        self.orch._db_initialized = True
        self.orch._db_conn = MagicMock()
        self.orch._db_conn.fetch_all = AsyncMock(return_value=[])

        # Mock PlaybackIntegrator
        self.pi = MagicMock()
        self.pi.get_story_intro_audio = AsyncMock(return_value=None)
        self.pi.get_encouragement_audio = AsyncMock(return_value=None)
        self.pi.get_sound_effect = AsyncMock(return_value=None)
        self.orch._playback_integrator = self.pi

        # Mock world DB
        self.orch._world_db = MagicMock()
        self.orch._world_db.load_world_state = AsyncMock(return_value={})
        self.orch._world_state_cache = {}

    def _run(self, **kwargs):
        defaults = {
            "session_id": "s1",
            "characters": {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
            "language": "en",
        }
        defaults.update(kwargs)
        return asyncio.get_event_loop().run_until_complete(
            self.orch.generate_rich_story_moment(**defaults)
        )

    def test_story_intro_on_first_beat(self):
        """STORY_INTRO is checked when user_input is None (first beat)."""
        self.pi.get_story_intro_audio = AsyncMock(return_value=PLAYBACK_RESULT)
        result = self._run(user_input=None)
        self.pi.get_story_intro_audio.assert_called_once()
        assert len(result["voice_recordings"]) == 1
        assert result["voice_recordings"][0]["type"] == "story_intro"

    def test_story_intro_on_story_start(self):
        """STORY_INTRO is checked when user_input is 'story_start'."""
        self.pi.get_story_intro_audio = AsyncMock(return_value=PLAYBACK_RESULT)
        result = self._run(user_input="story_start")
        self.pi.get_story_intro_audio.assert_called_once()

    def test_encouragement_on_brave_text(self):
        """ENCOURAGEMENT is triggered when story text contains brave keywords."""
        self.pi.get_encouragement_audio = AsyncMock(return_value=PLAYBACK_RESULT)
        result = self._run(user_input="I want to be brave")
        self.pi.get_encouragement_audio.assert_called_once()
        assert any(vr["type"] == "encouragement" for vr in result["voice_recordings"])

    def test_sound_effect_on_playful_text(self):
        """SOUND_EFFECT is triggered when story text contains playful keywords."""
        silly_story = dict(STORY)
        silly_story["text"] = "The silly dragon started to giggle!"
        self.orch.storyteller.generate_story_segment = AsyncMock(return_value=silly_story)
        self.pi.get_sound_effect = AsyncMock(return_value=PLAYBACK_RESULT)
        result = self._run(user_input="tell me something funny")
        self.pi.get_sound_effect.assert_called_once()
        assert any(vr["type"] == "sound_effect" for vr in result["voice_recordings"])

    def test_no_recordings_when_none_match(self):
        """voice_recordings is empty when no triggers match."""
        result = self._run(user_input="walk to the castle")
        assert result["voice_recordings"] == []

    def test_graceful_degradation_on_error(self):
        """If PlaybackIntegrator raises, voice_recordings is empty and story still returns."""
        self.pi.get_story_intro_audio = AsyncMock(side_effect=Exception("boom"))
        result = self._run(user_input=None)
        assert result["voice_recordings"] == []
        assert "text" in result  # Story still generated

    def test_no_crash_when_integrator_is_none(self):
        """If _playback_integrator is None, voice_recordings is empty."""
        self.orch._playback_integrator = None
        result = self._run(user_input=None)
        assert result["voice_recordings"] == []


# ---------------------------------------------------------------------------
# 6.3 — Voice command matching in WebSocket audio_segment handler
# ---------------------------------------------------------------------------

class TestVoiceCommandMatching:
    """Task 6.3: match_voice_command called after STT in audio_segment handler."""

    @pytest.fixture(autouse=True)
    def setup(self):
        import app.main as mod
        self.mod = mod

        self.ws = AsyncMock()
        self.mgr = mod.ConnectionManager()
        asyncio.get_event_loop().run_until_complete(self.mgr.connect(self.ws, "s1"))

        # Set session context with characters
        self.mgr.set_session_context("s1", {
            "characters": {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
            "language": "en",
        })

        from app.models.multimodal import TranscriptResult
        self.transcript = TranscriptResult(text="aventura magica", confidence=0.9, is_empty=False)
        self.stt = MagicMock(transcribe=AsyncMock(return_value=self.transcript))

        self.orch = MagicMock()
        self.orch.generate_rich_story_moment = AsyncMock(return_value=dict(STORY))
        self.orch._ensure_db_initialized = AsyncMock()

        self.pi = MagicMock()
        self.pi.match_voice_command = AsyncMock(return_value=VoiceCommandMatch(
            matched=True,
            command_action="start adventure",
            similarity_score=0.85,
            confirmation_audio_url="rec-456",
        ))
        self.orch._playback_integrator = self.pi

        self._ps = [
            patch.object(self.mod, "manager", self.mgr),
            patch.object(self.mod, "stt_service", self.stt),
            patch.object(self.mod, "orchestrator", self.orch),
        ]
        for p in self._ps:
            p.start()
        yield
        for p in self._ps:
            p.stop()

    def _run(self, d=None):
        asyncio.get_event_loop().run_until_complete(
            self.mod._process_audio_segment(
                "s1", d or {"data": _b64(), "timestamp": "2024-06-01T12:00:00Z"}
            )
        )

    def _msgs(self, t):
        return [c for c in self.ws.send_json.call_args_list if c[0][0].get("type") == t]

    def test_voice_command_match_sent(self):
        """When a voice command matches, a voice_command_match message is sent."""
        self._run()
        msgs = self._msgs("voice_command_match")
        assert len(msgs) == 1
        assert msgs[0][0][0]["command_action"] == "start adventure"
        assert msgs[0][0][0]["similarity_score"] == 0.85

    def test_no_match_no_message(self):
        """When no voice command matches, no voice_command_match message is sent."""
        self.pi.match_voice_command = AsyncMock(return_value=VoiceCommandMatch(
            matched=False, command_action=None, similarity_score=0.3,
        ))
        self._run()
        assert len(self._msgs("voice_command_match")) == 0

    def test_no_crash_when_integrator_none(self):
        """When _playback_integrator is None, no crash occurs."""
        self.orch._playback_integrator = None
        self._run()  # Should not raise
        assert len(self._msgs("voice_command_match")) == 0

    def test_no_crash_on_match_error(self):
        """When match_voice_command raises, no crash occurs."""
        self.pi.match_voice_command = AsyncMock(side_effect=Exception("db error"))
        self._run()  # Should not raise
        assert len(self._msgs("voice_command_match")) == 0


# ---------------------------------------------------------------------------
# 6.4 — voice_recordings key in response
# ---------------------------------------------------------------------------

class TestVoiceRecordingsInResponse:
    """Task 6.4: voice_recordings key present in rich story moment response."""

    @pytest.fixture(autouse=True)
    def setup(self):
        from app.agents.orchestrator import AgentOrchestrator
        self.orch = AgentOrchestrator()
        self.orch.storyteller = MagicMock()
        self.orch.storyteller.generate_story_segment = AsyncMock(return_value=dict(STORY))
        self.orch.storyteller._fallback_story = MagicMock(return_value=dict(STORY))
        self.orch.visual = MagicMock(enabled=False)
        self.orch.voice = MagicMock(enabled=False)
        self.orch.memory = MagicMock(enabled=False)
        self.orch.content_filter = MagicMock()
        from app.services.content_filter import ContentRating
        self.orch.content_filter.scan = MagicMock(
            return_value=MagicMock(rating=ContentRating.SAFE, reason=None, matched_terms=[])
        )
        self.orch._db_initialized = True
        self.orch._db_conn = MagicMock()
        self.orch._db_conn.fetch_all = AsyncMock(return_value=[])
        self.orch._playback_integrator = None
        self.orch._world_db = MagicMock()
        self.orch._world_db.load_world_state = AsyncMock(return_value={})
        self.orch._world_state_cache = {}

    def test_voice_recordings_key_always_present(self):
        """The response always contains a voice_recordings key."""
        result = asyncio.get_event_loop().run_until_complete(
            self.orch.generate_rich_story_moment(
                session_id="s1",
                characters={"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
                language="en",
                user_input="walk forward",
            )
        )
        assert "voice_recordings" in result
        assert isinstance(result["voice_recordings"], list)

    def test_voice_recordings_contains_metadata(self):
        """When a recording matches, the response includes full metadata."""
        pi = MagicMock()
        pi.get_story_intro_audio = AsyncMock(return_value=PLAYBACK_RESULT)
        pi.get_encouragement_audio = AsyncMock(return_value=None)
        pi.get_sound_effect = AsyncMock(return_value=None)
        self.orch._playback_integrator = pi

        result = asyncio.get_event_loop().run_until_complete(
            self.orch.generate_rich_story_moment(
                session_id="s1",
                characters={"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
                language="en",
                user_input=None,
            )
        )
        assert len(result["voice_recordings"]) == 1
        vr = result["voice_recordings"][0]
        assert vr["type"] == "story_intro"
        assert vr["audio_base64"] == "dGVzdA=="
        assert vr["source"] == "recording"
        assert vr["recorder_name"] == "Abuela"
        assert vr["recording_id"] == "rec-123"
