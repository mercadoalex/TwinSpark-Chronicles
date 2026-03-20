"""Pydantic data models for the Voice Recording System.

Defines structured models for voice recording capture, metadata tagging,
audio normalization, playback integration, voice command matching, and
voice cloning preparation used across the voice recording pipeline:
capture → normalize → store → playback.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class MessageType(str, Enum):
    """Category describing the purpose of a voice recording."""

    STORY_INTRO = "story_intro"
    ENCOURAGEMENT = "encouragement"
    SOUND_EFFECT = "sound_effect"
    VOICE_COMMAND = "voice_command"
    CUSTOM = "custom"


class RecordingMetadata(BaseModel):
    """Metadata submitted alongside a voice recording upload."""

    recorder_name: str
    relationship: str
    message_type: MessageType
    language: str = "en"
    sibling_pair_id: str
    command_phrase: str | None = None
    command_action: str | None = None


class VoiceRecordingRecord(BaseModel):
    """Persisted voice recording with audio file paths and metadata."""

    recording_id: str
    sibling_pair_id: str
    recorder_name: str
    relationship: str
    message_type: MessageType
    language: str
    duration_seconds: float
    wav_path: str
    mp3_path: str
    sample_path: str | None = None
    command_phrase: str | None = None
    command_action: str | None = None
    created_at: datetime


class NormalizedAudio(BaseModel):
    """In-memory result of audio normalization processing.

    Contains the processed audio bytes (WAV, MP3, and optional voice sample)
    along with the final duration. Not persisted to the database.
    """

    wav_bytes: bytes
    mp3_bytes: bytes
    sample_bytes: bytes | None = None
    duration_seconds: float


class VoiceRecordingResult(BaseModel):
    """Response returned after a voice recording is uploaded and processed."""

    recording_id: str
    duration_seconds: float
    message_type: MessageType
    message: str


class DeleteRecordingResult(BaseModel):
    """Response returned after a voice recording is deleted."""

    deleted_recording_id: str
    had_trigger_assignments: bool
    affected_triggers: list[str]


class VoiceCommandRecord(BaseModel):
    """A registered voice command extracted from a VOICE_COMMAND recording."""

    recording_id: str
    command_phrase: str
    command_action: str
    recorder_name: str
    language: str


class VoiceCommandMatch(BaseModel):
    """Result of matching transcribed speech against registered voice commands."""

    matched: bool
    command_action: str | None = None
    similarity_score: float = 0.0
    confirmation_audio_url: str | None = None


class PlaybackResult(BaseModel):
    """Audio payload delivered to the frontend during story playback."""

    source: str
    audio_base64: str
    recorder_name: str | None = None
    recording_id: str | None = None


class CloneStatus(BaseModel):
    """Voice cloning readiness status for a single family recorder."""

    recorder_name: str
    sample_count: int
    cloning_ready: bool


class RecordingStats(BaseModel):
    """Voice recording storage usage summary for a sibling pair."""

    recording_count: int
    max_recordings: int
    remaining: int
