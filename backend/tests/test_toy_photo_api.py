"""API integration tests for toy photo endpoints.

Tests POST /api/toy-photo/{sibling_pair_id}/{child_number} and
GET  /api/toy-photo/{sibling_pair_id}/{child_number} — including
response shape, 404 on missing photo, and 422 on invalid child_number.

Requirements: 3.1, 3.2, 3.6
"""

import io
import os
import shutil

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.services.toy_photo_service import ToyPhotoService
import app.main as main_module
from app.main import app

TEST_STORAGE = "test_toy_photo_api_storage"


def _make_jpeg(w: int = 200, h: int = 150) -> bytes:
    img = Image.new("RGB", (w, h), "blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


@pytest_asyncio.fixture
async def patched_service():
    """Create a ToyPhotoService with temp storage and patch into main module."""
    svc = ToyPhotoService(storage_root=TEST_STORAGE)
    original = main_module._toy_photo_service
    main_module._toy_photo_service = svc
    yield svc
    main_module._toy_photo_service = original
    if os.path.exists(TEST_STORAGE):
        shutil.rmtree(TEST_STORAGE)


@pytest_asyncio.fixture
async def client(patched_service):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Upload – correct response shape (Req 3.1)
# ---------------------------------------------------------------------------

class TestUpload:
    @pytest.mark.asyncio
    async def test_upload_returns_correct_shape(self, client):
        resp = await client.post(
            "/api/toy-photo/pair1/1",
            files={"file": ("toy.jpg", _make_jpeg(), "image/jpeg")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["child_number"] == 1
        assert "image_url" in body
        assert "uploaded_at" in body


# ---------------------------------------------------------------------------
# GET – 404 when no photo exists (Req 3.2)
# ---------------------------------------------------------------------------

class TestGetNotFound:
    @pytest.mark.asyncio
    async def test_get_returns_404_when_missing(self, client):
        resp = await client.get("/api/toy-photo/nonexistent/1")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Invalid child_number – 422 (Req 3.6)
# ---------------------------------------------------------------------------

class TestInvalidChildNumber:
    @pytest.mark.asyncio
    async def test_post_invalid_child_number_returns_422(self, client):
        resp = await client.post(
            "/api/toy-photo/pair1/3",
            files={"file": ("toy.jpg", _make_jpeg(), "image/jpeg")},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_invalid_child_number_returns_422(self, client):
        resp = await client.get("/api/toy-photo/pair1/0")
        assert resp.status_code == 422
