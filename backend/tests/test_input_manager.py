"""Unit tests for InputManager service."""

import json
import pytest

from app.services.input_manager import InputManager, safe_deserialize
from app.models.multimodal import (
    EmotionCategory,
    EmotionResult,
    MultimodalInputEvent,
    TranscriptResult,
)


def _transcript(text: str = "hello", confidence: float = 0.9) -> TranscriptResult:
    return TranscriptResult(text=text, confidence=confidence, is_empty=False)


def _empty_transcript() -> TranscriptResult:
    return TranscriptResult()


def _emotion(emotion: EmotionCategory = EmotionCategory.HAPPY, confidence: float = 0.8) -> EmotionResult:
    return EmotionResult(face_id=0, emotion=emotion, confidence=confidence)


TIMESTAMP = "2024-06-01T12:00:00Z"


class TestFuse:
    def test_audio_only_mode(self):
        """Camera unavailable: emotions empty, face_detected=False, transcript carries data."""
        mgr = InputManager("sess-1")
        event = mgr.fuse(_transcript("fight the dragon"), [], False, TIMESTAMP)

        assert event is not None
        assert event.transcript.text == "fight the dragon"
        assert event.emotions == []
        assert event.face_detected is False

    def test_camera_only_mode(self):
        """Mic unavailable: transcript empty, emotions and face carry camera data."""
        mgr = InputManager("sess-1")
        emotions = [_emotion()]
        event = mgr.fuse(_empty_transcript(), emotions, True, TIMESTAMP)

        assert event is not None
        assert event.transcript.is_empty is True
        assert event.transcript.text == ""
        assert event.emotions == emotions
        assert event.face_detected is True

    def test_full_multimodal(self):
        """Both modalities present."""
        mgr = InputManager("sess-1")
        emotions = [_emotion()]
        event = mgr.fuse(_transcript("yes"), emotions, True, TIMESTAMP)

        assert event is not None
        assert event.transcript.text == "yes"
        assert event.face_detected is True
        assert len(event.emotions) == 1

    def test_no_data_returns_none(self):
        """Neither modality provides data — returns None."""
        mgr = InputManager("sess-1")
        event = mgr.fuse(_empty_transcript(), [], False, TIMESTAMP)
        assert event is None

    def test_session_id_set(self):
        mgr = InputManager("sess-42")
        event = mgr.fuse(_transcript(), [], False, TIMESTAMP)
        assert event.session_id == "sess-42"

    def test_timestamp_preserved(self):
        mgr = InputManager("s")
        event = mgr.fuse(_transcript(), [], False, TIMESTAMP)
        assert event.timestamp == TIMESTAMP

    def test_speech_id_preserved(self):
        mgr = InputManager("s")
        event = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        assert event.speech_id == "sp-1"


class TestSpeechDeduplication:
    def test_first_call_returns_event(self):
        mgr = InputManager("s")
        event = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        assert event is not None

    def test_duplicate_speech_id_returns_none(self):
        mgr = InputManager("s")
        mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        dup = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        assert dup is None

    def test_different_speech_ids_both_produce_events(self):
        mgr = InputManager("s")
        e1 = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        e2 = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-2")
        assert e1 is not None
        assert e2 is not None

    def test_none_speech_id_never_deduplicates(self):
        mgr = InputManager("s")
        e1 = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id=None)
        e2 = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id=None)
        assert e1 is not None
        assert e2 is not None

    def test_reset_clears_dedup(self):
        mgr = InputManager("s")
        mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        mgr.reset()
        event = mgr.fuse(_transcript(), [], False, TIMESTAMP, speech_id="sp-1")
        assert event is not None


class TestSafeDeserialize:
    def test_valid_json(self):
        event = MultimodalInputEvent(session_id="s", timestamp=TIMESTAMP)
        raw = event.model_dump_json()
        result = safe_deserialize(raw)
        assert result is not None
        assert result.session_id == "s"

    def test_malformed_json_returns_none(self):
        assert safe_deserialize("{not valid json") is None

    def test_empty_string_returns_none(self):
        assert safe_deserialize("") is None

    def test_valid_json_wrong_schema_returns_none(self):
        assert safe_deserialize('{"foo": "bar"}') is None

    def test_non_json_string_returns_none(self):
        assert safe_deserialize("hello world") is None

    def test_round_trip(self):
        emotions = [_emotion(EmotionCategory.SCARED, 0.7)]
        event = MultimodalInputEvent(
            session_id="s",
            timestamp=TIMESTAMP,
            transcript=_transcript("dragon"),
            emotions=emotions,
            face_detected=True,
            speech_id="sp-99",
        )
        raw = event.model_dump_json()
        restored = safe_deserialize(raw)
        assert restored == event
