"""Voice recording lifecycle service.

Coordinates upload, validation, audio normalization, storage, CRUD operations,
voice command management, and cloning status for family voice recordings.
All state is persisted via the DatabaseConnection abstraction and the local
file system, following the same pattern as PhotoService.

Requirements: 2.2–2.4, 3.1–3.5, 4.1–4.7, 5.1–5.6, 7.1–7.6, 8.1–8.5, 10.2–10.4, 11.5
"""

from __future__ import annotations

import logging
import os
import shutil
from datetime import datetime
from uuid import uuid4

from app.db.connection import DatabaseConnection
from app.models.voice_recording import (
    CloneStatus,
    DeleteRecordingResult,
    MessageType,
    RecordingMetadata,
    VoiceCommandRecord,
    VoiceRecordingRecord,
    VoiceRecordingResult,
)
from app.services.audio_normalizer import AudioNormalizer, AudioNormalizationError

logger = logging.getLogger(__name__)

MAX_RECORDINGS_PER_PAIR = 50
MAX_VOICE_COMMANDS_PER_PAIR = 10

VALID_RELATIONSHIPS = {"grandparent", "parent", "sibling", "other"}


class VoiceRecordingValidationError(Exception):
    """Raised when recording metadata validation fails."""


class VoiceRecordingCapacityError(Exception):
    """Raised when recording capacity limits are reached."""


class VoiceRecordingService:
    """Central service coordinating the voice recording lifecycle.

    Stateless — all persistent state lives in the database and file system.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        audio_normalizer: AudioNormalizer,
        storage_root: str = "voice_recordings",
    ) -> None:
        self._db = db
        self._normalizer = audio_normalizer
        self._storage_root = storage_root
        os.makedirs(self._storage_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_metadata(self, metadata: RecordingMetadata) -> None:
        """Validate recording metadata fields.

        Raises VoiceRecordingValidationError for invalid inputs.
        """
        if not metadata.recorder_name or not metadata.recorder_name.strip():
            raise VoiceRecordingValidationError("Recorder name is required")

        # MessageType enum validation is handled by Pydantic, but double-check
        valid_types = {mt.value for mt in MessageType}
        if metadata.message_type.value not in valid_types:
            raise VoiceRecordingValidationError(
                f"Invalid message type. Must be one of: {', '.join(valid_types)}"
            )

        if metadata.language not in ("en", "es"):
            raise VoiceRecordingValidationError(
                "Language must be 'en' or 'es'"
            )

        # Voice command requires phrase and action
        if metadata.message_type == MessageType.VOICE_COMMAND:
            if not metadata.command_phrase or not metadata.command_phrase.strip():
                raise VoiceRecordingValidationError(
                    "Command phrase is required for voice command recordings"
                )
            if not metadata.command_action or not metadata.command_action.strip():
                raise VoiceRecordingValidationError(
                    "Command action is required for voice command recordings"
                )

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    async def upload_recording(
        self,
        sibling_pair_id: str,
        audio_bytes: bytes,
        metadata: RecordingMetadata,
    ) -> VoiceRecordingResult:
        """Full pipeline: validate → check capacity → normalize → store.

        Args:
            sibling_pair_id: The sibling pair this recording belongs to.
            audio_bytes: Raw audio bytes in any ffmpeg-supported format.
            metadata: Recording metadata (recorder name, type, language, etc.).

        Returns:
            VoiceRecordingResult with recording_id, duration, and message.

        Raises:
            VoiceRecordingValidationError: If metadata is invalid.
            VoiceRecordingCapacityError: If capacity limits are reached.
            AudioNormalizationError: If audio processing fails.
        """
        # 1. Validate metadata
        self._validate_metadata(metadata)

        # 2. Check overall capacity (50 max)
        current_count = await self.get_recording_count(sibling_pair_id)
        if current_count >= MAX_RECORDINGS_PER_PAIR:
            raise VoiceRecordingCapacityError(
                "Maximum of 50 recordings reached. Delete older recordings to make room."
            )

        # 3. Check voice command capacity (10 max)
        if metadata.message_type == MessageType.VOICE_COMMAND:
            cmd_row = await self._db.fetch_one(
                "SELECT COUNT(*) AS cnt FROM voice_recordings "
                "WHERE sibling_pair_id = ? AND message_type = ?",
                (sibling_pair_id, MessageType.VOICE_COMMAND.value),
            )
            cmd_count = cmd_row["cnt"] if cmd_row else 0
            if cmd_count >= MAX_VOICE_COMMANDS_PER_PAIR:
                raise VoiceRecordingCapacityError(
                    "Maximum of 10 voice commands reached."
                )

        # 4. Normalize audio
        normalized = self._normalizer.normalize(audio_bytes)

        # 5. Generate IDs and paths
        recording_id = str(uuid4())
        pair_dir = os.path.join(self._storage_root, sibling_pair_id)
        samples_dir = os.path.join(pair_dir, "samples")
        os.makedirs(pair_dir, exist_ok=True)
        os.makedirs(samples_dir, exist_ok=True)

        wav_path = os.path.join(pair_dir, f"{recording_id}.wav")
        mp3_path = os.path.join(pair_dir, f"{recording_id}.mp3")
        sample_path = os.path.join(samples_dir, f"{recording_id}_sample.wav")

        # 6. Save files to disk
        with open(wav_path, "wb") as f:
            f.write(normalized.wav_bytes)
        with open(mp3_path, "wb") as f:
            f.write(normalized.mp3_bytes)
        if normalized.sample_bytes:
            with open(sample_path, "wb") as f:
                f.write(normalized.sample_bytes)

        # 7. Insert DB row
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO voice_recordings "
            "(recording_id, sibling_pair_id, recorder_name, relationship, "
            "message_type, language, duration_seconds, wav_path, mp3_path, "
            "sample_path, command_phrase, command_action, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                recording_id,
                sibling_pair_id,
                metadata.recorder_name,
                metadata.relationship,
                metadata.message_type.value,
                metadata.language,
                normalized.duration_seconds,
                wav_path,
                mp3_path,
                sample_path if normalized.sample_bytes else None,
                metadata.command_phrase,
                metadata.command_action,
                now,
            ),
        )

        # 8. Log creation event
        await self.log_event(sibling_pair_id, "created", recording_id)

        return VoiceRecordingResult(
            recording_id=recording_id,
            duration_seconds=normalized.duration_seconds,
            message_type=metadata.message_type,
            message="Recording uploaded successfully!",
        )

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_recordings(
        self,
        sibling_pair_id: str,
        message_type: str | None = None,
        recorder_name: str | None = None,
    ) -> list[VoiceRecordingRecord]:
        """List recordings for a sibling pair with optional filters.

        Results are grouped by recorder_name and sorted by created_at
        within each group.
        """
        sql = "SELECT * FROM voice_recordings WHERE sibling_pair_id = ?"
        params: list = [sibling_pair_id]

        if message_type is not None:
            sql += " AND message_type = ?"
            params.append(message_type)

        if recorder_name is not None:
            sql += " AND recorder_name = ?"
            params.append(recorder_name)

        sql += " ORDER BY recorder_name ASC, created_at ASC"

        rows = await self._db.fetch_all(sql, tuple(params))
        return [self._row_to_record(row) for row in rows]

    async def get_recording(self, recording_id: str) -> VoiceRecordingRecord | None:
        """Fetch a single recording by ID."""
        row = await self._db.fetch_one(
            "SELECT * FROM voice_recordings WHERE recording_id = ?",
            (recording_id,),
        )
        if not row:
            return None
        return self._row_to_record(row)

    @staticmethod
    def _row_to_record(row: dict) -> VoiceRecordingRecord:
        """Convert a DB row dict to a VoiceRecordingRecord."""
        return VoiceRecordingRecord(
            recording_id=row["recording_id"],
            sibling_pair_id=row["sibling_pair_id"],
            recorder_name=row["recorder_name"],
            relationship=row["relationship"],
            message_type=MessageType(row["message_type"]),
            language=row["language"],
            duration_seconds=row["duration_seconds"],
            wav_path=row["wav_path"],
            mp3_path=row["mp3_path"],
            sample_path=row["sample_path"],
            command_phrase=row["command_phrase"],
            command_action=row["command_action"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    # ------------------------------------------------------------------
    # Delete operations
    # ------------------------------------------------------------------

    async def delete_recording(self, recording_id: str) -> DeleteRecordingResult:
        """Delete a single recording: remove files, DB row, log event.

        Returns info about whether trigger assignments were affected.
        """
        record = await self.get_recording(recording_id)
        if not record:
            raise VoiceRecordingValidationError("Recording not found")

        # Remove files from disk
        self._safe_delete_file(record.wav_path)
        self._safe_delete_file(record.mp3_path)
        if record.sample_path:
            self._safe_delete_file(record.sample_path)

        # Check for trigger assignments (voice commands have implicit triggers)
        affected_triggers: list[str] = []
        if record.message_type == MessageType.VOICE_COMMAND and record.command_phrase:
            affected_triggers.append(f"voice_command:{record.command_phrase}")

        # Delete DB row
        await self._db.execute(
            "DELETE FROM voice_recordings WHERE recording_id = ?",
            (recording_id,),
        )

        # Log deletion event
        await self.log_event(record.sibling_pair_id, "deleted", recording_id)

        return DeleteRecordingResult(
            deleted_recording_id=recording_id,
            had_trigger_assignments=len(affected_triggers) > 0,
            affected_triggers=affected_triggers,
        )

    async def delete_all_recordings(self, sibling_pair_id: str) -> int:
        """Bulk delete all recordings and files for a sibling pair.

        Returns the number of recordings deleted.
        """
        recordings = await self.get_recordings(sibling_pair_id)
        count = len(recordings)

        # Remove all files
        for rec in recordings:
            self._safe_delete_file(rec.wav_path)
            self._safe_delete_file(rec.mp3_path)
            if rec.sample_path:
                self._safe_delete_file(rec.sample_path)

        # Delete all DB rows
        await self._db.execute(
            "DELETE FROM voice_recordings WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )

        # Clean up the pair directory
        pair_dir = os.path.join(self._storage_root, sibling_pair_id)
        if os.path.exists(pair_dir):
            try:
                shutil.rmtree(pair_dir)
            except OSError as exc:
                logger.warning("Failed to remove directory %s: %s", pair_dir, exc)

        # Log bulk deletion event
        await self.log_event(sibling_pair_id, "bulk_deleted")

        return count

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    async def get_recording_count(self, sibling_pair_id: str) -> int:
        """Return the total number of recordings for a sibling pair."""
        row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM voice_recordings WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        return row["cnt"] if row else 0

    async def find_matching_recording(
        self,
        sibling_pair_id: str,
        message_type: str,
        language: str,
    ) -> VoiceRecordingRecord | None:
        """Find a recording matching sibling pair, message type, and language.

        Prefers recordings in the requested language; falls back to any
        recording of the same message type if no language match exists.
        """
        # Try exact language match first
        row = await self._db.fetch_one(
            "SELECT * FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? AND language = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (sibling_pair_id, message_type, language),
        )
        if row:
            return self._row_to_record(row)

        # Fallback: any recording of this message type
        row = await self._db.fetch_one(
            "SELECT * FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? "
            "ORDER BY created_at DESC LIMIT 1",
            (sibling_pair_id, message_type),
        )
        if row:
            return self._row_to_record(row)

        return None

    # ------------------------------------------------------------------
    # Voice commands & cloning status
    # ------------------------------------------------------------------

    async def get_voice_commands(
        self, sibling_pair_id: str
    ) -> list[VoiceCommandRecord]:
        """List all voice command recordings for a sibling pair."""
        rows = await self._db.fetch_all(
            "SELECT recording_id, command_phrase, command_action, "
            "recorder_name, language FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND message_type = ? "
            "AND command_phrase IS NOT NULL AND command_action IS NOT NULL "
            "ORDER BY created_at ASC",
            (sibling_pair_id, MessageType.VOICE_COMMAND.value),
        )
        return [
            VoiceCommandRecord(
                recording_id=r["recording_id"],
                command_phrase=r["command_phrase"],
                command_action=r["command_action"],
                recorder_name=r["recorder_name"],
                language=r["language"],
            )
            for r in rows
        ]

    async def get_cloning_status(
        self, sibling_pair_id: str
    ) -> dict[str, CloneStatus]:
        """Get voice cloning readiness status per recorder.

        A recorder is cloning-ready when they have 5+ voice samples.
        """
        rows = await self._db.fetch_all(
            "SELECT recorder_name, COUNT(*) AS sample_count "
            "FROM voice_recordings "
            "WHERE sibling_pair_id = ? AND sample_path IS NOT NULL "
            "GROUP BY recorder_name",
            (sibling_pair_id,),
        )
        return {
            r["recorder_name"]: CloneStatus(
                recorder_name=r["recorder_name"],
                sample_count=r["sample_count"],
                cloning_ready=r["sample_count"] >= 5,
            )
            for r in rows
        }

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    async def log_event(
        self,
        sibling_pair_id: str,
        event_type: str,
        recording_id: str | None = None,
    ) -> None:
        """Log a voice recording event for audit trail."""
        event_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        await self._db.execute(
            "INSERT INTO voice_recording_events "
            "(event_id, sibling_pair_id, recording_id, event_type, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (event_id, sibling_pair_id, recording_id, event_type, now),
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_delete_file(path: str) -> None:
        """Delete a file if it exists, logging any errors."""
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except OSError as exc:
            logger.warning("Failed to delete file %s: %s", path, exc)
