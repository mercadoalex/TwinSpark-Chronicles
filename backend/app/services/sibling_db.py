"""Async SQLite persistence layer for sibling dynamics structured data.

Provides CRUD operations for personality profiles, relationship models,
skill maps, and session summaries using aiosqlite. Each record stores
its domain object as a JSON string alongside metadata timestamps.

Requirements: 1.4, 8.1, 8.5, 10.1, 10.2
"""

from datetime import datetime, timezone

import aiosqlite


class SiblingDB:
    """Async SQLite wrapper for sibling dynamics structured data.

    Uses a single persistent connection to support both file-backed and
    in-memory (`:memory:`) databases. Call ``initialize()`` before any
    other method, and ``close()`` when done.
    """

    def __init__(self, db_path: str = "./sibling_data.db") -> None:
        self.db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def _get_db(self) -> aiosqlite.Connection:
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
        return self._db

    async def close(self) -> None:
        """Close the underlying database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def initialize(self) -> None:
        """Create tables if they don't exist."""
        db = await self._get_db()
        await db.execute(
            """CREATE TABLE IF NOT EXISTS personality_profiles (
                child_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS relationship_models (
                sibling_pair_id TEXT PRIMARY KEY,
                model_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS skill_maps (
                sibling_pair_id TEXT PRIMARY KEY,
                skill_map_json TEXT NOT NULL,
                evaluated_at TEXT NOT NULL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS session_summaries (
                session_id TEXT PRIMARY KEY,
                sibling_pair_id TEXT NOT NULL,
                score REAL NOT NULL,
                summary TEXT NOT NULL,
                suggestion TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        await db.execute(
            """CREATE TABLE IF NOT EXISTS initial_profiles (
                child_id TEXT PRIMARY KEY,
                profile_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        await db.commit()

    # ── Personality Profiles ──────────────────────────────────────────

    async def save_profile(self, child_id: str, profile_json: str) -> None:
        """Upsert a personality profile."""
        now = datetime.now(timezone.utc).isoformat()
        db = await self._get_db()
        await db.execute(
            """INSERT INTO personality_profiles (child_id, profile_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(child_id) DO UPDATE SET
                profile_json = excluded.profile_json,
                updated_at = excluded.updated_at""",
            (child_id, profile_json, now, now),
        )
        await db.commit()

    async def load_profile(self, child_id: str) -> str | None:
        """Load a personality profile JSON string. Returns None if not found."""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT profile_json FROM personality_profiles WHERE child_id = ?",
            (child_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # ── Relationship Models ───────────────────────────────────────────

    async def save_relationship(self, pair_id: str, model_json: str) -> None:
        """Upsert a relationship model."""
        now = datetime.now(timezone.utc).isoformat()
        db = await self._get_db()
        await db.execute(
            """INSERT INTO relationship_models (sibling_pair_id, model_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(sibling_pair_id) DO UPDATE SET
                model_json = excluded.model_json,
                updated_at = excluded.updated_at""",
            (pair_id, model_json, now, now),
        )
        await db.commit()

    async def load_relationship(self, pair_id: str) -> str | None:
        """Load a relationship model JSON string. Returns None if not found."""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT model_json FROM relationship_models WHERE sibling_pair_id = ?",
            (pair_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # ── Skill Maps ────────────────────────────────────────────────────

    async def save_skill_map(self, pair_id: str, skill_map_json: str) -> None:
        """Upsert a skill map."""
        now = datetime.now(timezone.utc).isoformat()
        db = await self._get_db()
        await db.execute(
            """INSERT INTO skill_maps (sibling_pair_id, skill_map_json, evaluated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(sibling_pair_id) DO UPDATE SET
                skill_map_json = excluded.skill_map_json,
                evaluated_at = excluded.evaluated_at""",
            (pair_id, skill_map_json, now),
        )
        await db.commit()

    async def load_skill_map(self, pair_id: str) -> str | None:
        """Load a skill map JSON string. Returns None if not found."""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT skill_map_json FROM skill_maps WHERE sibling_pair_id = ?",
            (pair_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None

    # ── Session Summaries ─────────────────────────────────────────────

    async def save_session_summary(
        self,
        session_id: str,
        pair_id: str,
        score: float,
        summary: str,
        suggestion: str | None = None,
    ) -> None:
        """Insert a session summary. Replaces if session_id already exists."""
        now = datetime.now(timezone.utc).isoformat()
        db = await self._get_db()
        await db.execute(
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
        await db.commit()

    async def load_session_summaries(
        self, pair_id: str, limit: int = 10
    ) -> list[dict]:
        """Load recent session summaries for a sibling pair, newest first."""
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT session_id, sibling_pair_id, score, summary, suggestion, created_at
            FROM session_summaries
            WHERE sibling_pair_id = ?
            ORDER BY created_at DESC
            LIMIT ?""",
            (pair_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def load_session_summary(self, session_id: str) -> dict | None:
        """Load a single session summary by session_id. Returns None if not found."""
        db = await self._get_db()
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT session_id, sibling_pair_id, score, summary, suggestion, created_at
            FROM session_summaries
            WHERE session_id = ?""",
            (session_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


    # ── Initial Profiles ──────────────────────────────────────────────

    async def save_initial_profile(
        self, child_id: str, profile_json: str
    ) -> None:
        """Save the first-ever snapshot of a child's profile (for growth tracking).
        Only inserts if no initial profile exists yet — never overwrites."""
        now = datetime.now(timezone.utc).isoformat()
        db = await self._get_db()
        await db.execute(
            """INSERT OR IGNORE INTO initial_profiles (child_id, profile_json, created_at)
            VALUES (?, ?, ?)""",
            (child_id, profile_json, now),
        )
        await db.commit()

    async def load_initial_profile(self, child_id: str) -> str | None:
        """Load the initial profile snapshot. Returns None if not found."""
        db = await self._get_db()
        cursor = await db.execute(
            "SELECT profile_json FROM initial_profiles WHERE child_id = ?",
            (child_id,),
        )
        row = await cursor.fetchone()
        return row[0] if row else None
