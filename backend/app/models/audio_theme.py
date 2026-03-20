"""Pydantic data models for the Scene Audio System.

Defines structured models for scene-to-audio theme mapping:
scene description → keyword matching → audio theme result with
ambient track and sound effect paths.
"""

from pydantic import BaseModel, Field


class SceneThemeRequest(BaseModel):
    """Request body for the scene-theme mapping endpoint."""

    scene_description: str = Field(..., min_length=1)


class AudioThemeResult(BaseModel):
    """Result of mapping a scene description to an audio theme."""

    theme: str
    ambient_track: str
    sound_effects: list[str] = []
