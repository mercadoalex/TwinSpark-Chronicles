"""Repository for photos, face_portraits, character_mappings, and style_transferred_portraits tables.

Encapsulates all SQL for photo-related data access. No business logic,
no file I/O, no validation — just database operations.
"""

from __future__ import annotations

from typing import Any

from app.db.base_repository import BaseRepository


class PhotoRepository(BaseRepository):
    """Data access for photos, face_portraits, character_mappings, and style_transferred_portraits."""

    # ── photos table ──────────────────────────────────────────────

    async def find_by_id(self, photo_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT * FROM photos WHERE photo_id = ?", (photo_id,)
        )

    async def find_all(self, sibling_pair_id: str | None = None, **filters: Any) -> list[dict]:
        if sibling_pair_id is not None:
            return await self._db.fetch_all(
                "SELECT * FROM photos WHERE sibling_pair_id = ? ORDER BY uploaded_at ASC",
                (sibling_pair_id,),
            )
        return await self._db.fetch_all("SELECT * FROM photos ORDER BY uploaded_at ASC")

    async def save(self, photo: dict) -> None:
        await self._db.execute(
            "INSERT INTO photos (photo_id, sibling_pair_id, filename, file_path, "
            "file_size_bytes, width, height, status, uploaded_at, content_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                photo["photo_id"], photo["sibling_pair_id"], photo["filename"],
                photo["file_path"], photo["file_size_bytes"], photo["width"],
                photo["height"], photo["status"], photo["uploaded_at"],
                photo["content_hash"],
            ),
        )

    async def delete(self, photo_id: str) -> bool:
        row = await self._db.fetch_one(
            "SELECT photo_id FROM photos WHERE photo_id = ?", (photo_id,)
        )
        if not row:
            return False
        await self._db.execute("DELETE FROM photos WHERE photo_id = ?", (photo_id,))
        return True

    async def update_status(self, photo_id: str, status: str) -> None:
        await self._db.execute(
            "UPDATE photos SET status = ? WHERE photo_id = ?", (status, photo_id)
        )

    async def get_content_hash(self, photo_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT content_hash FROM photos WHERE photo_id = ?", (photo_id,)
        )
        return row["content_hash"] if row and row["content_hash"] else None

    # ── face_portraits table ──────────────────────────────────────

    async def find_faces_by_photo(self, photo_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT * FROM face_portraits WHERE photo_id = ? ORDER BY face_index ASC",
            (photo_id,),
        )

    async def save_face(self, face: dict) -> None:
        await self._db.execute(
            "INSERT INTO face_portraits (face_id, photo_id, face_index, crop_path, "
            "bbox_x, bbox_y, bbox_width, bbox_height, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                face["face_id"], face["photo_id"], face["face_index"],
                face["crop_path"], face["bbox_x"], face["bbox_y"],
                face["bbox_width"], face["bbox_height"], face.get("content_hash"),
            ),
        )

    async def delete_faces_by_photo(self, photo_id: str) -> None:
        await self._db.execute(
            "DELETE FROM face_portraits WHERE photo_id = ?", (photo_id,)
        )

    async def update_face_label(self, face_id: str, name: str) -> None:
        await self._db.execute(
            "UPDATE face_portraits SET family_member_name = ? WHERE face_id = ?",
            (name, face_id),
        )

    async def find_face_with_pair(self, face_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT fp.*, p.sibling_pair_id FROM face_portraits fp "
            "JOIN photos p ON fp.photo_id = p.photo_id "
            "WHERE fp.face_id = ?",
            (face_id,),
        )

    async def get_face_content_hashes(self, photo_id: str) -> list[str]:
        rows = await self._db.fetch_all(
            "SELECT content_hash FROM face_portraits WHERE photo_id = ? AND content_hash IS NOT NULL",
            (photo_id,),
        )
        return [r["content_hash"] for r in rows]

    # ── character_mappings table ──────────────────────────────────

    async def find_mappings(self, sibling_pair_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT cm.*, fp.family_member_name, "
            "(SELECT stp.file_path FROM style_transferred_portraits stp "
            " WHERE stp.face_id = cm.face_id ORDER BY stp.generated_at DESC LIMIT 1) "
            "AS style_transferred_path "
            "FROM character_mappings cm "
            "LEFT JOIN face_portraits fp ON cm.face_id = fp.face_id "
            "WHERE cm.sibling_pair_id = ? "
            "ORDER BY cm.created_at ASC",
            (sibling_pair_id,),
        )

    async def find_mappings_by_face(self, face_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT mapping_id, character_role FROM character_mappings WHERE face_id = ?",
            (face_id,),
        )

    async def save_mapping(self, mapping: dict) -> None:
        await self._db.execute(
            "INSERT INTO character_mappings (mapping_id, sibling_pair_id, character_role, face_id, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                mapping["mapping_id"], mapping["sibling_pair_id"],
                mapping["character_role"], mapping["face_id"], mapping["created_at"],
            ),
        )

    async def delete_mapping(self, sibling_pair_id: str, character_role: str) -> None:
        await self._db.execute(
            "DELETE FROM character_mappings WHERE sibling_pair_id = ? AND character_role = ?",
            (sibling_pair_id, character_role),
        )

    async def nullify_face_in_mappings(self, face_id: str) -> None:
        await self._db.execute(
            "UPDATE character_mappings SET face_id = NULL WHERE face_id = ?",
            (face_id,),
        )

    async def find_face_family_name(self, face_id: str) -> str | None:
        row = await self._db.fetch_one(
            "SELECT family_member_name FROM face_portraits WHERE face_id = ?",
            (face_id,),
        )
        return row["family_member_name"] if row else None

    async def find_latest_style_portrait(self, face_id: str) -> dict | None:
        return await self._db.fetch_one(
            "SELECT file_path FROM style_transferred_portraits WHERE face_id = ? "
            "ORDER BY generated_at DESC LIMIT 1",
            (face_id,),
        )

    # ── style_transferred_portraits ───────────────────────────────

    async def find_style_portraits_by_face(self, face_id: str) -> list[dict]:
        return await self._db.fetch_all(
            "SELECT file_path FROM style_transferred_portraits WHERE face_id = ?",
            (face_id,),
        )

    async def delete_style_portraits_by_face(self, face_id: str) -> None:
        await self._db.execute(
            "DELETE FROM style_transferred_portraits WHERE face_id = ?",
            (face_id,),
        )

    # ── aggregates ────────────────────────────────────────────────

    async def get_storage_stats(self, sibling_pair_id: str) -> dict:
        photo_row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt, COALESCE(SUM(file_size_bytes), 0) AS total "
            "FROM photos WHERE sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        photo_count = photo_row["cnt"] if photo_row else 0
        total_size = photo_row["total"] if photo_row else 0

        face_row = await self._db.fetch_one(
            "SELECT COUNT(*) AS cnt FROM face_portraits fp "
            "JOIN photos p ON fp.photo_id = p.photo_id "
            "WHERE p.sibling_pair_id = ?",
            (sibling_pair_id,),
        )
        face_count = face_row["cnt"] if face_row else 0

        return {
            "photo_count": photo_count,
            "face_count": face_count,
            "total_size_bytes": total_size,
        }
