"""
Input Manager Module
Orchestrates camera, audio, and emotion detection for multimodal storytelling.
"""

import cv2
import threading
import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import EmotionalState, ChildProfile
from multimodal.camera_processor import CameraProcessor
from multimodal.audio_processor import AudioProcessor
from multimodal.emotion_detector import EmotionDetector


@dataclass
class MultimodalInput:
    """Combined multimodal input data at a given timestamp"""
    timestamp: datetime
    
    # Camera data
    faces_detected: int
    face_positions: List[tuple]
    gestures: List[str]
    
    # Emotion data
    emotions: List[Dict]  # From emotion_detector
    
    # Audio data
    voice_command: Optional[str]
    transcription: Optional[str]
    
    # Processed frame
    annotated_frame: Optional[any]


class InputManager:
    """
    Central hub for all multimodal inputs.
    Coordinates camera, audio, and emotion detection.
    """
    
    def __init__(
        self, 
        on_input_callback: Optional[Callable] = None,
        camera_index: int = 0
    ):
        """
        Args:
            on_input_callback: Function called with MultimodalInput when new data arrives
            camera_index: Camera device index (usually 0)
        """
        self.on_input_callback = on_input_callback
        
        # Initialize processors
        self.camera = CameraProcessor(camera_index=camera_index)
        self.audio = AudioProcessor()
        self.emotion_detector = EmotionDetector()
        
        # State tracking
        self.is_running = False
        self.processing_thread = None
        self._stop_event = threading.Event()
        
        # Latest data
        self.latest_input: Optional[MultimodalInput] = None
        self.children_mapping: Dict[int, ChildProfile] = {}  # face_id -> ChildProfile
        
        # Performance settings
        self.fps_target = 10  # Process 10 frames per second
        self.frame_interval = 1.0 / self.fps_target
        
        print("🎮 Input Manager initialized")
    
    def start(self):
        """Start all input processors"""
        if self.is_running:
            print("⚠️ Input Manager already running")
            return
        
        print("🚀 Starting Input Manager...")
        
        # Start camera
        self.camera.start()
        
        # Start audio listening
        self.audio.start_listening(callback=self._on_audio_detected)
        
        # Start processing thread
        self.is_running = True
        self._stop_event.clear()
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        print("✅ Input Manager running")
    
    def stop(self):
        """Stop all input processors"""
        if not self.is_running:
            return
        
        print("🛑 Stopping Input Manager...")
        
        self.is_running = False
        self._stop_event.set()
        
        # Stop audio
        self.audio.stop_listening()
        
        # Stop camera
        self.camera.stop()
        
        # Clean up emotion detector
        self.emotion_detector.cleanup()
        
        # Wait for processing thread
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        
        print("✅ Input Manager stopped")
    
    def _processing_loop(self):
        """Main processing loop that runs in a separate thread"""
        print("🔄 Processing loop started")
        
        while not self._stop_event.is_set():
            start_time = time.time()
            
            try:
                # Process one frame
                frame, camera_data = self.camera.process_frame()
                
                if frame is not None:
                    # Detect emotions
                    emotions = self.emotion_detector.detect_emotions(frame)
                    
                    # Get latest audio data
                    voice_command = self.audio.latest_command
                    transcription = self.audio.latest_transcription
                    
                    # Reset audio data after reading
                    self.audio.latest_command = None
                    self.audio.latest_transcription = ""
                    
                    # Create multimodal input
                    multimodal_input = MultimodalInput(
                        timestamp=datetime.now(),
                        faces_detected=camera_data.get('face_count', 0),
                        face_positions=camera_data.get('face_positions', []),
                        gestures=camera_data.get('gestures', []),
                        emotions=emotions,
                        voice_command=voice_command,
                        transcription=transcription,
                        annotated_frame=frame
                    )
                    
                    # Update latest
                    self.latest_input = multimodal_input
                    
                    # Call callback if provided
                    if self.on_input_callback:
                        self.on_input_callback(multimodal_input)
                    
            except Exception as e:
                print(f"❌ Error in processing loop: {e}")
            
            # Maintain target FPS
            elapsed = time.time() - start_time
            sleep_time = max(0, self.frame_interval - elapsed)
            time.sleep(sleep_time)
        
        print("🔄 Processing loop stopped")
    
    def _on_audio_detected(self, text: str):
        """Callback when audio is detected"""
        # Audio processor already updates its own state
        # This is just for logging or additional processing
        if text:
            print(f"🎤 Heard: '{text}'")
    
    def map_face_to_child(self, face_id: int, child_profile: ChildProfile):
        """
        Map a detected face to a specific child profile.
        This allows tracking which child is which.
        
        Args:
            face_id: Index from camera processor (0 or 1)
            child_profile: The child's profile
        """
        self.children_mapping[face_id] = child_profile
        print(f"👤 Mapped face {face_id} to {child_profile.name}")
    
    def get_child_emotion(self, child_profile: ChildProfile) -> Optional[EmotionalState]:
        """
        Get the current emotional state of a specific child.
        
        Args:
            child_profile: The child to check
            
        Returns:
            EmotionalState or None if not detected
        """
        if not self.latest_input:
            return None
        
        # Find face_id for this child
        face_id = None
        for fid, profile in self.children_mapping.items():
            if profile.name == child_profile.name:
                face_id = fid
                break
        
        if face_id is None:
            return None
        
        # Find emotion data for this face
        for emotion_data in self.latest_input.emotions:
            if emotion_data['face_id'] == face_id:
                return emotion_data['emotional_state']
        
        return None
    
    def get_both_children_emotions(self) -> Dict[str, EmotionalState]:
        """
        Get emotional states for both children.
        
        Returns:
            Dict mapping child names to EmotionalState
        """
        emotions = {}
        
        for face_id, child_profile in self.children_mapping.items():
            state = self.get_child_emotion(child_profile)
            if state:
                emotions[child_profile.name] = state
        
        return emotions
    
    def get_latest_frame(self):
        """Get the latest annotated camera frame for display"""
        if self.latest_input:
            return self.latest_input.annotated_frame
        return None
    
    def get_status_summary(self) -> Dict:
        """Get a summary of current input status"""
        if not self.latest_input:
            return {
                'running': self.is_running,
                'faces': 0,
                'emotions': [],
                'last_command': None
            }
        
        return {
            'running': self.is_running,
            'faces': self.latest_input.faces_detected,
            'emotions': [
                {
                    'state': e['emotional_state'].value,
                    'expression': e['expression'].value,
                    'confidence': e['confidence']
                }
                for e in self.latest_input.emotions
            ],
            'last_command': self.latest_input.voice_command,
            'last_transcription': self.latest_input.transcription,
            'gestures': self.latest_input.gestures
        }


# Test function
if __name__ == "__main__":
    import cv2
    
    def on_input(multimodal_input: MultimodalInput):
        """Callback to handle multimodal input"""
        print(f"\n⏰ {multimodal_input.timestamp.strftime('%H:%M:%S')}")
        print(f"👥 Faces: {multimodal_input.faces_detected}")
        
        for emotion in multimodal_input.emotions:
            emoji = EmotionDetector().get_emotion_emoji(emotion['expression'])
            print(f"   {emoji} {emotion['expression'].value} -> {emotion['emotional_state'].value}")
        
        if multimodal_input.gestures:
            print(f"👋 Gestures: {', '.join(multimodal_input.gestures)}")
        
        if multimodal_input.voice_command:
            print(f"🎤 Command: {multimodal_input.voice_command}")
        
        if multimodal_input.transcription:
            print(f"💬 Said: {multimodal_input.transcription}")
    
    print("🎮 Input Manager Test")
    print("Commands: start story, stop, generate image, left, right")
    print("Press 'q' in the video window to quit\n")
    
    manager = InputManager(on_input_callback=on_input)
    manager.start()
    
    try:
        while True:
            frame = manager.get_latest_frame()
            
            if frame is not None:
                # Add status overlay
                status = manager.get_status_summary()
                cv2.putText(frame, f"Faces: {status['faces']}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                if status['last_command']:
                    cv2.putText(frame, f"Command: {status['last_command']}", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                
                cv2.imshow('TwinSpark Input Manager', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    
    finally:
        manager.stop()
        cv2.destroyAllWindows()
        print("👋 Goodbye!")
