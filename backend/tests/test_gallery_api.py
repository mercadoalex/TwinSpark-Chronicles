"""API integration tests for the Gallery endpoints (Task 3.2).

Uses httpx AsyncClient with ASGITransport to verify status codes
and response shapes, following the test_scene_audio_api.py pattern.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


VALID_PIN = os.getenv("PARENT_PIN", "1234")


class TestGalleryListEndpoint:
    @pytest.mark.asyncio
    async def test_list_returns_200_with_json_array(self, client):
        resp = await client.get("/api/gallery/unknown-pair")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestGalleryDetailEndpoint:
    @pytest.mark.asyncio
    async def test_detail_returns_404_for_missing_storybook(self, client):
        resp = await client.get("/api/gallery/detail/nonexistent_id")
        assert resp.status_code == 404
        assert "Storybook not found" in resp.json()["detail"]


class TestGalleryDeleteEndpoint:
    @pytest.mark.asyncio
    async def test_delete_returns_401_without_pin(self, client):
        resp = await client.delete("/api/gallery/some_id")
        assert resp.status_code == 401
        assert "Parent PIN required" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_returns_404_for_missing_storybook_with_valid_pin(self, client):
        resp = await client.delete(
            "/api/gallery/nonexistent_id",
            headers={"X-Parent-Pin": VALID_PIN},
        )
        assert resp.status_code == 404
        assert "Storybook not found" in resp.json()["detail"]


class TestGalleryBulkDeleteEndpoint:
    @pytest.mark.asyncio
    async def test_bulk_delete_returns_401_without_pin(self, client):
        resp = await client.delete("/api/gallery/all/some-pair")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_delete_returns_correct_count(self, client):
        resp = await client.delete(
            "/api/gallery/all/unknown-pair",
            headers={"X-Parent-Pin": VALID_PIN},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["deleted_count"] == 0
