"""
Cache data models and content hash utility.

Shared types used by StyleTransferCache, FaceCropCache, CacheManager,
PhotoService, FaceExtractor, and StyleTransferAgent.
"""

import hashlib
from dataclasses import dataclass

from app.models.multimodal import FaceBBox


@dataclass
class CachedFaceCrop:
    """In-memory representation of a cached face extraction result."""

    face_index: int
    crop_bytes: bytes
    bbox: FaceBBox
    crop_width: int
    crop_height: int
    content_hash: str  # SHA-256 of crop_bytes


@dataclass
class StyleTransferCacheEntry:
    """Metadata for a disk-backed style transfer cache entry."""

    face_content_hash: str
    role: str
    file_path: str
    size_bytes: int
    created_at: float  # timestamp
    last_accessed: float  # timestamp


@dataclass
class CacheStats:
    """Aggregate cache statistics returned by /api/cache/stats."""

    style_transfer_entries: int
    style_transfer_disk_bytes: int
    style_transfer_hit_rate: float
    style_transfer_evictions: int
    face_crop_entries: int
    face_crop_hit_rate: float
    face_crop_evictions: int


def compute_content_hash(image_bytes: bytes) -> str:
    """Compute SHA-256 hex digest of image bytes.

    Used as a stable cache key that survives ID or file path changes.
    """
    return hashlib.sha256(image_bytes).hexdigest()
