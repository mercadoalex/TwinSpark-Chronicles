"""Unit tests for PhotoRepository — verifies SQL delegation to DatabaseConnection."""

import pytest
from unittest.mock import AsyncMock

from app.db.photo_repository import PhotoRepository


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.fetch_one = AsyncMock(return_value=None)
    db.fetch_all = AsyncMock(return_value=[])
    db.execute = AsyncMock()
    return db


@pytest.fixture
def repo(mock_db):
    return PhotoRepository(mock_db)


# ── photos table ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_find_by_id(repo, mock_db):
    mock_db.fetch_one.return_value = {"photo_id": "p1"}
    result = await repo.find_by_id("p1")
    assert result == {"photo_id": "p1"}
    mock_db.fetch_one.assert_called_once()
    sql = mock_db.fetch_one.call_args[0][0]
    assert "photos" in sql and "photo_id = ?" in sql


@pytest.mark.asyncio
async def test_find_all_with_pair(repo, mock_db):
    await repo.find_all(sibling_pair_id="pair1")
    mock_db.fetch_all.assert_called_once()
    sql = mock_db.fetch_all.call_args[0][0]
    assert "sibling_pair_id = ?" in sql
    assert "ORDER BY uploaded_at ASC" in sql


@pytest.mark.asyncio
async def test_find_all_no_filter(repo, mock_db):
    await repo.find_all()
    sql = mock_db.fetch_all.call_args[0][0]
    assert "sibling_pair_id" not in sql


@pytest.mark.asyncio
async def test_save_photo(repo, mock_db):
    photo = {
        "photo_id": "p1", "sibling_pair_id": "pair1", "filename": "test.jpg",
        "file_path": "/tmp/test.jpg", "file_size_bytes": 1024, "width": 100,
        "height": 100, "status": "safe", "uploaded_at": "2025-01-01T00:00:00",
        "content_hash": "abc123",
    }
    await repo.save(photo)
    mock_db.execute.assert_called_once()
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO photos" in sql


@pytest.mark.asyncio
async def test_delete_photo_exists(repo, mock_db):
    mock_db.fetch_one.return_value = {"photo_id": "p1"}
    result = await repo.delete("p1")
    assert result is True
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_delete_photo_not_found(repo, mock_db):
    mock_db.fetch_one.return_value = None
    result = await repo.delete("p1")
    assert result is False
    mock_db.execute.assert_not_called()


@pytest.mark.asyncio
async def test_update_status(repo, mock_db):
    await repo.update_status("p1", "safe")
    sql = mock_db.execute.call_args[0][0]
    assert "UPDATE photos SET status" in sql


@pytest.mark.asyncio
async def test_get_content_hash(repo, mock_db):
    mock_db.fetch_one.return_value = {"content_hash": "abc"}
    result = await repo.get_content_hash("p1")
    assert result == "abc"


@pytest.mark.asyncio
async def test_get_content_hash_none(repo, mock_db):
    mock_db.fetch_one.return_value = None
    result = await repo.get_content_hash("p1")
    assert result is None


# ── face_portraits table ──────────────────────────────────────


@pytest.mark.asyncio
async def test_find_faces_by_photo(repo, mock_db):
    await repo.find_faces_by_photo("p1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "face_portraits" in sql and "photo_id = ?" in sql


@pytest.mark.asyncio
async def test_save_face(repo, mock_db):
    face = {
        "face_id": "f1", "photo_id": "p1", "face_index": 0,
        "crop_path": "/tmp/f1.jpg", "bbox_x": 10, "bbox_y": 20,
        "bbox_width": 50, "bbox_height": 60, "content_hash": "hash1",
    }
    await repo.save_face(face)
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO face_portraits" in sql


@pytest.mark.asyncio
async def test_delete_faces_by_photo(repo, mock_db):
    await repo.delete_faces_by_photo("p1")
    sql = mock_db.execute.call_args[0][0]
    assert "DELETE FROM face_portraits" in sql


@pytest.mark.asyncio
async def test_update_face_label(repo, mock_db):
    await repo.update_face_label("f1", "Mom")
    sql = mock_db.execute.call_args[0][0]
    assert "UPDATE face_portraits SET family_member_name" in sql


@pytest.mark.asyncio
async def test_find_face_with_pair(repo, mock_db):
    await repo.find_face_with_pair("f1")
    sql = mock_db.fetch_one.call_args[0][0]
    assert "JOIN photos" in sql


@pytest.mark.asyncio
async def test_get_face_content_hashes(repo, mock_db):
    mock_db.fetch_all.return_value = [{"content_hash": "h1"}, {"content_hash": "h2"}]
    result = await repo.get_face_content_hashes("p1")
    assert result == ["h1", "h2"]


# ── character_mappings table ──────────────────────────────────


@pytest.mark.asyncio
async def test_find_mappings(repo, mock_db):
    await repo.find_mappings("pair1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "character_mappings" in sql and "sibling_pair_id = ?" in sql


@pytest.mark.asyncio
async def test_find_mappings_by_face(repo, mock_db):
    await repo.find_mappings_by_face("f1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "character_mappings" in sql and "face_id = ?" in sql


@pytest.mark.asyncio
async def test_save_mapping(repo, mock_db):
    mapping = {
        "mapping_id": "m1", "sibling_pair_id": "pair1",
        "character_role": "hero", "face_id": "f1",
        "created_at": "2025-01-01T00:00:00",
    }
    await repo.save_mapping(mapping)
    sql = mock_db.execute.call_args[0][0]
    assert "INSERT INTO character_mappings" in sql


@pytest.mark.asyncio
async def test_delete_mapping(repo, mock_db):
    await repo.delete_mapping("pair1", "hero")
    sql = mock_db.execute.call_args[0][0]
    assert "DELETE FROM character_mappings" in sql


@pytest.mark.asyncio
async def test_nullify_face_in_mappings(repo, mock_db):
    await repo.nullify_face_in_mappings("f1")
    sql = mock_db.execute.call_args[0][0]
    assert "UPDATE character_mappings SET face_id = NULL" in sql


# ── style_transferred_portraits ───────────────────────────────


@pytest.mark.asyncio
async def test_find_style_portraits_by_face(repo, mock_db):
    await repo.find_style_portraits_by_face("f1")
    sql = mock_db.fetch_all.call_args[0][0]
    assert "style_transferred_portraits" in sql


@pytest.mark.asyncio
async def test_delete_style_portraits_by_face(repo, mock_db):
    await repo.delete_style_portraits_by_face("f1")
    sql = mock_db.execute.call_args[0][0]
    assert "DELETE FROM style_transferred_portraits" in sql


# ── aggregates ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_get_storage_stats(repo, mock_db):
    mock_db.fetch_one.side_effect = [
        {"cnt": 5, "total": 10240},
        {"cnt": 3},
    ]
    result = await repo.get_storage_stats("pair1")
    assert result == {"photo_count": 5, "face_count": 3, "total_size_bytes": 10240}
