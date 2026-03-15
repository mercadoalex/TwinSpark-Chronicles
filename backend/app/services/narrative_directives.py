"""Narrative directive builder — Layer 4 logic for the Sibling Dynamics Engine.

Generates structured narrative directives from personality profiles,
relationship dynamics, skill maps, and session state. These directives
guide the StorytellerAgent to produce adaptive, emotionally safe,
balanced dual-child narratives.

Requirements: 5.2, 5.3, 5.4, 5.5, 6.2, 7.1, 7.2, 7.3, 7.5
"""

from __future__ import annotations

from app.models.sibling import (
    PersonalityProfile,
    RelationshipModel,
    SkillMap,
)

# Emotions that trigger a "soften tone" directive (Req 7.2)
_SOFT_TONE_EMOTIONS = {"sad", "scared"}


def build_narrative_directives(
    profiles: tuple[PersonalityProfile, PersonalityProfile],
    relationship: RelationshipModel,
    skill_map: SkillMap | None,
    current_emotions: dict[str, str] | None = None,
    previous_protagonists: list[str] | None = None,
) -> dict:
    """Build narrative directives from sibling dynamics state.

    Args:
        profiles: Personality profiles for both children.
        relationship: Current relationship model for the pair.
        skill_map: Complementary skill map (may be ``None``).
        current_emotions: Mapping of child_id → emotion name.
        previous_protagonists: Ordered list of recent protagonist child IDs
            (most recent last).

    Returns:
        A dict with keys:
        - ``directives``: list[str] — narrative instructions for the storyteller.
        - ``protagonist_child_id``: str — which child should lead this moment.
        - ``child_roles``: dict[str, str] — role description per child.
    """
    if current_emotions is None:
        current_emotions = {}
    if previous_protagonists is None:
        previous_protagonists = []

    profile_a, profile_b = profiles
    directives: list[str] = []

    # ── Leadership imbalance (Req 5.2) ────────────────────────────
    if relationship.is_leadership_imbalanced():
        # Determine which child is less active (the one NOT dominating)
        if relationship.leadership_balance > 0.5:
            less_active = relationship.child2_id
        else:
            less_active = relationship.child1_id
        directives.append(
            f"let less-active child lead: give {less_active} the next decision"
        )

    # ── Conflict / low cooperation (Req 5.3, 7.3) ────────────────
    has_conflict = len(relationship.conflict_events) > 0
    if has_conflict or relationship.is_low_cooperation():
        directives.append(
            "cooperative challenge: introduce a task requiring both children to contribute"
        )

    # ── Teaching scenario from complementary pairs (Req 5.4) ──────
    if skill_map is not None and skill_map.has_pairs():
        for pair in skill_map.complementary_pairs:
            scenario = pair.suggested_scenario or "a collaborative task"
            directives.append(
                f"teaching scenario: {pair.strength_holder_id} helps "
                f"{pair.growth_area_holder_id} with {pair.trait_dimension} "
                f"via {scenario}"
            )

    # ── Fear avoidance (Req 7.1) ──────────────────────────────────
    for profile in (profile_a, profile_b):
        for fear in profile.fears:
            directives.append(
                f"avoid fear: do not include {fear} "
                f"(sensitivity of {profile.child_id})"
            )

    # ── Soften tone on sad/scared (Req 7.2) ───────────────────────
    for child_id, emotion in current_emotions.items():
        if emotion.lower() in _SOFT_TONE_EMOTIONS:
            directives.append(
                f"soften tone: {child_id} is feeling {emotion}, "
                "introduce comforting elements"
            )

    # ── Protagonist alternation (Req 5.5) ─────────────────────────
    protagonist_child_id = _pick_protagonist(
        profile_a.child_id, profile_b.child_id, previous_protagonists
    )

    # ── Neglected child detection (Req 7.5) ───────────────────────
    neglected = _find_neglected_child(
        profile_a.child_id, profile_b.child_id, previous_protagonists
    )
    if neglected is not None:
        directives.append(
            f"feature neglected child: {neglected} has not been protagonist "
            "in the last 3 moments, feature them prominently"
        )
        # Override protagonist to the neglected child
        protagonist_child_id = neglected

    # ── Child roles (Req 6.2) ─────────────────────────────────────
    child_roles = _assign_roles(
        profile_a.child_id,
        profile_b.child_id,
        protagonist_child_id,
        skill_map,
    )

    return {
        "directives": directives,
        "protagonist_child_id": protagonist_child_id,
        "child_roles": child_roles,
    }


def _pick_protagonist(
    child1_id: str,
    child2_id: str,
    previous_protagonists: list[str],
) -> str:
    """Alternate protagonist between children across consecutive moments.

    If no history exists, child1 goes first. Otherwise, pick whichever
    child was NOT the most recent protagonist.
    """
    if not previous_protagonists:
        return child1_id

    last = previous_protagonists[-1]
    if last == child1_id:
        return child2_id
    elif last == child2_id:
        return child1_id
    else:
        # Unknown last protagonist — default to child1
        return child1_id


def _find_neglected_child(
    child1_id: str,
    child2_id: str,
    previous_protagonists: list[str],
) -> str | None:
    """Return the child_id not featured in the last 3 protagonist slots.

    Returns ``None`` if both children appeared or history is too short.
    """
    if len(previous_protagonists) < 3:
        return None

    last_three = previous_protagonists[-3:]
    child1_present = child1_id in last_three
    child2_present = child2_id in last_three

    if not child1_present:
        return child1_id
    if not child2_present:
        return child2_id
    return None


def _assign_roles(
    child1_id: str,
    child2_id: str,
    protagonist_id: str,
    skill_map: SkillMap | None,
) -> dict[str, str]:
    """Assign distinct narrative roles to each child (Req 6.2).

    The protagonist gets the "leader" role; the other child gets
    "supporter". If a skill map has complementary pairs, roles are
    enriched with skill-based descriptions.
    """
    supporter_id = child2_id if protagonist_id == child1_id else child1_id

    leader_role = "leader and decision-maker"
    supporter_role = "creative supporter and advisor"

    # Enrich roles from skill map when available
    if skill_map is not None and skill_map.has_pairs():
        for pair in skill_map.complementary_pairs:
            if pair.strength_holder_id == protagonist_id:
                leader_role = (
                    f"leader using {pair.trait_dimension} strength"
                )
                break
            elif pair.strength_holder_id == supporter_id:
                supporter_role = (
                    f"supporter contributing {pair.trait_dimension} expertise"
                )
                break

    return {
        protagonist_id: leader_role,
        supporter_id: supporter_role,
    }
