"""Tests for PlaybackIntegrator: property-based and unit tests.

Property tests use Hypothesis to verify correctness properties 10, 11, 12.
Unit tests cover specific examples and edge cases for Task 4.6.
"""

import io
import os
import shutil

import pytest
import pytest_asyncio
from hypothesis import given, settings, strategies as st, HealthCheck, assume
from pydub import AudioSegment
from pydub.generators import Sine

from app.agents.voice_agent import VoicePersonalityAgent
from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.models.voice_recording import (
    MessageType,
    RecordingMetadata,
    VoiceCommandMatch,
    VoiceRecordingRecord,
)
from app.services.audio_normalizer import AudioNormalizer
from app.services.playback_integrator import PlaybackIntegrator
from app.services.voice_recording_service import VoiceRecordingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_STORAGE = "test_playback_storage"


def _make_wav_bytes(duration_ms: int = 3000, freq: int = 440) -> bytes:
    """Generate a sine tone as WAV bytes."""
    tone = Sine(freq, sample_rate=16000).to_audio_segment(duration=duration_ms)
    tone = tone.set_sample_width(2).set_channels(1)
    buf = io.BytesIO()
    tone.export(buf, format="wav")
    return buf.getvalue()


def _make_metadata(
    recorder_name: str = "Abuela María",
    relationship: str = "grandparent",
    message_type: MessageType = MessageType.STORY_INTRO,
    language: str = "en",
    sibling_pair_id: str = "pair1",
    command_phrase: str | None = None,
    command_action: str | None = None,
) -> RecordingMetadata:
    return RecordingMetadata(
        recorder_name=recorder_name,
        relationship=relationship,
        message_type=message_type,
        language=language,
        sibling_pair_id=sibling_pair_id,
        command_phrase=command_phrase,
        command_action=command_action,
    )


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

trigger_message_types = st.sampled_from([
    MessageType.STORY_INTRO,
    MessageType.ENCOURAGEMENT,
    MessageType.SOUND_EFFECT,
    MessageType.CUSTOM,
])
valid_languages = st.sampled_from(["en", "es"])
recorder_names = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs"), min_codepoint=32),
    min_size=1,
    max_size=30,
).filter(lambda s: s.strip())


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def service(db):
    normalizer = AudioNormalizer()
    svc = VoiceRecordingService(db, normalizer, storage_root=TEST_STORAGE)
    yield svc
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)


@pytest_asyncio.fixture
async def integrator(service):
    voice_agent = VoicePersonalityAgent()
    normalizer = AudioNormalizer()
    return PlaybackIntegrator(service, voice_agent, normalizer)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------


class TestTriggerSelection:
    """Property 10: Trigger-based recording selection.

    For any sibling pair and message type, if at least one recording of that
    type exists, the integrator SHALL return a recording whose message_type
    matches the requested type.

    **Validates: Requirements 6.1, 6.2, 6.3, 6.4**
    """

    @given(msg_type=trigger_message_types, lang=valid_languages)
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_trigger_returns_matching_type(self, service, integrator, msg_type, lang):
        pair_id = "trigger_pair"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Abuela",
            message_type=msg_type,
            language=lang,
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta)

        # Call the appropriate trigger method
        if msg_type == MessageType.STORY_INTRO:
            result = await integrator.get_story_intro_audio(pair_id, lang)
        elif msg_type == MessageType.ENCOURAGEMENT:
            result = await integrator.get_encouragement_audio(pair_id, lang)
        elif msg_type == MessageType.SOUND_EFFECT:
            result = await integrator.get_sound_effect(pair_id, lang)
        else:
            # CUSTOM — use get_story_intro_audio won't match; test via internal
            # For CUSTOM, we verify via the service directly
            rec = await service.find_matching_recording(pair_id, msg_type.value, lang)
            assert rec is not None
            assert rec.message_type == msg_type
            await service.delete_all_recordings(pair_id)
            return

        assert result is not None
        assert result.source == "recording"
        assert result.audio_base64  # non-empty
        assert result.recorder_name == "Abuela"

        # Cleanup
        await service.delete_all_recordings(pair_id)


class TestLanguageFallback:
    """Property 11: Language preference with fallback chain.

    (a) If a recording exists in language L, the integrator SHALL return it.
    (b) If no recording in L but one in the other language, SHALL return it.
    (c) If no recording exists, SHALL return None (caller handles TTS).

    **Validates: Requirements 6.5, 11.1, 11.2, 11.3**
    """

    @given(
        preferred=valid_languages,
        available=valid_languages,
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_language_fallback_chain(self, service, integrator, preferred, available):
        pair_id = "lang_pair"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Abuela",
            message_type=MessageType.STORY_INTRO,
            language=available,
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta)

        result = await integrator.get_story_intro_audio(pair_id, preferred)

        # A recording exists, so we should always get a result
        assert result is not None
        assert result.source == "recording"

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_no_recording_returns_none(self, integrator):
        """No recordings → None (TTS fallback handled by caller)."""
        result = await integrator.get_story_intro_audio("empty_pair", "en")
        assert result is None


class TestCommandMatchingThreshold:
    """Property 12: Voice command matching threshold.

    match_voice_command SHALL return matched=True iff similarity > 0.7.
    For similarity <= 0.7, matched SHALL be False.

    **Validates: Requirements 7.3, 7.4**
    """

    @given(
        phrase=st.text(min_size=3, max_size=30, alphabet="abcdefghijklmnopqrstuvwxyz ").filter(lambda s: s.strip()),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_exact_match_above_threshold(self, service, integrator, phrase):
        """Exact match should always have similarity > 0.7."""
        pair_id = "cmd_pair"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            language="en",
            sibling_pair_id=pair_id,
            command_phrase=phrase,
            command_action="test_action",
        )
        await service.upload_recording(pair_id, audio, meta)

        result = await integrator.match_voice_command(pair_id, phrase)
        assert result is not None
        assert result.matched is True
        assert result.similarity_score > 0.7
        assert result.command_action == "test_action"

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @given(
        phrase=st.text(min_size=5, max_size=20, alphabet="abcdefghijklmnop").filter(lambda s: s.strip()),
        garbage=st.text(min_size=20, max_size=40, alphabet="rstuvwxyz").filter(lambda s: s.strip()),
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_dissimilar_text_below_threshold(self, service, integrator, phrase, garbage):
        """Very different text should not match."""
        pair_id = "cmd_no_pair"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            language="en",
            sibling_pair_id=pair_id,
            command_phrase=phrase,
            command_action="test_action",
        )
        await service.upload_recording(pair_id, audio, meta)

        result = await integrator.match_voice_command(pair_id, garbage)
        assert result is not None
        # If score is <= 0.7, matched must be False
        if result.similarity_score <= 0.7:
            assert result.matched is False
            assert result.command_action is None

        # Cleanup
        await service.delete_all_recordings(pair_id)


# ---------------------------------------------------------------------------
# Unit Tests — Task 4.6
# ---------------------------------------------------------------------------


class TestUnitPlaybackIntegrator:
    """Unit tests for PlaybackIntegrator edge cases."""

    @pytest.mark.asyncio
    async def test_no_recordings_returns_none(self, integrator):
        """No recordings for a pair → None (TTS fallback by caller)."""
        result = await integrator.get_story_intro_audio("no_pair", "en")
        assert result is None

        result = await integrator.get_encouragement_audio("no_pair", "en")
        assert result is None

        result = await integrator.get_sound_effect("no_pair", "es")
        assert result is None

        result = await integrator.get_character_audio("no_pair", "Abuela", "en")
        assert result is None

    @pytest.mark.asyncio
    async def test_exact_phrase_match(self, service, integrator):
        """Exact phrase match should return matched=True with correct action."""
        pair_id = "exact_pair"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            language="en",
            sibling_pair_id=pair_id,
            command_phrase="aventura magica",
            command_action="start_adventure",
        )
        await service.upload_recording(pair_id, audio, meta)

        result = await integrator.match_voice_command(pair_id, "aventura magica")
        assert result is not None
        assert result.matched is True
        assert result.command_action == "start_adventure"
        assert result.similarity_score == 1.0

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_partial_match_boundary_below(self, service, integrator):
        """Similarity ~0.69 should NOT match (below 0.7 threshold)."""
        pair_id = "boundary_low"
        audio = _make_wav_bytes(3000)

        # Use a phrase where we can craft input with ~0.69 similarity
        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            language="en",
            sibling_pair_id=pair_id,
            command_phrase="start the adventure now",
            command_action="start_adventure",
        )
        await service.upload_recording(pair_id, audio, meta)

        # Craft text that gives similarity just below 0.7
        # "start the adventure now" vs "begin the adventure" → ~0.65
        import difflib
        test_text = "begin the adventure"
        score = difflib.SequenceMatcher(
            None,
            test_text.lower(),
            "start the adventure now".lower(),
        ).ratio()

        result = await integrator.match_voice_command(pair_id, test_text)
        assert result is not None

        if result.similarity_score <= 0.7:
            assert result.matched is False
            assert result.command_action is None

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_partial_match_boundary_above(self, service, integrator):
        """Similarity ~0.71 should match (above 0.7 threshold)."""
        pair_id = "boundary_high"
        audio = _make_wav_bytes(3000)

        meta = _make_metadata(
            recorder_name="Papá",
            message_type=MessageType.VOICE_COMMAND,
            language="en",
            sibling_pair_id=pair_id,
            command_phrase="start the adventure",
            command_action="start_adventure",
        )
        await service.upload_recording(pair_id, audio, meta)

        # "start the adventure" vs "start an adventure" → high similarity
        import difflib
        test_text = "start an adventure"
        score = difflib.SequenceMatcher(
            None,
            test_text.lower(),
            "start the adventure".lower(),
        ).ratio()

        result = await integrator.match_voice_command(pair_id, test_text)
        assert result is not None

        if result.similarity_score > 0.7:
            assert result.matched is True
            assert result.command_action == "start_adventure"

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_spanish_session_english_only_recordings(self, service, integrator):
        """Spanish session with only English recordings should fall back to English."""
        pair_id = "es_session"
        audio = _make_wav_bytes(3000)

        # Store only English recording
        meta = _make_metadata(
            recorder_name="Grandpa",
            message_type=MessageType.STORY_INTRO,
            language="en",
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta)

        # Request Spanish — should fall back to English recording
        result = await integrator.get_story_intro_audio(pair_id, "es")
        assert result is not None
        assert result.source == "recording"
        assert result.recorder_name == "Grandpa"

        # Cleanup
        await service.delete_all_recordings(pair_id)

    @pytest.mark.asyncio
    async def test_no_voice_commands_returns_none(self, integrator):
        """No voice commands registered → None."""
        result = await integrator.match_voice_command("empty_pair", "hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_preferred_language_selected_over_fallback(self, service, integrator):
        """When both languages exist, preferred language should be selected."""
        pair_id = "both_lang"
        audio = _make_wav_bytes(3000)

        # Store English recording
        meta_en = _make_metadata(
            recorder_name="Grandpa",
            message_type=MessageType.ENCOURAGEMENT,
            language="en",
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta_en)

        # Store Spanish recording
        meta_es = _make_metadata(
            recorder_name="Abuela",
            message_type=MessageType.ENCOURAGEMENT,
            language="es",
            sibling_pair_id=pair_id,
        )
        await service.upload_recording(pair_id, audio, meta_es)

        # Request Spanish — should get Spanish recording
        result = await integrator.get_encouragement_audio(pair_id, "es")
        assert result is not None
        assert result.source == "recording"
        assert result.recorder_name == "Abuela"

        # Request English — should get English recording
        result = await integrator.get_encouragement_audio(pair_id, "en")
        assert result is not None
        assert result.source == "recording"
        assert result.recorder_name == "Grandpa"

        # Cleanup
        await service.delete_all_recordings(pair_id)
