"""Tests for ContentScanner — image safety scanning with Vision fallback."""

import sys
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio

from app.services.content_filter import ContentFilter, ContentRating, FilterResult
from app.services.content_scanner import (
    ContentScanner,
    ImageSafetyRating,
    ImageScanResult,
    _BLOCKED_THRESHOLD,
    _REVIEW_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def content_filter():
    """A real ContentFilter (uses fallback blocklist since no file on disk)."""
    return ContentFilter(blocklist_path="nonexistent.json")


@pytest.fixture
def scanner_no_vision(content_filter):
    """ContentScanner with Vision unavailable (default in test env)."""
    return ContentScanner(content_filter)


# ---------------------------------------------------------------------------
# ImageSafetyRating / ImageScanResult basics
# ---------------------------------------------------------------------------


class TestImageSafetyRating:
    def test_enum_values(self):
        assert ImageSafetyRating.SAFE == "SAFE"
        assert ImageSafetyRating.REVIEW == "REVIEW"
        assert ImageSafetyRating.BLOCKED == "BLOCKED"

    def test_scan_result_creation(self):
        result = ImageScanResult(rating=ImageSafetyRating.SAFE, reason="ok")
        assert result.rating == ImageSafetyRating.SAFE
        assert result.reason == "ok"


# ---------------------------------------------------------------------------
# Fallback behaviour (no Vision client)
# ---------------------------------------------------------------------------


class TestScanImageFallback:
    @pytest.mark.asyncio
    async def test_returns_review_when_vision_unavailable(self, scanner_no_vision):
        result = await scanner_no_vision.scan_image(b"\xff\xd8fake-jpeg")
        assert result.rating == ImageSafetyRating.REVIEW
        assert "unavailable" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_blocks_empty_image_bytes(self, scanner_no_vision):
        result = await scanner_no_vision.scan_image(b"")
        assert result.rating == ImageSafetyRating.BLOCKED
        assert "empty" in result.reason.lower()


# ---------------------------------------------------------------------------
# Vision client integration (mocked)
# ---------------------------------------------------------------------------


def _make_safe_search(adult=1, violence=1, racy=1, medical=1, spoof=1):
    """Build a mock SafeSearchAnnotation with given likelihood ints."""
    ss = MagicMock()
    ss.adult = adult
    ss.violence = violence
    ss.racy = racy
    ss.medical = medical
    ss.spoof = spoof
    return ss


def _make_vision_response(safe_search, error_message=""):
    resp = MagicMock()
    resp.safe_search_annotation = safe_search
    resp.error = MagicMock()
    resp.error.message = error_message
    return resp


class TestScanImageWithVision:
    def _scanner_with_mock_vision(self, content_filter, vision_response):
        """Create a scanner whose Vision client returns *vision_response*."""
        scanner = ContentScanner(content_filter)
        mock_client = MagicMock()
        mock_client.safe_search_detection.return_value = vision_response
        scanner._vision_client = mock_client
        return scanner

    @pytest.mark.asyncio
    async def test_safe_image(self, content_filter):
        ss = _make_safe_search(adult=1, violence=1, racy=1, medical=1, spoof=1)
        resp = _make_vision_response(ss)
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.SAFE
        assert "passes" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_blocked_image_adult(self, content_filter):
        ss = _make_safe_search(adult=_BLOCKED_THRESHOLD)
        resp = _make_vision_response(ss)
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.BLOCKED
        assert "adult" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_blocked_image_violence(self, content_filter):
        ss = _make_safe_search(violence=_BLOCKED_THRESHOLD)
        resp = _make_vision_response(ss)
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.BLOCKED
        assert "violence" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_review_image_racy(self, content_filter):
        ss = _make_safe_search(racy=_REVIEW_THRESHOLD)
        resp = _make_vision_response(ss)
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.REVIEW
        assert "racy" in result.reason.lower()

    @pytest.mark.asyncio
    async def test_blocked_takes_precedence_over_review(self, content_filter):
        ss = _make_safe_search(
            adult=_BLOCKED_THRESHOLD, racy=_REVIEW_THRESHOLD
        )
        resp = _make_vision_response(ss)
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.BLOCKED

    @pytest.mark.asyncio
    async def test_vision_api_error_falls_back_to_review(self, content_filter):
        ss = _make_safe_search()
        resp = _make_vision_response(ss, error_message="quota exceeded")
        scanner = self._scanner_with_mock_vision(content_filter, resp)

        result = await scanner.scan_image(b"\xff\xd8fake")
        # The error message is set, so RuntimeError is raised → fallback
        assert result.rating == ImageSafetyRating.REVIEW

    @pytest.mark.asyncio
    async def test_vision_exception_falls_back_to_review(self, content_filter):
        scanner = ContentScanner(content_filter)
        mock_client = MagicMock()
        mock_client.safe_search_detection.side_effect = RuntimeError("network")
        scanner._vision_client = mock_client

        result = await scanner.scan_image(b"\xff\xd8fake")
        assert result.rating == ImageSafetyRating.REVIEW
        assert "failed" in result.reason.lower()


# ---------------------------------------------------------------------------
# Text scanning delegation
# ---------------------------------------------------------------------------


class TestScanText:
    def test_delegates_to_content_filter(self, scanner_no_vision):
        result = scanner_no_vision.scan_text("a friendly story about teamwork")
        assert isinstance(result, FilterResult)
        assert result.rating == ContentRating.SAFE

    def test_blocked_text_detected(self, scanner_no_vision):
        result = scanner_no_vision.scan_text("the character used a weapon")
        assert result.rating == ContentRating.BLOCKED
        assert "weapon" in result.matched_terms
