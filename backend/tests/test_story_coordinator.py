"""Unit tests for StoryCoordinator."""

import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest

from app.agents.coordinators.story_coordinator import StoryCoordinator
from app.services.content_filter import ContentRating


def _make_sc(**overrides):
    """Create a StoryCoordinator with mocked dependencies."""
    storyteller = MagicMock()
    storyteller.generate_story_segment = AsyncMock(
        return_value={"text": "The brave dragon flew.", "interactive": {}}
    )
    storyteller._fallback_story = MagicMock(
        return_value={"text": "A gentle breeze blew.", "interactive": {}}
    )

    cf = MagicMock()
    cf.scan = MagicMock(
        return_value=MagicMock(rating=ContentRating.SAFE, reason=None, matched_terms=[])
    )

    memory = MagicMock(enabled=False)
    voice = MagicMock(enabled=False)

    defaults = dict(
        storyteller=storyteller,
        content_filter=cf,
        memory_agent=memory,
        voice_agent=voice,
        playback_integrator=None,
    )
    defaults.update(overrides)
    return StoryCoordinator(**defaults)


class TestGenerateSafeStorySegment:
    """generate_safe_story_segment with content filtering and retry."""

    @pytest.mark.asyncio
    async def test_returns_safe_segment(self):
        sc = _make_sc()
        result = await sc.generate_safe_story_segment({"session_id": "s1"}, "go")
        assert result["text"] == "The brave dragon flew."

    @pytest.mark.asyncio
    async def test_retries_on_review(self):
        sc = _make_sc()
        sc.content_filter.scan = MagicMock(side_effect=[
            MagicMock(rating=ContentRating.REVIEW, reason="scary", matched_terms=["dark"]),
            MagicMock(rating=ContentRating.SAFE, reason=None, matched_terms=[]),
        ])
        result = await sc.generate_safe_story_segment({"session_id": "s1"}, "go")
        assert result["text"] == "The brave dragon flew."
        assert sc.storyteller.generate_story_segment.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_after_exhaustion(self):
        sc = _make_sc()
        sc.content_filter.scan = MagicMock(
            return_value=MagicMock(rating=ContentRating.BLOCKED, reason="bad", matched_terms=[])
        )
        result = await sc.generate_safe_story_segment({"session_id": "s1"}, "go")
        assert result["text"] == "A gentle breeze blew."
        sc.storyteller._fallback_story.assert_called_once()

    @pytest.mark.asyncio
    async def test_fallback_on_filter_error(self):
        sc = _make_sc()
        sc.content_filter.scan = MagicMock(side_effect=Exception("filter crash"))
        result = await sc.generate_safe_story_segment({"session_id": "s1"}, "go")
        assert result["text"] == "A gentle breeze blew."


class TestFilterChoices:
    """filter_choices filters interactive text and individual choices."""

    def test_filters_unsafe_choice_text(self):
        sc = _make_sc()
        sc.content_filter.scan = MagicMock(
            return_value=MagicMock(rating=ContentRating.BLOCKED, reason="bad", matched_terms=[])
        )
        segment = {"text": "story", "interactive": {"text": "bad prompt", "choices": []}}
        result = sc.filter_choices(segment, "s1")
        assert result["interactive"]["text"] == "What would you like to do next?"

    def test_keeps_safe_choices(self):
        sc = _make_sc()
        segment = {
            "text": "story",
            "interactive": {"text": "Choose:", "choices": ["run", "hide"]},
        }
        result = sc.filter_choices(segment, "s1")
        assert len(result["interactive"]["choices"]) == 2

    def test_no_crash_on_empty_interactive(self):
        sc = _make_sc()
        segment = {"text": "story", "interactive": {}}
        result = sc.filter_choices(segment, "s1")
        assert result["interactive"] == {}


class TestCheckVoicePlayback:
    """check_voice_playback detects triggers and returns recordings."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_integrator(self):
        sc = _make_sc()
        result = await sc.check_voice_playback(
            {"text": "brave hero"}, {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
            None, "en",
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_story_intro_on_first_beat(self):
        from app.models.voice_recording import PlaybackResult
        pi = MagicMock()
        pi.get_story_intro_audio = AsyncMock(return_value=PlaybackResult(
            source="recording", audio_base64="abc", recorder_name="Mom", recording_id="r1",
        ))
        pi.get_encouragement_audio = AsyncMock(return_value=None)
        pi.get_sound_effect = AsyncMock(return_value=None)
        sc = _make_sc(playback_integrator=pi)
        result = await sc.check_voice_playback(
            {"text": "Once upon a time"}, {"child1": {"name": "Ale"}, "child2": {"name": "Sofi"}},
            None, "en",
        )
        assert len(result) == 1
        assert result[0]["type"] == "story_intro"

    @pytest.mark.asyncio
    async def test_graceful_on_error(self):
        pi = MagicMock()
        pi.get_story_intro_audio = AsyncMock(side_effect=Exception("boom"))
        sc = _make_sc(playback_integrator=pi)
        result = await sc.check_voice_playback(
            {"text": "story"}, {"child1": {"name": "A"}, "child2": {"name": "B"}},
            None, "en",
        )
        assert result == []


class TestTextExtraction:
    """extract_dialogues and extract_lesson helpers."""

    def test_extract_dialogues(self):
        sc = _make_sc()
        result = sc.extract_dialogues('She said "hello" and he said "goodbye"')
        assert len(result) == 2
        assert result[0]["text"] == "hello"

    def test_extract_lesson_courage(self):
        sc = _make_sc()
        assert sc.extract_lesson("The brave hero stood tall") == "courage"

    def test_extract_lesson_default(self):
        sc = _make_sc()
        assert sc.extract_lesson("The portal opened") == "adventure"
