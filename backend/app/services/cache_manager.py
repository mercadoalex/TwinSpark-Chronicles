"""
Central cache coordinator.

Manages periodic TTL cleanup, aggregate stats, and cascading invalidation
across StyleTransferCache and FaceCropCache.
"""

import asyncio
import logging

from app.services.cache_models import CacheStats
from app.services.face_crop_cache import FaceCropCache
from app.services.style_transfer_cache import StyleTransferCache

logger = logging.getLogger(__name__)


class CacheManager:
    """Coordinates StyleTransferCache and FaceCropCache lifecycle."""

    def __init__(
        self,
        style_transfer_cache: StyleTransferCache,
        face_crop_cache: FaceCropCache,
        cleanup_interval_minutes: int = 60,
    ) -> None:
        self._style_transfer_cache = style_transfer_cache
        self._face_crop_cache = face_crop_cache
        self._cleanup_interval_seconds = cleanup_interval_minutes * 60
        self._cleanup_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Background cleanup loop
    # ------------------------------------------------------------------

    async def start_cleanup_loop(self) -> None:
        """Start background asyncio task for periodic expired entry cleanup."""
        if self._cleanup_task is not None and not self._cleanup_task.done():
            return  # already running
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop_cleanup_loop(self) -> None:
        """Cancel the background cleanup task."""
        if self._cleanup_task is not None and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        self._cleanup_task = None

    async def _cleanup_loop(self) -> None:
        """Periodically remove expired entries from all caches."""
        while True:
            await asyncio.sleep(self._cleanup_interval_seconds)
            try:
                counts = await self.cleanup_expired()
                total = sum(counts.values())
                if total > 0:
                    logger.info("Cache cleanup removed %d entries: %s", total, counts)
            except Exception:
                logger.exception("Cache cleanup task failed; will retry next interval")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup_expired(self) -> dict[str, int]:
        """Remove expired entries from all caches. Returns eviction counts.

        Only StyleTransferCache has TTL-based expiration.
        FaceCropCache is purely LRU and has no TTL cleanup.
        """
        style_transfer_removed = self._style_transfer_cache.cleanup_expired()
        return {
            "style_transfer": style_transfer_removed,
        }

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def get_stats(self) -> CacheStats:
        """Return current sizes, hit/miss rates, eviction counts."""
        st_stats = self._style_transfer_cache.stats
        fc_stats = self._face_crop_cache.stats
        return CacheStats(
            style_transfer_entries=st_stats["entries"],
            style_transfer_disk_bytes=st_stats["disk_bytes"],
            style_transfer_hit_rate=st_stats["hit_rate"],
            style_transfer_evictions=st_stats["evictions"],
            face_crop_entries=fc_stats["entries"],
            face_crop_hit_rate=fc_stats["hit_rate"],
            face_crop_evictions=fc_stats["evictions"],
        )

    # ------------------------------------------------------------------
    # Invalidation
    # ------------------------------------------------------------------

    async def invalidate_photo(
        self, photo_content_hash: str, face_content_hashes: list[str]
    ) -> None:
        """Cascade invalidation: evict face crop cache + all style transfer entries for the photo's faces."""
        # Evict face crop cache entry for this photo
        self._face_crop_cache.evict(photo_content_hash)

        # Evict all style transfer entries for each face that belonged to this photo
        for face_hash in face_content_hashes:
            self._style_transfer_cache.evict(face_hash)

    async def invalidate_face(self, face_content_hash: str) -> None:
        """Evict all style transfer cache entries for a specific face."""
        self._style_transfer_cache.evict(face_content_hash)
