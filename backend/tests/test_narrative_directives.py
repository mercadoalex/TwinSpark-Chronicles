"""Property-based tests for narrative directive generation (Layer 4).

Tests Properties 16–19 from the Sibling Dynamics Engine design document,
covering directive conditions, protagonist alternation, dual-child roles,
and neglected child featuring.
"""

from __future__ import annotations

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.models.sibling import (
    ComplementaryPair,
    ConflictEvent,
    PersonalityProfile,
    RelationshipModel,
    SkillMap,
    TraitScore,
)
from app.services.narrative_directives import (
    build_narrative_directives,
    _pick_protagonist,
    _find_neglected_child,
)


# ---------------------------------------------------------------------------
# Shared helpers / strategies
# ---------------------------------------------------------------------------

_child_id = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=12
)
_unit_float = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_iso_ts = st.just("2024-01-01T00:00:00+00:00")
_fear = st.sampled_from(
    ["darkness", "loud-noises", "separation", "monsters", "water", "heights"]
)
_trait_name = st.sampled_from(
    ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]
)
_scenario = st.sampled_from(
    ["teaching moment", "collaborative puzzle", "rescue mission",
     "creative challenge", "exploration quest"]
)


def _make_trait(value: float = 0.5, confidence: float = 0.0) -> TraitScore:
    return TraitScore(value=value, confidence=confidence, observation_count=1)


def _make_profile(child_id: str, fears: list[str] | None = None) -> PersonalityProfile:
    return PersonalityProfile(
        child_id=child_id,
        fears=fears or [],
        total_interactions=10,
        status="established",
        first_observed="2024-01-01T00:00:00+00:00",
        last_updated="2024-01-01T00:00:00+00:00",
        created_at="2024-01-01T00:00:00+00:00",
    )


def _make_relationship(
    child1_id: str,
    child2_id: str,
    leadership_balance: float = 0.5,
    cooperation_score: float = 0.5,
    conflict_events: list[ConflictEvent] | None = None,
) -> RelationshipModel:
    return RelationshipModel(
        sibling_pair_id=f"{child1_id}_{child2_id}",
        child1_id=child1_id,
        child2_id=child2_id,
        leadership_balance=leadership_balance,
        cooperation_score=cooperation_score,
        emotional_synchrony=0.5,
        conflict_events=conflict_events or [],
        last_updated="2024-01-01T00:00:00+00:00",
        created_at="2024-01-01T00:00:00+00:00",
    )


def _make_skill_map(
    pair_id: str, pairs: list[ComplementaryPair] | None = None
) -> SkillMap:
    return SkillMap(
        sibling_pair_id=pair_id,
        complementary_pairs=pairs or [],
        last_evaluated_at="2024-01-01T00:00:00+00:00",
        interaction_count_at_evaluation=0,
    )


# ===================================================================
# Property 16: Narrative directives reflect active conditions
# Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
# Validates: Requirements 5.2, 5.3, 5.4, 7.1, 7.2, 7.3
# ===================================================================



class TestProperty16NarrativeDirectivesReflectConditions:
    """Property 16: Narrative directives reflect active conditions."""

    # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions

    @given(
        leadership_balance=st.floats(min_value=0.81, max_value=1.0, allow_nan=False)
        | st.floats(min_value=0.0, max_value=0.19, allow_nan=False),
    )
    @settings(max_examples=20)
    def test_leadership_imbalance_produces_let_less_active_lead(
        self, leadership_balance: float
    ):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 5.2"""
        c1, c2 = "alice", "bob"
        rel = _make_relationship(c1, c2, leadership_balance=leadership_balance)
        assert rel.is_leadership_imbalanced()

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("let less-active child lead" in d for d in directives_lower)

    @given(
        cooperation_score=st.floats(min_value=0.0, max_value=0.29, allow_nan=False),
    )
    @settings(max_examples=20)
    def test_low_cooperation_produces_cooperative_challenge(
        self, cooperation_score: float
    ):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 5.3, 7.3"""
        c1, c2 = "alice", "bob"
        rel = _make_relationship(c1, c2, cooperation_score=cooperation_score)
        assert rel.is_low_cooperation()

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("cooperative challenge" in d for d in directives_lower)

    @given(
        num_conflicts=st.integers(min_value=1, max_value=5),
    )
    @settings(max_examples=20)
    def test_conflict_events_produce_cooperative_challenge(
        self, num_conflicts: int
    ):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 5.3"""
        c1, c2 = "alice", "bob"
        conflicts = [
            ConflictEvent(
                timestamp="2024-01-01T00:00:00+00:00",
                session_id="s1",
                description="disagreement",
            )
            for _ in range(num_conflicts)
        ]
        rel = _make_relationship(c1, c2, cooperation_score=0.8, conflict_events=conflicts)

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("cooperative challenge" in d for d in directives_lower)

    @given(
        trait=_trait_name,
        scenario=_scenario,
    )
    @settings(max_examples=20)
    def test_complementary_pairs_produce_teaching_scenario(
        self, trait: str, scenario: str
    ):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 5.4"""
        c1, c2 = "alice", "bob"
        pair = ComplementaryPair(
            strength_holder_id=c1,
            growth_area_holder_id=c2,
            trait_dimension=trait,
            strength_score=0.9,
            growth_score=0.2,
            suggested_scenario=scenario,
        )
        sm = _make_skill_map(f"{c1}_{c2}", pairs=[pair])

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=sm,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("teaching scenario" in d for d in directives_lower)

    @given(
        fears_a=st.lists(_fear, min_size=1, max_size=3),
        fears_b=st.lists(_fear, min_size=0, max_size=3),
    )
    @settings(max_examples=20)
    def test_fears_produce_avoidance_directives(
        self, fears_a: list[str], fears_b: list[str]
    ):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 7.1"""
        c1, c2 = "alice", "bob"
        pa = _make_profile(c1, fears=fears_a)
        pb = _make_profile(c2, fears=fears_b)

        result = build_narrative_directives(
            profiles=(pa, pb),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        all_fears = fears_a + fears_b
        for fear in all_fears:
            assert any(fear.lower() in d for d in directives_lower), (
                f"Expected avoidance directive for fear '{fear}'"
            )

    @given(
        emotion=st.sampled_from(["sad", "scared"]),
    )
    @settings(max_examples=20)
    def test_sad_or_scared_produces_soften_tone(self, emotion: str):
        # Feature: sibling-dynamics-engine, Property 16: Narrative directives reflect active conditions
        """Validates: Requirements 7.2"""
        c1, c2 = "alice", "bob"
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            current_emotions={c1: emotion},
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("soften tone" in d for d in directives_lower)


# ===================================================================
# Property 17: Protagonist alternation
# Feature: sibling-dynamics-engine, Property 17: Protagonist alternation
# Validates: Requirements 5.5
# ===================================================================


class TestProperty17ProtagonistAlternation:
    """Property 17: Protagonist alternation."""

    # Feature: sibling-dynamics-engine, Property 17: Protagonist alternation

    @given(
        c1=_child_id,
        c2=_child_id,
        num_steps=st.integers(min_value=2, max_value=20),
    )
    @settings(max_examples=20)
    def test_protagonist_alternates_across_consecutive_moments(
        self, c1: str, c2: str, num_steps: int
    ):
        # Feature: sibling-dynamics-engine, Property 17: Protagonist alternation
        """Validates: Requirements 5.5"""
        assume(c1 != c2)

        protagonists: list[str] = []
        for _ in range(num_steps):
            chosen = _pick_protagonist(c1, c2, protagonists)
            protagonists.append(chosen)

        # Verify alternation: consecutive entries should differ
        for i in range(1, len(protagonists)):
            assert protagonists[i] != protagonists[i - 1], (
                f"Protagonist did not alternate at step {i}: {protagonists}"
            )

    @given(c1=_child_id, c2=_child_id)
    @settings(max_examples=20)
    def test_first_protagonist_is_child1_when_no_history(self, c1: str, c2: str):
        # Feature: sibling-dynamics-engine, Property 17: Protagonist alternation
        """Validates: Requirements 5.5"""
        assume(c1 != c2)
        result = _pick_protagonist(c1, c2, [])
        assert result == c1


# ===================================================================
# Property 18: Dual-child prompt addressing with distinct roles
# Feature: sibling-dynamics-engine, Property 18: Dual-child prompt addressing with distinct roles
# Validates: Requirements 6.1, 6.2
# ===================================================================


class TestProperty18DualChildRoles:
    """Property 18: Dual-child prompt addressing with distinct roles."""

    # Feature: sibling-dynamics-engine, Property 18: Dual-child prompt addressing with distinct roles

    @given(
        c1=_child_id,
        c2=_child_id,
    )
    @settings(max_examples=20)
    def test_child_roles_has_both_ids_with_different_values(
        self, c1: str, c2: str
    ):
        # Feature: sibling-dynamics-engine, Property 18: Dual-child prompt addressing with distinct roles
        """Validates: Requirements 6.1, 6.2"""
        assume(c1 != c2)

        pa = _make_profile(c1)
        pb = _make_profile(c2)
        rel = _make_relationship(c1, c2)

        result = build_narrative_directives(
            profiles=(pa, pb),
            relationship=rel,
            skill_map=None,
        )
        child_roles = result["child_roles"]

        # Both children must be present as keys
        assert c1 in child_roles, f"child_roles missing {c1}"
        assert c2 in child_roles, f"child_roles missing {c2}"

        # Roles must be distinct strings
        assert child_roles[c1] != child_roles[c2], (
            f"Both children got the same role: {child_roles[c1]}"
        )

    @given(
        c1=_child_id,
        c2=_child_id,
        trait=_trait_name,
        scenario=_scenario,
    )
    @settings(max_examples=20)
    def test_child_roles_distinct_with_skill_map(
        self, c1: str, c2: str, trait: str, scenario: str
    ):
        # Feature: sibling-dynamics-engine, Property 18: Dual-child prompt addressing with distinct roles
        """Validates: Requirements 6.1, 6.2"""
        assume(c1 != c2)

        pair = ComplementaryPair(
            strength_holder_id=c1,
            growth_area_holder_id=c2,
            trait_dimension=trait,
            strength_score=0.9,
            growth_score=0.2,
            suggested_scenario=scenario,
        )
        sm = _make_skill_map(f"{c1}_{c2}", pairs=[pair])

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=sm,
        )
        child_roles = result["child_roles"]

        assert c1 in child_roles
        assert c2 in child_roles
        assert child_roles[c1] != child_roles[c2]


# ===================================================================
# Property 19: Neglected child featuring
# Feature: sibling-dynamics-engine, Property 19: Neglected child featuring
# Validates: Requirements 7.5
# ===================================================================


class TestProperty19NeglectedChildFeaturing:
    """Property 19: Neglected child featuring."""

    # Feature: sibling-dynamics-engine, Property 19: Neglected child featuring

    @given(
        c1=_child_id,
        c2=_child_id,
        extra_count=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=20)
    def test_neglected_child_detected_after_3_absences(
        self, c1: str, c2: str, extra_count: int
    ):
        # Feature: sibling-dynamics-engine, Property 19: Neglected child featuring
        """Validates: Requirements 7.5"""
        assume(c1 != c2)

        # c2 has been protagonist for 3+ consecutive moments → c1 is neglected
        previous = [c2] * (3 + extra_count)
        neglected = _find_neglected_child(c1, c2, previous)
        assert neglected == c1

    @given(
        c1=_child_id,
        c2=_child_id,
        extra_count=st.integers(min_value=0, max_value=5),
    )
    @settings(max_examples=20)
    def test_neglected_child_directive_and_protagonist_override(
        self, c1: str, c2: str, extra_count: int
    ):
        # Feature: sibling-dynamics-engine, Property 19: Neglected child featuring
        """Validates: Requirements 7.5"""
        assume(c1 != c2)

        # c2 has been protagonist for 3+ consecutive moments → c1 is neglected
        previous = [c2] * (3 + extra_count)

        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            previous_protagonists=previous,
        )

        # Should include a "feature neglected child" directive mentioning c1
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("feature neglected child" in d for d in directives_lower), (
            f"Expected neglected child directive, got: {result['directives']}"
        )
        assert any(c1.lower() in d for d in directives_lower), (
            f"Expected neglected child {c1} mentioned in directives"
        )

        # Protagonist should be overridden to the neglected child
        assert result["protagonist_child_id"] == c1

    @given(c1=_child_id, c2=_child_id)
    @settings(max_examples=20)
    def test_no_neglected_child_when_both_present(self, c1: str, c2: str):
        # Feature: sibling-dynamics-engine, Property 19: Neglected child featuring
        """Validates: Requirements 7.5"""
        assume(c1 != c2)

        # Both children appear in last 3 → no neglected child
        previous = [c1, c2, c1]
        neglected = _find_neglected_child(c1, c2, previous)
        assert neglected is None

    @given(c1=_child_id, c2=_child_id)
    @settings(max_examples=20)
    def test_no_neglected_child_when_history_too_short(self, c1: str, c2: str):
        # Feature: sibling-dynamics-engine, Property 19: Neglected child featuring
        """Validates: Requirements 7.5"""
        assume(c1 != c2)

        # Fewer than 3 entries → no neglected child
        for length in range(3):
            previous = [c2] * length
            neglected = _find_neglected_child(c1, c2, previous)
            assert neglected is None


# ===================================================================
# Unit tests for narrative directives (Task 8.7)
# Requirements: 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.5
# ===================================================================


class TestDirectiveGenerationConditions:
    """Unit tests for directive generation under specific conditions."""

    def test_leadership_imbalance_high_balance_directs_child2(self):
        """Req 5.2: balance > 0.8 → directive naming child2 as less-active."""
        c1, c2 = "ale", "sofi"
        rel = _make_relationship(c1, c2, leadership_balance=0.9)
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("let less-active child lead" in d for d in directives_lower)
        assert any(c2 in d for d in directives_lower)

    def test_leadership_imbalance_low_balance_directs_child1(self):
        """Req 5.2: balance < 0.2 → directive naming child1 as less-active."""
        c1, c2 = "ale", "sofi"
        rel = _make_relationship(c1, c2, leadership_balance=0.1)
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("let less-active child lead" in d for d in directives_lower)
        assert any(c1 in d for d in directives_lower)

    def test_conflict_events_trigger_cooperative_challenge(self):
        """Req 5.3: conflict events present → cooperative challenge directive."""
        c1, c2 = "ale", "sofi"
        conflicts = [
            ConflictEvent(
                timestamp="2024-01-01T00:00:00+00:00",
                session_id="s1",
                description="disagreement",
            )
        ]
        rel = _make_relationship(c1, c2, cooperation_score=0.8, conflict_events=conflicts)
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("cooperative challenge" in d for d in directives_lower)

    def test_low_cooperation_triggers_cooperative_challenge(self):
        """Req 5.3, 7.3: cooperation < 0.3 → cooperative challenge directive."""
        c1, c2 = "ale", "sofi"
        rel = _make_relationship(c1, c2, cooperation_score=0.2)
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=rel,
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("cooperative challenge" in d for d in directives_lower)

    def test_fears_produce_avoid_directives(self):
        """Req 7.1: fears in profiles → avoid fear directives for each fear."""
        c1, c2 = "ale", "sofi"
        pa = _make_profile(c1, fears=["darkness", "monsters"])
        pb = _make_profile(c2, fears=["water"])
        result = build_narrative_directives(
            profiles=(pa, pb),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("darkness" in d and "avoid fear" in d for d in directives_lower)
        assert any("monsters" in d and "avoid fear" in d for d in directives_lower)
        assert any("water" in d and "avoid fear" in d for d in directives_lower)

    def test_sad_emotion_triggers_soften_tone(self):
        """Req 7.2: sad emotion → soften tone directive."""
        c1, c2 = "ale", "sofi"
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            current_emotions={c1: "sad"},
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("soften tone" in d for d in directives_lower)

    def test_scared_emotion_triggers_soften_tone(self):
        """Req 7.2: scared emotion → soften tone directive."""
        c1, c2 = "ale", "sofi"
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            current_emotions={c2: "scared"},
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("soften tone" in d for d in directives_lower)

    def test_happy_emotion_does_not_trigger_soften_tone(self):
        """Req 7.2: happy emotion should NOT trigger soften tone."""
        c1, c2 = "ale", "sofi"
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            current_emotions={c1: "happy", c2: "happy"},
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert not any("soften tone" in d for d in directives_lower)

    def test_complementary_pairs_produce_teaching_scenario(self):
        """Req 5.4: complementary pairs → teaching scenario directive."""
        c1, c2 = "ale", "sofi"
        pair = ComplementaryPair(
            strength_holder_id=c1,
            growth_area_holder_id=c2,
            trait_dimension="boldness",
            strength_score=0.9,
            growth_score=0.2,
            suggested_scenario="rescue mission",
        )
        sm = _make_skill_map(f"{c1}_{c2}", pairs=[pair])
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=sm,
        )
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("teaching scenario" in d for d in directives_lower)


class TestProtagonistAlternation:
    """Unit tests for protagonist alternation logic."""

    def test_child1_first_when_no_history(self):
        """Req 5.5: child1 is protagonist when no previous history."""
        result = _pick_protagonist("ale", "sofi", [])
        assert result == "ale"

    def test_alternates_after_child1(self):
        """Req 5.5: after child1, protagonist should be child2."""
        result = _pick_protagonist("ale", "sofi", ["ale"])
        assert result == "sofi"

    def test_alternates_after_child2(self):
        """Req 5.5: after child2, protagonist should be child1."""
        result = _pick_protagonist("ale", "sofi", ["sofi"])
        assert result == "ale"

    def test_alternation_over_multiple_steps(self):
        """Req 5.5: protagonist alternates across a sequence of moments."""
        history: list[str] = []
        for i in range(6):
            chosen = _pick_protagonist("ale", "sofi", history)
            history.append(chosen)
        assert history == ["ale", "sofi", "ale", "sofi", "ale", "sofi"]


class TestNeglectedChildDetection:
    """Unit tests for neglected child detection after 3 moments."""

    def test_neglected_child_after_3_consecutive_same_protagonist(self):
        """Req 7.5: child absent from last 3 moments is neglected."""
        result = _find_neglected_child("ale", "sofi", ["sofi", "sofi", "sofi"])
        assert result == "ale"

    def test_neglected_child_overrides_protagonist(self):
        """Req 7.5: neglected child overrides normal protagonist selection."""
        c1, c2 = "ale", "sofi"
        # sofi has been protagonist 3 times → ale is neglected
        # Normal alternation would pick ale anyway, but let's use 4 to make
        # the override clear (normal pick would be sofi after ale)
        previous = ["sofi", "sofi", "sofi", "sofi"]
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
            previous_protagonists=previous,
        )
        assert result["protagonist_child_id"] == "ale"
        directives_lower = [d.lower() for d in result["directives"]]
        assert any("feature neglected child" in d for d in directives_lower)

    def test_no_neglected_child_when_both_appear_in_last_3(self):
        """Req 7.5: no neglected child when both appear in last 3 moments."""
        result = _find_neglected_child("ale", "sofi", ["ale", "sofi", "ale"])
        assert result is None

    def test_no_neglected_child_when_history_less_than_3(self):
        """Req 7.5: no neglected child when history has fewer than 3 entries."""
        assert _find_neglected_child("ale", "sofi", []) is None
        assert _find_neglected_child("ale", "sofi", ["sofi"]) is None
        assert _find_neglected_child("ale", "sofi", ["sofi", "sofi"]) is None


class TestChildRolesDistinct:
    """Unit tests for child role assignment."""

    def test_roles_are_always_distinct(self):
        """Req 6.2: child roles must be distinct for the two children."""
        c1, c2 = "ale", "sofi"
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=None,
        )
        roles = result["child_roles"]
        assert c1 in roles
        assert c2 in roles
        assert roles[c1] != roles[c2]

    def test_roles_distinct_with_skill_map(self):
        """Req 6.2: roles remain distinct when skill map enriches them."""
        c1, c2 = "ale", "sofi"
        pair = ComplementaryPair(
            strength_holder_id=c1,
            growth_area_holder_id=c2,
            trait_dimension="empathy",
            strength_score=0.85,
            growth_score=0.25,
            suggested_scenario="nurturing quest",
        )
        sm = _make_skill_map(f"{c1}_{c2}", pairs=[pair])
        result = build_narrative_directives(
            profiles=(_make_profile(c1), _make_profile(c2)),
            relationship=_make_relationship(c1, c2),
            skill_map=sm,
        )
        roles = result["child_roles"]
        assert roles[c1] != roles[c2]
