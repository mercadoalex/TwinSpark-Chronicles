"""Pydantic data models for the Session Resumption feature.

Defines structured models for session snapshot persistence: saving,
loading, and managing story session state for sibling pairs.
"""

from pydantic import BaseModel


class SessionSnapshotPayload(BaseModel):
    """Payload for saving a session snapshot."""

    sibling_pair_id: str
    character_profiles: dict
    story_history: list
    current_beat: dict | None = None
    session_metadata: dict


class SessionSnapshotResponse(BaseModel):
    """Full session snapshot returned on load, including server-managed fields."""

    id: str
    sibling_pair_id: str
    character_profiles: dict
    story_history: list
    current_beat: dict | None = None
    session_metadata: dict
    created_at: str
    updated_at: str


class SessionSaveResult(BaseModel):
    """Response returned after a session snapshot is saved."""

    id: str
    updated_at: str
