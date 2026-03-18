"""Photo lifecycle service for Family Photo Integration.

Coordinates upload, validation, resize, content scanning, face extraction,
storage, and CRUD operations for family photos. All state is persisted via
the DatabaseConnection abstraction and the local file system.

Requirements: 1.3–1.6, 2.2–2.4, 3.3–3.4, 4.2, 4.6, 7.3–7.5, 8.1–8.3
"""

from __future__ import annotations

import io
import logging
import os
import shutil
from datetime import datetime, timezone
from uuid import uuid4

from PIL import Image

from app.db.connection import DatabaseConnection
from app.models.photo import (
    CharacterMapping,
    CharacterMappingInput,
    DeleteResult,
    FacePortraitRecord,
    FamilyMember,
    PhotoRecord,
    PhotoStatus,
    PhotoUploadResult,
    StorageStats,
)
from app.services.cache_models import compute_content_hash
from app.services.content_scanner import ContentScanner, ImageSafetyRating
from app.services.face_extractor import FaceExtractor, NoFacesFoundError

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
JPEG_MAGIC = b"\xff\xd8\xff"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


class ValidationError(Exception):
    """Raised when image validation fails (format or size)."""
    pass


class PhotoNotFoundError(Exception):
    """Raised when a photo record cannot be found."""
    pass


class PhotoService:
    """Central service coordinating the photo lifecycle.

    Stateless — all persistent state lives in the database and file system.
    """

    def __init__(
        self,
        db: DatabaseConnection,
        content_scanner: ContentScanner,
        face_extractor: FaceExtractor,
        storage_root: str = "photo_storage",
        cache_manager: "CacheManager | None" = None,
    ) -> None:
        self._db = db
        self._scanner = content_scanner
        self._extractor = face_extractor
        self._storage_root = storage_root
        self._cache_manager = cache_manager
        os.makedirs(self._storage_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Validation & resize
    # ------------------------------------------------------------------

    def validate_image(self, image_bytes: bytes, filename: str) -> None:
        """Check format (JPEG/PNG) and size (≤10 MB). Raises ValidationError."""
        # Check size first
        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValidationError("Photo must be under 10 MB")

        # Check extension
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError("Please upload a JPEG or PNG photo")

        # Check magic bytes match the claimed extension
        if ext in (".jpg", ".jpeg"):
            if not image_bytes[:3] == JPEG_MAGIC:
                raise ValidationError("Please upload a JPEG or PNG photo")
        elif ext == ".png":
            if not image_bytes[:8] == PNG_MAGIC:
                raise ValidationError("Please upload a JPEG or PNG photo")

    def resize_image(self, image_bytes: bytes, max_dimension: int = 1024) -> bytes:
        """Resize preserving aspect ratio so longest side ≤ max_dimension.

        Returns JPEG bytes. Images already within bounds are re-encoded
        without up-scaling.
        """
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size

        if max(w, h) > max_dimension:
            if w >= h:
                new_w = max_dimension
                new_h = max(1, round(h * max_dimension / w))
            else:
                new_h = max_dimension
                new_w = max(1, round(w * max_dimension / h))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Upload pipeline
    # ------------------------------------------------------------------

    async def upload_photo(
        self, sibling_pair_id: str, image_bytes: bytes, filename: str
    ) -> PhotoUploadResult:
        """Full pipeline: validate → resize → content scan → face extract → store."""
        # 1. Validate
        self.validate_image(image_bytes, filename)

        # 2. Resize
        resized_bytes = self.resize_image(image_bytes)

        # 2b. Compute content hash of resized image (for caching)
        content_hash = compute_content_hash(resized_bytes)

        # 3. Content scan
        scan_result = await self._scanner.scan_image(resized_bytes)

        # BLOCKED — don't store anything
        if scan_result.rating == ImageSafetyRating.BLOCKED:
            return PhotoUploadResult(
                photo_id="",
                status=PhotoStatus.BLOCKED,
                faces=[],
                message="This photo can't be used. Please try a different one.",
            )

        # 4. Determine dimensions of resized image
        img = Image.open(io.BytesIO(resized_bytes))
        width, height = img.size

        # 5. Generate IDs and store file
        photo_id = str(uuid4())
        pair_dir = os.path.join(self._storage_root, sibling_pair_id)
        originals_dir = os.path.join(pair_dir, "originals")
        os.makedirs(originals_dir, exist_ok=True)

        file_path = os.path.join(originals_dir, f"{photo_id}.jpg")
        with open(file_path, "wb") as f:
            f.write(resized_bytes)

        file_size = len(resized_bytes)
        now = datetime.now(timezone.utc).isoformat()

        status = (
            PhotoStatus.REVIEW
            if scan_result.rating == ImageSafetyRating.REVIEW
            else PhotoStatus.SAFE
        )

        # 6. Insert photo record
        await self._db.execute(
            "INSERT INTO photos (photo_id, sibling_pair_id, filename, file_path, "
            "file_size_bytes, width, height, status, uploaded_at, content_hash) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (photo_id, sibling_pair_id, filename, file_path, file_size, width, height, status.value, now, content_hash),
        )

        # 7. Face extraction (only for SAFE images)
        faces: list[FacePortraitRecord] = []
        message = "Photo uploaded successfully!"

        if status == PhotoStatus.SAFE:
            faces, message = await self._extract_and_store_faces(
                photo_id, sibling_pair_id, resized_bytes, content_hash
            )
        elif status == PhotoStatus.REVIEW:
            message = "Photo uploaded and pending parent review."

        return PhotoUploadResult(
            photo_id=photo_id,
            status=status,
            faces=faces,
            message=message,
        )

    async def _extract_and_store_faces(
        self, photo_id: str, sibling_pair_id: str, image_bytes: bytes, content_hash: str | None = None
    ) -> tuple[list[FacePortraitRecord], str]:
        """Run face extraction and persist face crops. Returns (faces, message)."""
        faces_dir = os.path.join(self._storage_root, sibling_pair_id, "faces")
        os.makedirs(faces_dir, exist_ok=True)

        try:
            extracted = self._extractor.extract_faces(image_bytes, content_hash=content_hash)
        except NoFacesFoundError:
            return [], "No faces found — try a clearer photo!"
        except Exception as exc:
            logger.error("Face extraction failed for photo %s: %s", photo_id, exc)
            return [], "Photo saved, but face detection encountered an issue."

        records: list[FacePortraitRecord] = []
        for face in extracted:
            face_id = str(uuid4())
            crop_path = os.path.join(faces_dir, f"{face_id}.jpg")
            with open(crop_path, "wb") as f:
                f.write(face.crop_bytes)

            # Compute per-face content hash
            face_content_hash = compute_content_hash(face.crop_bytes)

            await self._db.execute(
                "INSERT INTO face_portraits (face_id, photo_id, face_index, crop_path, "
                "bbox_x, bbox_y, bbox_width, bbox_height, content_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    face_id, photo_id, face.face_index, crop_path,
                    face.bbox.x, face.bbox.y, face.bbox.width, face.bbox.height,
                    face_content_hash,
                ),
            )
            records.append(
                FacePortraitRecord(
                    face_id=face_id,
                    photo_id=photo_id,
                    face_index=face.face_index,
                    crop_path=crop_path,
                    bbox_x=face.bbox.x,
                    bbox_y=face.bbox.y,
                    bbox_width=face.bbox.width,
                    bbox_height=face.bbox.height,
                )
            )

        message = (
            f"Photo uploaded with {len(records)} face(s) detected!"
            if records
            else "Photo uploaded successfully!"
        )
        return records, message

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_photos(self, sibling_pair_id: str) -> list[PhotoRecord]:
        """List all photos for a sibling pair, ordered by upload date."""
        rows = await self._db.fetch_all(
            "SELECT * FROM photos WHERE sibling_pair_id = ? ORDER BY uploaded_at ASC",
            (sibling_pair_id,),
        )
        photos: list[PhotoRecord] = []
        for row in rows:
            faces = await self._get_faces_for_photo(row["photo_id"])
            photos.append(
                PhotoRecord(
                    photo_id=row["photo_id"],
                    sibling_pair_id=row["sibling_pair_id"],
                    filename=row["filename"],
                    file_path=row["file_path"],
                    file_size_bytes=row["file_size_bytes"],
                    width=row["width"],
                    height=row["height"],
                    status=PhotoStatus(row["status"]),
                    uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
                    faces=faces,
                )
            )
        return photos

    async def get_photo(self, photo_id: str) -> PhotoRecord | None:
        """Retrieve a single photo record with face portraits."""
        row = await self._db.fetch_one(
            "SELECT * FROM photos WHERE photo_id = ?", (photo_id,)
        )
        if not row:
            return None

        faces = await self._get_faces_for_photo(photo_id)
        return PhotoRecord(
            photo_id=row["photo_id"],
            sibling_pair_id=row["sibling_pair_id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_size_bytes=row["file_size_bytes"],
            width=row["width"],
            height=row["height"],
            status=PhotoStatus(row["status"]),
            uploaded_at=datetime.fromisoformat(row["uploaded_at"]),
            faces=faces,
        )

    async def _get_faces_for_photo(self, photo_id: str) -> list[FacePortraitRecord]:
        """Load all face portrait records for a given photo."""
        rows = await self._db.fetch_all(
            "SELECT * FROM face_portraits WHERE photo_id = ? ORDER BY face_index ASC",
            (photo_id,),
        )
        return [
            FacePortraitRecord(
                face_id=r["face_id"],
                photo_id=r["photo_id"],
                face_index=r["face_index"],
                crop_path=r["crop_path"],
                bbox_x=r["bbox_x"],
                bbox_y=r["bbox_y"],
                bbox_width=r["bbox_width"],
                bbox_height=r["bbox_height"],
                family_member_name=r["family_member_name"],
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Delete (cascade)
    # ------------------------------------------------------------------

    async def delete_photo(self, photo_id: str) -> DeleteResult:
        """Cascade delete: photo + faces + style-transferred portraits + invalidate mappings."""
        photo = await self.get_photo(photo_id)
        if not photo:
            raise PhotoNotFoundError("Photo not found")

        face_ids = [f.face_id for f in photo.faces]

        # Cache invalidation: evict face crop and style transfer cache entries
        if self._cache_manager is not None:
            photo_content_hash = await self._get_photo_content_hash(photo_id)
            face_content_hashes = await self._get_face_content_hashes(photo_id)
            if photo_content_hash:
                await self._cache_manager.invalidate_photo(
                    photo_content_hash, face_content_hashes
                )

        # Find character mappings that reference these faces
        affected_roles: list[str] = []
        invalidated_count = 0
        for face_id in face_ids:
            mapping_rows = await self._db.fetch_all(
                "SELECT mapping_id, character_role FROM character_mappings WHERE face_id = ?",
                (face_id,),
            )
            for mr in mapping_rows:
                affected_roles.append(mr["character_role"])
                invalidated_count += 1

        # Delete style-transferred portraits for these faces
        for face_id in face_ids:
            # Get file paths to clean up
            portrait_rows = await self._db.fetch_all(
                "SELECT file_path FROM style_transferred_portraits WHERE face_id = ?",
                (face_id,),
            )
            for pr in portrait_rows:
                self._safe_delete_file(pr["file_path"])
            await self._db.execute(
                "DELETE FROM style_transferred_portraits WHERE face_id = ?",
                (face_id,),
            )

        # Invalidate character mappings (set face_id to NULL via ON DELETE SET NULL
        # is handled by cascade, but we do it explicitly for clarity)
        for face_id in face_ids:
            await self._db.execute(
                "UPDATE character_mappings SET face_id = NULL WHERE face_id = ?",
                (face_id,),
            )

        # Delete face portrait files
        for face in photo.faces:
            self._safe_delete_file(face.crop_path)

        # Delete face portrait records (CASCADE would handle this, but explicit)
        await self._db.execute(
            "DELETE FROM face_portraits WHERE photo_id = ?", (photo_id,)
        )

        # Delete photo file
        self._safe_delete_file(photo.file_path)

        # Delete photo record
        await self._db.execute(
            "DELETE FROM photos WHERE photo_id = ?", (photo_id,)
        )

        return DeleteResult(
            deleted_photo_id=photo_id,
            deleted_face_count=len(face_ids),
            invalidated_mapping_count=invalidated_count,
            affected_character_roles=affected_roles,
        )

    # ------------------------------------------------------------------
    # Approve (REVIEW → SAFE)
    # ------------------------------------------------------------------

    async def approve_photo(self, photo_id: str) -> PhotoRecord:
        """Parent approves a REVIEW photo: status → SAFE, then run face extraction."""
        photo = await self.get_photo(photo_id)
        if not photo:
            raise PhotoNotFoundError("Photo not found")

        if photo.status != PhotoStatus.REVIEW:
            raise ValidationError(
                f"Only photos with status 'review' can be approved (current: {photo.status.value})"
            )

        # Update status to SAFE
        await self._db.execute(
            "UPDATE photos SET status = ? WHERE photo_id = ?",
            (PhotoStatus.SAFE.value, photo_id),
        )

        # Read the stored image and run face extraction
        if os.path.exists(photo.file_path):
            with open(photo.file_path, "rb") as f:
                image_bytes = f.read()
            content_hash = await self._get_photo_content_hash(photo_id)
            await self._extract_and_store_faces(
                photo_id, photo.sibling_pair_id, image_bytes, content_hash
            )

        # Return updated record
        updated = await self.get_photo(photo_id)
        assert updated is not None
        return updated

    # ------------------------------------------------------------------
    # Family member labeling
    # ------------------------------------------------------------------

    async def save_family_member(self, face_portrait_id: str, name: str) -> FamilyMember:
        """Label a face portrait with a family member name."""
        row = await self._db.fetch_one(
            "SELECT fp.*, p.sibling_pair_id FROM face_portraits fp "
            "JOIN photos p ON fp.photo_id = p.photo_id "
            "WHERE fp.face_id = ?",
            (face_portrait_id,),
        )
        if not row:
            raise PhotoNotFoundError("Face portrait not found")

        await self._db.execute(
            "UPDATE face_portraits SET family_member_name = ? WHERE face_id = ?",
            (name, face_portrait_id),
        )

        return FamilyMember(
            face_id=face_portrait_id,
            name=name,
            crop_path=row["crop_path"],
            sibling_pair_id=row["sibling_pair_id"],
        )

    # ------------------------------------------------------------------
    # Character mappings
    # ------------------------------------------------------------------

    async def save_character_mapping(
        self, sibling_pair_id: str, mappings: list[CharacterMappingInput]
    ) -> list[CharacterMapping]:
        """Persist character-to-family-member assignments (upsert)."""
        results: list[CharacterMapping] = []
        now = datetime.now(timezone.utc).isoformat()

        for m in mappings:
            mapping_id = str(uuid4())

            # Upsert: delete existing mapping for this role, then insert
            await self._db.execute(
                "DELETE FROM character_mappings WHERE sibling_pair_id = ? AND character_role = ?",
                (sibling_pair_id, m.character_role),
            )
            await self._db.execute(
                "INSERT INTO character_mappings (mapping_id, sibling_pair_id, character_role, face_id, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (mapping_id, sibling_pair_id, m.character_role, m.face_id, now),
            )

            # Look up family member name if face_id is set
            family_member_name: str | None = None
            if m.face_id:
                face_row = await self._db.fetch_one(
                    "SELECT family_member_name FROM face_portraits WHERE face_id = ?",
                    (m.face_id,),
                )
                if face_row:
                    family_member_name = face_row["family_member_name"]

            # Look up style transferred path
            style_row = await self._db.fetch_one(
                "SELECT file_path FROM style_transferred_portraits WHERE face_id = ? "
                "ORDER BY generated_at DESC LIMIT 1",
                (m.face_id,),
            ) if m.face_id else None

            results.append(
                CharacterMapping(
                    mapping_id=mapping_id,
                    sibling_pair_id=sibling_pair_id,
                    character_role=m.character_role,
                    face_id=m.face_id,
                    family_member_name=family_member_name,
                    style_transferred_path=style_row["file_path"] if style_row else None,
                    created_at=datetime.fromisoformat(now),
                )
            )

        return results

    async def get_character_mappings(self, sibling_pair_id: str) -> list[CharacterMapping]:
        """Load all character mappings for a sibling pair."""
        rows = await self._db.fetch_all(
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
        return [
            CharacterMapping(
                mapping_id=r["mapping_id"],
                sibling_pair_id=r["sibling_pair_id"],
                character_role=r["character_role"],
                face_id=r["face_id"],
                family_member_name=r["family_member_name"],
                style_transferred_path=r["style_transferred_path"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Storage stats
    # ------------------------------------------------------------------

    async def get_storage_stats(self, sibling_pair_id: str) -> StorageStats:
        """Return photo count, face count, and total storage usage."""
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

        return StorageStats(
            photo_count=photo_count,
            face_count=face_count,
            total_size_bytes=total_size,
        )

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    async def _get_photo_content_hash(self, photo_id: str) -> str | None:
        """Look up the content_hash for a photo from the DB."""
        row = await self._db.fetch_one(
            "SELECT content_hash FROM photos WHERE photo_id = ?", (photo_id,)
        )
        if row and row["content_hash"]:
            return row["content_hash"]
        return None

    async def _get_face_content_hashes(self, photo_id: str) -> list[str]:
        """Collect content_hash values for all face crops belonging to a photo."""
        rows = await self._db.fetch_all(
            "SELECT content_hash FROM face_portraits WHERE photo_id = ? AND content_hash IS NOT NULL",
            (photo_id,),
        )
        return [r["content_hash"] for r in rows]

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
