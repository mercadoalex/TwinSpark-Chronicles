"""
In-memory LRU cache for face extraction results.

Entries are keyed by photo_content_hash and store lists of CachedFaceCrop.
An in-memory dict tracks (faces, last_accessed) tuples for fast lookup and
LRU eviction. All operations are guarded by a threading.Lock for thread
safety.
"""

import logging
import threading
import time

from app.services.cache_models import CachedFaceCrop

logger = logging.getLogger(__name__)

_DEFAULT_MAX_ENTRIES = 200


class FaceCropCache:
    """In-memory LRU cache for face extraction results."""

    def __init__(self, max_entries: int = _DEFAULT_MAX_ENTRIES) -> None:
        self._max_entries = max_entries

        # In-memory store: photo_content_hash -> (faces, last_accessed)
        self._entries: dict[str, tuple[list[CachedFaceCrop], float]] = {}
        self._lock = threading.Lock()

        # Stats counters
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _evict_lru(self) -> None:
        """Evict the least-recently-accessed entry.

        Caller must hold self._lock.
        """
        if not self._entries:
            return
        lru_key = min(self._entries, key=lambda k: self._entries[k][1])
        del self._entries[lru_key]
        self._evictions += 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, photo_content_hash: str) -> list[CachedFaceCrop] | None:
        """Return cached face crops or None. Updates access time on hit."""
        with self._lock:
            entry = self._entries.get(photo_content_hash)
            if entry is None:
                self._misses += 1
                return None

            faces, _ = entry
            self._entries[photo_content_hash] = (faces, time.time())
            self._hits += 1
            return faces

    def put(self, photo_content_hash: str, faces: list[CachedFaceCrop]) -> None:
        """Store face crops. Triggers LRU eviction if over entry limit."""
        now = time.time()
        with self._lock:
            # If key already exists, update in place (no eviction needed)
            if photo_content_hash in self._entries:
                self._entries[photo_content_hash] = (faces, now)
                return

            # Evict LRU entries until we have room for the new one
            while len(self._entries) >= self._max_entries:
                self._evict_lru()

            self._entries[photo_content_hash] = (faces, now)

    def evict(self, photo_content_hash: str) -> bool:
        """Evict entry for the given hash. Returns True if found."""
        with self._lock:
            if photo_content_hash in self._entries:
                del self._entries[photo_content_hash]
                self._evictions += 1
                return True
            return False

    @property
    def stats(self) -> dict:
        """Return cache statistics."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_rate = self._hits / total_requests if total_requests > 0 else 0.0
            return {
                "entries": len(self._entries),
                "hit_rate": hit_rate,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
            }
