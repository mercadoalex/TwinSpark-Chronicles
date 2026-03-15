"""ComplementarySkillsDiscoverer — Layer 3 of the Sibling Dynamics Engine.

Identifies where one child's strengths offset the other's growth areas
and surfaces opportunities for mutual learning through story scenarios.
Tracks growth over time by comparing current profiles against initial
snapshots stored in the database.

Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.4
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.sibling import (
    ComplementaryPair,
    PersonalityProfile,
    SkillMap,
)
from app.services.sibling_db import SiblingDB

logger = logging.getLogger(__name__)

# Suggested scenario templates keyed by trait dimension.
# Used to populate ComplementaryPair.suggested_scenario.
_SCENARIO_SUGGESTIONS: dict[str, str] = {
    "curiosity": "exploration quest where the curious child guides discovery",
    "boldness": "brave challenge where the bold child leads the way",
    "empathy": "caring mission where the empathetic child comforts a character",
    "creativity": "invention task where the creative child designs a solution",
    "patience": "careful puzzle where the patient child sets the pace",
    "humor": "comedy scene where the funny child entertains everyone",
}


class ComplementarySkillsDiscoverer:
    """Discovers complementary strengths between siblings and tracks growth.

    Evaluates pairs of personality profiles to find traits where one
    child excels (score > 0.7) and the other has room to grow (score < 0.4).
    Re-evaluation only happens every 10 interactions to avoid churn.
    """

    def __init__(self, db: SiblingDB) -> None:
        self.db = db

    # ── Public API ────────────────────────────────────────────────────

    async def evaluate(
        self,
        profiles: tuple[PersonalityProfile, PersonalityProfile],
        interaction_count: int,
    ) -> SkillMap | None:
        """Re-evaluate the skill map for a sibling pair (Req 4.1, 4.4).

        Returns None if both profiles don't have sufficient confidence
        (high_confidence_count >= 3). Only re-evaluates when the
        interaction count has advanced by at least 10 since the last
        evaluation.
        """
        profile_a, profile_b = profiles

        # Req 4.1: both profiles need >= 3 high-confidence traits
        if profile_a.high_confidence_count() < 3 or profile_b.high_confidence_count() < 3:
            return None

        # Build a stable pair ID from sorted child IDs
        pair_id = _pair_id(profile_a.child_id, profile_b.child_id)

        # Load existing skill map to check re-evaluation interval
        existing = await self.load_skill_map(pair_id)

        if existing is not None:
            # Req 4.4: only re-evaluate every 10 interactions
            if interaction_count < existing.interaction_count_at_evaluation + 10:
                return existing

        # Perform evaluation
        pairs = self._find_complementary_pairs(profile_a, profile_b)

        now = datetime.now(timezone.utc).isoformat()
        skill_map = SkillMap(
            sibling_pair_id=pair_id,
            complementary_pairs=pairs,
            last_evaluated_at=now,
            interaction_count_at_evaluation=interaction_count,
        )

        await self.persist_skill_map(pair_id, skill_map)
        return skill_map

    def _find_complementary_pairs(
        self,
        profile_a: PersonalityProfile,
        profile_b: PersonalityProfile,
    ) -> list[ComplementaryPair]:
        """Identify pairs where one child's strength (>0.7) meets the other's
        growth area (<0.4) (Req 4.2, 4.5).

        Checks both directions: A strong + B growing, and B strong + A growing.
        """
        pairs: list[ComplementaryPair] = []
        traits_a = profile_a.trait_dict()
        traits_b = profile_b.trait_dict()

        for dimension in traits_a:
            score_a = traits_a[dimension].value
            score_b = traits_b[dimension].value

            # A is strong, B has growth area
            if score_a > 0.7 and score_b < 0.4:
                pairs.append(
                    ComplementaryPair(
                        strength_holder_id=profile_a.child_id,
                        growth_area_holder_id=profile_b.child_id,
                        trait_dimension=dimension,
                        strength_score=score_a,
                        growth_score=score_b,
                        suggested_scenario=_SCENARIO_SUGGESTIONS.get(
                            dimension, f"scenario highlighting {dimension}"
                        ),
                    )
                )

            # B is strong, A has growth area
            if score_b > 0.7 and score_a < 0.4:
                pairs.append(
                    ComplementaryPair(
                        strength_holder_id=profile_b.child_id,
                        growth_area_holder_id=profile_a.child_id,
                        trait_dimension=dimension,
                        strength_score=score_b,
                        growth_score=score_a,
                        suggested_scenario=_SCENARIO_SUGGESTIONS.get(
                            dimension, f"scenario highlighting {dimension}"
                        ),
                    )
                )

        return pairs

    async def check_growth(
        self, child_id: str, current: PersonalityProfile
    ) -> list[str]:
        """Return trait names where the score improved by >= 0.2 since first
        observation (Req 8.4).

        Compares the current profile against the initial snapshot stored
        in the ``initial_profiles`` table. Returns an empty list if no
        initial profile exists or no trait improved enough.
        """
        initial_json = await self.db.load_initial_profile(child_id)
        if initial_json is None:
            return []

        initial = PersonalityProfile.model_validate_json(initial_json)
        improved: list[str] = []

        current_traits = current.trait_dict()
        initial_traits = initial.trait_dict()

        for dimension in current_traits:
            current_value = current_traits[dimension].value
            initial_value = initial_traits[dimension].value
            if current_value - initial_value >= 0.2:
                improved.append(dimension)

        return improved

    async def load_skill_map(self, sibling_pair_id: str) -> SkillMap | None:
        """Load a skill map from SQLite. Returns None if not found."""
        skill_map_json = await self.db.load_skill_map(sibling_pair_id)
        if skill_map_json is not None:
            return SkillMap.model_validate_json(skill_map_json)
        return None

    async def persist_skill_map(
        self, sibling_pair_id: str, skill_map: SkillMap
    ) -> None:
        """Write a skill map to SQLite."""
        await self.db.save_skill_map(sibling_pair_id, skill_map.model_dump_json())


def _pair_id(child_id_a: str, child_id_b: str) -> str:
    """Build a deterministic sibling pair ID from two child IDs."""
    return ":".join(sorted([child_id_a, child_id_b]))
