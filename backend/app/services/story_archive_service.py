"""Async persistence for archived storybooks.

Stores completed stories and their beats in SQLite so children can
revisit past adventures in the Storybook Gallery.

Requirements: 1.1–1.6, 2.1–2.3, 3.1–3.3, 4.1, 4.4
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from app.db.connection import DatabaseConnection
from app.models.storybook import (
    StorybookDetail,
    StorybookRecord,
    StorybookSummary,
    StoryBeatRecord,
)

logger = logging.getLogger(__name__)


class StoryArchiveService:
    """CRUD for archived storybooks using DatabaseConnection."""

    def __init__(self, db: DatabaseConnection) -> None:
        self._db = db

    async def _ensure_tables(self) -> None:
        """Create storybooks and story_beats tables if they don't exist."""
        await self._db.execute(
            """CREATE TABLE IF NOT EXISTS storybooks (
                storybook_id TEXT PRIMARY KEY,
                sibling_pair_id TEXT NOT NULL,
                title TEXT NOT NULL,
                language TEXT NOT NULL DEFAULT 'en',
                cover_image_url TEXT,
                beat_count INTEGER NOT NULL DEFAULT 0,
                duration_seconds INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT NOT NULL,
                created_at TEXT NOT NULL
            )"""
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_storybooks_pair "
            "ON storybooks(sibling_pair_id, completed_at DESC)"
        )
        await self._db.execute(
            """CREATE TABLE IF NOT EXISTS story_beats (
                beat_id TEXT PRIMARY KEY,
                storybook_id TEXT NOT NULL REFERENCES storybooks(storybook_id) ON DELETE CASCADE,
                beat_index INTEGER NOT NULL,
                narration TEXT NOT NULL,
                child1_perspective TEXT,
                child2_perspective TEXT,
                scene_image_url TEXT,
                choice_made TEXT,
                available_choices TEXT,
                created_at TEXT NOT NULL
            )"""
        )
        await self._db.execute(
            "CREATE INDEX IF NOT EXISTS idx_beats_storybook "
            "ON story_beats(storybook_id, beat_index ASC)"
        )

    # ── archive ───────────────────────────────────────────────────

    async def archive_story(
        self,
        sibling_pair_id: str,
        title: str,
        language: str,
        beats: list[dict],
        duration_seconds: int,
    ) -> StorybookRecord | None:
        """Archive a completed story with all beats in a single transaction.

        Returns ``None`` and logs a warning if *beats* is empty.
        """
        if not beats:
            logger.warning(
                "Skipping archival for pair %s — no beats to archive",
                sibling_pair_id,
            )
            return None

        now = datetime.now(timezone.utc).isoformat()
        storybook_id = uuid4().hex[:12]
        cover_image_url = beats[0].get("scene_image_url")

        async with self._db.transaction():
            await self._db.execute(
                """INSERT INTO storybooks
                    (storybook_id, sibling_pair_id, title, language,
                     cover_image_url, beat_count, duration_seconds,
                     completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    storybook_id,
                    sibling_pair_id,
                    title,
                    language,
                    cover_image_url,
                    len(beats),
                    duration_seconds,
                    now,
                    now,
                ),
            )

            for idx, beat in enumerate(beats):
                beat_id = uuid4().hex[:12]
                available_choices = json.dumps(beat.get("available_choices", []))
                await self._db.execute(
                    """INSERT INTO story_beats
                        (beat_id, storybook_id, beat_index, narration,
                         child1_perspective, child2_perspective,
                         scene_image_url, choice_made, available_choices,
                         created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        beat_id,
                        storybook_id,
                        idx,
                        beat.get("narration", ""),
                        beat.get("child1_perspective"),
                        beat.get("child2_perspective"),
                        beat.get("scene_image_url"),
                        beat.get("choice_made"),
                        available_choices,
                        now,
                    ),
                )

        return StorybookRecord(
            storybook_id=storybook_id,
            sibling_pair_id=sibling_pair_id,
            title=title,
            beat_count=len(beats),
            completed_at=now,
        )

    # ── listing ───────────────────────────────────────────────────

    async def list_storybooks(self, sibling_pair_id: str) -> list[StorybookSummary]:
        """Return storybook summaries sorted by completed_at DESC."""
        rows = await self._db.fetch_all(
            """SELECT storybook_id, title, cover_image_url, beat_count,
                      duration_seconds, completed_at
            FROM storybooks
            WHERE sibling_pair_id = ?
            ORDER BY completed_at DESC""",
            (sibling_pair_id,),
        )
        return [StorybookSummary(**row) for row in rows]

    # ── detail ────────────────────────────────────────────────────

    async def get_storybook(self, storybook_id: str) -> StorybookDetail | None:
        """Return full storybook with all beats in order."""
        row = await self._db.fetch_one(
            """SELECT storybook_id, sibling_pair_id, title, language,
                      cover_image_url, beat_count, duration_seconds,
                      completed_at
            FROM storybooks WHERE storybook_id = ?""",
            (storybook_id,),
        )
        if row is None:
            return None

        beat_rows = await self._db.fetch_all(
            """SELECT beat_id, beat_index, narration,
                      child1_perspective, child2_perspective,
                      scene_image_url, choice_made, available_choices
            FROM story_beats
            WHERE storybook_id = ?
            ORDER BY beat_index ASC""",
            (storybook_id,),
        )

        beats = []
        for br in beat_rows:
            choices_raw = br.get("available_choices", "[]")
            try:
                choices = json.loads(choices_raw) if choices_raw else []
            except (json.JSONDecodeError, TypeError):
                choices = []
            beats.append(
                StoryBeatRecord(
                    beat_id=br["beat_id"],
                    beat_index=br["beat_index"],
                    narration=br["narration"],
                    child1_perspective=br.get("child1_perspective"),
                    child2_perspective=br.get("child2_perspective"),
                    scene_image_url=br.get("scene_image_url"),
                    choice_made=br.get("choice_made"),
                    available_choices=choices,
                )
            )

        return StorybookDetail(
            storybook_id=row["storybook_id"],
            sibling_pair_id=row["sibling_pair_id"],
            title=row["title"],
            language=row["language"],
            cover_image_url=row.get("cover_image_url"),
            beat_count=row["beat_count"],
            duration_seconds=row["duration_seconds"],
            completed_at=row["completed_at"],
            beats=beats,
        )

    # ── deletion ──────────────────────────────────────────────────

    async def delete_storybook(self, storybook_id: str) -> bool:
        """Delete a storybook and its beats. Returns True if found."""
        existing = await self._db.fetch_one(
            "SELECT storybook_id FROM storybooks WHERE storybook_id = ?",
            (storybook_id,),
        )
        if existing is None:
            return False

        # Enable foreign key CASCADE for SQLite
        await self._db.execute("PRAGMA foreign_keys = ON")
        await self._db.execute(
            "DELETE FROM storybooks WHERE storybook_id = ?",
            (storybook_id,),
        )
        return True

    async def delete_all_storybooks(self, sibling_pair_id: str) -> int:
        """Bulk delete all storybooks for a sibling pair. Returns count."""
        row = await self._db.fetch_one(
            "SELECT COUNT(*) as cnt FROM storybooks WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        count = row["cnt"] if row else 0

        if count > 0:
            # Enable foreign key CASCADE for SQLite
            await self._db.execute("PRAGMA foreign_keys = ON")
            await self._db.execute(
                "DELETE FROM storybooks WHERE sibling_pair_id = ?",
                (sibling_pair_id,),
            )

        return count
