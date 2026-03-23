"""Repository for voice_recordings and voice_recording_events tables.

Encapsulates all SQL for voice recording data access. No audio processing,
no file I/O — just database operations.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4
from datetime import datetime

from app.db.base_repository import BaseRepository


class VoiceRecordingRepository(BaseRepository):
    """Data access for voice_recordings and voice_recording_events."""

    # ── voice_recordings table ────────────────────────────────────

    async def find_by_id(self, recording_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT * FROM voice_recordings WHERE recording_id = ?",
            (recording_id,),
        )

    async def find_all(
        self,
        sibling_pair_id: str | None = None,
        message_type: str | None = None,
        recorder_name: str | None = None,
        **filters: Any,
    ) -> list[dict]:
        sql = "SELECT * FROM voice_recordings WHERE 1=1"
        params: list = []

        if sibling_pair_id is not None:
            sql += " AND sibling_pair_id = ?"
            params.append(sibling_pair_id)
        if message_type is not None:
            sql += " AND message_type = ?"
            params.append(message_type)
        if recorder_name is not None:
            sql += " AND recorder_name = ?"
            params.append(recorder_name)

        sql += " ORDER BY recorder_name ASC, created_at ASC"
        return await self._db.fetch_all(sql, tuple(params))

    async def save(self, recording: dict) -> None:
        await self._db.execute(
            "INSERT INTO voice_recordings "
            "(recording_id, sibling_pair_id, recorder_name, relationship, "
            "message_type, language, duration_seconds, wav_path, mp3_path, "
            "sample_path, command_phrase, command_action, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                recording["recording_id"], recording["sibling_pair_id"],
                recording["recorder_name"], recording["relationship"],
                recording["message_type"], recording["language"],
                recording["duration_seconds"], recording["wav_path"],
                recording["mp3_path"], recording.get("sample_path"),
                recording.get("command_phrase"), recording.get("command_action"),
                recording["created_at"],
            ),
        )

    async def delete(self, recording_id: str) -> bool:
        row = await self._db.fetch_one(
            "SELECT recording_id FROM voice_recordings WHERE recording_id = ?",
            (recording_id,),
        )
        if not row:
            return False
        await self._db.execute(
            "DELETE FROM voice_recordings WHERE recording_id = ?",
            (recording_id,),
        )
        return True

    async def delete_all_by_pair(self, sibling_pair_id: str) -> None:
        await self._db.execute(
            "DELETE FROM voice_recordings WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )

    async def count_by_pair(self, sibling_pair_id: str) -> int:
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM voice_recordings WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        return row["cnt"] if row else 0

    async def count_by_type(self, sibling_pair_id: str, message_type: str) -> int:
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ?",
            (sibling_pair_id, message_type),
        )
        return row["cnt"] if row else 0

    async def find_matching(
        self, sibling_pair_id: str, message_type: str, language: str
    ) -> dict | None:
        # Try exact language match first
        row = await self._db.fetch_one(
            "SELECT * FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? AND language = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (sibling_pair_id, message_type, language),
        )
        if row:
            return row
        # Fallback: any recording of this message type
        return await self._db.fetch_one(
            "SELECT * FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (sibling_pair_id, message_type),
        )

    async def get_voice_commands(self, sibling_pair_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT recording_id, command_phrase, command_action, "
            "recorder_name, language FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? "
            "AND command_phrase IS NOT NULL AND command_action IS NOT NULL "
            "ORDER BY created_at ASC",
            (sibling_pair_id, "voice_command"),
        )

    async def get_cloning_stats(self, sibling_pair_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT recorder_name, COUNT(*) AS sample_count "
            "FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND sample_path IS NOT NULL "
            "GROUP BY recorder_name",
            (sibling_pair_id,),
        )

    # ── voice_recording_events table ──────────────────────────────

    async def save_event(self, event: dict) -> None:
        await self._db.execute(
            "INSERT INTO voice_recording_events "
            "(event_id, sibling_pair_id, recording_id, event_type, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                event["event_id"], event["sibling_pair_id"],
                event.get("recording_id"), event["event_type"],
                event["created_at"],
            ),
        )
