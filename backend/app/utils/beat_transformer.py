"""Transform frontend story beats into the archive format.

Maps frontend beat keys to the schema expected by StoryArchiveService,
dropping frontend-only fields like ``timestamp``.

Requirements: 2.3
"""

from __future__ import annotations

# Keys that pass through unchanged
_PASSTHROUGH_KEYS = (
    "narration",
    "child1_perspective",
    "child2_perspective",
    "scene_image_url",
)

# Keys that get renamed: frontend_key → archive_key
_RENAME_MAP = {
    "choiceMade": "choice_made",
    "choices": "available_choices",
}


def transform_beats(story_history: list[dict]) -> list[dict]:
    """Convert frontend story_history entries to archive beat dicts.

    Each output beat contains only the keys expected by
    ``StoryArchiveService.archive_story()``.  Unknown / frontend-only
    keys (e.g. ``timestamp``) are silently dropped.

    Missing optional fields default to ``None`` (scalars) or ``[]``
    (list fields like ``available_choices``).
    """
    return [_transform_single(beat) for beat in story_history]


def _transform_single(beat: dict) -> dict:
    result: dict = {}

    for key in _PASSTHROUGH_KEYS:
        result[key] = beat.get(key)

    result["choice_made"] = beat.get("choiceMade")
    result["available_choices"] = beat.get("choices") if beat.get("choices") is not None else []

    return result
