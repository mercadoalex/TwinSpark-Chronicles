"""Unit tests for EmotionDetector service."""

import io
import pytest
import numpy as np
from PIL import Image
from unittest.mock import patch, MagicMock

from app.services.emotion_detector import EmotionDetector, _distance, _get_point
from app.models.multimodal import EmotionCategory, EmotionResult, FaceBBox


def _make_jpeg(width: int = 640, height: int = 480) -> bytes:
    """Create a blank JPEG image for testing."""
    img = Image.fromarray(np.zeros((height, width, 3), dtype=np.uint8))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_bbox(x=0.1, y=0.1, width=0.5, height=0.5, confidence=0.9) -> FaceBBox:
    return FaceBBox(x=x, y=y, width=width, height=height, confidence=confidence)


class TestEmotionDetectorInit:
    def test_enabled_when_mediapipe_available(self):
        detector = EmotionDetector()
        assert detector.enabled is True

    def test_disabled_when_mediapipe_fails(self):
        """EmotionDetector gracefully disables when mediapipe import fails."""
        with patch.dict(
            "sys.modules",
            {"mediapipe": None, "mediapipe.solutions": None, "mediapipe.solutions.face_mesh": None},
        ):
            import importlib
            import app.services.emotion_detector as ed_mod

            importlib.reload(ed_mod)
            detector = ed_mod.EmotionDetector()
            assert detector.enabled is False
        # Restore
        import importlib
        import app.services.emotion_detector as ed_mod

        importlib.reload(ed_mod)

    def test_enabled_property(self):
        detector = EmotionDetector()
        assert isinstance(detector.enabled, bool)


class TestClassify:
    def test_returns_neutral_when_disabled(self):
        detector = EmotionDetector.__new__(EmotionDetector)
        detector._enabled = False
        detector._face_mesh = None

        result = detector.classify(_make_jpeg(), _make_bbox())
        assert result.emotion == EmotionCategory.NEUTRAL
        assert result.confidence == 0.0

    def test_returns_neutral_on_invalid_bytes(self):
        detector = EmotionDetector()
        result = detector.classify(b"not a jpeg", _make_bbox())
        assert result.emotion == EmotionCategory.NEUTRAL
        assert result.confidence == 0.0

    def test_returns_neutral_on_tiny_crop(self):
        """Very small bounding box should return neutral."""
        detector = EmotionDetector()
        tiny_bbox = FaceBBox(x=0.0, y=0.0, width=0.01, height=0.01, confidence=0.9)
        result = detector.classify(_make_jpeg(), tiny_bbox)
        assert result.emotion == EmotionCategory.NEUTRAL
        assert result.confidence == 0.0

    def test_returns_emotion_result_type(self):
        detector = EmotionDetector()
        result = detector.classify(_make_jpeg(), _make_bbox())
        assert isinstance(result, EmotionResult)

    def test_returns_valid_emotion_category(self):
        """Result emotion must be one of the 6 valid categories."""
        detector = EmotionDetector()
        result = detector.classify(_make_jpeg(), _make_bbox())
        assert result.emotion in list(EmotionCategory)

    def test_confidence_in_valid_range(self):
        detector = EmotionDetector()
        result = detector.classify(_make_jpeg(), _make_bbox())
        assert 0.0 <= result.confidence <= 1.0

    def test_face_id_passed_through(self):
        detector = EmotionDetector()
        result = detector.classify(_make_jpeg(), _make_bbox(), face_id=42)
        assert result.face_id == 42

    def test_low_confidence_returns_neutral_with_zero_confidence(self):
        """When internal confidence < 0.3, must return NEUTRAL with 0.0 confidence."""
        detector = EmotionDetector()

        # Mock face mesh to return landmarks that produce low confidence
        mock_results = MagicMock()
        mock_results.multi_face_landmarks = None  # No landmarks found

        detector._face_mesh.process = MagicMock(return_value=mock_results)

        result = detector.classify(_make_jpeg(), _make_bbox())
        assert result.emotion == EmotionCategory.NEUTRAL
        assert result.confidence == 0.0

    def test_returns_neutral_on_exception(self):
        """Exceptions during processing should return neutral gracefully."""
        detector = EmotionDetector()
        detector._face_mesh.process = MagicMock(side_effect=RuntimeError("boom"))

        result = detector.classify(_make_jpeg(), _make_bbox())
        assert result.emotion == EmotionCategory.NEUTRAL
        assert result.confidence == 0.0


class TestClassifyAll:
    def test_returns_one_result_per_bbox(self):
        detector = EmotionDetector()
        bboxes = [_make_bbox() for _ in range(3)]
        results = detector.classify_all(_make_jpeg(), bboxes)
        assert len(results) == len(bboxes)

    def test_returns_empty_list_for_no_bboxes(self):
        detector = EmotionDetector()
        results = detector.classify_all(_make_jpeg(), [])
        assert results == []

    def test_face_ids_are_sequential(self):
        detector = EmotionDetector()
        bboxes = [_make_bbox() for _ in range(3)]
        results = detector.classify_all(_make_jpeg(), bboxes)
        assert [r.face_id for r in results] == [0, 1, 2]

    def test_all_results_are_emotion_result(self):
        detector = EmotionDetector()
        bboxes = [_make_bbox(), _make_bbox()]
        results = detector.classify_all(_make_jpeg(), bboxes)
        assert all(isinstance(r, EmotionResult) for r in results)


class TestHelpers:
    def test_distance_same_point(self):
        assert _distance((0.5, 0.5), (0.5, 0.5)) == 0.0

    def test_distance_known_value(self):
        assert _distance((0.0, 0.0), (3.0, 4.0)) == pytest.approx(5.0)

    def test_get_point_extracts_xy(self):
        mock_lm = MagicMock()
        mock_lm.x = 0.3
        mock_lm.y = 0.7
        landmarks = [mock_lm]
        assert _get_point(landmarks, 0) == (0.3, 0.7)


class TestApplyRules:
    """Test the rule-based classification logic directly."""

    def _make_detector(self):
        detector = EmotionDetector.__new__(EmotionDetector)
        detector._enabled = True
        detector._face_mesh = None
        return detector

    def test_neutral_baseline(self):
        """With all features at zero/neutral, should return neutral."""
        detector = self._make_detector()
        emotion, confidence = detector._apply_rules(
            mar=0.2, mouth_openness=0.05, ear=0.2,
            avg_brow_height=0.035, inner_brow_dist=0.12,
            avg_corner_offset=0.0,
        )
        assert emotion == EmotionCategory.NEUTRAL

    def test_surprised_high_openness(self):
        """Wide open mouth + wide eyes + raised brows = surprised."""
        detector = self._make_detector()
        emotion, confidence = detector._apply_rules(
            mar=0.6, mouth_openness=0.3, ear=0.3,
            avg_brow_height=0.045, inner_brow_dist=0.12,
            avg_corner_offset=0.0,
        )
        assert emotion == EmotionCategory.SURPRISED
        assert confidence >= 0.3

    def test_happy_smile(self):
        """Mouth corners pulled up = happy."""
        detector = self._make_detector()
        emotion, confidence = detector._apply_rules(
            mar=0.25, mouth_openness=0.05, ear=0.2,
            avg_brow_height=0.035, inner_brow_dist=0.12,
            avg_corner_offset=0.025,
        )
        assert emotion == EmotionCategory.HAPPY
        assert confidence >= 0.3

    def test_angry_furrowed_brows(self):
        """Furrowed brows + squinted eyes = angry."""
        detector = self._make_detector()
        emotion, confidence = detector._apply_rules(
            mar=0.2, mouth_openness=0.05, ear=0.15,
            avg_brow_height=0.02, inner_brow_dist=0.05,
            avg_corner_offset=0.0,
        )
        assert emotion == EmotionCategory.ANGRY
        assert confidence >= 0.3

    def test_sad_frown(self):
        """Mouth corners pulled down = sad."""
        detector = self._make_detector()
        emotion, confidence = detector._apply_rules(
            mar=0.2, mouth_openness=0.05, ear=0.2,
            avg_brow_height=0.03, inner_brow_dist=0.12,
            avg_corner_offset=-0.025,
        )
        assert emotion == EmotionCategory.SAD
        assert confidence >= 0.3

    def test_confidence_capped_at_one(self):
        """Confidence should never exceed 1.0."""
        detector = self._make_detector()
        _, confidence = detector._apply_rules(
            mar=1.0, mouth_openness=1.0, ear=1.0,
            avg_brow_height=1.0, inner_brow_dist=0.01,
            avg_corner_offset=1.0,
        )
        assert confidence <= 1.0
