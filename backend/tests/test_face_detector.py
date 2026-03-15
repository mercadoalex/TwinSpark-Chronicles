"""Unit tests for FaceDetector service."""

import io
import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock

from app.services.face_detector import FaceDetector
from app.models.multimodal import FaceBBox


def _make_jpeg(width: int = 640, height: int = 480) -> bytes:
    """Create a blank JPEG image for testing."""
    img = Image.fromarray(np.zeros((height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


class TestFaceDetectorInit:
    def test_enabled_when_mediapipe_available(self):
        detector = FaceDetector()
        assert detector.enabled is True

    def test_disabled_when_mediapipe_fails(self):
        """FaceDetector gracefully disables when mediapipe import fails."""
        with patch.dict("sys.modules", {"mediapipe": None, "mediapipe.solutions": None}):
            # Force re-import to trigger the ImportError path
            import importlib
            import app.services.face_detector as fd_mod
            importlib.reload(fd_mod)
            detector = fd_mod.FaceDetector()
            assert detector.enabled is False
        # Reload again to restore normal state
        import importlib
        import app.services.face_detector as fd_mod
        importlib.reload(fd_mod)

    def test_custom_min_confidence(self):
        detector = FaceDetector(min_confidence=0.7)
        assert detector._min_confidence == 0.7


class TestFaceDetectorDetect:
    def test_returns_empty_list_when_disabled(self):
        detector = FaceDetector.__new__(FaceDetector)
        detector._enabled = False
        detector._face_detection = None
        detector._min_confidence = 0.5
        result = detector.detect(_make_jpeg())
        assert result == []

    def test_returns_empty_list_on_no_faces(self):
        detector = FaceDetector()
        # A blank black image should have no faces
        result = detector.detect(_make_jpeg())
        assert result == []
        assert isinstance(result, list)

    def test_returns_empty_list_on_invalid_bytes(self):
        detector = FaceDetector()
        result = detector.detect(b"not a jpeg")
        assert result == []

    def test_returns_facebbox_objects(self):
        """Verify that when faces are detected, FaceBBox objects are returned."""
        detector = FaceDetector()

        # Mock the mediapipe detection to return a fake face
        mock_detection = MagicMock()
        mock_detection.score = [0.95]
        mock_bbox = MagicMock()
        mock_bbox.xmin = 0.2
        mock_bbox.ymin = 0.3
        mock_bbox.width = 0.4
        mock_bbox.height = 0.5
        mock_detection.location_data.relative_bounding_box = mock_bbox

        mock_results = MagicMock()
        mock_results.detections = [mock_detection]

        detector._face_detection.process = MagicMock(return_value=mock_results)

        result = detector.detect(_make_jpeg())
        assert len(result) == 1
        assert isinstance(result[0], FaceBBox)
        assert result[0].x == pytest.approx(0.2)
        assert result[0].y == pytest.approx(0.3)
        assert result[0].width == pytest.approx(0.4)
        assert result[0].height == pytest.approx(0.5)
        assert result[0].confidence == pytest.approx(0.95)

    def test_filters_low_confidence_faces(self):
        """Faces below min_confidence threshold are excluded."""
        detector = FaceDetector(min_confidence=0.5)

        low_conf = MagicMock()
        low_conf.score = [0.3]
        low_bbox = MagicMock()
        low_bbox.xmin = 0.1
        low_bbox.ymin = 0.1
        low_bbox.width = 0.2
        low_bbox.height = 0.2
        low_conf.location_data.relative_bounding_box = low_bbox

        high_conf = MagicMock()
        high_conf.score = [0.8]
        high_bbox = MagicMock()
        high_bbox.xmin = 0.5
        high_bbox.ymin = 0.5
        high_bbox.width = 0.3
        high_bbox.height = 0.3
        high_conf.location_data.relative_bounding_box = high_bbox

        mock_results = MagicMock()
        mock_results.detections = [low_conf, high_conf]
        detector._face_detection.process = MagicMock(return_value=mock_results)

        result = detector.detect(_make_jpeg())
        assert len(result) == 1
        assert result[0].confidence == pytest.approx(0.8)

    def test_clamps_coordinates_to_valid_range(self):
        """Coordinates outside [0,1] are clamped."""
        detector = FaceDetector()

        mock_detection = MagicMock()
        mock_detection.score = [0.9]
        mock_bbox = MagicMock()
        mock_bbox.xmin = -0.1  # Should clamp to 0.0
        mock_bbox.ymin = 1.5   # Should clamp to 1.0
        mock_bbox.width = 0.3
        mock_bbox.height = 0.3
        mock_detection.location_data.relative_bounding_box = mock_bbox

        mock_results = MagicMock()
        mock_results.detections = [mock_detection]
        detector._face_detection.process = MagicMock(return_value=mock_results)

        result = detector.detect(_make_jpeg())
        assert len(result) == 1
        assert result[0].x == 0.0
        assert result[0].y == 1.0

    def test_multiple_faces_detected(self):
        """Multiple faces are all returned when above threshold."""
        detector = FaceDetector()

        detections = []
        for i, conf in enumerate([0.7, 0.85, 0.6]):
            d = MagicMock()
            d.score = [conf]
            bbox = MagicMock()
            bbox.xmin = 0.1 * (i + 1)
            bbox.ymin = 0.1 * (i + 1)
            bbox.width = 0.2
            bbox.height = 0.2
            d.location_data.relative_bounding_box = bbox
            detections.append(d)

        mock_results = MagicMock()
        mock_results.detections = detections
        detector._face_detection.process = MagicMock(return_value=mock_results)

        result = detector.detect(_make_jpeg())
        assert len(result) == 3
        assert all(isinstance(f, FaceBBox) for f in result)
        assert all(f.confidence >= 0.5 for f in result)
