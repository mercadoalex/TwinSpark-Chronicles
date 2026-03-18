"""Unit tests for FaceExtractor service."""

import io
import pytest
import numpy as np
from PIL import Image
from unittest.mock import MagicMock

from app.models.multimodal import FaceBBox
from app.services.face_extractor import (
    FaceExtractor,
    ExtractedFace,
    NoFacesFoundError,
    MAX_FACES,
)


def _make_jpeg(width: int = 640, height: int = 480) -> bytes:
    """Create a blank JPEG image for testing."""
    img = Image.fromarray(np.zeros((height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_color_jpeg(width: int = 640, height: int = 480) -> bytes:
    """Create a colorful JPEG image for testing (easier to verify crops)."""
    rng = np.random.RandomState(42)
    arr = rng.randint(0, 256, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _mock_detector(bboxes: list[FaceBBox]) -> MagicMock:
    """Create a mock FaceDetector that returns the given bboxes."""
    detector = MagicMock()
    detector.detect.return_value = bboxes
    return detector


class TestNoFacesFoundError:
    def test_raises_when_no_faces(self):
        detector = _mock_detector([])
        extractor = FaceExtractor(detector)
        with pytest.raises(NoFacesFoundError):
            extractor.extract_faces(_make_jpeg())

    def test_error_message(self):
        detector = _mock_detector([])
        extractor = FaceExtractor(detector)
        with pytest.raises(NoFacesFoundError, match="No faces"):
            extractor.extract_faces(_make_jpeg())


class TestExtractFaces:
    def test_single_face_extraction(self):
        bbox = FaceBBox(x=0.2, y=0.3, width=0.4, height=0.3, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg(640, 480))

        assert len(result) == 1
        face = result[0]
        assert isinstance(face, ExtractedFace)
        assert face.face_index == 0
        assert face.bbox == bbox
        assert isinstance(face.crop_bytes, bytes)
        assert face.crop_width > 0
        assert face.crop_height > 0

        # Verify the crop is a valid JPEG
        img = Image.open(io.BytesIO(face.crop_bytes))
        assert img.format == "JPEG"

    def test_crop_dimensions_match_margin_formula(self):
        """Verify crop dimensions match the design formula with 20% margin."""
        img_w, img_h = 640, 480
        bbox = FaceBBox(x=0.25, y=0.25, width=0.5, height=0.5, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg(img_w, img_h))
        face = result[0]

        # Pixel coords
        px_x = bbox.x * img_w   # 160
        px_y = bbox.y * img_h   # 120
        px_w = bbox.width * img_w  # 320
        px_h = bbox.height * img_h  # 240

        # Expected crop with 20% margin
        margin = 0.2
        exp_crop_x = max(0, px_x - margin * px_w)
        exp_crop_y = max(0, px_y - margin * px_h)
        exp_crop_right = min(img_w, px_x + (1 + margin) * px_w)
        exp_crop_bottom = min(img_h, px_y + (1 + margin) * px_h)
        exp_w = exp_crop_right - exp_crop_x
        exp_h = exp_crop_bottom - exp_crop_y

        assert face.crop_width == int(round(exp_w))
        assert face.crop_height == int(round(exp_h))

    def test_crop_clamped_to_image_boundaries(self):
        """Face near edge: crop should not exceed image dimensions."""
        img_w, img_h = 200, 200
        # Face at top-left corner
        bbox = FaceBBox(x=0.0, y=0.0, width=0.3, height=0.3, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg(img_w, img_h))
        face = result[0]

        # crop_x should be clamped to 0 (can't go negative)
        assert face.crop_width <= img_w
        assert face.crop_height <= img_h

    def test_crop_clamped_bottom_right(self):
        """Face near bottom-right: crop should not exceed image dimensions."""
        img_w, img_h = 200, 200
        bbox = FaceBBox(x=0.8, y=0.8, width=0.2, height=0.2, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg(img_w, img_h))
        face = result[0]

        assert face.crop_width <= img_w
        assert face.crop_height <= img_h

    def test_multiple_faces(self):
        bboxes = [
            FaceBBox(x=0.1, y=0.1, width=0.2, height=0.2, confidence=0.9),
            FaceBBox(x=0.5, y=0.5, width=0.2, height=0.2, confidence=0.8),
            FaceBBox(x=0.7, y=0.1, width=0.15, height=0.15, confidence=0.7),
        ]
        detector = _mock_detector(bboxes)
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg())
        assert len(result) == 3
        for i, face in enumerate(result):
            assert face.face_index == i
            assert face.bbox == bboxes[i]

    def test_max_10_faces(self):
        """Only the first 10 faces should be returned."""
        bboxes = [
            FaceBBox(x=0.05 * i, y=0.05 * i, width=0.04, height=0.04, confidence=0.9)
            for i in range(15)
        ]
        detector = _mock_detector(bboxes)
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_jpeg(1000, 1000))
        assert len(result) == MAX_FACES

    def test_custom_margin(self):
        """Custom margin value should be applied."""
        img_w, img_h = 400, 400
        bbox = FaceBBox(x=0.25, y=0.25, width=0.5, height=0.5, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        margin = 0.5
        result = extractor.extract_faces(_make_jpeg(img_w, img_h), margin=margin)
        face = result[0]

        px_x = bbox.x * img_w
        px_y = bbox.y * img_h
        px_w = bbox.width * img_w
        px_h = bbox.height * img_h

        exp_crop_x = max(0, px_x - margin * px_w)
        exp_crop_y = max(0, px_y - margin * px_h)
        exp_crop_right = min(img_w, px_x + (1 + margin) * px_w)
        exp_crop_bottom = min(img_h, px_y + (1 + margin) * px_h)
        exp_w = exp_crop_right - exp_crop_x
        exp_h = exp_crop_bottom - exp_crop_y

        assert face.crop_width == int(round(exp_w))
        assert face.crop_height == int(round(exp_h))

    def test_extracted_face_crop_is_valid_jpeg(self):
        """Each extracted face crop should be a decodable JPEG."""
        bboxes = [
            FaceBBox(x=0.1, y=0.1, width=0.3, height=0.3, confidence=0.9),
            FaceBBox(x=0.5, y=0.5, width=0.2, height=0.2, confidence=0.8),
        ]
        detector = _mock_detector(bboxes)
        extractor = FaceExtractor(detector)

        result = extractor.extract_faces(_make_color_jpeg())
        for face in result:
            img = Image.open(io.BytesIO(face.crop_bytes))
            assert img.format == "JPEG"
            assert img.size[0] > 0
            assert img.size[1] > 0

    def test_detector_called_with_image_bytes(self):
        """FaceExtractor should pass image_bytes to the detector."""
        bbox = FaceBBox(x=0.2, y=0.2, width=0.3, height=0.3, confidence=0.9)
        detector = _mock_detector([bbox])
        extractor = FaceExtractor(detector)

        image_bytes = _make_jpeg()
        extractor.extract_faces(image_bytes)

        detector.detect.assert_called_once_with(image_bytes)
