"""
Emotion Detector Module
Extracts emotions from facial expressions using MediaPipe and maps them to EmotionalState enum.
"""

import cv2
import mediapipe as mp
import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum

# Import from models
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import EmotionalState


class FacialExpression(Enum):
    """Detected facial expressions"""
    HAPPY = "happy"
    SAD = "sad"
    EXCITED = "excited"
    SCARED = "scared"
    ANGRY = "angry"
    SURPRISED = "surprised"
    NEUTRAL = "neutral"


class EmotionDetector:
    """
    Detects emotions from facial landmarks using MediaPipe Face Mesh.
    Maps facial expressions to EmotionalState for the Twin Intelligence Engine.
    """
    
    def __init__(self):
        # Initialize MediaPipe Face Mesh for detailed facial analysis
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=2,  # Track up to 2 children
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # Key landmark indices for emotion detection
        # Based on MediaPipe's 468 facial landmarks
        self.MOUTH_INDICES = [61, 291, 0, 17]  # Corners and center of mouth
        self.EYE_INDICES = {
            'left': [33, 133, 159, 145],  # Left eye landmarks
            'right': [362, 263, 386, 374]  # Right eye landmarks
        }
        self.EYEBROW_INDICES = {
            'left': [70, 63, 105, 66],
            'right': [300, 293, 334, 296]
        }
        
        # Emotion thresholds (tuned for 6-year-olds)
        self.SMILE_THRESHOLD = 0.02
        self.EYE_OPEN_THRESHOLD = 0.015
        self.EYEBROW_RAISE_THRESHOLD = 0.03
        
    def detect_emotions(self, frame: np.ndarray) -> List[Dict]:
        """
        Detect emotions from facial landmarks in a video frame.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            List of dicts with emotion data for each detected face:
            [
                {
                    'face_id': 0,
                    'expression': FacialExpression,
                    'emotional_state': EmotionalState,
                    'confidence': float,
                    'position': (x, y, w, h)
                }
            ]
        """
        if frame is None:
            return []
            
        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.face_mesh.process(rgb_frame)
        
        emotions = []
        
        if results.multi_face_landmarks:
            for face_id, face_landmarks in enumerate(results.multi_face_landmarks):
                # Extract key measurements
                expression, confidence = self._analyze_face_landmarks(face_landmarks, frame.shape)
                emotional_state = self._map_to_emotional_state(expression)
                
                # Get face bounding box
                h, w = frame.shape[:2]
                landmarks_points = [(int(lm.x * w), int(lm.y * h)) for lm in face_landmarks.landmark]
                x_coords = [p[0] for p in landmarks_points]
                y_coords = [p[1] for p in landmarks_points]
                
                position = (
                    min(x_coords), min(y_coords),
                    max(x_coords) - min(x_coords),
                    max(y_coords) - min(y_coords)
                )
                
                emotions.append({
                    'face_id': face_id,
                    'expression': expression,
                    'emotional_state': emotional_state,
                    'confidence': confidence,
                    'position': position
                })
                
        return emotions
    
    def _analyze_face_landmarks(
        self, 
        face_landmarks, 
        frame_shape: Tuple[int, int]
    ) -> Tuple[FacialExpression, float]:
        """
        Analyze facial landmarks to determine expression.
        
        Returns:
            (expression, confidence_score)
        """
        h, w = frame_shape[:2]
        landmarks = face_landmarks.landmark
        
        # Calculate key measurements
        mouth_openness = self._calculate_mouth_openness(landmarks, h, w)
        eye_openness = self._calculate_eye_openness(landmarks, h, w)
        eyebrow_position = self._calculate_eyebrow_position(landmarks, h, w)
        mouth_curvature = self._calculate_mouth_curvature(landmarks, h, w)
        
        # Detect expression based on measurements
        confidence = 0.5  # Base confidence
        
        # Happy: Smile + normal eyes
        if mouth_curvature > self.SMILE_THRESHOLD and eye_openness > 0.01:
            return FacialExpression.HAPPY, 0.8
        
        # Excited: Big smile + wide eyes
        if mouth_curvature > self.SMILE_THRESHOLD * 1.5 and eye_openness > self.EYE_OPEN_THRESHOLD:
            return FacialExpression.EXCITED, 0.85
        
        # Surprised: Raised eyebrows + wide eyes + open mouth
        if eyebrow_position > self.EYEBROW_RAISE_THRESHOLD and eye_openness > self.EYE_OPEN_THRESHOLD:
            if mouth_openness > 0.05:
                return FacialExpression.SURPRISED, 0.8
        
        # Sad: Mouth down + slightly closed eyes
        if mouth_curvature < -self.SMILE_THRESHOLD * 0.5 and eye_openness < 0.012:
            return FacialExpression.SAD, 0.75
        
        # Scared: Wide eyes + slightly open mouth + raised eyebrows
        if eye_openness > self.EYE_OPEN_THRESHOLD and eyebrow_position > self.EYEBROW_RAISE_THRESHOLD * 0.7:
            return FacialExpression.SCARED, 0.7
        
        # Angry: Furrowed brows + tight mouth
        if eyebrow_position < -0.01 and mouth_openness < 0.02:
            return FacialExpression.ANGRY, 0.7
        
        # Default to neutral
        return FacialExpression.NEUTRAL, 0.6
    
    def _calculate_mouth_openness(self, landmarks, h: int, w: int) -> float:
        """Calculate how open the mouth is (vertical distance)"""
        upper_lip = landmarks[13]  # Upper lip center
        lower_lip = landmarks[14]  # Lower lip center
        
        distance = abs(upper_lip.y - lower_lip.y)
        return distance
    
    def _calculate_mouth_curvature(self, landmarks, h: int, w: int) -> float:
        """Calculate mouth curvature (positive = smile, negative = frown)"""
        left_corner = landmarks[61]
        right_corner = landmarks[291]
        center = landmarks[13]
        
        # Average y-position of corners
        corner_y = (left_corner.y + right_corner.y) / 2
        
        # Positive if corners higher than center (smile)
        # Negative if corners lower than center (frown)
        return center.y - corner_y
    
    def _calculate_eye_openness(self, landmarks, h: int, w: int) -> float:
        """Calculate average eye openness"""
        left_eye_top = landmarks[159]
        left_eye_bottom = landmarks[145]
        right_eye_top = landmarks[386]
        right_eye_bottom = landmarks[374]
        
        left_openness = abs(left_eye_top.y - left_eye_bottom.y)
        right_openness = abs(right_eye_top.y - right_eye_bottom.y)
        
        return (left_openness + right_openness) / 2
    
    def _calculate_eyebrow_position(self, landmarks, h: int, w: int) -> float:
        """Calculate eyebrow height (positive = raised, negative = lowered)"""
        # Left eyebrow
        left_brow = landmarks[70]
        left_eye_top = landmarks[159]
        
        # Right eyebrow
        right_brow = landmarks[300]
        right_eye_top = landmarks[386]
        
        left_distance = left_eye_top.y - left_brow.y
        right_distance = right_eye_top.y - right_brow.y
        
        return (left_distance + right_distance) / 2
    
    def _map_to_emotional_state(self, expression: FacialExpression) -> EmotionalState:
        """
        Map facial expression to EmotionalState for Twin Intelligence Engine.
        """
        mapping = {
            FacialExpression.HAPPY: EmotionalState.JOYFUL,
            FacialExpression.EXCITED: EmotionalState.EXCITED,
            FacialExpression.SAD: EmotionalState.SAD,
            FacialExpression.SCARED: EmotionalState.SCARED,
            FacialExpression.ANGRY: EmotionalState.FRUSTRATED,
            FacialExpression.SURPRISED: EmotionalState.CURIOUS,
            FacialExpression.NEUTRAL: EmotionalState.CALM
        }
        
        return mapping.get(expression, EmotionalState.CALM)
    
    def get_emotion_emoji(self, expression: FacialExpression) -> str:
        """Get emoji representation of expression"""
        emoji_map = {
            FacialExpression.HAPPY: "😊",
            FacialExpression.EXCITED: "🤩",
            FacialExpression.SAD: "😢",
            FacialExpression.SCARED: "😨",
            FacialExpression.ANGRY: "😠",
            FacialExpression.SURPRISED: "😲",
            FacialExpression.NEUTRAL: "😐"
        }
        return emoji_map.get(expression, "😐")
    
    def cleanup(self):
        """Release resources"""
        self.face_mesh.close()


# Test function
if __name__ == "__main__":
    import cv2
    
    detector = EmotionDetector()
    cap = cv2.VideoCapture(0)
    
    print("🎭 Emotion Detector Test")
    print("Press 'q' to quit")
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        emotions = detector.detect_emotions(frame)
        
        # Draw results
        for emotion_data in emotions:
            x, y, w, h = emotion_data['position']
            expression = emotion_data['expression']
            emotional_state = emotion_data['emotional_state']
            confidence = emotion_data['confidence']
            emoji = detector.get_emotion_emoji(expression)
            
            # Draw bounding box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Draw emotion text
            text = f"{emoji} {expression.value} -> {emotional_state.value}"
            cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.6, (0, 255, 0), 2)
        
        cv2.imshow('Emotion Detection', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    detector.cleanup()
