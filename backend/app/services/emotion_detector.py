"""
Emotion Detection Service using MediaPipe Face Mesh landmarks.
Classifies facial expressions into one of 6 emotion categories:
happy, sad, surprised, angry, scared, neutral.

Uses geometric features derived from face mesh landmarks:
- Mouth Aspect Ratio (MAR) for smile/surprise detection
- Eye Aspect Ratio (EAR) for blink/squint detection
- Eyebrow position relative to eyes for angry/sad
- Overall face openness for surprised/scared
"""

import io
import logging
import math

import numpy as np
from PIL import Image

from app.models.multimodal import EmotionCategory, EmotionResult, FaceBBox

logger = logging.getLogger(__name__)

# MediaPipe Face Mesh landmark indices for key facial features.
# Reference: https://github.com/google/mediapipe/blob/master/mediapipe/modules/face_geometry/data/canonical_face_model_uv_visualization.png

# Mouth landmarks (outer lips)
_UPPER_LIP_TOP = 13
_LOWER_LIP_BOTTOM = 14
_MOUTH_LEFT = 61
_MOUTH_RIGHT = 291

# Inner mouth (for openness)
_UPPER_INNER_LIP = 82
_LOWER_INNER_LIP = 87

# Left eye landmarks
_LEFT_EYE_TOP = 159
_LEFT_EYE_BOTTOM = 145
_LEFT_EYE_LEFT = 33
_LEFT_EYE_RIGHT = 133

# Right eye landmarks
_RIGHT_EYE_TOP = 386
_RIGHT_EYE_BOTTOM = 374
_RIGHT_EYE_LEFT = 362
_RIGHT_EYE_RIGHT = 263

# Eyebrow landmarks
_LEFT_EYEBROW_TOP = 105
_RIGHT_EYEBROW_TOP = 334
_LEFT_EYEBROW_INNER = 107
_RIGHT_EYEBROW_INNER = 336

# Nose tip (reference point)
_NOSE_TIP = 1

# Confidence threshold below which we default to neutral
_CONFIDENCE_THRESHOLD = 0.3


def _distance(p1, p2) -> float:
    """Euclidean distance between two landmark points (x, y)."""
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def _get_point(landmarks, idx) -> tuple[float, float]:
    """Extract (x, y) from a Face Mesh landmark by index."""
    lm = landmarks[idx]
    return (lm.x, lm.y)


class EmotionDetector:
    """
    Classifies facial expressions using MediaPipe Face Mesh landmarks.
    Gracefully degrades if MediaPipe fails to initialize.
    """

    def __init__(self):
        self._enabled = False
        self._face_mesh = None

        try:
            import mediapipe as mp

            self._face_mesh = mp.solutions.face_mesh.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5,
            )
            self._enabled = True
            logger.info(
                "✅ Emotion detector initialized with MediaPipe Face Mesh"
            )
        except Exception as e:
            logger.warning(f"⚠️  Emotion detector disabled: {e}")
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def classify(
        self, frame_bytes: bytes, bbox: FaceBBox, face_id: int = 0
    ) -> EmotionResult:
        """Classify the emotion of a single face region.

        Crops the face from the frame using the bounding box, runs
        MediaPipe Face Mesh, and classifies the emotion based on
        landmark geometry.

        Args:
            frame_bytes: Full JPEG-encoded frame.
            bbox: Normalized bounding box of the face.
            face_id: Identifier for this face in the results.

        Returns:
            EmotionResult with classified emotion and confidence.
            Returns NEUTRAL with confidence 0.0 when detector is
            disabled or processing fails.
        """
        if not self._enabled:
            return EmotionResult(
                face_id=face_id,
                emotion=EmotionCategory.NEUTRAL,
                confidence=0.0,
            )

        try:
            # Decode full frame
            image = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
            img_w, img_h = image.size

            # Crop face region from bounding box (normalized coords)
            x1 = max(0, int(bbox.x * img_w))
            y1 = max(0, int(bbox.y * img_h))
            x2 = min(img_w, int((bbox.x + bbox.width) * img_w))
            y2 = min(img_h, int((bbox.y + bbox.height) * img_h))

            # Ensure minimum crop size
            if x2 - x1 < 10 or y2 - y1 < 10:
                return EmotionResult(
                    face_id=face_id,
                    emotion=EmotionCategory.NEUTRAL,
                    confidence=0.0,
                )

            face_crop = image.crop((x1, y1, x2, y2))
            face_array = np.array(face_crop)

            # Run Face Mesh on the cropped face
            results = self._face_mesh.process(face_array)

            if not results.multi_face_landmarks:
                return EmotionResult(
                    face_id=face_id,
                    emotion=EmotionCategory.NEUTRAL,
                    confidence=0.0,
                )

            landmarks = results.multi_face_landmarks[0].landmark
            emotion, confidence = self._classify_from_landmarks(landmarks)

            # Default to neutral when confidence is too low
            if confidence < _CONFIDENCE_THRESHOLD:
                return EmotionResult(
                    face_id=face_id,
                    emotion=EmotionCategory.NEUTRAL,
                    confidence=0.0,
                )

            return EmotionResult(
                face_id=face_id,
                emotion=emotion,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Emotion classification failed: {e}")
            return EmotionResult(
                face_id=face_id,
                emotion=EmotionCategory.NEUTRAL,
                confidence=0.0,
            )

    def classify_all(
        self, frame_bytes: bytes, bboxes: list[FaceBBox]
    ) -> list[EmotionResult]:
        """Classify emotions for all detected faces.

        Args:
            frame_bytes: Full JPEG-encoded frame.
            bboxes: List of face bounding boxes.

        Returns:
            List of EmotionResult, exactly one per input bbox.
        """
        return [
            self.classify(frame_bytes, bbox, face_id=i)
            for i, bbox in enumerate(bboxes)
        ]

    def _classify_from_landmarks(
        self, landmarks
    ) -> tuple[EmotionCategory, float]:
        """Classify emotion from Face Mesh landmarks using geometric features.

        Computes:
        - Mouth Aspect Ratio (MAR): vertical/horizontal mouth ratio
        - Mouth openness: inner lip distance
        - Eye Aspect Ratio (EAR): vertical/horizontal eye ratio
        - Eyebrow height: distance from eyebrow to eye relative to face height
        - Smile indicator: mouth width relative to resting + upward curvature

        Returns:
            Tuple of (EmotionCategory, confidence).
        """
        # Extract key points
        upper_lip = _get_point(landmarks, _UPPER_LIP_TOP)
        lower_lip = _get_point(landmarks, _LOWER_LIP_BOTTOM)
        mouth_left = _get_point(landmarks, _MOUTH_LEFT)
        mouth_right = _get_point(landmarks, _MOUTH_RIGHT)
        upper_inner = _get_point(landmarks, _UPPER_INNER_LIP)
        lower_inner = _get_point(landmarks, _LOWER_INNER_LIP)

        left_eye_top = _get_point(landmarks, _LEFT_EYE_TOP)
        left_eye_bottom = _get_point(landmarks, _LEFT_EYE_BOTTOM)
        left_eye_left = _get_point(landmarks, _LEFT_EYE_LEFT)
        left_eye_right = _get_point(landmarks, _LEFT_EYE_RIGHT)

        right_eye_top = _get_point(landmarks, _RIGHT_EYE_TOP)
        right_eye_bottom = _get_point(landmarks, _RIGHT_EYE_BOTTOM)
        right_eye_left = _get_point(landmarks, _RIGHT_EYE_LEFT)
        right_eye_right = _get_point(landmarks, _RIGHT_EYE_RIGHT)

        left_brow = _get_point(landmarks, _LEFT_EYEBROW_TOP)
        right_brow = _get_point(landmarks, _RIGHT_EYEBROW_TOP)
        left_brow_inner = _get_point(landmarks, _LEFT_EYEBROW_INNER)
        right_brow_inner = _get_point(landmarks, _RIGHT_EYEBROW_INNER)

        nose_tip = _get_point(landmarks, _NOSE_TIP)

        # --- Compute geometric features ---

        # Mouth Aspect Ratio: vertical opening / horizontal width
        mouth_h = _distance(upper_lip, lower_lip)
        mouth_w = _distance(mouth_left, mouth_right)
        mar = mouth_h / mouth_w if mouth_w > 0 else 0.0

        # Inner mouth openness (more sensitive to open mouth)
        inner_mouth_h = _distance(upper_inner, lower_inner)
        mouth_openness = inner_mouth_h / mouth_w if mouth_w > 0 else 0.0

        # Eye Aspect Ratio (average of both eyes)
        left_ear = _distance(left_eye_top, left_eye_bottom) / (
            _distance(left_eye_left, left_eye_right) or 1e-6
        )
        right_ear = _distance(right_eye_top, right_eye_bottom) / (
            _distance(right_eye_left, right_eye_right) or 1e-6
        )
        ear = (left_ear + right_ear) / 2.0

        # Eyebrow height: distance from brow to eye center, normalized
        left_eye_center_y = (left_eye_top[1] + left_eye_bottom[1]) / 2.0
        right_eye_center_y = (right_eye_top[1] + right_eye_bottom[1]) / 2.0
        left_brow_dist = left_eye_center_y - left_brow[1]
        right_brow_dist = right_eye_center_y - right_brow[1]
        avg_brow_height = (left_brow_dist + right_brow_dist) / 2.0

        # Inner eyebrow distance (furrowed brows come closer together)
        inner_brow_dist = _distance(left_brow_inner, right_brow_inner)

        # Mouth corner position relative to mouth center
        # Positive = corners pulled up (smile), negative = pulled down (frown)
        mouth_center_y = (upper_lip[1] + lower_lip[1]) / 2.0
        left_corner_y = mouth_left[1]
        right_corner_y = mouth_right[1]
        avg_corner_offset = (
            (mouth_center_y - left_corner_y)
            + (mouth_center_y - right_corner_y)
        ) / 2.0

        # --- Classify based on feature thresholds ---
        return self._apply_rules(
            mar=mar,
            mouth_openness=mouth_openness,
            ear=ear,
            avg_brow_height=avg_brow_height,
            inner_brow_dist=inner_brow_dist,
            avg_corner_offset=avg_corner_offset,
        )

    def _apply_rules(
        self,
        mar: float,
        mouth_openness: float,
        ear: float,
        avg_brow_height: float,
        inner_brow_dist: float,
        avg_corner_offset: float,
    ) -> tuple[EmotionCategory, float]:
        """Apply rule-based classification from geometric features.

        Each rule produces a score; the emotion with the highest score wins.
        Confidence is derived from how strongly the features match.
        """
        scores: dict[EmotionCategory, float] = {
            EmotionCategory.HAPPY: 0.0,
            EmotionCategory.SAD: 0.0,
            EmotionCategory.SURPRISED: 0.0,
            EmotionCategory.ANGRY: 0.0,
            EmotionCategory.SCARED: 0.0,
            EmotionCategory.NEUTRAL: 0.0,
        }

        # SURPRISED: wide open mouth + wide open eyes + raised brows
        if mouth_openness > 0.15 and ear > 0.25 and avg_brow_height > 0.04:
            scores[EmotionCategory.SURPRISED] = (
                0.3 + min(mouth_openness / 0.4, 1.0) * 0.4
                + min(ear / 0.4, 1.0) * 0.3
            )

        # HAPPY: mouth corners pulled up + moderate mouth width
        if avg_corner_offset > 0.005:
            scores[EmotionCategory.HAPPY] = (
                0.3 + min(avg_corner_offset / 0.03, 1.0) * 0.5
                + (0.2 if mar < 0.4 else 0.0)
            )

        # ANGRY: furrowed brows (close together, low) + squinted eyes
        if inner_brow_dist < 0.08 and avg_brow_height < 0.03:
            scores[EmotionCategory.ANGRY] = (
                0.3 + (1.0 - min(inner_brow_dist / 0.08, 1.0)) * 0.4
                + (1.0 - min(ear / 0.3, 1.0)) * 0.3
            )

        # SAD: mouth corners pulled down + low brows
        if avg_corner_offset < -0.005:
            scores[EmotionCategory.SAD] = (
                0.3 + min(abs(avg_corner_offset) / 0.03, 1.0) * 0.4
                + (0.3 if avg_brow_height < 0.04 else 0.0)
            )

        # SCARED: open mouth + wide eyes + raised brows (similar to surprised but with tension)
        if mouth_openness > 0.1 and ear > 0.28 and avg_brow_height > 0.05:
            scores[EmotionCategory.SCARED] = (
                0.25 + min(mouth_openness / 0.3, 1.0) * 0.3
                + min(ear / 0.4, 1.0) * 0.25
                + min(avg_brow_height / 0.07, 1.0) * 0.2
            )

        # NEUTRAL: baseline score — wins when nothing else is strong
        scores[EmotionCategory.NEUTRAL] = 0.25

        # Pick the highest-scoring emotion
        best_emotion = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_emotion]

        # Normalize confidence to [0, 1]
        confidence = min(best_score, 1.0)

        return best_emotion, confidence
