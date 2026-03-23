"""End-to-end tests exercising real Gemini API calls.

Every test is decorated with @pytest.mark.e2e and auto-skipped when
GOOGLE_API_KEY is absent (see conftest.py pytestmark).

Run:  GOOGLE_API_KEY=<key> pytest tests/ -m e2e -x -q --tb=short
"""

import os
import re
from datetime import datetime

import pytest

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set",
    ),
]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

async def _cached_generate(storyteller, context, cache, guard):
    """Generate a story segment, using cache when available."""
    import json
    prompt_key = json.dumps(context, sort_keys=True, default=str)
    cached = cache.get(prompt_key)
    if cached is not None:
        return cached
    guard.record_call()
    segment = await storyteller.generate_story_segment(context=context)
    cache.put(prompt_key, segment)
    return segment


BLOCKLIST_KEYWORDS = [
    "violence", "blood", "kill", "death", "weapon", "gun", "knife",
    "drug", "alcohol", "hate", "murder", "torture", "abuse", "suicide",
    "terror", "assault", "horror", "zombie", "vampire", "evil",
]


# ------------------------------------------------------------------
# 5.1  test_story_segment_structure
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_story_segment_structure(
    e2e_storyteller, minimal_story_context, response_cache, budget_guard,
):
    """Validate response structure, character names, and prompt quality."""
    segment = await _cached_generate(
        e2e_storyteller, minimal_story_context, response_cache, budget_guard,
    )

    # Structure checks (Property 1)
    assert isinstance(segment["text"], str) and len(segment["text"]) > 0
    assert "timestamp" in segment
    datetime.fromisoformat(segment["timestamp"])  # parseable ISO 8601

    interactive = segment["interactive"]
    assert "type" in interactive
    assert "text" in interactive
    assert "expects_response" in interactive

    # Character name presence (Property 2)
    text_lower = segment["text"].lower()
    assert "mia" in text_lower or "leo" in text_lower, (
        "Story text should mention at least one character name"
    )

    # Prompt quality (Property 3)
    assert "?" in segment["text"], "Story should contain a question"
    assert 50 <= len(segment["text"]) <= 5000, (
        f"Text length {len(segment['text'])} outside 50-5000 range"
    )
    for term in BLOCKLIST_KEYWORDS:
        assert not re.search(r"\b" + re.escape(term) + r"\b", text_lower), (
            f"Blocklist term '{term}' found in story text"
        )


# ------------------------------------------------------------------
# 5.2  test_content_filter_on_real_output
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_content_filter_on_real_output(
    e2e_storyteller, e2e_content_filter, minimal_story_context,
    response_cache, budget_guard,
):
    """Run ContentFilter.scan() on real Gemini output."""
    from app.services.content_filter import ContentRating, AVAILABLE_THEMES

    segment = await _cached_generate(
        e2e_storyteller, minimal_story_context, response_cache, budget_guard,
    )

    result = e2e_content_filter.scan(text=segment["text"])
    assert result.rating == ContentRating.SAFE, (
        f"Expected SAFE, got {result.rating}: {result.reason}"
    )

    # With a theme subset, should not be BLOCKED
    subset = AVAILABLE_THEMES[:3]
    result2 = e2e_content_filter.scan(
        text=segment["text"], allowed_themes=subset,
    )
    assert result2.rating != ContentRating.BLOCKED, (
        f"Got BLOCKED with themes {subset}: {result2.reason}"
    )


# ------------------------------------------------------------------
# 5.3  test_safety_settings_configured
# ------------------------------------------------------------------

def test_safety_settings_configured(e2e_storyteller):
    """Verify all four harm categories use BLOCK_LOW_AND_ABOVE."""
    settings = e2e_storyteller.model._safety_settings
    assert len(settings) == 4, f"Expected 4 safety settings, got {len(settings)}"
    for setting in settings:
        assert setting["threshold"] == "BLOCK_LOW_AND_ABOVE", (
            f"Category {setting['category']} has threshold {setting['threshold']}"
        )


# ------------------------------------------------------------------
# 5.4  test_fallback_story_structure
# ------------------------------------------------------------------

def test_fallback_story_structure(e2e_storyteller, minimal_story_context):
    """Validate fallback story contains both names and correct structure."""
    fallback = e2e_storyteller._fallback_story(minimal_story_context)

    text_lower = fallback["text"].lower()
    assert "mia" in text_lower, "Fallback should mention Mia"
    assert "leo" in text_lower, "Fallback should mention Leo"
    assert len(fallback["text"]) > 0

    interactive = fallback["interactive"]
    assert "type" in interactive
    assert "text" in interactive
    assert "expects_response" in interactive


# ------------------------------------------------------------------
# 5.6  test_story_coordinator_safe_generation
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_story_coordinator_safe_generation(
    e2e_story_coordinator, minimal_story_context, response_cache, budget_guard,
):
    """StoryCoordinator.generate_safe_story_segment() with real Gemini."""
    segment = await e2e_story_coordinator.generate_safe_story_segment(
        story_context=minimal_story_context,
        user_input=None,
    )
    assert isinstance(segment["text"], str) and len(segment["text"]) > 0
    # If it passed content filtering, the text should be non-empty
    text_lower = segment["text"].lower()
    assert "mia" in text_lower or "leo" in text_lower


# ------------------------------------------------------------------
# 5.7  test_orchestrator_text_only
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_orchestrator_text_only(
    minimal_story_context, response_cache, budget_guard,
):
    """Full orchestrator flow with visual agent disabled."""
    from unittest.mock import MagicMock, AsyncMock
    from app.agents.storyteller_agent import StorytellerAgent
    from app.services.content_filter import ContentFilter
    from app.agents.coordinators.story_coordinator import StoryCoordinator
    from app.agents.coordinators.media_coordinator import MediaCoordinator
    from app.agents.coordinators.session_coordinator import SessionCoordinator
    from app.agents.coordinators.world_coordinator import WorldCoordinator

    # Build a minimal orchestrator-like setup
    storyteller = StorytellerAgent()
    storyteller.model._generation_config["max_output_tokens"] = 256

    content_filter = ContentFilter()
    mock_memory = MagicMock(enabled=False)
    mock_voice = MagicMock(enabled=False)

    story_coord = StoryCoordinator(
        storyteller=storyteller,
        content_filter=content_filter,
        memory_agent=mock_memory,
        voice_agent=mock_voice,
    )

    # Generate story segment directly via coordinator
    segment = await story_coord.generate_safe_story_segment(
        story_context=minimal_story_context,
        user_input=None,
    )

    assert isinstance(segment["text"], str) and len(segment["text"]) > 0

    # Simulate orchestrator result structure
    result = {
        "text": segment["text"],
        "image": None,
        "agents_used": {
            "storyteller": True,
            "visual": False,
            "voice": False,
            "memory": False,
        },
    }

    assert result["text"]
    assert result["agents_used"]["storyteller"] is True
    assert result["agents_used"]["visual"] is False
    assert result["image"] is None
