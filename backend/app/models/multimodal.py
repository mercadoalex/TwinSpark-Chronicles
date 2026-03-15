from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class EmotionCategory(str, Enum):
    HAPPY = "happy"
    SAD = "sad"
    SURPRISED = "surprised"
    ANGRY = "angry"
    SCARED = "scared"
    NEUTRAL = "neutral"


class FaceBBox(BaseModel):
    x: float = Field(ge=0.0, le=1.0, description="Normalized x coordinate")
    y: float = Field(ge=0.0, le=1.0, description="Normalized y coordinate")
    width: float = Field(gt=0.0, le=1.0)
    height: float = Field(gt=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)


class EmotionResult(BaseModel):
    face_id: int
    emotion: EmotionCategory
    confidence: float = Field(ge=0.0, le=1.0)


class TranscriptResult(BaseModel):
    text: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    language: str = "en-US"
    is_empty: bool = True


class MultimodalInputEvent(BaseModel):
    session_id: str
    timestamp: str = Field(description="ISO 8601 UTC")
    transcript: TranscriptResult = Field(default_factory=TranscriptResult)
    emotions: list[EmotionResult] = Field(default_factory=list)
    face_detected: bool = False
    speech_id: Optional[str] = None

    def to_orchestrator_context(self) -> dict:
        """Convert to the format expected by AgentOrchestrator.generate_rich_story_moment."""
        primary_emotion = self._get_primary_emotion()
        return {
            "user_input": self.transcript.text if not self.transcript.is_empty else None,
            "emotion": primary_emotion.emotion.value if primary_emotion else "neutral",
            "emotion_confidence": primary_emotion.confidence if primary_emotion else 0.0,
            "face_detected": self.face_detected,
            "timestamp": self.timestamp,
        }

    def _get_primary_emotion(self) -> Optional[EmotionResult]:
        """Get highest-confidence emotion from detected faces."""
        if not self.emotions:
            return None
        return max(self.emotions, key=lambda e: e.confidence)
