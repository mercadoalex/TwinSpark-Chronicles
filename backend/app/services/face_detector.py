"""
Face Detection Service using MediaPipe Face Detection.
Detects child faces in video frames for emotion analysis pipeline.
Uses short-range model optimized for faces within 2 meters (children at screen).
"""

import io
import logging
from PIL import Image
import numpy as np

from app.models.multimodal import FaceBBox

logger = logging.getLogger(__name__)


class FaceDetector:
    """
    Detects faces in JPEG video frames using MediaPipe Face Detection.
    Gracefully degrades if MediaPipe fails to initialize.
    """

    def __init__(self, min_confidence: float = 0.5):
        self._min_confidence = min_confidence
        self._enabled = False
        self._face_detection = None

        try:
            import mediapipe as mp

            self._face_detection = mp.solutions.face_detection.FaceDetection(
                model_selection=0,  # 0 = short-range (< 2m)
                min_detection_confidence=min_confidence,
            )
            self._enabled = True
            logger.info("✅ Face detector initialized with MediaPipe (short-range model)")
        except Exception as e:
            logger.warning(f"⚠️  Face detector disabled: {e}")
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def detect(self, frame_bytes: bytes) -> list[FaceBBox]:
        """Detect faces in a JPEG-encoded frame.

        Args:
            frame_bytes: JPEG-encoded image bytes.

        Returns:
            List of FaceBBox with normalized coordinates and confidence scores.
            Only faces with confidence >= min_confidence are returned.
            Returns empty list if no faces detected or detector is disabled.
        """
        if not self._enabled:
            return []

        try:
            # Decode JPEG bytes into RGB numpy array
            image = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
            image_array = np.array(image)

            # Run MediaPipe face detection
            results = self._face_detection.process(image_array)

            if not results.detections:
                return []

            faces: list[FaceBBox] = []
            for detection in results.detections:
                confidence = detection.score[0]

                # Only include faces meeting the confidence threshold
                if confidence < self._min_confidence:
                    continue

                bbox = detection.location_data.relative_bounding_box

                # Clamp normalized coordinates to [0, 1]
                x = max(0.0, min(1.0, bbox.xmin))
                y = max(0.0, min(1.0, bbox.ymin))
                width = max(0.0, min(1.0, bbox.width))
                height = max(0.0, min(1.0, bbox.height))

                # Skip degenerate bounding boxes
                if width <= 0.0 or height <= 0.0:
                    continue

                faces.append(
                    FaceBBox(
                        x=x,
                        y=y,
                        width=width,
                        height=height,
                        confidence=confidence,
                    )
                )

            return faces

        except Exception as e:
            logger.error(f"Face detection failed: {e}")
            return []
