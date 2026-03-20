"""Pydantic data models for the Storybook Gallery.

Defines structured models for archived storybooks and their beats:
story completion → archive → gallery listing → detail retrieval → deletion.
"""

from pydantic import BaseModel


class StorybookSummary(BaseModel):
    """Lightweight storybook info for gallery listing."""

    storybook_id: str
    title: str
    cover_image_url: str | None
    beat_count: int
    duration_seconds: int
    completed_at: str


class StoryBeatRecord(BaseModel):
    """A single beat within a storybook."""

    beat_id: str
    beat_index: int
    narration: str
    child1_perspective: str | None
    child2_perspective: str | None
    scene_image_url: str | None
    choice_made: str | None
    available_choices: list[str]


class StorybookDetail(BaseModel):
    """Full storybook with all beats for the reader."""

    storybook_id: str
    sibling_pair_id: str
    title: str
    language: str
    cover_image_url: str | None
    beat_count: int
    duration_seconds: int
    completed_at: str
    beats: list[StoryBeatRecord]


class StorybookRecord(BaseModel):
    """Internal record returned after archival."""

    storybook_id: str
    sibling_pair_id: str
    title: str
    beat_count: int
    completed_at: str


class DeleteStorybookResult(BaseModel):
    """Response after deleting storybooks."""

    deleted_count: int
