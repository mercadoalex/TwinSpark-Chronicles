"""Async persistence layer for sibling dynamics structured data.

Uses the DatabaseConnection abstraction so the same code works with
SQLite (dev) and PostgreSQL (production). Schema creation is handled
by the migration runner — ``initialize()`` is a no-op kept for
backward compatibility.

Requirements: 1.4, 6.1, 6.3, 6.4, 8.1, 8.5, 10.1, 10.2
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.db.connection import DatabaseConnection


class SiblingDB:
    """Async wrapper for sibling dynamics structured data."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    async def initialize(self) -> None:
        """No-op — schema is managed by the migration runner."""
        pass

    # kept for legacy callers that still reference _get_db
    async def _get_db(self):
        return self._db._conn

    # ── Personality Profiles ──────────────────────────────────────

    async def save_profile(self, child_id: str, profile_json: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT INTO personality_profiles (child_id, profile_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(child_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at""",
            (child_id, profile_json, now, now),
        )

    async def load_profile(self, child_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT profile_json FROM personality_profiles WHERE child_id = ?",
            (child_id,),
        )
        return row["profile_json"] if row else None

    # ── Relationship Models ───────────────────────────────────────

    async def save_relationship(self, pair_id: str, model_json: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT INTO relationship_models (sibling_pair_id, model_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(sibling_pair_id) DO UPDATE SET
                model_json = excluded.model_json,
                updated_at = excluded.updated_at""",
            (pair_id, model_json, now, now),
        )

    async def load_relationship(self, pair_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT model_json FROM relationship_models WHERE sibling_pair_id = ?",
            (pair_id,),
        )
        return row["model_json"] if row else None

    # ── Skill Maps ────────────────────────────────────────────────

    async def save_skill_map(self, pair_id: str, skill_map_json: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT INTO skill_maps (sibling_pair_id, skill_map_json, evaluated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(sibling_pair_id) DO UPDATE SET
                skill_map_json = excluded.skill_map_json,
                evaluated_at = excluded.evaluated_at""",
            (pair_id, skill_map_json, now),
        )

    async def load_skill_map(self, pair_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT skill_map_json FROM skill_maps WHERE sibling_pair_id = ?",
            (pair_id,),
        )
        return row["skill_map_json"] if row else None

    # ── Session Summaries ─────────────────────────────────────────

    async def save_session_summary(
        self,
        session_id: str,
        pair_id: str,
        score: float,
        summary: str,
        suggestion: str | None = None,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT INTO session_summaries
                (session_id, sibling_pair_id, score, summary, suggestion, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(session_id) DO UPDATE SET
                score = excluded.score,
                summary = excluded.summary,
                suggestion = excluded.suggestion,
                created_at = excluded.created_at""",
            (session_id, pair_id, score, summary, suggestion, now),
        )

    async def load_session_summaries(
        self, pair_id: str, limit: int = 10
    ) -> list[dict]:
        return await self._db.fetch_all(
            """SELECT session_id, sibling_pair_id, score, summary, suggestion, created_at
            FROM session_summaries
            WHERE sibling_pair_id = ?
            ORDER BY created_at DESC
            LIMIT ?""",
            (pair_id, limit),
        )

    async def load_session_summary(self, session_id: str) -> dict | None:
        return await self._db.fetch_one(
            """SELECT session_id, sibling_pair_id, score, summary, suggestion, created_at
            FROM session_summaries
            WHERE session_id = ?""",
            (session_id,),
        )

    # ── Initial Profiles ──────────────────────────────────────────

    async def save_initial_profile(
        self, child_id: str, profile_json: str
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """INSERT OR IGNORE INTO initial_profiles (child_id, profile_json, created_at)
            VALUES (?, ?, ?)""",
            (child_id, profile_json, now),
        )

    async def load_initial_profile(self, child_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT profile_json FROM initial_profiles WHERE child_id = ?",
            (child_id,),
        )
        return row["profile_json"] if row else None
