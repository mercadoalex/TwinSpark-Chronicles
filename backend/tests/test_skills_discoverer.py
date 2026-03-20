"""Property-based tests for ComplementarySkillsDiscoverer (Layer 3).

Tests cover skill map generation threshold, complementary pair identification,
skill map re-evaluation interval, and growth detection using Hypothesis
strategies from conftest.py.
"""

from __future__ import annotations

import pytest
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from app.models.sibling import (
    ComplementaryPair,
    PersonalityProfile,
    SkillMap,
    TraitScore,
)
from app.services.skills_discoverer import ComplementarySkillsDiscoverer, _pair_id
from app.services.sibling_db import SiblingDB

from tests.conftest import st_personality_profile, st_trait_score

import itertools

# ---- Helpers ----------------------------------------------------------------

_unit_float = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_high_conf = st.floats(min_value=0.51, max_value=1.0, allow_nan=False)
_low_conf = st.floats(min_value=0.0, max_value=0.49, allow_nan=False)

_counter = itertools.count()


def _make_profile(
    child_id: str,
    trait_values: dict[str, float] | None = None,
    trait_confidences: dict[str, float] | None = None,
) -> PersonalityProfile:
    """Build a PersonalityProfile with explicit trait values and confidences."""
    dims = ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]
    kwargs: dict = {"child_id": child_id}
    for dim in dims:
        val = (trait_values or {}).get(dim, 0.5)
        conf = (trait_confidences or {}).get(dim, 0.0)
        kwargs[dim] = TraitScore(value=val, confidence=conf, observation_count=10)
    return PersonalityProfile(**kwargs)


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 12: Skill map generation threshold
# Validates: Requirements 4.1
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(data=st.data())
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_skill_map_generation_threshold(sibling_db: SiblingDB, data):
    """For any pair of PersonalityProfiles, evaluate() returns a non-None
    SkillMap if and only if both profiles have high_confidence_count() >= 3.

    We generate two profiles with controlled confidence values:
    - "above threshold": all 6 traits have confidence > 0.5
    - "below threshold": fewer than 3 traits have confidence > 0.5

    **Validates: Requirements 4.1**
    """
    dims = ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]

    # Decide whether each profile meets the threshold
    a_above = data.draw(st.booleans(), label="profile_a_above_threshold")
    b_above = data.draw(st.booleans(), label="profile_b_above_threshold")

    # Build confidence dicts
    if a_above:
        conf_a = {d: data.draw(_high_conf, label=f"a_{d}_conf") for d in dims}
    else:
        # Pick 0-2 traits to be high confidence, rest low
        high_count = data.draw(st.integers(min_value=0, max_value=2), label="a_high_count")
        conf_a = {}
        for i, d in enumerate(dims):
            if i < high_count:
                conf_a[d] = data.draw(_high_conf, label=f"a_{d}_conf")
            else:
                conf_a[d] = data.draw(_low_conf, label=f"a_{d}_conf")

    if b_above:
        conf_b = {d: data.draw(_high_conf, label=f"b_{d}_conf") for d in dims}
    else:
        high_count = data.draw(st.integers(min_value=0, max_value=2), label="b_high_count")
        conf_b = {}
        for i, d in enumerate(dims):
            if i < high_count:
                conf_b[d] = data.draw(_high_conf, label=f"b_{d}_conf")
            else:
                conf_b[d] = data.draw(_low_conf, label=f"b_{d}_conf")

    # Use unique child IDs per example to avoid DB state leaking across runs
    uid = next(_counter)
    profile_a = _make_profile(f"a_th_{uid}", trait_confidences=conf_a)
    profile_b = _make_profile(f"b_th_{uid}", trait_confidences=conf_b)

    discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
    result = await discoverer.evaluate((profile_a, profile_b), interaction_count=1000)

    both_above = a_above and b_above

    if both_above:
        assert result is not None, (
            f"Expected non-None SkillMap when both profiles meet threshold. "
            f"a_high={profile_a.high_confidence_count()}, b_high={profile_b.high_confidence_count()}"
        )
    else:
        assert result is None, (
            f"Expected None when at least one profile is below threshold. "
            f"a_high={profile_a.high_confidence_count()}, b_high={profile_b.high_confidence_count()}"
        )


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 13: Complementary pair identification
# Validates: Requirements 4.2
# ---------------------------------------------------------------------------


@given(
    strong_val=st.floats(min_value=0.71, max_value=1.0, allow_nan=False),
    weak_val=st.floats(min_value=0.0, max_value=0.39, allow_nan=False),
    dimension=st.sampled_from(
        ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]
    ),
    a_is_strong=st.booleans(),
)
@settings(max_examples=20)
def test_complementary_pair_identification(
    strong_val: float, weak_val: float, dimension: str, a_is_strong: bool
):
    """For any two PersonalityProfiles where at least one trait has child A's
    score > 0.7 and child B's score < 0.4 (or vice versa),
    _find_complementary_pairs should return at least one ComplementaryPair
    with the correct strength holder and growth area holder.

    **Validates: Requirements 4.2**
    """
    if a_is_strong:
        vals_a = {dimension: strong_val}
        vals_b = {dimension: weak_val}
    else:
        vals_a = {dimension: weak_val}
        vals_b = {dimension: strong_val}

    profile_a = _make_profile("child_a_comp", trait_values=vals_a)
    profile_b = _make_profile("child_b_comp", trait_values=vals_b)

    discoverer = ComplementarySkillsDiscoverer(db=None)  # type: ignore[arg-type]
    pairs = discoverer._find_complementary_pairs(profile_a, profile_b)

    # There should be at least one pair for the controlled dimension
    assert len(pairs) >= 1, (
        f"Expected at least one complementary pair for dimension '{dimension}' "
        f"(a={vals_a.get(dimension)}, b={vals_b.get(dimension)}), got {len(pairs)}"
    )

    # Find the pair for our controlled dimension
    matching = [p for p in pairs if p.trait_dimension == dimension]
    assert len(matching) >= 1, (
        f"No pair found for dimension '{dimension}' among {[p.trait_dimension for p in pairs]}"
    )

    pair = matching[0]
    if a_is_strong:
        assert pair.strength_holder_id == "child_a_comp", (
            f"Expected child_a_comp as strength holder, got {pair.strength_holder_id}"
        )
        assert pair.growth_area_holder_id == "child_b_comp", (
            f"Expected child_b_comp as growth area holder, got {pair.growth_area_holder_id}"
        )
    else:
        assert pair.strength_holder_id == "child_b_comp", (
            f"Expected child_b_comp as strength holder, got {pair.strength_holder_id}"
        )
        assert pair.growth_area_holder_id == "child_a_comp", (
            f"Expected child_a_comp as growth area holder, got {pair.growth_area_holder_id}"
        )


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 14: Skill map re-evaluation interval
# Validates: Requirements 4.4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(data=st.data())
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_skill_map_reevaluation_interval(sibling_db: SiblingDB, data):
    """For any SkillMap with interaction_count_at_evaluation = N, calling
    evaluate() with interaction_count < N + 10 should return the existing
    skill map unchanged. Calling with interaction_count >= N + 10 should
    trigger re-evaluation.

    **Validates: Requirements 4.4**
    """
    base_count = data.draw(st.integers(min_value=0, max_value=9990), label="base_count")
    delta = data.draw(st.integers(min_value=0, max_value=20), label="delta")

    # Use unique child IDs per example to avoid DB state leaking across runs
    uid = next(_counter)
    child_a_id = f"a_re_{uid}"
    child_b_id = f"b_re_{uid}"

    dims = ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]
    # Build profiles that meet the confidence threshold (all high confidence)
    high_conf = {d: 0.9 for d in dims}
    profile_a = _make_profile(child_a_id, trait_confidences=high_conf)
    profile_b = _make_profile(child_b_id, trait_confidences=high_conf)

    discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
    pair_id = _pair_id(child_a_id, child_b_id)

    # Seed an initial skill map at base_count
    initial_result = await discoverer.evaluate(
        (profile_a, profile_b), interaction_count=base_count
    )
    assert initial_result is not None

    # Reload to get the persisted version
    stored = await discoverer.load_skill_map(pair_id)
    assert stored is not None
    assert stored.interaction_count_at_evaluation == base_count

    new_count = base_count + delta

    result = await discoverer.evaluate((profile_a, profile_b), interaction_count=new_count)
    assert result is not None

    if delta < 10:
        # Should return existing skill map unchanged
        assert result.interaction_count_at_evaluation == base_count, (
            f"Expected unchanged evaluation count {base_count}, "
            f"got {result.interaction_count_at_evaluation} (delta={delta})"
        )
    else:
        # Should trigger re-evaluation with new interaction count
        assert result.interaction_count_at_evaluation == new_count, (
            f"Expected re-evaluated count {new_count}, "
            f"got {result.interaction_count_at_evaluation} (delta={delta})"
        )



# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 21: Growth detection
# Validates: Requirements 8.4
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@given(data=st.data())
@settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_growth_detection(sibling_db: SiblingDB, data):
    """For any child whose current trait score exceeds the initial trait score
    by 0.2 or more on any dimension, check_growth should return that trait
    dimension in its result list. If no trait improved by >= 0.2, the result
    should be empty.

    **Validates: Requirements 8.4**
    """
    dims = ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]

    # Generate initial trait values (capped at 0.7 to leave room for growth bump)
    initial_values = {
        d: data.draw(
            st.floats(min_value=0.0, max_value=0.7, allow_nan=False),
            label=f"init_{d}",
        )
        for d in dims
    }

    # For each dimension, decide whether it should show growth
    grows = {
        d: data.draw(st.booleans(), label=f"grows_{d}")
        for d in dims
    }

    # Build current values: if grows, add >= 0.2; otherwise add < 0.2
    current_values: dict[str, float] = {}
    for d in dims:
        init_v = initial_values[d]
        if grows[d]:
            # Improvement of at least 0.2, capped at 1.0
            # Use 0.201 to avoid floating-point boundary issues (0.5 + 0.2 != 0.7 exactly)
            bump = data.draw(
                st.floats(min_value=0.201, max_value=min(0.5, 1.0 - init_v), allow_nan=False),
                label=f"bump_{d}",
            )
            current_values[d] = init_v + bump
        else:
            # Improvement less than 0.2
            max_bump = min(0.19, 1.0 - init_v)
            if max_bump <= 0.0:
                current_values[d] = init_v
            else:
                bump = data.draw(
                    st.floats(min_value=0.0, max_value=max_bump, allow_nan=False),
                    label=f"bump_{d}",
                )
                current_values[d] = init_v + bump

    # Use unique child ID per example to avoid DB state leaking across runs
    child_id = f"g_{next(_counter)}"

    initial_profile = _make_profile(child_id, trait_values=initial_values)
    current_profile = _make_profile(child_id, trait_values=current_values)

    # Store the initial profile in the DB
    await sibling_db.save_initial_profile(child_id, initial_profile.model_dump_json())

    discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
    result = await discoverer.check_growth(child_id, current_profile)

    expected_growth = {d for d in dims if grows[d]}

    for d in expected_growth:
        assert d in result, (
            f"Expected dimension '{d}' in growth result "
            f"(init={initial_values[d]:.3f}, current={current_values[d]:.3f}, "
            f"diff={current_values[d] - initial_values[d]:.3f})"
        )

    for d in result:
        # Every returned dimension should have actual improvement >= 0.2
        diff = current_values[d] - initial_values[d]
        assert diff >= 0.2 - 1e-9, (
            f"Dimension '{d}' returned but improvement only {diff:.3f}"
        )


# ===========================================================================
# Unit tests for ComplementarySkillsDiscoverer
# Validates: Requirements 4.1, 4.2, 4.4, 8.4
# ===========================================================================


class TestEvaluateConfidenceThreshold:
    """evaluate() returns None when profiles lack sufficient confidence (Req 4.1)."""

    @pytest.mark.asyncio
    async def test_returns_none_when_profile_a_lacks_confidence(self, sibling_db: SiblingDB):
        """evaluate() returns None when profile A has < 3 high-confidence traits."""
        uid = next(_counter)
        # A: only 2 traits with confidence > 0.5
        profile_a = _make_profile(
            f"a_conf_{uid}",
            trait_confidences={"curiosity": 0.8, "boldness": 0.7, "empathy": 0.3,
                               "creativity": 0.2, "patience": 0.1, "humor": 0.0},
        )
        # B: all 6 traits high confidence
        profile_b = _make_profile(
            f"b_conf_{uid}",
            trait_confidences={d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                                  "creativity", "patience", "humor"]},
        )
        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.evaluate((profile_a, profile_b), interaction_count=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_profile_b_lacks_confidence(self, sibling_db: SiblingDB):
        """evaluate() returns None when profile B has < 3 high-confidence traits."""
        uid = next(_counter)
        profile_a = _make_profile(
            f"a_conf2_{uid}",
            trait_confidences={d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                                  "creativity", "patience", "humor"]},
        )
        profile_b = _make_profile(
            f"b_conf2_{uid}",
            trait_confidences={"curiosity": 0.6, "boldness": 0.1, "empathy": 0.1,
                               "creativity": 0.1, "patience": 0.1, "humor": 0.1},
        )
        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.evaluate((profile_a, profile_b), interaction_count=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_skill_map_when_both_have_confidence(self, sibling_db: SiblingDB):
        """evaluate() returns a SkillMap when both profiles have >= 3 high-confidence traits."""
        uid = next(_counter)
        high_conf = {d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                       "creativity", "patience", "humor"]}
        profile_a = _make_profile(f"a_ok_{uid}", trait_confidences=high_conf)
        profile_b = _make_profile(f"b_ok_{uid}", trait_confidences=high_conf)

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.evaluate((profile_a, profile_b), interaction_count=100)
        assert result is not None
        assert isinstance(result, SkillMap)


class TestFindComplementaryPairs:
    """_find_complementary_pairs() with known trait values (Req 4.2)."""

    def test_finds_pair_when_a_strong_b_weak(self):
        """A has curiosity=0.9, B has curiosity=0.2 → should find a pair."""
        profile_a = _make_profile("strong_a", trait_values={"curiosity": 0.9})
        profile_b = _make_profile("weak_b", trait_values={"curiosity": 0.2})

        discoverer = ComplementarySkillsDiscoverer(db=None)  # type: ignore[arg-type]
        pairs = discoverer._find_complementary_pairs(profile_a, profile_b)

        matching = [p for p in pairs if p.trait_dimension == "curiosity"]
        assert len(matching) == 1
        assert matching[0].strength_holder_id == "strong_a"
        assert matching[0].growth_area_holder_id == "weak_b"
        assert matching[0].strength_score == 0.9
        assert matching[0].growth_score == 0.2

    def test_finds_pair_when_b_strong_a_weak(self):
        """B has empathy=0.85, A has empathy=0.1 → pair with B as strength holder."""
        profile_a = _make_profile("weak_a2", trait_values={"empathy": 0.1})
        profile_b = _make_profile("strong_b2", trait_values={"empathy": 0.85})

        discoverer = ComplementarySkillsDiscoverer(db=None)  # type: ignore[arg-type]
        pairs = discoverer._find_complementary_pairs(profile_a, profile_b)

        matching = [p for p in pairs if p.trait_dimension == "empathy"]
        assert len(matching) == 1
        assert matching[0].strength_holder_id == "strong_b2"
        assert matching[0].growth_area_holder_id == "weak_a2"

    def test_no_pairs_when_traits_similar(self):
        """All traits at 0.5 for both → no complementary pairs."""
        vals = {d: 0.5 for d in ["curiosity", "boldness", "empathy",
                                  "creativity", "patience", "humor"]}
        profile_a = _make_profile("sim_a", trait_values=vals)
        profile_b = _make_profile("sim_b", trait_values=vals)

        discoverer = ComplementarySkillsDiscoverer(db=None)  # type: ignore[arg-type]
        pairs = discoverer._find_complementary_pairs(profile_a, profile_b)
        assert pairs == []

    def test_bidirectional_pairs(self):
        """A strong in curiosity, B strong in boldness → two pairs found."""
        profile_a = _make_profile(
            "bi_a",
            trait_values={"curiosity": 0.9, "boldness": 0.2},
        )
        profile_b = _make_profile(
            "bi_b",
            trait_values={"curiosity": 0.2, "boldness": 0.9},
        )

        discoverer = ComplementarySkillsDiscoverer(db=None)  # type: ignore[arg-type]
        pairs = discoverer._find_complementary_pairs(profile_a, profile_b)

        dims = {p.trait_dimension for p in pairs}
        assert "curiosity" in dims
        assert "boldness" in dims


class TestReevaluationInterval:
    """Re-evaluation skipped when interaction count delta < 10 (Req 4.4)."""

    @pytest.mark.asyncio
    async def test_skips_reevaluation_when_delta_less_than_10(self, sibling_db: SiblingDB):
        """Second evaluate() with delta < 10 returns existing skill map unchanged."""
        uid = next(_counter)
        high_conf = {d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                       "creativity", "patience", "humor"]}
        profile_a = _make_profile(f"a_skip_{uid}", trait_confidences=high_conf)
        profile_b = _make_profile(f"b_skip_{uid}", trait_confidences=high_conf)

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)

        # Initial evaluation at count 50
        first = await discoverer.evaluate((profile_a, profile_b), interaction_count=50)
        assert first is not None
        assert first.interaction_count_at_evaluation == 50

        # Second call at count 55 (delta=5 < 10) → should return existing
        second = await discoverer.evaluate((profile_a, profile_b), interaction_count=55)
        assert second is not None
        assert second.interaction_count_at_evaluation == 50  # unchanged

    @pytest.mark.asyncio
    async def test_reevaluates_when_delta_equals_10(self, sibling_db: SiblingDB):
        """evaluate() re-evaluates when interaction count delta == 10."""
        uid = next(_counter)
        high_conf = {d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                       "creativity", "patience", "humor"]}
        profile_a = _make_profile(f"a_re10_{uid}", trait_confidences=high_conf)
        profile_b = _make_profile(f"b_re10_{uid}", trait_confidences=high_conf)

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)

        first = await discoverer.evaluate((profile_a, profile_b), interaction_count=20)
        assert first is not None

        # Delta exactly 10 → should re-evaluate
        second = await discoverer.evaluate((profile_a, profile_b), interaction_count=30)
        assert second is not None
        assert second.interaction_count_at_evaluation == 30

    @pytest.mark.asyncio
    async def test_reevaluates_when_delta_exceeds_10(self, sibling_db: SiblingDB):
        """evaluate() re-evaluates when interaction count delta > 10."""
        uid = next(_counter)
        high_conf = {d: 0.9 for d in ["curiosity", "boldness", "empathy",
                                       "creativity", "patience", "humor"]}
        profile_a = _make_profile(f"a_re15_{uid}", trait_confidences=high_conf)
        profile_b = _make_profile(f"b_re15_{uid}", trait_confidences=high_conf)

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)

        first = await discoverer.evaluate((profile_a, profile_b), interaction_count=10)
        assert first is not None

        second = await discoverer.evaluate((profile_a, profile_b), interaction_count=25)
        assert second is not None
        assert second.interaction_count_at_evaluation == 25


class TestCheckGrowth:
    """check_growth() detects improvement >= 0.2 (Req 8.4)."""

    @pytest.mark.asyncio
    async def test_detects_growth_above_threshold(self, sibling_db: SiblingDB):
        """check_growth returns trait names where improvement >= 0.2."""
        uid = next(_counter)
        child_id = f"grow_{uid}"

        initial = _make_profile(child_id, trait_values={"curiosity": 0.3, "boldness": 0.4})
        current = _make_profile(child_id, trait_values={"curiosity": 0.6, "boldness": 0.4})

        await sibling_db.save_initial_profile(child_id, initial.model_dump_json())

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.check_growth(child_id, current)

        assert "curiosity" in result  # improved by 0.3
        assert "boldness" not in result  # no change

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_sufficient_growth(self, sibling_db: SiblingDB):
        """check_growth returns empty list when no trait improved by >= 0.2."""
        uid = next(_counter)
        child_id = f"nogrow_{uid}"

        initial = _make_profile(child_id, trait_values={"curiosity": 0.5, "empathy": 0.6})
        current = _make_profile(child_id, trait_values={"curiosity": 0.6, "empathy": 0.7})

        await sibling_db.save_initial_profile(child_id, initial.model_dump_json())

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.check_growth(child_id, current)

        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_initial_profile(self, sibling_db: SiblingDB):
        """check_growth returns empty list when no initial profile exists."""
        uid = next(_counter)
        child_id = f"noinit_{uid}"

        current = _make_profile(child_id, trait_values={"curiosity": 0.9})

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.check_growth(child_id, current)

        assert result == []

    @pytest.mark.asyncio
    async def test_detects_multiple_growth_traits(self, sibling_db: SiblingDB):
        """check_growth returns multiple traits when several improved >= 0.2."""
        uid = next(_counter)
        child_id = f"multigrow_{uid}"

        initial = _make_profile(
            child_id,
            trait_values={"curiosity": 0.2, "boldness": 0.3, "empathy": 0.1},
        )
        current = _make_profile(
            child_id,
            trait_values={"curiosity": 0.5, "boldness": 0.6, "empathy": 0.1},
        )

        await sibling_db.save_initial_profile(child_id, initial.model_dump_json())

        discoverer = ComplementarySkillsDiscoverer(db=sibling_db)
        result = await discoverer.check_growth(child_id, current)

        assert "curiosity" in result   # +0.3
        assert "boldness" in result    # +0.3
        assert "empathy" not in result # no change
