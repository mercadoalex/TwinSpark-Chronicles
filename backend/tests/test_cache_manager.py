"""Unit tests for CacheManager.

Covers:
- get_stats returns correct aggregate stats
- invalidate_photo evicts from both caches
- invalidate_face evicts from style transfer cache
- cleanup_expired delegates to style transfer cache
- start/stop cleanup loop lifecycle
"""

import asyncio
import os
import tempfile
import time

import pytest

from app.services.cache_manager import CacheManager
from app.services.cache_models import CachedFaceCrop, CacheStats
from app.services.face_crop_cache import FaceCropCache
from app.services.style_transfer_cache import StyleTransferCache
from app.models.multimodal import FaceBBox


@pytest.fixture
def tmp_cache_dir(tmp_path):
    """Provide a temporary directory for StyleTransferCache storage."""
    return str(tmp_path / "style_cache")


@pytest.fixture
def style_cache(tmp_cache_dir):
    return StyleTransferCache(storage_root=tmp_cache_dir, max_disk_bytes=10 * 1024 * 1024, ttl_seconds=3600)


@pytest.fixture
def face_cache():
    return FaceCropCache(max_entries=200)


@pytest.fixture
def cache_manager(style_cache, face_cache):
    return CacheManager(style_cache, face_cache, cleanup_interval_minutes=60)


def _make_face_crop(index: int = 0, content_hash: str = "abc123") -> CachedFaceCrop:
    return CachedFaceCrop(
        face_index=index,
        crop_bytes=b"fake_crop_bytes",
        bbox=FaceBBox(x=0.0, y=0.0, width=0.5, height=0.5, confidence=0.99),
        crop_width=50,
        crop_height=50,
        content_hash=content_hash,
    )


# ------------------------------------------------------------------
# get_stats
# ------------------------------------------------------------------


def test_get_stats_empty(cache_manager):
    """get_stats on empty caches returns zeroed CacheStats."""
    stats = cache_manager.get_stats()
    assert isinstance(stats, CacheStats)
    assert stats.style_transfer_entries == 0
    assert stats.style_transfer_disk_bytes == 0
    assert stats.style_transfer_hit_rate == 0.0
    assert stats.style_transfer_evictions == 0
    assert stats.face_crop_entries == 0
    assert stats.face_crop_hit_rate == 0.0
    assert stats.face_crop_evictions == 0


def test_get_stats_with_entries(cache_manager, style_cache, face_cache):
    """get_stats reflects entries added to both caches."""
    # Add a style transfer entry
    style_cache.put("face_hash_1", "hero", b"portrait_bytes_hero")
    # Add a face crop entry
    face_cache.put("photo_hash_1", [_make_face_crop()])

    stats = cache_manager.get_stats()
    assert stats.style_transfer_entries == 1
    assert stats.style_transfer_disk_bytes > 0
    assert stats.face_crop_entries == 1


def test_get_stats_hit_rate(cache_manager, style_cache, face_cache):
    """get_stats reflects hit rates after cache accesses."""
    style_cache.put("fh1", "hero", b"portrait")
    style_cache.get("fh1", "hero")  # hit
    style_cache.get("fh1", "missing_role")  # miss

    face_cache.put("ph1", [_make_face_crop()])
    face_cache.get("ph1")  # hit
    face_cache.get("ph_missing")  # miss

    stats = cache_manager.get_stats()
    assert stats.style_transfer_hit_rate == pytest.approx(0.5)
    assert stats.face_crop_hit_rate == pytest.approx(0.5)


# ------------------------------------------------------------------
# invalidate_photo
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_photo_evicts_both_caches(cache_manager, style_cache, face_cache):
    """invalidate_photo removes face crop entry and all style transfer entries for the photo's faces."""
    photo_hash = "photo_abc"
    face_hash_1 = "face_1"
    face_hash_2 = "face_2"

    # Populate face crop cache
    face_cache.put(photo_hash, [_make_face_crop(0, face_hash_1), _make_face_crop(1, face_hash_2)])

    # Populate style transfer cache with entries for both faces
    style_cache.put(face_hash_1, "hero", b"portrait_hero_1")
    style_cache.put(face_hash_1, "villain", b"portrait_villain_1")
    style_cache.put(face_hash_2, "sidekick", b"portrait_sidekick_2")

    # Also add an unrelated entry that should survive
    style_cache.put("unrelated_face", "hero", b"unrelated_portrait")

    await cache_manager.invalidate_photo(photo_hash, [face_hash_1, face_hash_2])

    # Face crop cache should be empty for this photo
    assert face_cache.get(photo_hash) is None

    # Style transfer entries for both faces should be gone
    assert style_cache.get(face_hash_1, "hero") is None
    assert style_cache.get(face_hash_1, "villain") is None
    assert style_cache.get(face_hash_2, "sidekick") is None

    # Unrelated entry should survive
    assert style_cache.get("unrelated_face", "hero") is not None


@pytest.mark.asyncio
async def test_invalidate_photo_no_op_on_missing(cache_manager, style_cache, face_cache):
    """invalidate_photo is a no-op when entries don't exist."""
    # Should not raise
    await cache_manager.invalidate_photo("nonexistent_photo", ["nonexistent_face"])


# ------------------------------------------------------------------
# invalidate_face
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_face_evicts_style_transfer(cache_manager, style_cache):
    """invalidate_face removes all style transfer entries for the given face hash."""
    face_hash = "face_xyz"
    style_cache.put(face_hash, "hero", b"portrait_hero")
    style_cache.put(face_hash, "villain", b"portrait_villain")
    style_cache.put("other_face", "hero", b"other_portrait")

    await cache_manager.invalidate_face(face_hash)

    assert style_cache.get(face_hash, "hero") is None
    assert style_cache.get(face_hash, "villain") is None
    # Other face should survive
    assert style_cache.get("other_face", "hero") is not None


@pytest.mark.asyncio
async def test_invalidate_face_no_op_on_missing(cache_manager):
    """invalidate_face is a no-op when the face hash doesn't exist."""
    await cache_manager.invalidate_face("nonexistent_face")


# ------------------------------------------------------------------
# cleanup_expired
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cleanup_expired_delegates_to_style_transfer(tmp_path):
    """cleanup_expired removes TTL-expired entries from style transfer cache."""
    cache_dir = str(tmp_path / "style_cache_ttl")
    # Very short TTL for testing
    style_cache = StyleTransferCache(storage_root=cache_dir, ttl_seconds=1)
    face_cache = FaceCropCache()
    mgr = CacheManager(style_cache, face_cache)

    style_cache.put("fh1", "hero", b"portrait_data")
    assert style_cache.stats["entries"] == 1

    # Wait for TTL to expire
    import time
    time.sleep(1.1)

    counts = await mgr.cleanup_expired()
    assert counts["style_transfer"] == 1
    assert style_cache.stats["entries"] == 0


@pytest.mark.asyncio
async def test_cleanup_expired_no_expired(cache_manager, style_cache):
    """cleanup_expired returns 0 when nothing is expired."""
    style_cache.put("fh1", "hero", b"portrait_data")
    counts = await cache_manager.cleanup_expired()
    assert counts["style_transfer"] == 0


# ------------------------------------------------------------------
# Cleanup loop lifecycle
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_start_stop_cleanup_loop(cache_manager):
    """start_cleanup_loop creates a task; stop_cleanup_loop cancels it."""
    await cache_manager.start_cleanup_loop()
    assert cache_manager._cleanup_task is not None
    assert not cache_manager._cleanup_task.done()

    await cache_manager.stop_cleanup_loop()
    assert cache_manager._cleanup_task is None


@pytest.mark.asyncio
async def test_start_cleanup_loop_idempotent(cache_manager):
    """Calling start_cleanup_loop twice reuses the existing task."""
    await cache_manager.start_cleanup_loop()
    task1 = cache_manager._cleanup_task

    await cache_manager.start_cleanup_loop()
    task2 = cache_manager._cleanup_task

    assert task1 is task2
    await cache_manager.stop_cleanup_loop()
