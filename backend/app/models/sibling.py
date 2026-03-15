"""Pydantic data models for the Sibling Dynamics Engine.

Defines structured models for personality profiles, relationship dynamics,
complementary skill maps, and extended story moments used across all four
layers of the engine.
"""

from pydantic import BaseModel, Field


class TraitScore(BaseModel):
    """A single personality trait measurement with confidence tracking.

    Attributes:
        value: The trait score, 0.0 to 1.0 (0.5 = neutral default).
        confidence: How reliable the score is based on observation volume.
        observation_count: Number of observations that informed this score.
    """

    value: float = Field(ge=0.0, le=1.0, default=0.5)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    observation_count: int = Field(ge=0, default=0)


class PersonalityProfile(BaseModel):
    """A child's observed personality model built from interaction data.

    Contains six trait dimensions (Req 2.1), preferred themes (Req 2.2),
    fears/sensitivities (Req 2.3), and confidence tracking (Req 2.4).
    Profiles start as "emerging" until 5+ interactions are recorded (Req 2.5).
    """

    child_id: str

    # Trait dimensions (Req 2.1)
    curiosity: TraitScore = Field(default_factory=TraitScore)
    boldness: TraitScore = Field(default_factory=TraitScore)
    empathy: TraitScore = Field(default_factory=TraitScore)
    creativity: TraitScore = Field(default_factory=TraitScore)
    patience: TraitScore = Field(default_factory=TraitScore)
    humor: TraitScore = Field(default_factory=TraitScore)

    # Preferences (Req 2.2, 2.3)
    preferred_themes: list[str] = Field(default_factory=list)
    fears: list[str] = Field(default_factory=list)

    # Meta
    status: str = Field(default="emerging")  # "emerging" | "established"
    total_interactions: int = Field(ge=0, default=0)
    first_observed: str = Field(default="")  # ISO 8601
    last_updated: str = Field(default="")  # ISO 8601
    created_at: str = Field(default="")  # ISO 8601

    def is_emerging(self) -> bool:
        """Check if the profile lacks sufficient observations (Req 2.5).

        Returns True when fewer than 5 interactions have been recorded,
        indicating the engine should use conservative defaults.
        """
        return self.total_interactions < 5

    def trait_dict(self) -> dict[str, TraitScore]:
        """Return all six trait dimensions as a name-keyed dictionary."""
        return {
            "curiosity": self.curiosity,
            "boldness": self.boldness,
            "empathy": self.empathy,
            "creativity": self.creativity,
            "patience": self.patience,
            "humor": self.humor,
        }

    def high_confidence_count(self) -> int:
        """Count traits with confidence above 0.5 (Req 4.1 threshold)."""
        return sum(1 for t in self.trait_dict().values() if t.confidence > 0.5)


class ConflictEvent(BaseModel):
    """A recorded conflict between siblings during a session (Req 3.5)."""

    timestamp: str
    session_id: str
    description: str = ""


class RelationshipModel(BaseModel):
    """The dynamic between a sibling pair, tracking leadership, cooperation,
    conflict, and emotional synchrony across sessions.
    """

    sibling_pair_id: str
    child1_id: str
    child2_id: str

    # Metrics (Req 3.2, 3.4, 3.6)
    leadership_balance: float = Field(ge=0.0, le=1.0, default=0.5)
    cooperation_score: float = Field(ge=0.0, le=1.0, default=0.5)
    emotional_synchrony: float = Field(ge=0.0, le=1.0, default=0.5)

    # Tracking
    conflict_events: list[ConflictEvent] = Field(default_factory=list)
    total_shared_choices: int = Field(ge=0, default=0)
    consecutive_disagreements: int = Field(ge=0, default=0)

    # Meta
    last_updated: str = Field(default="")
    created_at: str = Field(default="")

    def is_leadership_imbalanced(self) -> bool:
        """Req 3.3: deviation > 0.3 from midpoint (0.5)."""
        return abs(self.leadership_balance - 0.5) > 0.3

    def is_low_cooperation(self) -> bool:
        """Req 7.3: cooperation below 0.3."""
        return self.cooperation_score < 0.3

    def sibling_dynamics_score(self) -> float:
        """Req 9.1: equal-weighted composite of centered leadership,
        cooperation, and emotional synchrony.

        Leadership is centered so that 0.5 (balanced) maps to 1.0 and
        extremes (0.0 or 1.0) map to 0.0.
        """
        centered_leadership = 1.0 - abs(self.leadership_balance - 0.5) * 2
        return (
            centered_leadership + self.cooperation_score + self.emotional_synchrony
        ) / 3.0


class ComplementaryPair(BaseModel):
    """A discovered pairing where one child's strength offsets the other's
    growth area on a specific trait dimension (Req 4.2, 4.5).
    """

    strength_holder_id: str
    growth_area_holder_id: str
    trait_dimension: str
    strength_score: float = Field(ge=0.0, le=1.0)
    growth_score: float = Field(ge=0.0, le=1.0)
    suggested_scenario: str = ""


class SkillMap(BaseModel):
    """Maps complementary strengths and growth areas for a sibling pair (Req 4.5)."""

    sibling_pair_id: str
    complementary_pairs: list[ComplementaryPair] = Field(default_factory=list)
    last_evaluated_at: str = Field(default="")
    interaction_count_at_evaluation: int = Field(ge=0, default=0)

    def has_pairs(self) -> bool:
        """Check whether any complementary pairs have been identified."""
        return len(self.complementary_pairs) > 0


class StoryMoment(BaseModel):
    """A single narrative segment delivered to the children, extended with
    sibling dynamics fields for dual-child storytelling.
    """

    text: str
    timestamp: str
    characters: dict
    interactive: dict

    # Sibling dynamics extensions
    protagonist_child_id: str | None = None
    child_roles: dict[str, str] = Field(default_factory=dict)  # child_id -> role
    addresses_both: bool = False
    narrative_directives_used: list[str] = Field(default_factory=list)
