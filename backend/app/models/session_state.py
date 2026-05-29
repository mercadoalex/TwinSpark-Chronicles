"""Pydantic data model for session state.

Tracks the current state of a storytelling session including
turn-taking between twins, story context for the memory agent,
and session continuity data for auto-resume.
"""

from typing import Optional

from pydantic import BaseModel


class SessionState(BaseModel):
    """Persisted state for a storytelling session.

    Manages turn alternation between twins, tracks the current
    position in the story, and holds context for the memory agent
    to maintain narrative continuity.
    """

    session_id: str
    active_twin: str  # 'twin1' or 'twin2'
    turn_count: int = 0
    last_beat_id: Optional[str] = None
    theme: Optional[str] = None
    story_context: dict = {}  # for memory agent

    def switch_turn(self) -> None:
        """Alternate active_twin between 'twin1' and 'twin2' and increment turn_count."""
        self.active_twin = "twin2" if self.active_twin == "twin1" else "twin1"
        self.turn_count += 1
