"""Unit tests for ToyPhotoService.

Covers validation (JPEG/PNG accept, GIF reject, >10 MB reject),
resize (≤512px longest side, aspect ratio preserved),
upload/get round-trip, re-upload replacement, and delete.

Requirements: 2.6, 3.3, 3.4, 3.5, 3.6
"""

import io
import os

import pytest
import pytest_asyncio
from PIL import Image

from app.services.toy_photo_service import ToyPhotoService
from app.services.photo_service import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jpeg(w: int = 200, h: int = 150) -> bytes:
    img = Image.new("RGB", (w, h), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png(w: int = 200, h: int = 150) -> bytes:
    img = Image.new("RGB", (w, h), "red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def svc(tmp_path):
    return ToyPhotoService(storage_root=str(tmp_path / "toy_photos"))


# ---------------------------------------------------------------------------
# validate_image
# ---------------------------------------------------------------------------

class TestValidateImage:
    def test_accepts_jpeg(self, svc):
        svc.validate_image(_make_jpeg(), "toy.jpg")

    def test_accepts_png(self, svc):
        svc.validate_image(_make_png(), "toy.png")

    def test_rejects_gif(self, svc):
        with pytest.raises(ValidationError, match="JPEG or PNG"):
            svc.validate_image(_make_jpeg(), "toy.gif")

    def test_rejects_over_10mb(self, svc):
        big = b"\xff\xd8\xff" + b"\x00" * (10 * 1024 * 1024 + 1)
        with pytest.raises(ValidationError, match="10 MB"):
            svc.validate_image(big, "big.jpg")


# ---------------------------------------------------------------------------
# resize_image
# ---------------------------------------------------------------------------

class TestResizeImage:
    def test_longest_side_at_most_512(self, svc):
        result = svc.resize_image(_make_jpeg(1000, 800))
        img = Image.open(io.BytesIO(result))
        assert max(img.size) <= 512

    def test_preserves_aspect_ratio(self, svc):
        result = svc.resize_image(_make_jpeg(1000, 500))
        img = Image.open(io.BytesIO(result))
        assert abs(img.size[0] / img.size[1] - 2.0) < 0.02

    def test_small_image_not_upscaled(self, svc):
        result = svc.resize_image(_make_jpeg(100, 80))
        img = Image.open(io.BytesIO(result))
        assert img.size == (100, 80)


# ---------------------------------------------------------------------------
# upload / get round-trip
# ---------------------------------------------------------------------------

class TestUploadAndGet:
    @pytest.mark.asyncio
    async def test_upload_stores_and_get_returns_metadata(self, svc):
        res = await svc.upload_toy_photo("pair1", 1, _make_jpeg(), "bear.jpg")
        assert res.child_number == 1
        assert res.image_url != ""

        meta = await svc.get_toy_photo("pair1", 1)
        assert meta is not None
        assert meta.child_number == 1
        assert meta.original_filename == "bear.jpg"
        assert os.path.exists(meta.file_path)

    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self, svc):
        assert await svc.get_toy_photo("nope", 1) is None


# ---------------------------------------------------------------------------
# re-upload replaces previous
# ---------------------------------------------------------------------------

class TestReupload:
    @pytest.mark.asyncio
    async def test_reupload_replaces_file(self, svc):
        await svc.upload_toy_photo("pair1", 1, _make_jpeg(), "old.jpg")
        await svc.upload_toy_photo("pair1", 1, _make_png(), "new.png")

        meta = await svc.get_toy_photo("pair1", 1)
        assert meta.original_filename == "new.png"


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_delete_removes_files(self, svc):
        await svc.upload_toy_photo("pair1", 1, _make_jpeg(), "del.jpg")
        deleted = await svc.delete_toy_photo("pair1", 1)
        assert deleted is True
        assert await svc.get_toy_photo("pair1", 1) is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, svc):
        assert await svc.delete_toy_photo("nope", 1) is False
