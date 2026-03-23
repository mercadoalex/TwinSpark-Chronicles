"""Property-based tests for StoryArchiveService (Tasks 2.6–2.9).

Uses Hypothesis to validate:
  Property 1 — Storybook round-trip preservation
  Property 2 — Archive metadata invariants
  Property 3 — Gallery listing order
  Property 4 — Deletion completeness
"""

import asyncio
import time

import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from app.services.story_archive_service import StoryArchiveService


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

_text_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=60,
)

_optional_text_st = st.one_of(st.none(), _text_st)

_choices_st = st.lists(_text_st, min_size=0, max_size=4)

_beat_st = st.fixed_dictionaries(
    {
        "narration": _text_st,
        "child1_perspective": _optional_text_st,
        "child2_perspective": _optional_text_st,
        "scene_image_url": _optional_text_st,
        "choice_made": _optional_text_st,
        "available_choices": _choices_st,
    }
)

_beats_st = st.lists(_beat_st, min_size=1, max_size=10)

_duration_st = st.integers(min_value=0, max_value=36000)


# ---------------------------------------------------------------------------
# Property 1 — Storybook round-trip preservation (Task 2.6)
# ---------------------------------------------------------------------------

class TestRoundTripPreservation:
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(beats=_beats_st, title=_text_st, duration=_duration_st)
    @pytest.mark.asyncio
    async def test_archive_then_retrieve_preserves_all_fields(
        self, story_archive_service, beats, title, duration
    ):
        record = await story_archive_service.archive_story(
            sibling_pair_id="prop:pair",
            title=title,
            language="en",
            beats=beats,
            duration_seconds=duration,
        )
        assert record is not None

        detail = await story_archive_service.get_storybook(record.storybook_id)
        assert detail is not None
        assert detail.title == title
        assert detail.language == "en"
        assert detail.duration_seconds == duration
        assert len(detail.beats) == len(beats)

        for i, (expected, actual) in enumerate(zip(beats, detail.beats)):
            assert actual.beat_index == i
            assert actual.narration == expected["narration"]
            assert actual.child1_perspective == expected.get("child1_perspective")
            assert actual.child2_perspective == expected.get("child2_perspective")
            assert actual.scene_image_url == expected.get("scene_image_url")
            assert actual.choice_made == expected.get("choice_made")
            assert actual.available_choices == expected.get("available_choices", [])


# ---------------------------------------------------------------------------
# Property 2 — Archive metadata invariants (Task 2.7)
# ---------------------------------------------------------------------------

class TestArchiveMetadataInvariants:
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(beats=_beats_st, duration=_duration_st)
    @pytest.mark.asyncio
    async def test_beat_count_and_cover_image_match_input(
        self, story_archive_service, beats, duration
    ):
        record = await story_archive_service.archive_story(
            sibling_pair_id="meta:pair",
            title="Metadata Test",
            language="en",
            beats=beats,
            duration_seconds=duration,
        )
        assert record is not None
        assert record.beat_count == len(beats)

        detail = await story_archive_service.get_storybook(record.storybook_id)
        assert detail is not None
        assert detail.beat_count == len(beats)
        assert detail.duration_seconds == duration
        assert detail.cover_image_url == beats[0].get("scene_image_url")


# ---------------------------------------------------------------------------
# Property 3 — Gallery listing order (Task 2.8)
# ---------------------------------------------------------------------------

class TestGalleryListingOrder:
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(count=st.integers(min_value=2, max_value=6))
    @pytest.mark.asyncio
    async def test_listing_is_newest_first_and_complete(
        self, story_archive_service, count
    ):
        pair_id = f"order:{time.monotonic_ns()}"
        ids = []
        for i in range(count):
            rec = await story_archive_service.archive_story(
                sibling_pair_id=pair_id,
                title=f"Story {i}",
                language="en",
                beats=[{"narration": f"beat {i}", "available_choices": []}],
                duration_seconds=i * 10,
            )
            ids.append(rec.storybook_id)

        summaries = await story_archive_service.list_storybooks(pair_id)
        assert len(summaries) == count

        # All IDs present
        listed_ids = {s.storybook_id for s in summaries}
        assert listed_ids == set(ids)

        # Descending order by completed_at
        for j in range(len(summaries) - 1):
            assert summaries[j].completed_at >= summaries[j + 1].completed_at


# ---------------------------------------------------------------------------
# Property 4 — Deletion completeness (Task 2.9)
# ---------------------------------------------------------------------------

class TestDeletionCompleteness:
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        beat_counts=st.lists(
            st.integers(min_value=1, max_value=5), min_size=2, max_size=5
        )
    )
    @pytest.mark.asyncio
    async def test_single_delete_removes_storybook_and_beats(
        self, story_archive_service, beat_counts
    ):
        pair_id = f"del:{time.monotonic_ns()}"
        records = []
        for i, bc in enumerate(beat_counts):
            beats = [
                {"narration": f"n{j}", "available_choices": []}
                for j in range(bc)
            ]
            rec = await story_archive_service.archive_story(
                sibling_pair_id=pair_id,
                title=f"Del {i}",
                language="en",
                beats=beats,
                duration_seconds=10,
            )
            records.append(rec)

        # Delete the first one
        target = records[0]
        assert await story_archive_service.delete_storybook(target.storybook_id) is True
        assert await story_archive_service.get_storybook(target.storybook_id) is None

        # Others still exist
        remaining = await story_archive_service.list_storybooks(pair_id)
        assert len(remaining) == len(beat_counts) - 1

    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(count=st.integers(min_value=1, max_value=5))
    @pytest.mark.asyncio
    async def test_bulk_delete_removes_all(
        self, story_archive_service, count
    ):
        pair_id = f"bulk:{time.monotonic_ns()}"
        for i in range(count):
            await story_archive_service.archive_story(
                sibling_pair_id=pair_id,
                title=f"Bulk {i}",
                language="en",
                beats=[{"narration": "b", "available_choices": []}],
                duration_seconds=5,
            )

        deleted = await story_archive_service.delete_all_storybooks(pair_id)
        assert deleted == count

        remaining = await story_archive_service.list_storybooks(pair_id)
        assert remaining == []
