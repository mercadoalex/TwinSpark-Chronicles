"""Pydantic data models for story input events.

Defines a unified input event format for both voice transcription
and suggestion card (Spark) tap inputs. Both paths produce identical
StoryInputEvent objects for the backend to process.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class InputType(str, Enum):
    """Type of story input from the child."""

    VOICE = "voice"
    CARD = "card"


class StoryInputEvent(BaseModel):
    """Unified input event sent to the backend for story progression.

    Whether the child speaks into the mic or taps a suggestion card,
    the result is normalized into this single event format.
    """

    session_id: str
    active_twin: str  # 'twin1' or 'twin2'
    input_type: InputType
    text: str  # transcript for voice, story_direction for card
    card_id: Optional[str] = None  # only populated for card input
    timestamp: str  # ISO 8601 UTC
