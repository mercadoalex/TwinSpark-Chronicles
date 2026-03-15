"""RelationshipMapper — Layer 2 of the Sibling Dynamics Engine.

Models the dynamic between a sibling pair by tracking leadership balance,
cooperation style, conflict patterns, and emotional synchrony. Provides
cross-session decay so historical metrics gradually regress toward neutral
defaults, and computes a composite Sibling_Dynamics_Score at session end.

Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.3, 9.1, 9.2, 9.3, 9.4
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.models.multimodal import MultimodalInputEvent
from app.models.sibling import (
    ConflictEvent,
    PersonalityProfile,
    RelationshipModel,
)
from app.services.sibling_db import SiblingDB

logger = logging.getLogger(__name__)

# EMA alpha for relationship metric updates
_METRIC_ALPHA = 0.3


class RelationshipMapper:
    """Tracks and updates sibling relationship dynamics from multimodal data.

    Each public method that mutates the model also persists it to SQLite
    via the injected ``SiblingDB`` instance.
    """

    def __init__(self, db: SiblingDB) -> None:
        self.db = db

    # ── Public API ────────────────────────────────────────────────────

    async def update_from_event(
        self,
        event: MultimodalInputEvent,
        profiles: tuple[PersonalityProfile, PersonalityProfile],
    ) -> RelationshipModel:
        """Update relationship metrics from a multimodal event (Req 3.6).

        Computes emotional synchrony from paired emotion readings when
        both children have detected emotions in the event.
        """
        profile_a, profile_b = profiles
        pair_id = self._pair_id(profile_a.child_id, profile_b.child_id)
        model = await self.load_model(pair_id)

        # Ensure child IDs are set on the model
        if not model.child1_id:
            model.child1_id = profile_a.child_id
        if not model.child2_id:
            model.child2_id = profile_b.child_id

        # Compute emotional synchrony from paired emotion readings (Req 3.6)
        if len(event.emotions) >= 2:
            emotion_a = event.emotions[0].emotion
            emotion_b = event.emotions[1].emotion
            sync_signal = 1.0 if emotion_a == emotion_b else 0.0
            model.emotional_synchrony = self._ema(
                model.emotional_synchrony, sync_signal
            )

        model.last_updated = datetime.now(timezone.utc).isoformat()
        await self.persist_model(pair_id, model)
        return model

    async def record_shared_choice(
        self,
        initiator_child_id: str,
        follower_child_id: str,
        cooperative: bool,
    ) -> RelationshipModel:
        """Record a shared choice and update leadership/cooperation (Req 3.1, 3.2, 3.4, 3.5).

        Leadership balance shifts toward the initiator. Cooperation score
        increases for cooperative choices, decreases for competitive ones.
        Two consecutive disagreements trigger a conflict event.
        """
        pair_id = self._pair_id(initiator_child_id, follower_child_id)
        model = await self.load_model(pair_id)

        # Ensure child IDs are set
        if not model.child1_id:
            model.child1_id = initiator_child_id
        if not model.child2_id:
            model.child2_id = follower_child_id

        model.total_shared_choices += 1

        # Leadership balance: shift toward initiator (Req 3.1, 3.2)
        # child1 initiating → balance shifts toward 0.0
        # child2 initiating → balance shifts toward 1.0
        if initiator_child_id == model.child1_id:
            leadership_signal = 0.0
        else:
            leadership_signal = 1.0
        model.leadership_balance = self._ema(
            model.leadership_balance, leadership_signal
        )

        # Cooperation score (Req 3.4)
        coop_signal = 1.0 if cooperative else 0.0
        model.cooperation_score = self._ema(model.cooperation_score, coop_signal)

        # Conflict tracking (Req 3.5)
        if not cooperative:
            model.consecutive_disagreements += 1
            if model.consecutive_disagreements >= 2:
                conflict = ConflictEvent(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    session_id=model.sibling_pair_id,
                    description="Two consecutive disagreements on story choices",
                )
                model.conflict_events.append(conflict)
                # Reset counter after recording the conflict
                model.consecutive_disagreements = 0
        else:
            model.consecutive_disagreements = 0

        model.last_updated = datetime.now(timezone.utc).isoformat()
        await self.persist_model(pair_id, model)
        return model

    async def record_conflict(self, session_id: str) -> RelationshipModel:
        """Manually record a conflict event for a session (Req 3.5)."""
        model = await self.load_model(session_id)
        conflict = ConflictEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            description="Conflict detected during session",
        )
        model.conflict_events.append(conflict)
        model.last_updated = datetime.now(timezone.utc).isoformat()
        await self.persist_model(session_id, model)
        return model

    async def compute_session_score(self, session_id: str) -> float:
        """Compute Sibling_Dynamics_Score (Req 9.1).

        Equal-weighted mean of:
        - centered leadership (1.0 when balanced at 0.5, 0.0 at extremes)
        - cooperation_score
        - emotional_synchrony
        """
        model = await self.load_model(session_id)
        return model.sibling_dynamics_score()

    async def generate_summary(self, session_id: str) -> str:
        """Generate a 2-3 sentence plain-language summary (Req 9.2, 9.3, 9.4).

        Includes a suggestion if the score dropped > 0.2 from the previous
        session.
        """
        model = await self.load_model(session_id)
        score = model.sibling_dynamics_score()

        # Build the summary sentences
        sentences: list[str] = []

        # Sentence 1: overall dynamic
        if score >= 0.7:
            sentences.append(
                "The siblings had a great session with strong cooperation and balanced interaction."
            )
        elif score >= 0.4:
            sentences.append(
                "The siblings had a mixed session with some cooperation and occasional tension."
            )
        else:
            sentences.append(
                "The siblings had a challenging session with limited cooperation."
            )

        # Sentence 2: specific observations
        observations: list[str] = []
        if model.is_leadership_imbalanced():
            observations.append("one child dominated the decision-making")
        if model.is_low_cooperation():
            observations.append("cooperation was low")
        if len(model.conflict_events) > 0:
            observations.append(
                f"{len(model.conflict_events)} conflict(s) were detected"
            )
        if model.emotional_synchrony > 0.7:
            observations.append("they showed strong emotional connection")

        if observations:
            sentences.append("Notably, " + ", ".join(observations) + ".")
        else:
            sentences.append("The interaction was generally smooth with no major concerns.")

        # Check for score drop and add suggestion (Req 9.4)
        suggestion = await self._check_score_drop(model.sibling_pair_id, score)
        if suggestion:
            sentences.append(suggestion)

        return " ".join(sentences)

    async def load_model(self, sibling_pair_id: str) -> RelationshipModel:
        """Load from SQLite. Returns default model if not found."""
        model_json = await self.db.load_relationship(sibling_pair_id)
        if model_json is not None:
            return RelationshipModel.model_validate_json(model_json)
        now = datetime.now(timezone.utc).isoformat()
        return RelationshipModel(
            sibling_pair_id=sibling_pair_id,
            child1_id="",
            child2_id="",
            created_at=now,
        )

    async def persist_model(
        self, sibling_pair_id: str, model: RelationshipModel
    ) -> None:
        """Write model to SQLite."""
        await self.db.save_relationship(sibling_pair_id, model.model_dump_json())

    def _apply_cross_session_decay(
        self, model: RelationshipModel, factor: float = 0.9
    ) -> RelationshipModel:
        """Apply decay factor to historical metrics at session start (Req 8.3).

        - leadership_balance decays toward 0.5 (neutral)
        - cooperation_score decays toward 0
        - emotional_synchrony decays toward 0
        """
        model.leadership_balance = 0.5 + factor * (model.leadership_balance - 0.5)
        model.cooperation_score = factor * model.cooperation_score
        model.emotional_synchrony = factor * model.emotional_synchrony
        return model

    # ── Internal helpers ──────────────────────────────────────────────

    def _ema(self, current: float, new_signal: float, alpha: float = _METRIC_ALPHA) -> float:
        """Exponential moving average update, clamped to [0.0, 1.0]."""
        result = alpha * new_signal + (1.0 - alpha) * current
        return max(0.0, min(1.0, result))

    @staticmethod
    def _pair_id(child_a_id: str, child_b_id: str) -> str:
        """Deterministic pair ID from two child IDs (sorted for consistency)."""
        return ":".join(sorted([child_a_id, child_b_id]))

    async def _check_score_drop(
        self, sibling_pair_id: str, current_score: float
    ) -> str | None:
        """Check if score dropped > 0.2 from previous session (Req 9.4).

        Returns a suggestion string if a significant drop is detected,
        otherwise None.
        """
        summaries = await self.db.load_session_summaries(sibling_pair_id, limit=1)
        if not summaries:
            return None

        previous_score = summaries[0].get("score", current_score)
        if previous_score - current_score > 0.2:
            return (
                "Suggestion: Consider encouraging more collaborative activities "
                "between the siblings to rebuild their cooperative dynamic."
            )
        return None
