"""Pydantic data models for the Story Beat system.

Defines structured models for the turn-based story loop:
AI narration response with scene illustration, concise narration,
and contextual suggestion cards (Sparks) for the next turn.
"""

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SuggestionData(BaseModel):
    """A single illustrated suggestion card (Spark) for the next turn.

    Each suggestion provides a short label (max 4 words), an illustration,
    and the full story direction text sent to the backend if selected.
    """

    id: str
    label: str = Field(max_length=30)
    illustration_prompt: str
    illustration_url: Optional[str] = None
    story_direction: str

    @field_validator("label")
    @classmethod
    def label_max_words(cls, v: str) -> str:
        if len(v.split()) > 4:
            raise ValueError("Label must be 4 words or fewer")
        return v


class StoryBeatResponse(BaseModel):
    """Response from the AI storyteller for a single story beat.

    Contains concise narration (max 3 sentences), a scene illustration,
    2-3 contextual suggestions for the next turn, the narrative perspective,
    and whether this beat is a milestone (triggers celebration animation).
    """

    narration: str
    illustration_prompt: str
    illustration_url: Optional[str] = None
    suggestions: list[SuggestionData] = Field(min_length=2, max_length=3)
    perspective: str
    is_milestone: bool = False

    @field_validator("narration")
    @classmethod
    def narration_max_sentences(cls, v: str) -> str:
        sentences = re.split(r"[.!?]+", v.strip())
        sentences = [s for s in sentences if s.strip()]
        if len(sentences) > 3:
            raise ValueError("Narration must be 3 sentences or fewer")
        return v

    @field_validator("suggestions")
    @classmethod
    def suggestions_count(cls, v: list) -> list:
        if len(v) < 2 or len(v) > 3:
            raise ValueError("Must have 2-3 suggestions")
        return v
