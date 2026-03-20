"""Property-based tests for Sibling Dynamics Engine data models.

Uses Hypothesis to verify serialization round-trips, field bounds,
helper method correctness, and structural completeness across all
valid model instances.
"""

from hypothesis import given, settings

from app.models.sibling import (
    ComplementaryPair,
    PersonalityProfile,
    RelationshipModel,
    SkillMap,
    TraitScore,
)

# Import strategies from conftest (auto-discovered by pytest)
from tests.conftest import (
    st_complementary_pair,
    st_personality_profile,
    st_relationship_model,
    st_skill_map,
    st_trait_score,
)


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 1: PersonalityProfile serialization round-trip
# Validates: Requirements 10.1, 10.3, 10.5, 1.4
# ---------------------------------------------------------------------------


@given(profile=st_personality_profile())
@settings(max_examples=20)
def test_personality_profile_serialization_round_trip(profile: PersonalityProfile):
    """For any valid PersonalityProfile, serialize to JSON and deserialize
    back → equivalent object."""
    json_str = profile.model_dump_json()
    restored = PersonalityProfile.model_validate_json(json_str)
    assert restored == profile


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 2: RelationshipModel serialization round-trip
# Validates: Requirements 10.2, 10.4, 10.6
# ---------------------------------------------------------------------------


@given(model=st_relationship_model())
@settings(max_examples=20)
def test_relationship_model_serialization_round_trip(model: RelationshipModel):
    """For any valid RelationshipModel, serialize to JSON and deserialize
    back → equivalent object."""
    json_str = model.model_dump_json()
    restored = RelationshipModel.model_validate_json(json_str)
    assert restored == model


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 3: Model bounds invariant
# Validates: Requirements 2.4, 3.2, 3.4
# ---------------------------------------------------------------------------


@given(profile=st_personality_profile(), model=st_relationship_model(), ts=st_trait_score())
@settings(max_examples=20)
def test_model_bounds_invariant(
    profile: PersonalityProfile, model: RelationshipModel, ts: TraitScore
):
    """For any valid PersonalityProfile, all trait value and confidence fields
    in [0.0, 1.0]. For any valid RelationshipModel, leadership_balance,
    cooperation_score, emotional_synchrony in [0.0, 1.0]. For any valid
    TraitScore, observation_count >= 0."""
    # PersonalityProfile trait bounds
    for name, trait in profile.trait_dict().items():
        assert 0.0 <= trait.value <= 1.0, f"{name}.value out of bounds"
        assert 0.0 <= trait.confidence <= 1.0, f"{name}.confidence out of bounds"
        assert trait.observation_count >= 0, f"{name}.observation_count negative"

    # RelationshipModel metric bounds
    assert 0.0 <= model.leadership_balance <= 1.0
    assert 0.0 <= model.cooperation_score <= 1.0
    assert 0.0 <= model.emotional_synchrony <= 1.0

    # Standalone TraitScore bounds
    assert 0.0 <= ts.value <= 1.0
    assert 0.0 <= ts.confidence <= 1.0
    assert ts.observation_count >= 0


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 4: Emerging profile threshold
# Validates: Requirements 2.5
# ---------------------------------------------------------------------------


@given(profile=st_personality_profile())
@settings(max_examples=20)
def test_emerging_profile_threshold(profile: PersonalityProfile):
    """For any PersonalityProfile with total_interactions < 5, is_emerging()
    returns True. For any with total_interactions >= 5, is_emerging() returns
    False."""
    if profile.total_interactions < 5:
        assert profile.is_emerging() is True
    else:
        assert profile.is_emerging() is False


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 22: Sibling dynamics score formula
# Validates: Requirements 9.1
# ---------------------------------------------------------------------------


@given(model=st_relationship_model())
@settings(max_examples=20)
def test_sibling_dynamics_score_formula(model: RelationshipModel):
    """For any valid RelationshipModel, sibling_dynamics_score() equals
    ((1.0 - abs(leadership_balance - 0.5) * 2) + cooperation_score +
    emotional_synchrony) / 3.0 and the result is in [0.0, 1.0]."""
    expected = (
        (1.0 - abs(model.leadership_balance - 0.5) * 2)
        + model.cooperation_score
        + model.emotional_synchrony
    ) / 3.0
    actual = model.sibling_dynamics_score()

    assert abs(actual - expected) < 1e-9, f"Score mismatch: {actual} != {expected}"
    assert 0.0 <= actual <= 1.0, f"Score out of bounds: {actual}"


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 9: Leadership imbalance detection
# Validates: Requirements 3.3
# ---------------------------------------------------------------------------


@given(model=st_relationship_model())
@settings(max_examples=20)
def test_leadership_imbalance_detection(model: RelationshipModel):
    """For any leadership_balance in [0.0, 1.0], is_leadership_imbalanced()
    returns True iff abs(leadership_balance - 0.5) > 0.3."""
    expected = abs(model.leadership_balance - 0.5) > 0.3
    assert model.is_leadership_imbalanced() == expected


# ---------------------------------------------------------------------------
# Feature: sibling-dynamics-engine, Property 15: Complementary pair structure completeness
# Validates: Requirements 4.5
# ---------------------------------------------------------------------------


@given(skill_map=st_skill_map())
@settings(max_examples=20)
def test_complementary_pair_structure_completeness(skill_map: SkillMap):
    """For any ComplementaryPair in a SkillMap, strength_holder_id,
    growth_area_holder_id, trait_dimension, and suggested_scenario must all
    be non-empty strings."""
    for pair in skill_map.complementary_pairs:
        assert isinstance(pair.strength_holder_id, str) and len(pair.strength_holder_id) > 0, \
            "strength_holder_id must be a non-empty string"
        assert isinstance(pair.growth_area_holder_id, str) and len(pair.growth_area_holder_id) > 0, \
            "growth_area_holder_id must be a non-empty string"
        assert isinstance(pair.trait_dimension, str) and len(pair.trait_dimension) > 0, \
            "trait_dimension must be a non-empty string"
        assert isinstance(pair.suggested_scenario, str) and len(pair.suggested_scenario) > 0, \
            "suggested_scenario must be a non-empty string"
