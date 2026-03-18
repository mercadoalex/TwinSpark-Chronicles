"""
Disk-backed LRU cache for style-transferred portrait images.

Entries are keyed by (face_content_hash, role) and stored as PNG files
on disk. An in-memory dict tracks metadata for fast lookup, LRU eviction,
and TTL enforcement. All in-memory operations are guarded by a
threading.Lock for thread safety.
"""

import logging
import os
import threading
import time

from app.services.cache_models import StyleTransferCacheEntry

logger = logging.getLogger(__name__)

# Defaults
_DEFAULT_MAX_DISK_BYTES = 500 * 1024 * 1024  # 500 MB
_DEFAULT_TTL_SECONDS = 7 * 24 * 3600          # 7 days


class StyleTransferCache:
    """Disk-backed LRU cache for style-transferred portrait images."""

    def __init__(
        self,
        storage_root: str,
        max_disk_bytes: int = _DEFAULT_MAX_DISK_BYTES,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
    ) -> None:
        self._storage_root = storage_root
        self._max_disk_bytes = max_disk_bytes
        self._ttl_seconds = ttl_seconds

        # In-memory index: (face_content_hash, role) -> StyleTransferCacheEntry
        self._entries: dict[tuple[str, str], StyleTransferCacheEntry] = {}
        self._lock = threading.Lock()

        # Stats counters
        self._hits = 0
        self._misses = 0
        self._evictions = 0

        # Ensure storage directory exists
        os.makedirs(self._storage_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _file_path(self, face_content_hash: str, role: str) -> str:
        """Return the on-disk path for a cache entry."""
        return os.path.join(self._storage_root, f"{face_content_hash}_{role}.png")

    def _total_disk_bytes(self) -> int:
        """Sum of size_bytes across all tracked entries (must hold lock)."""
        return sum(e.size_bytes for e in self._entries.values())

    def _evict_lru_until_under_limit(self) -> None:
        """Evict least-recently-accessed entries until total size <= max.

        Caller must hold self._lock.
        """
        while self._total_disk_bytes() > self._max_disk_bytes and self._entries:
            # Find the LRU entry
            lru_key = min(self._entries, key=lambda k: self._entries[k].last_accessed)
            self._remove_entry(lru_key)
            self._evictions += 1

    def _remove_entry(self, key: tuple[str, str]) -> None:
        """Delete an entry from the in-memory index and disk.

        Caller must hold self._lock.
        """
        entry = self._entries.pop(key, None)
        if entry is None:
            return
        try:
            if os.path.exists(entry.file_path):
                os.remove(entry.file_path)
        except OSError:
            logger.warning("Failed to delete cache file %s", entry.file_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, face_content_hash: str, role: str) -> bytes | None:
        """Return cached portrait bytes or None.

        Updates access time on hit. If the cache record exists but the
        file is missing from disk, evicts the stale record and returns None.
        """
        key = (face_content_hash, role)
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            # Check TTL
            if time.time() - entry.created_at > self._ttl_seconds:
                self._remove_entry(key)
                self._misses += 1
                return None

            # Verify file still exists on disk
            if not os.path.exists(entry.file_path):
                self._remove_entry(key)
                self._misses += 1
                return None

            # Read file
            try:
                with open(entry.file_path, "rb") as f:
                    data = f.read()
            except OSError:
                logger.warning("Failed to read cache file %s", entry.file_path)
                self._remove_entry(key)
                self._misses += 1
                return None

            # Update access time
            entry.last_accessed = time.time()
            self._hits += 1
            return data

    def put(self, face_content_hash: str, role: str, portrait_bytes: bytes) -> None:
        """Store portrait bytes on disk.

        Triggers LRU eviction when total disk usage exceeds max_disk_bytes.
        """
        key = (face_content_hash, role)
        file_path = self._file_path(face_content_hash, role)
        now = time.time()
        size_bytes = len(portrait_bytes)

        with self._lock:
            # If key already exists, remove old entry (metadata only, file will be overwritten)
            old = self._entries.pop(key, None)

            # Write to disk
            try:
                os.makedirs(self._storage_root, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(portrait_bytes)
            except OSError:
                logger.warning("Failed to write cache file %s", file_path)
                # Clean up old disk file if it was a different path
                if old and old.file_path != file_path:
                    try:
                        os.remove(old.file_path)
                    except OSError:
                        pass
                return

            # Clean up old disk file if it was at a different path
            if old and old.file_path != file_path:
                try:
                    os.remove(old.file_path)
                except OSError:
                    pass

            self._entries[key] = StyleTransferCacheEntry(
                face_content_hash=face_content_hash,
                role=role,
                file_path=file_path,
                size_bytes=size_bytes,
                created_at=now,
                last_accessed=now,
            )

            # Enforce disk size limit
            self._evict_lru_until_under_limit()

    def evict(self, face_content_hash: str, role: str | None = None) -> int:
        """Remove cache entries.

        If role is provided, remove only that specific entry.
        If role is None, remove all entries for the given face hash.
        Returns the count of entries evicted.
        """
        count = 0
        with self._lock:
            if role is not None:
                key = (face_content_hash, role)
                if key in self._entries:
                    self._remove_entry(key)
                    count = 1
                    self._evictions += 1
            else:
                keys_to_remove = [
                    k for k in self._entries if k[0] == face_content_hash
                ]
                for k in keys_to_remove:
                    self._remove_entry(k)
                    count += 1
                    self._evictions += 1
        return count

    def cleanup_expired(self) -> int:
        """Remove entries older than TTL. Returns count removed."""
        now = time.time()
        count = 0
        with self._lock:
            expired_keys = [
                k
                for k, e in self._entries.items()
                if now - e.created_at > self._ttl_seconds
            ]
            for k in expired_keys:
                self._remove_entry(k)
                count += 1
                self._evictions += 1
        return count

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            return {
                "entries": len(self._entries),
                "disk_bytes": self._total_disk_bytes(),
                "hit_rate": hit_rate,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
            }
