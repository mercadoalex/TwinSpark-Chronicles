"""Shared test fixtures — mock heavy third-party modules so app.main can import."""

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pre-populate sys.modules with mocks for packages that may not be installed
# in the test environment.  This must happen BEFORE any app.* import that
# transitively pulls in these packages.
# ---------------------------------------------------------------------------

_MOCK_MODULES = {
    # Google AI / Cloud
    "google.generativeai": MagicMock(),
    "google.cloud.speech_v1": MagicMock(),
    "google.cloud.texttospeech_v1": MagicMock(),
    "google.cloud.texttospeech": MagicMock(),
    "google.cloud.aiplatform": MagicMock(),
    "google.cloud.storage": MagicMock(),
    # Vertex AI (visual_agent.py: from vertexai.preview.vision_models import ...)
    "vertexai": MagicMock(),
    "vertexai.preview": MagicMock(),
    "vertexai.preview.vision_models": MagicMock(),
    # ChromaDB (memory_agent.py)
    "chromadb": MagicMock(),
}

for mod_name, mock in _MOCK_MODULES.items():
    sys.modules.setdefault(mod_name, mock)


# ---------------------------------------------------------------------------
# Hypothesis strategies for Sibling Dynamics Engine models
# ---------------------------------------------------------------------------

from datetime import datetime, timezone

from hypothesis import strategies as st

from app.models.multimodal import (
    EmotionCategory,
    EmotionResult,
    MultimodalInputEvent,
    TranscriptResult,
)
from app.models.sibling import (
    ComplementaryPair,
    ConflictEvent,
    PersonalityProfile,
    RelationshipModel,
    SkillMap,
    TraitScore,
)

# ---- Primitive helpers ----

_unit_float = st.floats(min_value=0.0, max_value=1.0, allow_nan=False)
_non_neg_int = st.integers(min_value=0, max_value=10_000)
_child_id = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=12
)
_iso_timestamp = st.builds(
    lambda dt: dt.isoformat(),
    st.datetimes(
        min_value=datetime(2020, 1, 1),
        max_value=datetime(2030, 1, 1),
        timezones=st.just(timezone.utc),
    ),
)
_theme = st.sampled_from(
    ["exploration", "puzzle-solving", "nurturing", "action", "mystery", "friendship"]
)
_fear = st.sampled_from(
    ["darkness", "loud-noises", "separation", "monsters", "water", "heights"]
)
_trait_name = st.sampled_from(
    ["curiosity", "boldness", "empathy", "creativity", "patience", "humor"]
)
_scenario = st.sampled_from(
    [
        "teaching moment",
        "collaborative puzzle",
        "rescue mission",
        "creative challenge",
        "exploration quest",
    ]
)


# ---- Model strategies ----


@st.composite
def st_trait_score(draw):
    """Generate a valid TraitScore satisfying all Pydantic constraints."""
    return TraitScore(
        value=draw(_unit_float),
        confidence=draw(_unit_float),
        observation_count=draw(_non_neg_int),
    )


@st.composite
def st_personality_profile(draw):
    """Generate a valid PersonalityProfile with random traits, themes, and fears."""
    total = draw(_non_neg_int)
    status = "emerging" if total < 5 else draw(st.sampled_from(["emerging", "established"]))
    return PersonalityProfile(
        child_id=draw(_child_id),
        curiosity=draw(st_trait_score()),
        boldness=draw(st_trait_score()),
        empathy=draw(st_trait_score()),
        creativity=draw(st_trait_score()),
        patience=draw(st_trait_score()),
        humor=draw(st_trait_score()),
        preferred_themes=draw(st.lists(_theme, max_size=4)),
        fears=draw(st.lists(_fear, max_size=3)),
        status=status,
        total_interactions=total,
        first_observed=draw(_iso_timestamp),
        last_updated=draw(_iso_timestamp),
        created_at=draw(_iso_timestamp),
    )


@st.composite
def st_relationship_model(draw):
    """Generate a valid RelationshipModel with metrics in valid ranges."""
    c1 = draw(_child_id)
    c2 = draw(_child_id.filter(lambda x: x != c1))
    pair_id = f"{c1}_{c2}"

    conflicts = draw(
        st.lists(
            st.builds(
                ConflictEvent,
                timestamp=_iso_timestamp,
                session_id=_child_id,
                description=st.text(max_size=40),
            ),
            max_size=5,
        )
    )

    return RelationshipModel(
        sibling_pair_id=pair_id,
        child1_id=c1,
        child2_id=c2,
        leadership_balance=draw(_unit_float),
        cooperation_score=draw(_unit_float),
        emotional_synchrony=draw(_unit_float),
        conflict_events=conflicts,
        total_shared_choices=draw(_non_neg_int),
        consecutive_disagreements=draw(st.integers(min_value=0, max_value=100)),
        last_updated=draw(_iso_timestamp),
        created_at=draw(_iso_timestamp),
    )


@st.composite
def st_complementary_pair(draw):
    """Generate a valid ComplementaryPair with distinct holder IDs."""
    s_id = draw(_child_id)
    g_id = draw(_child_id.filter(lambda x: x != s_id))
    return ComplementaryPair(
        strength_holder_id=s_id,
        growth_area_holder_id=g_id,
        trait_dimension=draw(_trait_name),
        strength_score=draw(_unit_float),
        growth_score=draw(_unit_float),
        suggested_scenario=draw(_scenario),
    )


@st.composite
def st_skill_map(draw):
    """Generate a valid SkillMap with zero or more complementary pairs."""
    return SkillMap(
        sibling_pair_id=draw(_child_id),
        complementary_pairs=draw(st.lists(st_complementary_pair(), max_size=6)),
        last_evaluated_at=draw(_iso_timestamp),
        interaction_count_at_evaluation=draw(_non_neg_int),
    )


@st.composite
def st_multimodal_event(draw):
    """Generate a valid MultimodalInputEvent with optional emotions and transcript."""
    has_transcript = draw(st.booleans())
    has_emotions = draw(st.booleans())

    transcript_text = draw(st.text(min_size=1, max_size=100)) if has_transcript else ""
    transcript = TranscriptResult(
        text=transcript_text,
        confidence=draw(_unit_float) if has_transcript else 0.0,
        language="en-US",
        is_empty=not has_transcript,
    )

    emotions = (
        draw(
            st.lists(
                st.builds(
                    EmotionResult,
                    face_id=st.integers(min_value=0, max_value=3),
                    emotion=st.sampled_from(list(EmotionCategory)),
                    confidence=_unit_float,
                ),
                min_size=1,
                max_size=4,
            )
        )
        if has_emotions
        else []
    )

    return MultimodalInputEvent(
        session_id=draw(_child_id),
        timestamp=draw(_iso_timestamp),
        transcript=transcript,
        emotions=emotions,
        face_detected=has_emotions,
        speech_id=draw(st.none() | _child_id),
    )
