"""Playback integration service for voice recordings during story sessions.

Called by the Orchestrator during story moment generation to select and
deliver family voice recordings at appropriate trigger points, falling
back to TTS when no recording matches.

Requirements: 6.1–6.6, 7.3, 7.4, 11.1–11.3
"""

from __future__ import annotations

import base64
import difflib
import logging

from app.agents.voice_agent import VoicePersonalityAgent
from app.models.voice_recording import (
    MessageType,
    PlaybackResult,
    VoiceCommandMatch,
    VoiceRecordingRecord,
)
from app.services.audio_normalizer import AudioNormalizer
from app.services.voice_recording_service import VoiceRecordingService

logger = logging.getLogger(__name__)

COMMAND_MATCH_THRESHOLD = 0.7


class PlaybackIntegrator:
    """Selects and delivers voice recordings at story trigger points.

    Queries the VoiceRecordingService for matching recordings, applies
    fade-in/fade-out via AudioNormalizer, and falls back to TTS via
    VoicePersonalityAgent when no recording is available.
    """

    def __init__(
        self,
        voice_recording_service: VoiceRecordingService,
        voice_agent: VoicePersonalityAgent,
        audio_normalizer: AudioNormalizer,
    ) -> None:
        self._vrs = voice_recording_service
        self._voice_agent = voice_agent
        self._normalizer = audio_normalizer

    # ------------------------------------------------------------------
    # Public trigger methods
    # ------------------------------------------------------------------

    async def get_story_intro_audio(
        self, sibling_pair_id: str, language: str
    ) -> PlaybackResult | None:
        """Get a STORY_INTRO recording for session start.

        Returns a PlaybackResult with the recording audio (fade applied)
        or None if no recording exists (caller handles TTS fallback).
        """
        return await self._get_trigger_audio(
            sibling_pair_id, MessageType.STORY_INTRO, language
        )

    async def get_encouragement_audio(
        self, sibling_pair_id: str, language: str
    ) -> PlaybackResult | None:
        """Get an ENCOURAGEMENT recording for brave decisions."""
        return await self._get_trigger_audio(
            sibling_pair_id, MessageType.ENCOURAGEMENT, language
        )

    async def get_character_audio(
        self, sibling_pair_id: str, recorder_name: str, language: str
    ) -> PlaybackResult | None:
        """Get a recording from a specific Family_Recorder for character dialogue."""
        recordings = await self._vrs.get_recordings(
            sibling_pair_id, recorder_name=recorder_name
        )
        if not recordings:
            return None

        selected = self._select_by_language(recordings, language)
        if selected is None:
            return None

        return await self._build_playback_result(selected)

    async def get_sound_effect(
        self, sibling_pair_id: str, language: str
    ) -> PlaybackResult | None:
        """Get a SOUND_EFFECT recording for playful moments."""
        return await self._get_trigger_audio(
            sibling_pair_id, MessageType.SOUND_EFFECT, language
        )

    # ------------------------------------------------------------------
    # Voice command matching
    # ------------------------------------------------------------------

    async def match_voice_command(
        self, sibling_pair_id: str, transcribed_text: str
    ) -> VoiceCommandMatch | None:
        """Match transcribed speech against registered voice commands.

        Uses difflib.SequenceMatcher with a 0.7 threshold. Returns the
        best match above threshold, or a non-matched result if none qualify.
        """
        commands = await self._vrs.get_voice_commands(sibling_pair_id)
        if not commands:
            return None

        best_score = 0.0
        best_action: str | None = None
        best_recording_id: str | None = None

        normalized_text = transcribed_text.strip().lower()

        for cmd in commands:
            normalized_phrase = cmd.command_phrase.strip().lower()
            score = difflib.SequenceMatcher(
                None, normalized_text, normalized_phrase
            ).ratio()

            if score > best_score:
                best_score = score
                best_action = cmd.command_action
                best_recording_id = cmd.recording_id

        matched = best_score > COMMAND_MATCH_THRESHOLD

        return VoiceCommandMatch(
            matched=matched,
            command_action=best_action if matched else None,
            similarity_score=best_score,
            confirmation_audio_url=best_recording_id if matched else None,
        )

    # ------------------------------------------------------------------
    # Language selection
    # ------------------------------------------------------------------

    def _select_by_language(
        self,
        recordings: list[VoiceRecordingRecord],
        preferred_lang: str,
    ) -> VoiceRecordingRecord | None:
        """Select a recording using the language fallback chain.

        Fallback order:
        1. Recording in preferred language
        2. Recording in any other language
        3. None
        """
        if not recordings:
            return None

        # Prefer exact language match
        for rec in recordings:
            if rec.language == preferred_lang:
                return rec

        # Fallback: any other language
        return recordings[0]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_trigger_audio(
        self,
        sibling_pair_id: str,
        message_type: MessageType,
        language: str,
    ) -> PlaybackResult | None:
        """Query recordings by message type and apply language fallback.

        Returns a PlaybackResult with faded audio, or None if no recording.
        """
        recordings = await self._vrs.get_recordings(
            sibling_pair_id, message_type=message_type.value
        )
        if not recordings:
            return None

        selected = self._select_by_language(recordings, language)
        if selected is None:
            return None

        return await self._build_playback_result(selected)

    async def _build_playback_result(
        self, recording: VoiceRecordingRecord
    ) -> PlaybackResult | None:
        """Read MP3 from disk, apply fade, encode to base64."""
        try:
            with open(recording.mp3_path, "rb") as f:
                mp3_bytes = f.read()
        except (OSError, FileNotFoundError) as exc:
            logger.warning(
                "Could not read recording file %s: %s", recording.mp3_path, exc
            )
            return None

        # Apply fade-in/fade-out
        try:
            faded_bytes = self._normalizer._apply_fade(mp3_bytes, fade_ms=500)
        except Exception:
            # If fade fails, use original bytes
            faded_bytes = mp3_bytes

        audio_b64 = base64.b64encode(faded_bytes).decode("utf-8")

        return PlaybackResult(
            source="recording",
            audio_base64=audio_b64,
            recorder_name=recording.recorder_name,
            recording_id=recording.recording_id,
        )
