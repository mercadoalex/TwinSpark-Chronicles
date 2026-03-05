"""
Voice Recorder Module
Records and stores family voices for narration in stories.
"""

import os
import json
import wave
import pyaudio
from datetime import datetime
from typing import Optional, Dict, List
import threading
import time

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class VoiceRecorder:
    """
    Handles family voice recording and playback.
    Features:
    - Record voice messages
    - Store with metadata
    - Playback during stories
    - Voice type categorization
    """
    
    def __init__(self, recordings_dir: Optional[str] = None):
        """
        Args:
            recordings_dir: Directory for storing voice recordings.
                           Defaults to assets/voice_recordings/
        """
        if recordings_dir is None:
            self.recordings_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "assets", "voice_recordings"
            )
        else:
            self.recordings_dir = recordings_dir
        
        os.makedirs(self.recordings_dir, exist_ok=True)
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1  # Mono
        self.RATE = 44100  # Sample rate
        
        # PyAudio instance
        try:
            self.audio = pyaudio.PyAudio()
            self.has_audio = True
        except Exception as e:
            print(f"⚠️  Audio not available: {e}")
            self.has_audio = False
        
        # Recording state
        self.is_recording = False
        self.frames = []
        self._recording_thread = None
        
        print(f"🎤 Voice Recorder initialized (recordings: {self.recordings_dir})")
    
    def start_recording(self) -> bool:
        """
        Start recording audio.
        
        Returns:
            True if recording started successfully
        """
        if not self.has_audio:
            print("❌ No audio device available")
            return False
        
        if self.is_recording:
            print("⚠️  Already recording")
            return False
        
        try:
            self.frames = []
            self.is_recording = True
            
            # Start recording thread
            self._recording_thread = threading.Thread(target=self._record_loop, daemon=True)
            self._recording_thread.start()
            
            print("🔴 Recording started...")
            return True
            
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.is_recording = False
            return False
    
    def _record_loop(self):
        """Internal recording loop (runs in separate thread)"""
        try:
            stream = self.audio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK
            )
            
            while self.is_recording:
                try:
                    data = stream.read(self.CHUNK, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    print(f"⚠️  Recording error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"❌ Recording loop error: {e}")
            self.is_recording = False
    
    def stop_recording(self) -> int:
        """
        Stop recording audio.
        
        Returns:
            Number of frames recorded
        """
        if not self.is_recording:
            print("⚠️  Not currently recording")
            return 0
        
        self.is_recording = False
        
        # Wait for recording thread to finish
        if self._recording_thread:
            self._recording_thread.join(timeout=2)
        
        frame_count = len(self.frames)
        print(f"⏹️  Recording stopped ({frame_count} frames)")
        
        return frame_count
    
    def save_recording(
        self,
        speaker_name: str,
        message_type: str = "general",
        transcription: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Save the recorded audio to file.
        
        Args:
            speaker_name: Name of the speaker (e.g., "Grandma", "Dad")
            message_type: Type of message ("greeting", "encouragement", 
                         "story_intro", "bedtime", "celebration", "general")
            transcription: Optional text transcription
            description: Optional description
            
        Returns:
            Metadata dict or None if no recording to save
        """
        if not self.frames:
            print("❌ No recording to save")
            return None
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = speaker_name.lower().replace(' ', '_')
        unique_name = f"{safe_name}_{message_type}_{timestamp}"
        
        # Save audio file
        audio_path = os.path.join(self.recordings_dir, f"{unique_name}.wav")
        
        try:
            wf = wave.open(audio_path, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            # Calculate duration
            duration_seconds = len(self.frames) * self.CHUNK / self.RATE
            
            # Create metadata
            metadata = {
                "unique_name": unique_name,
                "file_path": audio_path,
                "speaker_name": speaker_name,
                "message_type": message_type,
                "transcription": transcription,
                "description": description,
                "recorded_at": datetime.now().isoformat(),
                "duration_seconds": round(duration_seconds, 2),
                "enabled": True,
                "sample_rate": self.RATE,
                "channels": self.CHANNELS
            }
            
            # Save metadata
            metadata_path = os.path.join(self.recordings_dir, f"{unique_name}_metadata.json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Clear frames
            self.frames = []
            
            print(f"✅ Recording saved: {unique_name} ({duration_seconds:.1f}s)")
            return metadata
            
        except Exception as e:
            print(f"❌ Error saving recording: {e}")
            return None
    
    def record_message(
        self,
        speaker_name: str,
        message_type: str = "general",
        duration_seconds: Optional[int] = None,
        transcription: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Convenience method: record, wait, and save.
        
        Args:
            speaker_name: Name of speaker
            message_type: Type of message
            duration_seconds: How long to record (None = manual stop)
            transcription: Optional transcription
            
        Returns:
            Metadata dict or None
        """
        if not self.start_recording():
            return None
        
        if duration_seconds:
            print(f"🎤 Recording for {duration_seconds} seconds...")
            time.sleep(duration_seconds)
            self.stop_recording()
        else:
            print("🎤 Recording... (press Enter to stop)")
            input()
            self.stop_recording()
        
        return self.save_recording(speaker_name, message_type, transcription)
    
    def play_recording(self, unique_name: str) -> bool:
        """
        Play a recorded voice message.
        
        Args:
            unique_name: Unique name of the recording
            
        Returns:
            True if playback successful
        """
        if not self.has_audio:
            print("❌ No audio device available")
            return False
        
        metadata = self.get_recording(unique_name)
        if not metadata:
            print(f"❌ Recording not found: {unique_name}")
            return False
        
        audio_path = metadata['file_path']
        
        if not os.path.exists(audio_path):
            print(f"❌ Audio file not found: {audio_path}")
            return False
        
        try:
            # Open wave file
            wf = wave.open(audio_path, 'rb')
            
            # Open stream
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True
            )
            
            print(f"▶️  Playing: {metadata['speaker_name']} - {metadata['message_type']}")
            
            # Play
            data = wf.readframes(self.CHUNK)
            while data:
                stream.write(data)
                data = wf.readframes(self.CHUNK)
            
            # Cleanup
            stream.stop_stream()
            stream.close()
            wf.close()
            
            print("✅ Playback complete")
            return True
            
        except Exception as e:
            print(f"❌ Playback error: {e}")
            return False
    
    def list_recordings(
        self,
        message_type: Optional[str] = None,
        speaker_name: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict]:
        """
        List all recordings.
        
        Args:
            message_type: Filter by type
            speaker_name: Filter by speaker
            enabled_only: Only return enabled recordings
            
        Returns:
            List of metadata dicts
        """
        recordings = []
        
        for filename in os.listdir(self.recordings_dir):
            if filename.endswith('_metadata.json'):
                metadata_path = os.path.join(self.recordings_dir, filename)
                
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                
                # Apply filters
                if message_type and metadata.get('message_type') != message_type:
                    continue
                
                if speaker_name and metadata.get('speaker_name') != speaker_name:
                    continue
                
                if enabled_only and not metadata.get('enabled', True):
                    continue
                
                recordings.append(metadata)
        
        # Sort by date (most recent first)
        recordings.sort(key=lambda x: x.get('recorded_at', ''), reverse=True)
        
        return recordings
    
    def get_recording(self, unique_name: str) -> Optional[Dict]:
        """Get recording metadata by unique name"""
        metadata_path = os.path.join(self.recordings_dir, f"{unique_name}_metadata.json")
        
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def disable_recording(self, unique_name: str) -> bool:
        """Disable a recording (parent control)"""
        metadata = self.get_recording(unique_name)
        if not metadata:
            return False
        
        metadata['enabled'] = False
        metadata_path = os.path.join(self.recordings_dir, f"{unique_name}_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"🚫 Recording disabled: {unique_name}")
        return True
    
    def enable_recording(self, unique_name: str) -> bool:
        """Enable a recording"""
        metadata = self.get_recording(unique_name)
        if not metadata:
            return False
        
        metadata['enabled'] = True
        metadata_path = os.path.join(self.recordings_dir, f"{unique_name}_metadata.json")
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Recording enabled: {unique_name}")
        return True
    
    def delete_recording(self, unique_name: str) -> bool:
        """Delete a recording and its files"""
        metadata = self.get_recording(unique_name)
        if not metadata:
            return False
        
        # Delete files
        files_to_delete = [
            metadata.get('file_path'),
            os.path.join(self.recordings_dir, f"{unique_name}_metadata.json")
        ]
        
        for filepath in files_to_delete:
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        
        print(f"🗑️  Recording deleted: {unique_name}")
        return True
    
    def get_stats(self) -> Dict:
        """Get statistics about recordings"""
        all_recordings = self.list_recordings(enabled_only=False)
        
        stats = {
            "total_recordings": len(all_recordings),
            "enabled_recordings": len([r for r in all_recordings if r.get('enabled', True)]),
            "disabled_recordings": len([r for r in all_recordings if not r.get('enabled', True)]),
            "total_duration": sum(r.get('duration_seconds', 0) for r in all_recordings),
            "by_type": {},
            "by_speaker": {}
        }
        
        # Count by type and speaker
        for recording in all_recordings:
            msg_type = recording.get('message_type', 'general')
            speaker = recording.get('speaker_name', 'unknown')
            
            stats['by_type'][msg_type] = stats['by_type'].get(msg_type, 0) + 1
            stats['by_speaker'][speaker] = stats['by_speaker'].get(speaker, 0) + 1
        
        return stats
    
    def cleanup(self):
        """Release audio resources"""
        if self.has_audio and self.audio:
            self.audio.terminate()
        print("🎤 Voice Recorder cleanup complete")


# Test function
if __name__ == "__main__":
    print("🎤 Voice Recorder Test\n")
    
    recorder = VoiceRecorder()
    
    if not recorder.has_audio:
        print("❌ No audio device available. Cannot run test.")
    else:
        print("Available message types:")
        print("  - greeting")
        print("  - encouragement")
        print("  - story_intro")
        print("  - bedtime")
        print("  - celebration")
        print("")
        
        # Interactive test
        print("Test 1: Record a short message")
        print("Press Enter to start recording (will record for 3 seconds)...")
        input()
        
        metadata = recorder.record_message(
            speaker_name="Test User",
            message_type="greeting",
            duration_seconds=3,
            transcription="This is a test recording"
        )
        
        if metadata:
            print(f"\n✅ Recording saved!")
            print(f"   Speaker: {metadata['speaker_name']}")
            print(f"   Type: {metadata['message_type']}")
            print(f"   Duration: {metadata['duration_seconds']}s")
            
            # Playback test
            print("\nTest 2: Playback")
            print("Press Enter to play back the recording...")
            input()
            
            recorder.play_recording(metadata['unique_name'])
            
            # Stats
            print("\n📊 Stats:")
            stats = recorder.get_stats()
            print(f"   Total recordings: {stats['total_recordings']}")
            print(f"   Total duration: {stats['total_duration']:.1f}s")
            print(f"   By type: {stats['by_type']}")
        
        recorder.cleanup()
    
    print("\n✅ Voice Recorder test complete!")
