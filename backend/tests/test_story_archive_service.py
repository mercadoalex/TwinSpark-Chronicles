"""Unit tests for StoryArchiveService.

Requirements: 1.1–1.6, 2.1, 3.1, 4.1, 4.4
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.db.connection import DatabaseConnection
from app.services.story_archive_service import StoryArchiveService


def _make_beat(
    narration: str = "Once upon a time...",
    scene_image_url: str | None = "/assets/scene_1.png",
    child1_perspective: str | None = "Ale sees a dragon",
    child2_perspective: str | None = "Sofi hears a melody",
    choice_made: str | None = "Open the door",
    available_choices: list[str] | None = None,
) -> dict:
    return {
        "narration": narration,
        "scene_image_url": scene_image_url,
        "child1_perspective": child1_perspective,
        "child2_perspective": child2_perspective,
        "choice_made": choice_made,
        "available_choices": available_choices or ["Open the door", "Run away"],
    }


@pytest_asyncio.fixture
async def svc():
    db = DatabaseConnection("sqlite:///:memory:")
    await db.connect()
    service = StoryArchiveService(db)
    await service._ensure_tables()
    yield service
    await db.close()


# ── archive ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_with_beats_persists_all_fields(svc):
    beats = [
        _make_beat("Beat one", "/img/1.png", "Ale1", "Sofi1", "Go left", ["Go left", "Go right"]),
        _make_beat("Beat two", "/img/2.png", "Ale2", "Sofi2", "Jump", ["Jump", "Duck"]),
        _make_beat("Beat three", "/img/3.png", "Ale3", "Sofi3", "Sing", ["Sing", "Dance", "Wait"]),
    ]
    record = await svc.archive_story("Ale:Sofi", "Dragon Quest", "en", beats, 300)

    assert record is not None
    assert record.title == "Dragon Quest"
    assert record.sibling_pair_id == "Ale:Sofi"
    assert record.beat_count == 3

    detail = await svc.get_storybook(record.storybook_id)
    assert detail is not None
    assert detail.title == "Dragon Quest"
    assert detail.language == "en"
    assert detail.duration_seconds == 300
    assert len(detail.beats) == 3

    # Verify beat fields
    b0 = detail.beats[0]
    assert b0.beat_index == 0
    assert b0.narration == "Beat one"
    assert b0.child1_perspective == "Ale1"
    assert b0.child2_perspective == "Sofi1"
    assert b0.scene_image_url == "/img/1.png"
    assert b0.choice_made == "Go left"
    assert b0.available_choices == ["Go left", "Go right"]

    b2 = detail.beats[2]
    assert b2.beat_index == 2
    assert b2.narration == "Beat three"
    assert b2.available_choices == ["Sing", "Dance", "Wait"]


@pytest.mark.asyncio
async def test_archive_empty_beats_returns_none(svc):
    record = await svc.archive_story("Ale:Sofi", "Empty Story", "en", [], 0)
    assert record is None


# ── listing ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_storybooks_empty_returns_empty_list(svc):
    result = await svc.list_storybooks("Nobody:Here")
    assert result == []


# ── detail ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_storybook_nonexistent_returns_none(svc):
    result = await svc.get_storybook("nonexistent_id")
    assert result is None


# ── deletion ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(svc):
    result = await svc.delete_storybook("nonexistent_id")
    assert result is False


@pytest.mark.asyncio
async def test_bulk_delete_returns_count_and_removes_all(svc):
    # Archive 3 storybooks
    for i in range(3):
        await svc.archive_story(
            "Ale:Sofi", f"Story {i}", "en", [_make_beat()], 60
        )

    # Verify they exist
    books = await svc.list_storybooks("Ale:Sofi")
    assert len(books) == 3

    # Bulk delete
    count = await svc.delete_all_storybooks("Ale:Sofi")
    assert count == 3

    # Verify all gone
    books = await svc.list_storybooks("Ale:Sofi")
    assert len(books) == 0


# ── cover image ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cover_image_equals_first_beat_scene_image(svc):
    beats = [
        _make_beat(scene_image_url="/img/cover.png"),
        _make_beat(scene_image_url="/img/other.png"),
    ]
    record = await svc.archive_story("Ale:Sofi", "Cover Test", "en", beats, 120)
    assert record is not None

    detail = await svc.get_storybook(record.storybook_id)
    assert detail is not None
    assert detail.cover_image_url == "/img/cover.png"
