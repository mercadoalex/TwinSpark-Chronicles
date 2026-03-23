"""Property-based tests for Orchestrator Decomposition.

Covers:
- 1.4: SessionCoordinator cancel_session cancels all non-done tasks, removes key
- 2.3: StoryCoordinator generate_safe_story_segment never returns REVIEW/BLOCKED
- 3.3: WorldCoordinator extract_and_persist invalidates cache
- 6.3: Facade property accessors resolve to coordinator attributes
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, settings, strategies as st

from app.agents.coordinators.session_coordinator import SessionCoordinator
from app.agents.coordinators.story_coordinator import StoryCoordinator
from app.agents.coordinators.world_coordinator import WorldCoordinator
from app.services.content_filter import ContentRating


_safe_id = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789",
    min_size=1,
    max_size=12,
)


# ── 1.4  SessionCoordinator: cancel_session clears all tasks ──


@settings(max_examples=20)
@given(
    session_id=_safe_id,
    num_pending=st.integers(min_value=0, max_value=8),
    num_done=st.integers(min_value=0, max_value=4),
)
@pytest.mark.asyncio
async def test_cancel_session_clears_all_tasks(session_id, num_pending, num_done):
    """After cancel_session, all non-done tasks are cancelled and session key is removed."""
    sc = SessionCoordinator()

    pending_tasks = []
    done_tasks = []

    # Create real asyncio tasks — pending ones sleep forever
    for _ in range(num_pending):
        t = asyncio.ensure_future(asyncio.sleep(9999))
        pending_tasks.append(t)

    # Done tasks: already-completed coroutines
    for _ in range(num_done):
        t = asyncio.ensure_future(asyncio.sleep(0))
        await t  # let it finish
        done_tasks.append(t)

    all_tasks = set(pending_tasks + done_tasks)
    if all_tasks:
        sc._session_tasks[session_id] = all_tasks

    result = await sc.cancel_session(session_id)

    # Session key must be removed
    assert session_id not in sc._session_tasks

    # All pending tasks must be cancelled
    for t in pending_tasks:
        assert t.cancelled() or t.done()

    # Cancelled count matches pending (non-done) tasks
    assert result["cancelled_tasks"] == num_pending
    assert result["status"] == "stopped"


# ── 2.3  StoryCoordinator: never returns REVIEW or BLOCKED ───

# Strategy: generate a random sequence of content ratings the filter returns.
# The property: the final result is always either the SAFE segment or fallback.

_rating_sequence = st.lists(
    st.sampled_from([ContentRating.SAFE, ContentRating.REVIEW, ContentRating.BLOCKED]),
    min_size=1,
    max_size=5,
)

FALLBACK_TEXT = "A gentle breeze blew through the meadow."
SAFE_TEXT = "The brave dragon flew over the mountain."


def _make_story_coordinator(rating_seq):
    """Build a StoryCoordinator with mocked deps returning the given rating sequence."""
    storyteller = MagicMock()
    storyteller.generate_story_segment = AsyncMock(
        return_value={"text": SAFE_TEXT, "interactive": {}}
    )
    storyteller._fallback_story = MagicMock(
        return_value={"text": FALLBACK_TEXT, "interactive": {}}
    )

    scan_results = [
        MagicMock(rating=r, reason=None if r == ContentRating.SAFE else "flagged", matched_terms=[])
        for r in rating_seq
    ]
    cf = MagicMock()
    cf.scan = MagicMock(side_effect=scan_results)

    return StoryCoordinator(
        storyteller=storyteller,
        content_filter=cf,
        memory_agent=MagicMock(enabled=False),
        voice_agent=MagicMock(enabled=False),
        playback_integrator=None,
    )


@settings(max_examples=20)
@given(ratings=_rating_sequence)
@pytest.mark.asyncio
async def test_generate_safe_never_returns_review_or_blocked(ratings):
    """generate_safe_story_segment always returns SAFE text or fallback, never REVIEW/BLOCKED."""
    sc = _make_story_coordinator(ratings)
    result = await sc.generate_safe_story_segment({"session_id": "s1"}, "go")

    # Result must be either the safe segment or the fallback
    assert result["text"] in (SAFE_TEXT, FALLBACK_TEXT)

    # If any rating was SAFE, we should get the safe text
    if ContentRating.SAFE in ratings[:3]:  # only first 3 matter (MAX_CONTENT_RETRIES=3)
        first_safe_idx = next(i for i, r in enumerate(ratings[:3]) if r == ContentRating.SAFE)
        # The storyteller was called first_safe_idx+1 times, and we got the safe text
        assert result["text"] == SAFE_TEXT
    else:
        # All 3 retries were non-SAFE → fallback
        assert result["text"] == FALLBACK_TEXT


# ── 3.3  WorldCoordinator: cache empty after extract ──────────


@settings(max_examples=20)
@given(
    pair_id=_safe_id,
    num_locations=st.integers(min_value=0, max_value=3),
    num_npcs=st.integers(min_value=0, max_value=3),
    num_items=st.integers(min_value=0, max_value=3),
)
@pytest.mark.asyncio
async def test_cache_empty_after_extract(pair_id, num_locations, num_npcs, num_items):
    """After extract_and_persist_world_state, cache for that pair_id is always empty."""
    world_db = MagicMock()
    world_db.save_location = AsyncMock()
    world_db.save_npc = AsyncMock()
    world_db.save_item = AsyncMock()
    world_db.load_locations = AsyncMock(return_value=[])
    world_db.load_npcs = AsyncMock(return_value=[])

    changes = {
        "new_locations": [{"name": f"loc{i}", "description": "d", "state": "discovered"} for i in range(num_locations)],
        "new_npcs": [{"name": f"npc{i}", "description": "d", "relationship_level": 1} for i in range(num_npcs)],
        "new_items": [{"name": f"item{i}", "description": "d"} for i in range(num_items)],
        "location_updates": [],
        "npc_updates": [],
    }
    extractor = MagicMock()
    extractor.extract = AsyncMock(return_value=changes)
    formatter = MagicMock()

    wc = WorldCoordinator(world_db, extractor, formatter)

    # Pre-populate cache
    wc._world_state_cache[pair_id] = {"locations": [{"name": "old"}], "npcs": [], "items": []}

    memory = MagicMock(enabled=True)
    memory.story_memories.get.return_value = {"metadatas": [{"session_id": "s1"}]}

    await wc.extract_and_persist_world_state("s1", pair_id, memory)

    # Cache must be invalidated
    assert pair_id not in wc._world_state_cache


# ── 6.3  Facade: property accessors match coordinator attrs ───

# The property mapping: (facade_attr, coordinator_name, coordinator_attr)
_FACADE_MAPPINGS = [
    ("session_time_enforcer", "session", "session_time_enforcer"),
    ("ws_manager", "session", "ws_manager"),
    ("_session_tasks", "session", "_session_tasks"),
    ("_world_db", "world", "_world_db"),
    ("content_filter", "story", "content_filter"),
    ("_playback_integrator", "story", "playback_integrator"),
    ("_world_state_cache", "world", "_world_state_cache"),
    ("_world_extractor", "world", "_world_extractor"),
]


@settings(max_examples=20)
@given(mapping_idx=st.integers(min_value=0, max_value=len(_FACADE_MAPPINGS) - 1))
def test_facade_accessor_matches_coordinator(mapping_idx):
    """Accessing a property on the facade returns the same object as the coordinator's attribute."""
    from app.agents.orchestrator import AgentOrchestrator

    orch = AgentOrchestrator()
    facade_attr, coord_name, coord_attr = _FACADE_MAPPINGS[mapping_idx]

    coordinator = getattr(orch, coord_name)
    facade_value = getattr(orch, facade_attr)
    coord_value = getattr(coordinator, coord_attr)

    assert facade_value is coord_value
