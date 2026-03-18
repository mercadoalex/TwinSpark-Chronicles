"""Unit tests for StyleTransferAgent."""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from PIL import Image

from app.agents.style_transfer_agent import StyleTransferAgent, _make_default_avatar
from app.db.connection import DatabaseConnection
from app.db.migration_runner import MigrationRunner
from app.models.photo import CharacterMapping


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_face_jpeg(size: tuple[int, int] = (100, 100)) -> bytes:
    """Create a minimal JPEG image for testing."""
    img = Image.new("RGB", size, color=(200, 150, 100))
    buf = BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_mapping(
    role: str,
    face_id: str | None = None,
    sibling_pair_id: str = "pair-1",
) -> CharacterMapping:
    return CharacterMapping(
        mapping_id=f"map-{role}",
        sibling_pair_id=sibling_pair_id,
        character_role=role,
        face_id=face_id,
        family_member_name=f"Name-{role}" if face_id else None,
        created_at=datetime.now(timezone.utc),
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


@pytest.fixture
def storage_root(tmp_path):
    return str(tmp_path / "photo_storage")


# ---------------------------------------------------------------------------
# Tests — initialisation
# ---------------------------------------------------------------------------

class TestInit:
    def test_disabled_when_no_project_id(self, storage_root):
        with patch.dict(os.environ, {}, clear=True):
            # Remove GOOGLE_PROJECT_ID if present
            os.environ.pop("GOOGLE_PROJECT_ID", None)
            agent = StyleTransferAgent(storage_root=storage_root)
            assert agent._enabled is False
            assert agent._model is None

    def test_enabled_when_project_id_set(self, storage_root):
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)
            assert agent._enabled is True


# ---------------------------------------------------------------------------
# Tests — generate_portrait
# ---------------------------------------------------------------------------

class TestGeneratePortrait:
    @pytest.mark.asyncio
    async def test_returns_none_when_disabled(self, storage_root):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_PROJECT_ID", None)
            agent = StyleTransferAgent(storage_root=storage_root)
            result = await agent.generate_portrait(b"fake", {"role": "hero"})
            assert result is None

    @pytest.mark.asyncio
    async def test_returns_bytes_on_success(self, storage_root):
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        fake_image = MagicMock()
        fake_image._image_bytes = b"png-portrait-bytes"
        mock_response = MagicMock()
        mock_response.images = [fake_image]
        agent._model.generate_images = MagicMock(return_value=mock_response)

        result = await agent.generate_portrait(
            _make_face_jpeg(), {"role": "brave explorer"}
        )
        assert result == b"png-portrait-bytes"

    @pytest.mark.asyncio
    async def test_returns_none_on_empty_response(self, storage_root):
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        mock_response = MagicMock()
        mock_response.images = []
        agent._model.generate_images = MagicMock(return_value=mock_response)

        result = await agent.generate_portrait(
            _make_face_jpeg(), {"role": "sidekick"}
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, storage_root):
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        agent._model.generate_images = MagicMock(
            side_effect=RuntimeError("API down")
        )

        result = await agent.generate_portrait(
            _make_face_jpeg(), {"role": "villain"}
        )
        assert result is None


# ---------------------------------------------------------------------------
# Tests — generate_portraits_for_session
# ---------------------------------------------------------------------------

class TestGeneratePortraitsForSession:
    async def _seed_face(self, db, face_id, crop_path, photo_id="photo-1"):
        """Insert a photo + face row so the agent can look it up."""
        await db.execute(
            "INSERT OR IGNORE INTO photos "
            "(photo_id, sibling_pair_id, filename, file_path, "
            "file_size_bytes, width, height, status, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (photo_id, "pair-1", "f.jpg", "/tmp/f.jpg",
             1000, 100, 100, "safe",
             datetime.now(timezone.utc).isoformat()),
        )
        await db.execute(
            "INSERT INTO face_portraits "
            "(face_id, photo_id, face_index, crop_path, "
            "bbox_x, bbox_y, bbox_width, bbox_height) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (face_id, photo_id, 0, crop_path, 0.1, 0.1, 0.3, 0.3),
        )

    @pytest.mark.asyncio
    async def test_unmapped_roles_get_default_avatar(self, db, storage_root):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_PROJECT_ID", None)
            agent = StyleTransferAgent(storage_root=storage_root)

        mappings = [_make_mapping("wise guide", face_id=None)]
        result = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )

        assert "wise guide" in result
        # Should be valid base64
        decoded = base64.b64decode(result["wise guide"])
        img = Image.open(BytesIO(decoded))
        assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_fallback_on_missing_face_crop(self, db, storage_root):
        """When face crop file doesn't exist on disk, fall back to default."""
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("GOOGLE_PROJECT_ID", None)
            agent = StyleTransferAgent(storage_root=storage_root)

        await self._seed_face(db, "face-1", "/nonexistent/crop.jpg")
        mappings = [_make_mapping("hero", face_id="face-1")]

        result = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )
        assert "hero" in result
        # Should be the default avatar (decodable PNG)
        decoded = base64.b64decode(result["hero"])
        img = Image.open(BytesIO(decoded))
        assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_caches_and_reuses_portrait(self, db, storage_root):
        """Second call for same face+session should hit cache."""
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        # Write a real face crop file
        crop_dir = os.path.join(storage_root, "pair-1", "faces")
        os.makedirs(crop_dir, exist_ok=True)
        crop_path = os.path.join(crop_dir, "face-1.jpg")
        with open(crop_path, "wb") as f:
            f.write(_make_face_jpeg())

        await self._seed_face(db, "face-1", crop_path)

        # Mock Imagen to return portrait bytes
        fake_image = MagicMock()
        fake_image._image_bytes = b"portrait-png-data"
        mock_response = MagicMock()
        mock_response.images = [fake_image]
        agent._model.generate_images = MagicMock(return_value=mock_response)

        mappings = [_make_mapping("hero", face_id="face-1")]

        # First call — generates
        r1 = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )
        assert agent._model.generate_images.call_count == 1

        # Second call — should use cache, no new generation
        r2 = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )
        assert agent._model.generate_images.call_count == 1
        assert r1["hero"] == r2["hero"]

    @pytest.mark.asyncio
    async def test_fallback_when_generation_fails(self, db, storage_root):
        """When Imagen fails, the role should still get a default avatar."""
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        crop_dir = os.path.join(storage_root, "pair-1", "faces")
        os.makedirs(crop_dir, exist_ok=True)
        crop_path = os.path.join(crop_dir, "face-2.jpg")
        with open(crop_path, "wb") as f:
            f.write(_make_face_jpeg())

        await self._seed_face(db, "face-2", crop_path, photo_id="photo-2")

        # Make generate_images raise
        agent._model.generate_images = MagicMock(
            side_effect=RuntimeError("quota exceeded")
        )

        mappings = [_make_mapping("explorer", face_id="face-2")]
        result = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )

        assert "explorer" in result
        decoded = base64.b64decode(result["explorer"])
        img = Image.open(BytesIO(decoded))
        assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_multiple_mappings_mixed(self, db, storage_root):
        """Mix of mapped and unmapped roles returns correct count."""
        with patch.dict(os.environ, {"GOOGLE_PROJECT_ID": "test-project"}):
            agent = StyleTransferAgent(storage_root=storage_root)

        crop_dir = os.path.join(storage_root, "pair-1", "faces")
        os.makedirs(crop_dir, exist_ok=True)
        crop_path = os.path.join(crop_dir, "face-3.jpg")
        with open(crop_path, "wb") as f:
            f.write(_make_face_jpeg())

        await self._seed_face(db, "face-3", crop_path, photo_id="photo-3")

        fake_image = MagicMock()
        fake_image._image_bytes = b"portrait-data"
        mock_response = MagicMock()
        mock_response.images = [fake_image]
        agent._model.generate_images = MagicMock(return_value=mock_response)

        mappings = [
            _make_mapping("hero", face_id="face-3"),
            _make_mapping("guide", face_id=None),
            _make_mapping("villain", face_id=None),
        ]

        result = await agent.generate_portraits_for_session(
            "pair-1", "sess-1", mappings, db
        )

        assert len(result) == 3
        assert all(role in result for role in ["hero", "guide", "villain"])
        # Only 1 call to Imagen (for the mapped face)
        assert agent._model.generate_images.call_count == 1


class TestDefaultAvatar:
    def test_default_avatar_is_valid_png(self):
        data = _make_default_avatar()
        img = Image.open(BytesIO(data))
        assert img.format == "PNG"
        assert img.size == (256, 256)
