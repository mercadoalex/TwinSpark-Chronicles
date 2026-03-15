"""PersonalityEngine — Layer 1 of the Sibling Dynamics Engine.

Builds and maintains individual personality profiles for each child by
processing multimodal input events (emotions, transcripts) and story
choices. Uses exponential moving average (EMA) for temporal decay so
recent observations are weighted higher than older ones.

Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 11.2, 11.3
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from app.models.multimodal import EmotionCategory, MultimodalInputEvent
from app.models.sibling import PersonalityProfile, TraitScore
from app.services.sibling_db import SiblingDB

logger = logging.getLogger(__name__)

# Mapping from detected emotions to the personality traits they influence
# and the signal direction (high value = more of that trait).
_EMOTION_TRAIT_MAP: dict[EmotionCategory, list[tuple[str, float]]] = {
    EmotionCategory.HAPPY: [("humor", 0.8), ("boldness", 0.6)],
    EmotionCategory.SAD: [("empathy", 0.7), ("patience", 0.6)],
    EmotionCategory.SURPRISED: [("curiosity", 0.8), ("creativity", 0.6)],
    EmotionCategory.ANGRY: [("boldness", 0.7)],
    EmotionCategory.SCARED: [("empathy", 0.6), ("patience", 0.7)],
    EmotionCategory.NEUTRAL: [("patience", 0.5)],
}

# Keyword patterns for transcript analysis → trait signals
_TRANSCRIPT_PATTERNS: list[tuple[str, str, float]] = [
    # (regex pattern, trait_name, signal_strength)
    (r"\b(why|how|what if|wonder|curious)\b", "curiosity", 0.7),
    (r"\b(let me|i will|i can|watch this|dare)\b", "boldness", 0.7),
    (r"\b(please|sorry|thank you|are you ok|feel)\b", "empathy", 0.7),
    (r"\b(imagine|pretend|what about|create|invent)\b", "creativity", 0.7),
    (r"\b(wait|let\'?s see|take our time|slowly|careful)\b", "patience", 0.7),
    (r"\b(haha|funny|silly|joke|laugh)\b", "humor", 0.7),
    (r"\?", "curiosity", 0.5),  # questions signal curiosity
]


class PersonalityEngine:
    """Builds and updates per-child personality profiles from multimodal data.

    Each public method that mutates a profile also persists it to SQLite
    via the injected ``SiblingDB`` instance.
    """

    def __init__(self, db: SiblingDB) -> None:
        self.db = db

    # ── Public API ────────────────────────────────────────────────────

    async def update_from_event(
        self, child_id: str, event: MultimodalInputEvent
    ) -> PersonalityProfile:
        """Update a child's profile from a multimodal event (Req 1.1, 1.2, 11.2).

        Processes emotion signals and transcript text, applies EMA updates
        to relevant traits, increments interaction count, and persists.
        """
        profile = await self.load_profile(child_id)

        # Process emotion signals (Req 1.2, 11.2)
        for emotion_result in event.emotions:
            # Discard low-confidence signals (< 0.1) to avoid noise
            if emotion_result.confidence < 0.1:
                continue
            trait_signals = _EMOTION_TRAIT_MAP.get(emotion_result.emotion, [])
            for trait_name, signal_value in trait_signals:
                self._update_trait(
                    profile, trait_name, signal_value, emotion_result.confidence
                )

        # Process transcript signals (Req 11.3)
        if not event.transcript.is_empty and event.transcript.text.strip():
            transcript_signals = self._analyze_transcript(event.transcript.text)
            for trait_name, signal_value in transcript_signals.items():
                self._update_trait(profile, trait_name, signal_value)

        # Increment interaction count and update timestamps (Req 2.5)
        profile.total_interactions += 1
        now = datetime.now(timezone.utc).isoformat()
        profile.last_updated = now
        if not profile.first_observed:
            profile.first_observed = now

        # Update status based on interaction count
        if profile.total_interactions >= 5:
            profile.status = "established"

        await self.persist_profile(child_id, profile)
        return profile

    async def record_choice(
        self, child_id: str, choice: str, theme: str
    ) -> PersonalityProfile:
        """Record a story choice and update preferred themes (Req 1.1, 2.2).

        Adds the theme to ``preferred_themes`` if not already present.
        """
        profile = await self.load_profile(child_id)

        if theme and theme not in profile.preferred_themes:
            profile.preferred_themes.append(theme)

        profile.total_interactions += 1
        now = datetime.now(timezone.utc).isoformat()
        profile.last_updated = now

        if profile.total_interactions >= 5:
            profile.status = "established"

        await self.persist_profile(child_id, profile)
        return profile

    async def load_profile(self, child_id: str) -> PersonalityProfile:
        """Load from SQLite. Returns default 'emerging' profile if not found (Req 1.4)."""
        profile_json = await self.db.load_profile(child_id)
        if profile_json is not None:
            return PersonalityProfile.model_validate_json(profile_json)
        # Return a fresh emerging profile with conservative defaults
        now = datetime.now(timezone.utc).isoformat()
        return PersonalityProfile(
            child_id=child_id,
            status="emerging",
            created_at=now,
            first_observed=now,
        )

    async def persist_profile(
        self, child_id: str, profile: PersonalityProfile
    ) -> None:
        """Write profile to SQLite (Req 1.4)."""
        await self.db.save_profile(child_id, profile.model_dump_json())
        # Save initial snapshot for growth tracking (only first time)
        await self.db.save_initial_profile(child_id, profile.model_dump_json())

    # ── Internal helpers ──────────────────────────────────────────────

    def _apply_temporal_decay(
        self, current: float, new_signal: float, alpha: float = 0.3
    ) -> float:
        """EMA update: ``alpha * new_signal + (1 - alpha) * current`` (Req 1.5).

        The result is always between ``current`` and ``new_signal``, weighting
        recent observations higher when alpha > 0.
        """
        return alpha * new_signal + (1.0 - alpha) * current

    def _analyze_transcript(self, text: str) -> dict[str, float]:
        """Extract personality signals from transcript text (Req 11.3).

        Scans for keyword patterns associated with each trait dimension.
        Returns a dict of trait_name → signal_strength for matched traits.
        """
        signals: dict[str, float] = {}
        lower_text = text.lower()

        for pattern, trait_name, signal_strength in _TRANSCRIPT_PATTERNS:
            if re.search(pattern, lower_text):
                # Keep the strongest signal per trait
                if trait_name not in signals or signal_strength > signals[trait_name]:
                    signals[trait_name] = signal_strength

        return signals

    def _update_trait(
        self,
        profile: PersonalityProfile,
        trait_name: str,
        signal_value: float,
        confidence_boost: float = 0.5,
        alpha: float = 0.3,
    ) -> None:
        """Apply an EMA update to a single trait on the profile.

        Updates the trait's value via temporal decay, bumps observation_count,
        and increases confidence toward 1.0.
        """
        traits = profile.trait_dict()
        trait = traits.get(trait_name)
        if trait is None:
            return

        # EMA update on trait value
        new_value = self._apply_temporal_decay(trait.value, signal_value, alpha)
        # Clamp to [0.0, 1.0]
        new_value = max(0.0, min(1.0, new_value))

        new_count = trait.observation_count + 1
        # Confidence grows with observations, asymptotically approaching 1.0
        new_confidence = min(1.0, trait.confidence + confidence_boost * (1.0 - trait.confidence) * 0.3)

        # Write back to the profile via attribute access
        updated_trait = TraitScore(
            value=new_value,
            confidence=new_confidence,
            observation_count=new_count,
        )
        setattr(profile, trait_name, updated_trait)