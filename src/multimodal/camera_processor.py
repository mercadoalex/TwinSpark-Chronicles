import cv2
import mediapipe as mp
import time
import math

class CameraProcessor:
    def __init__(self, camera_index=0, on_event=None):
        self.camera_index = camera_index
        self.cap = None
        self.on_event = on_event
        self.last_gesture_time = 0
        
        # Initialize MediaPipe Face Detection
        self.mp_face = mp.solutions.face_detection
        self.face_detection = self.mp_face.FaceDetection(
            min_detection_confidence=0.5,
            model_selection=0 # 0 for close-range (within 2 meters)
        )
        
        # Initialize MediaPipe Hands for gesture tracking
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=4, # Tracking potentially 4 hands (2 per child)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        self.mp_drawing = mp.solutions.drawing_utils
        
    def start(self):
        """Initializes the webcam."""
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_index)
            # Set resolution (tradeoff between quality and speed)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
    def stop(self):
        """Releases the webcam."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            
    def process_frame(self):
        """Reads a frame, processes faces and gestures, and returns the annotated frame and data."""
        if self.cap is None or not self.cap.isOpened():
            return None, {}
            
        success, image = self.cap.read()
        if not success:
            return None, {}
            
        # Flip image horizontally for a selfie-view display
        image = cv2.flip(image, 1)
        # Convert BGR to RGB for MediaPipe
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Process detections
        face_results = self.face_detection.process(rgb_image)
        hand_results = self.hands.process(rgb_image)
        
        frame_data = {
            "faces_detected": 0,
            "face_locations": [],
            "gestures": [],
            "timestamp": time.time()
        }
        
        # Annotate faces
        if face_results.detections:
            frame_data["faces_detected"] = len(face_results.detections)
            for detection in face_results.detections:
                self.mp_drawing.draw_detection(image, detection)
                # Store normalized bounding box
                bbox = detection.location_data.relative_bounding_box
                frame_data["face_locations"].append({
                    "xmin": bbox.xmin, "ymin": bbox.ymin,
                    "width": bbox.width, "height": bbox.height
                })
                
        # Annotate hands and detect gestures
        if hand_results.multi_hand_landmarks:
            for hand_landmarks, hand_class in zip(hand_results.multi_hand_landmarks, hand_results.multi_handedness):
                self.mp_drawing.draw_landmarks(
                    image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                
                # Basic gesture detection
                gesture = self._detect_gesture(hand_landmarks)
                if gesture:
                    hand_label = hand_class.classification[0].label # "Left" or "Right"
                    
                    # Determine physical zone (Left side of screen vs Right side of screen)
                    # Coordinates are normalized 0-1. 0 is Left, 1 is Right.
                    x_pos = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].x
                    zone = "Ale" if x_pos < 0.5 else "Sofi"
                    
                    frame_data["gestures"].append({
                        "hand": hand_label, 
                        "gesture": gesture,
                        "zone": zone
                    })
                    
                    # Draw gesture text near the wrist
                    h, w, _ = image.shape
                    wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
                    cx, cy = int(wrist.x * w), int(wrist.y * h)
                    cv2.putText(image, f"{zone}: {gesture}", (cx, cy - 20), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                
                    # Debounce callback (prevent firing 30 times a second)
                    current_time = time.time()
                    if self.on_event and (current_time - self.last_gesture_time) > 2.0:
                        self.last_gesture_time = current_time
                        
                        # Map gestures to story actions
                        action = None
                        if gesture == "Thumbs Up":
                            action = "choose_left" if zone == "Ale" else "choose_right"
                        elif gesture == "Wave/High-Five":
                            action = "high_five"
                            
                        if action:
                            self.on_event({
                                "action": action,
                                "user_id": "c1" if zone == "Ale" else "c2"
                            })
                                
        # Optional: Add simulated basic emotion text above faces for now
        # until a dedicated emotion model is integrated
        if frame_data["faces_detected"] > 0:
            h, w, _ = image.shape
            for i, face_loc in enumerate(frame_data["face_locations"]):
                # Determine which child it might be based on X position (very naive)
                # Assuming they sit next to each other
                name = "Ale" if face_loc["xmin"] < 0.5 else "Sofi"
                x_px = int(face_loc["xmin"] * w)
                y_px = int(face_loc["ymin"] * h)
                cv2.putText(image, f"Detected: {name} (Tracking)", (x_px, max(20, y_px - 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
                            
        return image, frame_data
        
    def _detect_gesture(self, hand_landmarks):
        """Basic heuristic-based gesture detection."""
        # Get landmarks
        lm = hand_landmarks.landmark
        
        # Thumb tips and bases
        thumb_tip = lm[self.mp_hands.HandLandmark.THUMB_TIP]
        thumb_ip = lm[self.mp_hands.HandLandmark.THUMB_IP]
        
        # Fingers tips and pips (middle joints)
        index_tip = lm[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        index_pip = lm[self.mp_hands.HandLandmark.INDEX_FINGER_PIP]
        
        middle_tip = lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        middle_pip = lm[self.mp_hands.HandLandmark.MIDDLE_FINGER_PIP]
        
        ring_tip = lm[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        ring_pip = lm[self.mp_hands.HandLandmark.RING_FINGER_PIP]
        
        pinky_tip = lm[self.mp_hands.HandLandmark.PINKY_TIP]
        pinky_pip = lm[self.mp_hands.HandLandmark.PINKY_PIP]
        
        # Check if fingers are up (y coordinate is visually lower = physically higher in image)
        index_up = index_tip.y < index_pip.y
        middle_up = middle_tip.y < middle_pip.y
        ring_up = ring_tip.y < ring_pip.y
        pinky_up = pinky_tip.y < pinky_pip.y
        
        # Check thumb orientation (is it pointing up?)
        # Wrist is at bottom (highest Y). Tip should be higher (lower Y) than IP.
        thumb_up = thumb_tip.y < thumb_ip.y - 0.05 # Adding a threshold to ensure it's distinctly up
        
        # Wave or High Five: All fingers up
        if index_up and middle_up and ring_up and pinky_up:
            return "Wave/High-Five"
            
        # Thumbs up: Only thumb is up, other fingers curled down (their tips are below their pips physically)
        if thumb_up and not index_up and not middle_up and not ring_up and not pinky_up:
            return "Thumbs Up"
            
        return None

if __name__ == "__main__":
    print("Initializing CameraProcessor...")
    processor = CameraProcessor(camera_index=0)
    processor.start()
    
    print("Starting webcam loop. Press 'q' to quit.")
    try:
        while True:
            annotated_frame, data = processor.process_frame()
            if annotated_frame is not None:
                # Add overlay text
                cv2.putText(annotated_frame, f"Faces: {data['faces_detected']} | Gestures: {len(data['gestures'])}", 
                            (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow("TwinSpark Camera Test", annotated_frame)
                
            if cv2.waitKey(5) & 0xFF == ord('q'):
                break
    finally:
        processor.stop()
        cv2.destroyAllWindows()
