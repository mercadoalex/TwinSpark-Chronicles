"""
Unit tests for StyleTransferCache — disk-backed LRU cache for style-transferred portraits.
"""

import os
import time

import pytest

from app.services.style_transfer_cache import StyleTransferCache


@pytest.fixture
def cache_dir(tmp_path):
    """Return a temporary directory for cache storage."""
    return str(tmp_path / "style_cache")


@pytest.fixture
def cache(cache_dir):
    """Small cache with 1 KB limit and 5-second TTL for testing."""
    return StyleTransferCache(
        storage_root=cache_dir,
        max_disk_bytes=1024,
        ttl_seconds=5,
    )


class TestGet:
    def test_miss_returns_none(self, cache):
        assert cache.get("abc123", "hero") is None

    def test_hit_returns_bytes(self, cache):
        data = b"portrait-data"
        cache.put("hash1", "hero", data)
        assert cache.get("hash1", "hero") == data

    def test_hit_updates_access_time(self, cache):
        cache.put("hash1", "hero", b"data")
        time.sleep(0.05)
        cache.get("hash1", "hero")
        entry = cache._entries[("hash1", "hero")]
        assert entry.last_accessed > entry.created_at

    def test_stale_record_file_missing(self, cache, cache_dir):
        cache.put("hash1", "hero", b"data")
        # Delete the file behind the cache's back
        os.remove(os.path.join(cache_dir, "hash1_hero.png"))
        result = cache.get("hash1", "hero")
        assert result is None
        assert ("hash1", "hero") not in cache._entries

    def test_expired_entry_returns_none(self):
        """Entry past TTL should return None and be evicted."""
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            c = StyleTransferCache(storage_root=td, ttl_seconds=0)
            c.put("hash1", "hero", b"data")
            # TTL=0 means immediately expired
            time.sleep(0.01)
            assert c.get("hash1", "hero") is None


class TestPut:
    def test_creates_file_on_disk(self, cache, cache_dir):
        cache.put("hash1", "hero", b"portrait")
        assert os.path.exists(os.path.join(cache_dir, "hash1_hero.png"))

    def test_overwrites_existing_entry(self, cache):
        cache.put("hash1", "hero", b"old")
        cache.put("hash1", "hero", b"new")
        assert cache.get("hash1", "hero") == b"new"
        assert cache.stats["entries"] == 1

    def test_lru_eviction_on_size_limit(self, cache):
        """When total size exceeds max, LRU entries are evicted."""
        # max_disk_bytes = 1024
        cache.put("h1", "r1", b"x" * 400)
        cache.put("h2", "r2", b"y" * 400)
        # Access h1 to make h2 the LRU
        cache.get("h1", "r1")
        # This should push over 1024 and evict h2 (LRU)
        cache.put("h3", "r3", b"z" * 400)
        assert cache.get("h2", "r2") is None
        assert cache.get("h1", "r1") is not None
        assert cache.get("h3", "r3") is not None


class TestEvict:
    def test_evict_specific_entry(self, cache):
        cache.put("hash1", "hero", b"data")
        count = cache.evict("hash1", "hero")
        assert count == 1
        assert cache.get("hash1", "hero") is None

    def test_evict_all_for_face_hash(self, cache):
        cache.put("hash1", "hero", b"a")
        cache.put("hash1", "villain", b"b")
        cache.put("hash2", "hero", b"c")
        count = cache.evict("hash1")
        assert count == 2
        assert cache.get("hash1", "hero") is None
        assert cache.get("hash1", "villain") is None
        assert cache.get("hash2", "hero") == b"c"

    def test_evict_nonexistent_returns_zero(self, cache):
        assert cache.evict("nope", "nope") == 0

    def test_evict_deletes_disk_file(self, cache, cache_dir):
        cache.put("hash1", "hero", b"data")
        fpath = os.path.join(cache_dir, "hash1_hero.png")
        assert os.path.exists(fpath)
        cache.evict("hash1", "hero")
        assert not os.path.exists(fpath)


class TestCleanupExpired:
    def test_removes_expired_entries(self):
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            c = StyleTransferCache(storage_root=td, ttl_seconds=0)
            c.put("h1", "r1", b"a")
            c.put("h2", "r2", b"b")
            time.sleep(0.01)
            removed = c.cleanup_expired()
            assert removed == 2
            assert c.stats["entries"] == 0

    def test_keeps_non_expired_entries(self, cache):
        cache.put("h1", "r1", b"a")
        removed = cache.cleanup_expired()
        assert removed == 0
        assert cache.stats["entries"] == 1


class TestStats:
    def test_initial_stats(self, cache):
        s = cache.stats
        assert s["entries"] == 0
        assert s["disk_bytes"] == 0
        assert s["hit_rate"] == 0.0
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["evictions"] == 0

    def test_stats_after_operations(self, cache):
        cache.put("h1", "r1", b"data")
        cache.get("h1", "r1")  # hit
        cache.get("h2", "r2")  # miss
        s = cache.stats
        assert s["entries"] == 1
        assert s["disk_bytes"] == 4
        assert s["hits"] == 1
        assert s["misses"] == 1
        assert s["hit_rate"] == 0.5
