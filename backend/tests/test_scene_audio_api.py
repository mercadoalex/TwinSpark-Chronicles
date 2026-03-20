"""API integration tests for the scene-theme endpoint.

Uses httpx AsyncClient with ASGITransport to verify 200/422 responses
and response shape.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestSceneThemeEndpoint:
    @pytest.mark.asyncio
    async def test_valid_description_returns_200(self, client):
        resp = await client.post(
            "/api/audio/scene-theme",
            json={"scene_description": "A dark crystal cave with echoing tunnels"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["theme"] == "cave"
        assert data["ambient_track"] == "/audio/ambient/cave.mp3"

    @pytest.mark.asyncio
    async def test_response_shape_matches_audio_theme_result(self, client):
        resp = await client.post(
            "/api/audio/scene-theme",
            json={"scene_description": "The twins sailed across the ocean"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "theme" in data
        assert "ambient_track" in data
        assert "sound_effects" in data
        assert isinstance(data["theme"], str)
        assert isinstance(data["ambient_track"], str)
        assert isinstance(data["sound_effects"], list)

    @pytest.mark.asyncio
    async def test_empty_string_returns_422(self, client):
        resp = await client.post(
            "/api/audio/scene-theme",
            json={"scene_description": ""},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_field_returns_422(self, client):
        resp = await client.post(
            "/api/audio/scene-theme",
            json={},
        )
        assert resp.status_code == 422
