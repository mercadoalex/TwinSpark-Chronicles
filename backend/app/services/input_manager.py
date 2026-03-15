"""
Input Manager — fuses speech, emotion, and face detection signals
into a single MultimodalInputEvent for the Orchestrator.

Handles:
- Audio-only mode (no camera): emotions empty, face_detected=False
- Camera-only mode (no mic): transcript empty
- Speech deduplication via speech_id tracking
- Safe JSON deserialization of incoming messages
"""

import json
import logging
from typing import Optional

from app.models.multimodal import (
    MultimodalInputEvent,
    TranscriptResult,
    EmotionResult,
)

logger = logging.getLogger(__name__)


class InputManager:
    """Fuses multimodal signals and manages speech deduplication."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._seen_speech_ids: set[str] = set()

    def fuse(
        self,
        transcript: TranscriptResult,
        emotions: list[EmotionResult],
        faces_detected: bool,
        timestamp: str,
        speech_id: Optional[str] = None,
    ) -> Optional[MultimodalInputEvent]:
        """Combine the latest signals into a single MultimodalInputEvent.

        Args:
            transcript: Speech-to-text result (empty TranscriptResult when mic unavailable).
            emotions: Emotion classifications per face (empty list when camera unavailable).
            faces_detected: Whether any face was found in the frame.
            timestamp: ISO 8601 UTC timestamp string.
            speech_id: Optional identifier for speech dedup. If already seen, returns None.

        Returns:
            A fused MultimodalInputEvent, or None when:
            - The speech_id has already been processed (duplicate).
            - Neither modality provides data (transcript empty AND no faces).
        """
        # --- Speech deduplication ---
        if speech_id is not None:
            if speech_id in self._seen_speech_ids:
                logger.debug(
                    "Duplicate speech_id=%s for session=%s — skipping",
                    speech_id,
                    self.session_id,
                )
                return None
            self._seen_speech_ids.add(speech_id)

        # --- Check for "no data" scenario ---
        has_speech = not transcript.is_empty
        has_vision = faces_detected

        if not has_speech and not has_vision:
            logger.info(
                "No input data for session=%s (transcript empty, no faces) — skipping",
                self.session_id,
            )
            return None

        return MultimodalInputEvent(
            session_id=self.session_id,
            timestamp=timestamp,
            transcript=transcript,
            emotions=emotions,
            face_detected=faces_detected,
            speech_id=speech_id,
        )

    def reset(self) -> None:
        """Clear deduplication tracking (call on session cleanup)."""
        self._seen_speech_ids.clear()
        logger.debug("InputManager reset for session=%s", self.session_id)


def safe_deserialize(raw: str) -> Optional[MultimodalInputEvent]:
    """Parse a JSON string into a MultimodalInputEvent.

    Returns None (never crashes) on malformed JSON or invalid schema.
    """
    try:
        data = json.loads(raw)
        return MultimodalInputEvent.model_validate(data)
    except (json.JSONDecodeError, Exception) as exc:
        logger.error("Failed to deserialize MultimodalInputEvent: %s", exc)
        return None
