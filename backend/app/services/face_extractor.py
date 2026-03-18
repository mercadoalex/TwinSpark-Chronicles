"""
Face Extraction Service.
Wraps FaceDetector with cropping logic to extract individual face portraits
with consistent margin padding.
"""

import io
import logging
from dataclasses import dataclass

from PIL import Image

from app.models.multimodal import FaceBBox
from app.services.cache_models import CachedFaceCrop, compute_content_hash
from app.services.face_detector import FaceDetector

logger = logging.getLogger(__name__)

MAX_FACES = 10


class NoFacesFoundError(Exception):
    """Raised when no faces are detected in an image."""
    pass


@dataclass
class ExtractedFace:
    face_index: int
    crop_bytes: bytes       # JPEG bytes of the cropped face
    bbox: FaceBBox          # Original bounding box from FaceDetector
    crop_width: int
    crop_height: int


class FaceExtractor:
    """Detects faces and crops each with consistent margin padding."""

    def __init__(self, face_detector: FaceDetector, face_crop_cache: "FaceCropCache | None" = None):
        self._detector = face_detector
        self._face_crop_cache = face_crop_cache

    def extract_faces(
        self, image_bytes: bytes, margin: float = 0.2, content_hash: str | None = None
    ) -> list[ExtractedFace]:
        """Detect faces and crop each with `margin` padding (default 20%).

        Returns up to 10 face crops sorted by detection order.
        Raises NoFacesFoundError if no faces are detected.

        If `content_hash` is provided and a FaceCropCache is configured,
        cached results are returned on hit. On miss, results are computed
        and stored in the cache.
        """
        # Check cache on hit
        if content_hash and self._face_crop_cache is not None:
            cached = self._face_crop_cache.get(content_hash)
            if cached is not None:
                logger.debug("Face crop cache hit for %s", content_hash[:12])
                return [
                    ExtractedFace(
                        face_index=c.face_index,
                        crop_bytes=c.crop_bytes,
                        bbox=c.bbox,
                        crop_width=c.crop_width,
                        crop_height=c.crop_height,
                    )
                    for c in cached
                ]

        # Detect faces via the underlying FaceDetector
        bboxes = self._detector.detect(image_bytes)

        if not bboxes:
            raise NoFacesFoundError("No faces were found in the image.")

        # Limit to MAX_FACES
        bboxes = bboxes[:MAX_FACES]

        # Decode the image once for all crops
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_w, img_h = image.size

        extracted: list[ExtractedFace] = []
        for idx, bbox in enumerate(bboxes):
            # Convert normalized coordinates to pixel coordinates
            px_x = bbox.x * img_w
            px_y = bbox.y * img_h
            px_w = bbox.width * img_w
            px_h = bbox.height * img_h

            # Apply margin padding, clamped to image boundaries
            crop_x = max(0, px_x - margin * px_w)
            crop_y = max(0, px_y - margin * px_h)
            crop_right = min(img_w, px_x + (1 + margin) * px_w)
            crop_bottom = min(img_h, px_y + (1 + margin) * px_h)

            crop_w = crop_right - crop_x
            crop_h = crop_bottom - crop_y

            # Crop the face region (Pillow uses left, upper, right, lower)
            cropped = image.crop((crop_x, crop_y, crop_right, crop_bottom))

            # Encode as JPEG
            buf = io.BytesIO()
            cropped.save(buf, format="JPEG", quality=90)
            crop_bytes = buf.getvalue()

            extracted.append(
                ExtractedFace(
                    face_index=idx,
                    crop_bytes=crop_bytes,
                    bbox=bbox,
                    crop_width=int(round(crop_w)),
                    crop_height=int(round(crop_h)),
                )
            )

        # Store in cache on miss
        if content_hash and self._face_crop_cache is not None:
            cached_faces = [
                CachedFaceCrop(
                    face_index=f.face_index,
                    crop_bytes=f.crop_bytes,
                    bbox=f.bbox,
                    crop_width=f.crop_width,
                    crop_height=f.crop_height,
                    content_hash=compute_content_hash(f.crop_bytes),
                )
                for f in extracted
            ]
            self._face_crop_cache.put(content_hash, cached_faces)

        return extracted
