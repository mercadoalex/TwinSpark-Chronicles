"""Unit tests for StoryArchiveService (Tasks 2.1–2.5)."""

import logging

import pytest

from app.services.story_archive_service import StoryArchiveService


def _make_beats(count=3):
    """Build a list of beat dicts for archival."""
    return [
        {
            "narration": f"Beat {i} narration",
            "child1_perspective": f"Child1 sees beat {i}",
            "child2_perspective": f"Child2 hears beat {i}",
            "scene_image_url": f"/assets/scene_{i}.png",
            "choice_made": f"Choice {i}",
            "available_choices": [f"Choice {i}", f"Alt {i}A", f"Alt {i}B"],
        }
        for i in range(count)
    ]


class TestArchiveStory:
    @pytest.mark.asyncio
    async def test_archive_with_3_beats_persists_all_fields(self, story_archive_service, db):
        beats = _make_beats(3)
        result = await story_archive_service.archive_story(
            sibling_pair_id="Ale:Sofi",
            title="Dragon Garden",
            language="en",
            beats=beats,
            duration_seconds=420,
        )

        assert result is not None
        assert result.sibling_pair_id == "Ale:Sofi"
        assert result.title == "Dragon Garden"
        assert result.beat_count == 3
        assert len(result.storybook_id) == 12
        assert len(result.completed_at) > 0

        # Verify via get_storybook
        detail = await story_archive_service.get_storybook(result.storybook_id)
        assert detail is not None
        assert detail.title == "Dragon Garden"
        assert detail.language == "en"
        assert detail.duration_seconds == 420
        assert detail.beat_count == 3
        assert len(detail.beats) == 3

        for i, beat in enumerate(detail.beats):
            assert beat.beat_index == i
            assert beat.narration == f"Beat {i} narration"
            assert beat.child1_perspective == f"Child1 sees beat {i}"
            assert beat.child2_perspective == f"Child2 hears beat {i}"
            assert beat.scene_image_url == f"/assets/scene_{i}.png"
            assert beat.choice_made == f"Choice {i}"
            assert beat.available_choices == [f"Choice {i}", f"Alt {i}A", f"Alt {i}B"]

    @pytest.mark.asyncio
    async def test_archive_empty_beats_returns_none(self, story_archive_service, caplog):
        with caplog.at_level(logging.WARNING):
            result = await story_archive_service.archive_story(
                sibling_pair_id="Ale:Sofi",
                title="Empty Story",
                language="en",
                beats=[],
                duration_seconds=0,
            )

        assert result is None
        assert "no beats provided" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_cover_image_equals_first_beat_scene_image(self, story_archive_service):
        beats = _make_beats(2)
        beats[0]["scene_image_url"] = "/assets/cover_scene.png"

        result = await story_archive_service.archive_story(
            sibling_pair_id="Ale:Sofi",
            title="Cover Test",
            language="en",
            beats=beats,
            duration_seconds=60,
        )

        detail = await story_archive_service.get_storybook(result.storybook_id)
        assert detail.cover_image_url == "/assets/cover_scene.png"


class TestListStorybooks:
    @pytest.mark.asyncio
    async def test_list_empty_returns_empty_list(self, story_archive_service):
        result = await story_archive_service.list_storybooks("nobody:here")
        assert result == []

    @pytest.mark.asyncio
    async def test_list_returns_summaries_newest_first(self, story_archive_service):
        for i in range(3):
            await story_archive_service.archive_story(
                sibling_pair_id="Ale:Sofi",
                title=f"Story {i}",
                language="en",
                beats=_make_beats(1),
                duration_seconds=100 * i,
            )

        summaries = await story_archive_service.list_storybooks("Ale:Sofi")
        assert len(summaries) == 3
        # Newest first (descending completed_at)
        for j in range(len(summaries) - 1):
            assert summaries[j].completed_at >= summaries[j + 1].completed_at


class TestGetStorybook:
    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, story_archive_service):
        result = await story_archive_service.get_storybook("nonexistent_id")
        assert result is None


class TestDeleteStorybook:
    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, story_archive_service):
        result = await story_archive_service.delete_storybook("nonexistent_id")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_existing_returns_true_and_removes(self, story_archive_service):
        record = await story_archive_service.archive_story(
            sibling_pair_id="Ale:Sofi",
            title="To Delete",
            language="en",
            beats=_make_beats(2),
            duration_seconds=60,
        )

        assert await story_archive_service.delete_storybook(record.storybook_id) is True
        assert await story_archive_service.get_storybook(record.storybook_id) is None


class TestDeleteAllStorybooks:
    @pytest.mark.asyncio
    async def test_bulk_delete_returns_count_and_removes_all(self, story_archive_service):
        for i in range(4):
            await story_archive_service.archive_story(
                sibling_pair_id="Ale:Sofi",
                title=f"Bulk {i}",
                language="en",
                beats=_make_beats(1),
                duration_seconds=30,
            )

        count = await story_archive_service.delete_all_storybooks("Ale:Sofi")
        assert count == 4

        remaining = await story_archive_service.list_storybooks("Ale:Sofi")
        assert remaining == []

    @pytest.mark.asyncio
    async def test_bulk_delete_empty_returns_zero(self, story_archive_service):
        count = await story_archive_service.delete_all_storybooks("nobody:here")
        assert count == 0
