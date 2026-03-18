"""Unit tests for PhotoService.

Covers validation, resize, upload pipeline (SAFE/REVIEW/BLOCKED),
CRUD operations, cascade delete, approve flow, family member labeling,
character mappings, and storage stats.
"""

import io
import os
import shutil
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from PIL import Image

from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.models.multimodal import FaceBBox
from app.models.photo import (
    CharacterMappingInput,
    PhotoStatus,
)
from app.services.content_scanner import ImageSafetyRating, ImageScanResult
from app.services.face_extractor import ExtractedFace, NoFacesFoundError
from app.services.photo_service import PhotoService, ValidationError, PhotoNotFoundError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_STORAGE = "test_photo_storage"


def _make_jpeg_bytes(width: int = 200, height: int = 150) -> bytes:
    """Create minimal valid JPEG bytes."""
    img = Image.new("RGB", (width, height), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes(width: int = 200, height: int = 150) -> bytes:
    """Create minimal valid PNG bytes."""
    img = Image.new("RGB", (width, height), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_extracted_face(index: int = 0) -> ExtractedFace:
    """Create a mock ExtractedFace."""
    crop = _make_jpeg_bytes(80, 80)
    return ExtractedFace(
        face_index=index,
        crop_bytes=crop,
        bbox=FaceBBox(x=0.2, y=0.2, width=0.3, height=0.4, confidence=0.95),
        crop_width=80,
        crop_height=80,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db():
    conn = DatabaseConnection("sqlite:///:memory:")
    await conn.connect()
    runner = MigrationRunner(conn)
    await runner.apply_all()
    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def photo_service(db):
    scanner = MagicMock()
    scanner.scan_image = AsyncMock(
        return_value=ImageScanResult(rating=ImageSafetyRating.SAFE, reason="OK")
    )
    extractor = MagicMock()
    extractor.extract_faces = MagicMock(return_value=[_make_extracted_face(0)])

    svc = PhotoService(db, scanner, extractor, storage_root=TEST_STORAGE)
    yield svc

    # Cleanup test storage
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------

class TestValidateImage:
    def test_valid_jpeg(self, photo_service):
        data = _make_jpeg_bytes()
        photo_service.validate_image(data, "family.jpg")  # no error

    def test_valid_png(self, photo_service):
        data = _make_png_bytes()
        photo_service.validate_image(data, "family.png")  # no error

    def test_rejects_too_large(self, photo_service):
        data = b"\xff\xd8\xff" + b"\x00" * (10 * 1024 * 1024 + 1)
        with pytest.raises(ValidationError, match="under 10 MB"):
            photo_service.validate_image(data, "big.jpg")

    def test_rejects_invalid_extension(self, photo_service):
        data = _make_jpeg_bytes()
        with pytest.raises(ValidationError, match="JPEG or PNG"):
            photo_service.validate_image(data, "photo.gif")

    def test_rejects_mismatched_magic_bytes(self, photo_service):
        png_data = _make_png_bytes()
        with pytest.raises(ValidationError, match="JPEG or PNG"):
            photo_service.validate_image(png_data, "photo.jpg")

    def test_exactly_10mb_is_accepted(self, photo_service):
        """Boundary: exactly 10 MB should pass."""
        data = _make_jpeg_bytes()
        # Pad to exactly 10 MB (the JPEG header is valid)
        padded = data + b"\x00" * (10 * 1024 * 1024 - len(data))
        photo_service.validate_image(padded, "exact.jpg")


# ---------------------------------------------------------------------------
# Resize tests
# ---------------------------------------------------------------------------

class TestResizeImage:
    def test_large_image_resized(self, photo_service):
        data = _make_jpeg_bytes(2000, 1500)
        result = photo_service.resize_image(data)
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 1024
        # Aspect ratio preserved
        assert abs(img.size[0] / img.size[1] - 2000 / 1500) < 0.02

    def test_small_image_not_upscaled(self, photo_service):
        data = _make_jpeg_bytes(500, 300)
        result = photo_service.resize_image(data)
        img = Image.open(io.BytesIO(result))
        assert img.size == (500, 300)

    def test_returns_jpeg(self, photo_service):
        data = _make_png_bytes(800, 600)
        result = photo_service.resize_image(data)
        assert result[:3] == b"\xff\xd8\xff"  # JPEG magic


# ---------------------------------------------------------------------------
# Upload pipeline tests
# ---------------------------------------------------------------------------

class TestUploadPhoto:
    @pytest.mark.asyncio
    async def test_safe_upload_stores_photo_and_faces(self, photo_service):
        data = _make_jpeg_bytes()
        result = await photo_service.upload_photo("pair1", data, "family.jpg")

        assert result.status == PhotoStatus.SAFE
        assert result.photo_id != ""
        assert len(result.faces) == 1

        # Verify persisted
        photo = await photo_service.get_photo(result.photo_id)
        assert photo is not None
        assert photo.sibling_pair_id == "pair1"
        assert len(photo.faces) == 1

    @pytest.mark.asyncio
    async def test_blocked_upload_stores_nothing(self, photo_service):
        photo_service._scanner.scan_image = AsyncMock(
            return_value=ImageScanResult(rating=ImageSafetyRating.BLOCKED, reason="unsafe")
        )
        data = _make_jpeg_bytes()
        result = await photo_service.upload_photo("pair1", data, "bad.jpg")

        assert result.status == PhotoStatus.BLOCKED
        assert result.photo_id == ""
        assert len(result.faces) == 0

        # Nothing in DB
        photos = await photo_service.get_photos("pair1")
        assert len(photos) == 0

    @pytest.mark.asyncio
    async def test_review_upload_stores_without_faces(self, photo_service):
        photo_service._scanner.scan_image = AsyncMock(
            return_value=ImageScanResult(rating=ImageSafetyRating.REVIEW, reason="needs review")
        )
        data = _make_jpeg_bytes()
        result = await photo_service.upload_photo("pair1", data, "maybe.jpg")

        assert result.status == PhotoStatus.REVIEW
        assert result.photo_id != ""
        assert len(result.faces) == 0

        photo = await photo_service.get_photo(result.photo_id)
        assert photo is not None
        assert photo.status == PhotoStatus.REVIEW

    @pytest.mark.asyncio
    async def test_no_faces_found_still_stores_photo(self, photo_service):
        photo_service._extractor.extract_faces = MagicMock(
            side_effect=NoFacesFoundError("No faces")
        )
        data = _make_jpeg_bytes()
        result = await photo_service.upload_photo("pair1", data, "noface.jpg")

        assert result.status == PhotoStatus.SAFE
        assert result.photo_id != ""
        assert len(result.faces) == 0
        assert "No faces found" in result.message


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------

class TestGetPhotos:
    @pytest.mark.asyncio
    async def test_empty_list(self, photo_service):
        photos = await photo_service.get_photos("nonexistent")
        assert photos == []

    @pytest.mark.asyncio
    async def test_returns_photos_for_pair(self, photo_service):
        data = _make_jpeg_bytes()
        await photo_service.upload_photo("pair1", data, "a.jpg")
        await photo_service.upload_photo("pair1", data, "b.jpg")
        await photo_service.upload_photo("pair2", data, "c.jpg")

        pair1_photos = await photo_service.get_photos("pair1")
        assert len(pair1_photos) == 2

        pair2_photos = await photo_service.get_photos("pair2")
        assert len(pair2_photos) == 1


class TestDeletePhoto:
    @pytest.mark.asyncio
    async def test_cascade_delete(self, photo_service):
        data = _make_jpeg_bytes()
        result = await photo_service.upload_photo("pair1", data, "del.jpg")
        photo_id = result.photo_id

        # Create a character mapping referencing the face
        face_id = result.faces[0].face_id
        await photo_service.save_character_mapping(
            "pair1", [CharacterMappingInput(character_role="hero", face_id=face_id)]
        )

        # Delete
        del_result = await photo_service.delete_photo(photo_id)
        assert del_result.deleted_photo_id == photo_id
        assert del_result.deleted_face_count == 1
        assert del_result.invalidated_mapping_count == 1
        assert "hero" in del_result.affected_character_roles

        # Photo gone
        assert await photo_service.get_photo(photo_id) is None

        # Mapping face_id is NULL
        mappings = await photo_service.get_character_mappings("pair1")
        assert len(mappings) == 1
        assert mappings[0].face_id is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_raises(self, photo_service):
        with pytest.raises(PhotoNotFoundError):
            await photo_service.delete_photo("nonexistent")


# ---------------------------------------------------------------------------
# Approve tests
# ---------------------------------------------------------------------------

class TestApprovePhoto:
    @pytest.mark.asyncio
    async def test_approve_review_photo(self, photo_service):
        photo_service._scanner.scan_image = AsyncMock(
            return_value=ImageScanResult(rating=ImageSafetyRating.REVIEW, reason="review")
        )
        data = _make_jpeg_bytes()
        upload = await photo_service.upload_photo("pair1", data, "review.jpg")

        # Reset scanner for approve flow (not called again)
        photo_service._scanner.scan_image = AsyncMock(
            return_value=ImageScanResult(rating=ImageSafetyRating.SAFE, reason="OK")
        )

        approved = await photo_service.approve_photo(upload.photo_id)
        assert approved.status == PhotoStatus.SAFE
        assert len(approved.faces) == 1  # faces extracted on approval

    @pytest.mark.asyncio
    async def test_approve_safe_photo_raises(self, photo_service):
        data = _make_jpeg_bytes()
        upload = await photo_service.upload_photo("pair1", data, "safe.jpg")

        with pytest.raises(ValidationError, match="review"):
            await photo_service.approve_photo(upload.photo_id)


# ---------------------------------------------------------------------------
# Family member labeling
# ---------------------------------------------------------------------------

class TestSaveFamilyMember:
    @pytest.mark.asyncio
    async def test_label_face(self, photo_service):
        data = _make_jpeg_bytes()
        upload = await photo_service.upload_photo("pair1", data, "fam.jpg")
        face_id = upload.faces[0].face_id

        member = await photo_service.save_family_member(face_id, "Alice")
        assert member.name == "Alice"
        assert member.face_id == face_id
        assert member.sibling_pair_id == "pair1"

        # Verify persisted
        photo = await photo_service.get_photo(upload.photo_id)
        assert photo.faces[0].family_member_name == "Alice"

    @pytest.mark.asyncio
    async def test_label_nonexistent_face_raises(self, photo_service):
        with pytest.raises(PhotoNotFoundError):
            await photo_service.save_family_member("nonexistent", "Bob")


# ---------------------------------------------------------------------------
# Character mappings
# ---------------------------------------------------------------------------

class TestCharacterMappings:
    @pytest.mark.asyncio
    async def test_save_and_load_mappings(self, photo_service):
        data = _make_jpeg_bytes()
        upload = await photo_service.upload_photo("pair1", data, "map.jpg")
        face_id = upload.faces[0].face_id

        mappings = await photo_service.save_character_mapping(
            "pair1",
            [
                CharacterMappingInput(character_role="hero", face_id=face_id),
                CharacterMappingInput(character_role="sidekick", face_id=None),
            ],
        )
        assert len(mappings) == 2
        assert mappings[0].character_role == "hero"
        assert mappings[0].face_id == face_id
        assert mappings[1].face_id is None

        loaded = await photo_service.get_character_mappings("pair1")
        assert len(loaded) == 2

    @pytest.mark.asyncio
    async def test_upsert_replaces_existing(self, photo_service):
        data = _make_jpeg_bytes()
        upload = await photo_service.upload_photo("pair1", data, "up.jpg")
        face_id = upload.faces[0].face_id

        await photo_service.save_character_mapping(
            "pair1", [CharacterMappingInput(character_role="hero", face_id=face_id)]
        )
        await photo_service.save_character_mapping(
            "pair1", [CharacterMappingInput(character_role="hero", face_id=None)]
        )

        loaded = await photo_service.get_character_mappings("pair1")
        assert len(loaded) == 1
        assert loaded[0].face_id is None


# ---------------------------------------------------------------------------
# Storage stats
# ---------------------------------------------------------------------------

class TestStorageStats:
    @pytest.mark.asyncio
    async def test_stats_for_pair(self, photo_service):
        data = _make_jpeg_bytes()
        await photo_service.upload_photo("pair1", data, "s1.jpg")
        await photo_service.upload_photo("pair1", data, "s2.jpg")

        stats = await photo_service.get_storage_stats("pair1")
        assert stats.photo_count == 2
        assert stats.face_count == 2  # 1 face per photo
        assert stats.total_size_bytes > 0

    @pytest.mark.asyncio
    async def test_stats_empty_pair(self, photo_service):
        stats = await photo_service.get_storage_stats("empty_pair")
        assert stats.photo_count == 0
        assert stats.face_count == 0
        assert stats.total_size_bytes == 0
