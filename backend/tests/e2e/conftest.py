"""E2E test fixtures — restore real google.generativeai and provide shared agents.

All fixtures are session-scoped to minimise API calls and agent init overhead.
Module-level skipif ensures every test in this package is skipped when
GOOGLE_API_KEY is absent.
"""

import os
import sys

import pytest

# Skip entire module when credentials are missing
pytestmark = pytest.mark.skipif(
    not os.environ.get("GOOGLE_API_KEY"),
    reason="GOOGLE_API_KEY not set",
)


# ------------------------------------------------------------------
# Restore real google.generativeai (undo root conftest mocks)
# ------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _restore_real_genai():
    """Pop mock entries from sys.modules so the real SDK is imported."""
    mock_keys = [k for k in sys.modules if k.startswith(("google.generativeai",))]
    for key in mock_keys:
        sys.modules.pop(key, None)
    import google.generativeai  # noqa: F401 — force real import


# ------------------------------------------------------------------
# Cost-control fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def response_cache(request):
    from pathlib import Path
    from tests.e2e.response_cache import ResponseCache

    cache_dir = Path(__file__).resolve().parent.parent / "e2e_cache"
    cache = ResponseCache(cache_dir)
    if request.config.getoption("--e2e-no-cache", default=False):
        # Return a no-op cache
        cache.get = lambda prompt: None
        cache.put = lambda prompt, response: None
    return cache


@pytest.fixture(scope="session")
def budget_guard(request):
    from tests.e2e.budget_guard import BudgetGuard

    max_calls = request.config.getoption("--e2e-max-calls", default=20)
    return BudgetGuard(max_calls=max_calls)


# ------------------------------------------------------------------
# Agent / service fixtures
# ------------------------------------------------------------------

@pytest.fixture(scope="session")
def e2e_storyteller():
    """StorytellerAgent with reduced max_output_tokens for cost control."""
    from app.agents.storyteller_agent import StorytellerAgent

    agent = StorytellerAgent()
    # Override generation config to 256 tokens
    agent.model._generation_config["max_output_tokens"] = 256
    return agent


@pytest.fixture(scope="session")
def e2e_content_filter():
    from app.services.content_filter import ContentFilter

    return ContentFilter()


@pytest.fixture(scope="session")
def e2e_story_coordinator(e2e_storyteller, e2e_content_filter):
    from unittest.mock import MagicMock
    from app.agents.coordinators.story_coordinator import StoryCoordinator

    return StoryCoordinator(
        storyteller=e2e_storyteller,
        content_filter=e2e_content_filter,
        memory_agent=MagicMock(enabled=False),
        voice_agent=MagicMock(enabled=False),
    )


@pytest.fixture(scope="session")
def minimal_story_context():
    return {
        "characters": {
            "child1": {"name": "Mia", "gender": "girl", "spirit_animal": "dolphin"},
            "child2": {"name": "Leo", "gender": "boy", "spirit_animal": "eagle"},
        },
        "session_id": "e2e-test-session",
        "language": "en",
    }
