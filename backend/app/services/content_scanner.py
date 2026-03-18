"""Content scanner service for image safety analysis.

Extends the existing ContentFilter with image scanning via Google Cloud
Vision SafeSearch detection.  Falls back to REVIEW rating when the Vision
client is unavailable (e.g. in test environments or when credentials are
missing).
"""

import logging
from dataclasses import dataclass
from enum import Enum

from app.services.content_filter import ContentFilter, FilterResult

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Try to import Google Cloud Vision; gracefully degrade if absent.
# ---------------------------------------------------------------------------
try:
    from google.cloud import vision as _vision  # type: ignore[import-untyped]

    _VISION_AVAILABLE = True
except Exception:  # ImportError, ModuleNotFoundError, etc.
    _VISION_AVAILABLE = False
    logger.warning(
        "google.cloud.vision is not available — image scanning will fall back to REVIEW rating"
    )


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------


class ImageSafetyRating(str, Enum):
    """Tri-state safety rating for uploaded images."""

    SAFE = "SAFE"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


@dataclass
class ImageScanResult:
    """Result of an image safety scan."""

    rating: ImageSafetyRating
    reason: str


# ---------------------------------------------------------------------------
# Likelihood helpers
# ---------------------------------------------------------------------------

# Google Vision SafeSearch likelihoods ordered by severity.
# Values mirror google.cloud.vision.Likelihood enum (1–5).
_BLOCKED_THRESHOLD = 4   # LIKELY
_REVIEW_THRESHOLD = 3    # POSSIBLE


def _likelihood_value(likelihood) -> int:
    """Return the integer value of a Vision Likelihood enum member."""
    try:
        return int(likelihood)
    except (TypeError, ValueError):
        return 0


# ---------------------------------------------------------------------------
# ContentScanner
# ---------------------------------------------------------------------------


class ContentScanner:
    """Image + text content safety scanner.

    Wraps the existing ``ContentFilter`` for text and adds image scanning
    powered by Google Cloud Vision SafeSearch.  When Vision is unavailable
    the scanner conservatively returns ``REVIEW`` so that a human can
    approve the image.
    """

    def __init__(self, content_filter: ContentFilter) -> None:
        self._text_filter = content_filter
        self._vision_client = None

        if _VISION_AVAILABLE:
            try:
                self._vision_client = _vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision client initialised for image scanning")
            except Exception as exc:
                logger.warning(
                    "Failed to create Vision client (%s) — falling back to REVIEW",
                    exc,
                )

    # ------------------------------------------------------------------
    # Image scanning
    # ------------------------------------------------------------------

    async def scan_image(self, image_bytes: bytes) -> ImageScanResult:
        """Scan *image_bytes* for inappropriate content.

        Uses Google Cloud Vision SafeSearch detection when available.
        Falls back to ``REVIEW`` with a logged warning otherwise.
        """
        if not image_bytes:
            return ImageScanResult(
                rating=ImageSafetyRating.BLOCKED,
                reason="Empty image data",
            )

        if self._vision_client is None:
            logger.warning(
                "Vision client unavailable — returning REVIEW for uploaded image"
            )
            return ImageScanResult(
                rating=ImageSafetyRating.REVIEW,
                reason="Automated scanning unavailable — flagged for manual review",
            )

        try:
            return await self._scan_with_vision(image_bytes)
        except Exception as exc:
            logger.warning(
                "Vision SafeSearch call failed (%s) — returning REVIEW", exc
            )
            return ImageScanResult(
                rating=ImageSafetyRating.REVIEW,
                reason="Automated scanning failed — flagged for manual review",
            )

    async def _scan_with_vision(self, image_bytes: bytes) -> ImageScanResult:
        """Run Google Cloud Vision SafeSearch and map likelihoods to a rating."""
        image = {"content": image_bytes}
        if _VISION_AVAILABLE:
            image = _vision.Image(content=image_bytes)  # type: ignore[possibly-undefined]
        response = self._vision_client.safe_search_detection(image=image)

        if response.error and response.error.message:
            raise RuntimeError(f"Vision API error: {response.error.message}")

        safe_search = response.safe_search_annotation

        # Collect the five SafeSearch categories.
        categories = {
            "adult": _likelihood_value(safe_search.adult),
            "violence": _likelihood_value(safe_search.violence),
            "racy": _likelihood_value(safe_search.racy),
            "medical": _likelihood_value(safe_search.medical),
            "spoof": _likelihood_value(safe_search.spoof),
        }

        # Determine the worst-case category.
        blocked_categories = [
            name for name, val in categories.items() if val >= _BLOCKED_THRESHOLD
        ]
        review_categories = [
            name
            for name, val in categories.items()
            if _REVIEW_THRESHOLD <= val < _BLOCKED_THRESHOLD
        ]

        if blocked_categories:
            return ImageScanResult(
                rating=ImageSafetyRating.BLOCKED,
                reason=f"Image flagged for: {', '.join(blocked_categories)}",
            )

        if review_categories:
            return ImageScanResult(
                rating=ImageSafetyRating.REVIEW,
                reason=f"Image needs review for: {', '.join(review_categories)}",
            )

        return ImageScanResult(
            rating=ImageSafetyRating.SAFE,
            reason="Image passes all safety checks",
        )

    # ------------------------------------------------------------------
    # Text scanning (delegates to existing ContentFilter)
    # ------------------------------------------------------------------

    def scan_text(self, text: str, **kwargs) -> FilterResult:
        """Delegate text scanning to the existing ContentFilter."""
        return self._text_filter.scan(text, **kwargs)
