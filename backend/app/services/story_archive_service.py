"""Async persistence for archived storybooks and their beats.

Archives completed stories so siblings can revisit past adventures
in the gallery. Uses the DatabaseConnection abstraction (same pattern
as SessionService).

Requirements: 1.1–1.6, 2.1–2.3, 3.1–3.3, 4.1, 4.4
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone

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

    async def archive_story(
        self,
        sibling_pair_id: str,
        title: str,
        language: str,
        beats: list[dict],
        duration_seconds: int,
    ) -> StorybookRecord | None:
        """Archive a completed story with all beats in a single transaction.

        Returns None and logs a warning if the beats list is empty.
        """
        if not beats:
            logger.warning(
                "Skipping archival for pair %s — no beats provided",
                sibling_pair_id,
            )
            return None

        storybook_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc).isoformat()
        cover_image_url = beats[0].get("scene_image_url")
        beat_count = len(beats)

        async with self._db.transaction():
            await self._db.execute(
                """INSERT INTO storybooks
                    (storybook_id, sibling_pair_id, title, language,
                     cover_image_url, beat_count, duration_seconds,
                     completed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    storybook_id, sibling_pair_id, title, language,
                    cover_image_url, beat_count, duration_seconds,
                    now, now,
                ),
            )

            for idx, beat in enumerate(beats):
                beat_id = uuid.uuid4().hex[:12]
                available_choices = json.dumps(
                    beat.get("available_choices", [])
                )
                await self._db.execute(
                    """INSERT INTO story_beats
                        (beat_id, storybook_id, beat_index, narration,
                         child1_perspective, child2_perspective,
                         scene_image_url, choice_made,
                         available_choices, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        beat_id, storybook_id, idx,
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
            beat_count=beat_count,
            completed_at=now,
        )

    async def list_storybooks(
        self, sibling_pair_id: str
    ) -> list[StorybookSummary]:
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

    async def get_storybook(
        self, storybook_id: str
    ) -> StorybookDetail | None:
        """Return full storybook with all beats in order."""
        book_row = await self._db.fetch_one(
            """SELECT storybook_id, sibling_pair_id, title, language,
                      cover_image_url, beat_count, duration_seconds,
                      completed_at
            FROM storybooks WHERE storybook_id = ?""",
            (storybook_id,),
        )
        if book_row is None:
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

        beats = [
            StoryBeatRecord(
                beat_id=row["beat_id"],
                beat_index=row["beat_index"],
                narration=row["narration"],
                child1_perspective=row["child1_perspective"],
                child2_perspective=row["child2_perspective"],
                scene_image_url=row["scene_image_url"],
                choice_made=row["choice_made"],
                available_choices=json.loads(row["available_choices"])
                if row["available_choices"]
                else [],
            )
            for row in beat_rows
        ]

        return StorybookDetail(**book_row, beats=beats)

    async def delete_storybook(self, storybook_id: str) -> bool:
        """Delete a storybook and its beats (CASCADE). Returns True if found."""
        row = await self._db.fetch_one(
            "SELECT storybook_id FROM storybooks WHERE storybook_id = ?",
            (storybook_id,),
        )
        if row is None:
            return False

        await self._db.execute(
            "DELETE FROM storybooks WHERE storybook_id = ?",
            (storybook_id,),
        )
        return True

    async def delete_all_storybooks(self, sibling_pair_id: str) -> int:
        """Bulk delete all storybooks for a sibling pair. Returns count."""
        rows = await self._db.fetch_all(
            "SELECT storybook_id FROM storybooks WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        count = len(rows)

        if count > 0:
            await self._db.execute(
                "DELETE FROM storybooks WHERE sibling_pair_id = ?",
                (sibling_pair_id,),
            )

        return count
