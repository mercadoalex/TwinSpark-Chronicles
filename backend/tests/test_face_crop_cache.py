"""
Unit tests for FaceCropCache — in-memory LRU cache for face extraction results.
"""

import time

import pytest

from app.models.multimodal import FaceBBox
from app.services.cache_models import CachedFaceCrop
from app.services.face_crop_cache import FaceCropCache


def _make_face(index: int = 0, data: bytes = b"face-bytes") -> CachedFaceCrop:
    """Helper to build a CachedFaceCrop with sensible defaults."""
    return CachedFaceCrop(
        face_index=index,
        crop_bytes=data,
        bbox=FaceBBox(x=0.1, y=0.2, width=0.3, height=0.4, confidence=0.95),
        crop_width=100,
        crop_height=100,
        content_hash="face_hash",
    )


@pytest.fixture
def cache():
    """Small cache with 5-entry limit for testing."""
    return FaceCropCache(max_entries=5)


class TestGet:
    def test_miss_returns_none(self, cache):
        assert cache.get("nonexistent") is None

    def test_hit_returns_faces(self, cache):
        faces = [_make_face(0), _make_face(1)]
        cache.put("photo_hash_1", faces)
        result = cache.get("photo_hash_1")
        assert result is not None
        assert len(result) == 2
        assert result[0].crop_bytes == b"face-bytes"

    def test_hit_updates_access_time(self, cache):
        cache.put("h1", [_make_face()])
        _, t1 = cache._entries["h1"]
        time.sleep(0.05)
        cache.get("h1")
        _, t2 = cache._entries["h1"]
        assert t2 > t1

    def test_miss_increments_miss_counter(self, cache):
        cache.get("nope")
        cache.get("nope2")
        assert cache.stats["misses"] == 2

    def test_hit_increments_hit_counter(self, cache):
        cache.put("h1", [_make_face()])
        cache.get("h1")
        cache.get("h1")
        assert cache.stats["hits"] == 2


class TestPut:
    def test_stores_entry(self, cache):
        faces = [_make_face()]
        cache.put("h1", faces)
        assert cache.stats["entries"] == 1

    def test_overwrites_existing_entry(self, cache):
        cache.put("h1", [_make_face(0, b"old")])
        cache.put("h1", [_make_face(0, b"new")])
        result = cache.get("h1")
        assert result[0].crop_bytes == b"new"
        assert cache.stats["entries"] == 1

    def test_overwrite_does_not_trigger_eviction(self):
        c = FaceCropCache(max_entries=1)
        c.put("h1", [_make_face(0, b"old")])
        c.put("h1", [_make_face(0, b"new")])
        assert c.stats["entries"] == 1
        assert c.stats["evictions"] == 0

    def test_lru_eviction_on_entry_limit(self, cache):
        """When entry count exceeds max, LRU entries are evicted."""
        # max_entries = 5
        for i in range(5):
            cache.put(f"h{i}", [_make_face(i)])

        # Access h0 to make it recently used; h1 becomes LRU
        cache.get("h0")

        # Insert a 6th entry — should evict h1 (LRU)
        cache.put("h5", [_make_face(5)])

        assert cache.get("h1") is None  # evicted
        assert cache.get("h0") is not None  # kept (recently accessed)
        assert cache.get("h5") is not None  # just inserted
        assert cache.stats["entries"] == 5

    def test_eviction_count_increments(self):
        c = FaceCropCache(max_entries=2)
        c.put("h1", [_make_face()])
        c.put("h2", [_make_face()])
        c.put("h3", [_make_face()])  # evicts h1
        assert c.stats["evictions"] == 1


class TestEvict:
    def test_evict_existing_entry(self, cache):
        cache.put("h1", [_make_face()])
        assert cache.evict("h1") is True
        assert cache.get("h1") is None

    def test_evict_nonexistent_returns_false(self, cache):
        assert cache.evict("nope") is False

    def test_evict_increments_eviction_counter(self, cache):
        cache.put("h1", [_make_face()])
        cache.evict("h1")
        assert cache.stats["evictions"] == 1

    def test_evict_reduces_entry_count(self, cache):
        cache.put("h1", [_make_face()])
        cache.put("h2", [_make_face()])
        cache.evict("h1")
        assert cache.stats["entries"] == 1


class TestStats:
    def test_initial_stats(self, cache):
        s = cache.stats
        assert s["entries"] == 0
        assert s["hit_rate"] == 0.0
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["evictions"] == 0

    def test_stats_after_operations(self, cache):
        cache.put("h1", [_make_face()])
        cache.get("h1")  # hit
        cache.get("h2")  # miss
        s = cache.stats
        assert s["entries"] == 1
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["hit_rate"] == 0.5

    def test_hit_rate_all_hits(self, cache):
        cache.put("h1", [_make_face()])
        cache.get("h1")
        cache.get("h1")
        assert cache.stats["hit_rate"] == 1.0

    def test_hit_rate_all_misses(self, cache):
        cache.get("nope")
        cache.get("nope2")
        assert cache.stats["hit_rate"] == 0.0
