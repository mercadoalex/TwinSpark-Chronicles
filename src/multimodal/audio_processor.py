import speech_recognition as sr
import threading
import time

class AudioProcessor:
    def __init__(self):
        # Initialize the recognizer and microphone
        self.recognizer = sr.Recognizer()
        
        # Adjust for ambient noise on initialization if possible
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("🎙️ Adjusting for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except OSError:
            print("⚠️ No microphone found or accessible. Audio features will be disabled.")
            self.microphone = None
            
        self.is_listening = False
        self._stop_event = threading.Event()
        self._listener_thread = None
        
        # Buffer to store recognized text and detected commands
        self.latest_transcription = ""
        self.latest_command = None
        
        # Common voice commands for a 6-year-old using the app
        self.command_keywords = {
            "start_story": ["start story", "begin", "let's go"],
            "choose_left": ["left", "the left one", "number one"],
            "choose_right": ["right", "the right one", "number two"],
            "stop": ["stop", "pause", "wait"],
            "generate_image": ["make an image", "take a picture", "draw"]
        }

    def start_listening(self, callback=None):
        """Starts a background thread to continuously listen to the microphone."""
        if self.microphone is None:
            return False
            
        if self.is_listening:
            return True
            
        self.is_listening = True
        self.callback = callback
        self._stop_event.clear()
        
        # Start background listening
        # The stop_listening returned is a function we call to stop the background thread
        try:
            self._stop_bg_listen = self.recognizer.listen_in_background(
                self.microphone, 
                self._audio_callback
            )
            print("🎙️ AudioProcessor started listening in background...")
            return True
        except Exception as e:
            print(f"❌ Failed to start background listening: {e}")
            self.is_listening = False
            return False

    def stop_listening(self):
        """Stops the background listening thread."""
        if self.is_listening and hasattr(self, '_stop_bg_listen'):
            self._stop_bg_listen(wait_for_stop=False)
            self.is_listening = False
            self._stop_event.set()
            print("🛑 AudioProcessor stopped listening.")

    def _audio_callback(self, recognizer, audio):
        """Called automatically when PyAudio detects a phrase."""
        try:
            # We use Google's free Web Speech API
            # For production, we would use Whisper or a local model for privacy
            text = recognizer.recognize_google(audio).lower()
            print(f"\n🗣️ Heard: '{text}'")
            
            self.latest_transcription = text
            self._process_commands(text)
            
            # Simple tone/emotion detection based on speed/volume (placeholder for advanced audio analysis)
            # A real implementation would use Librosa or an audio classification model
            self._detect_basic_emotion(text)
            
            # Fire the callback to instantly notify the SessionManager
            if hasattr(self, 'callback') and self.callback:
                self.callback({
                    "transcription": self.latest_transcription,
                    "command": self.latest_command
                })
            
        except sr.UnknownValueError:
            # Speech was detected but not understood
            pass
        except sr.RequestError as e:
            print(f"⚠️ Speech recognition service error: {e}")

    def _process_commands(self, text):
        """Checks detected text for specific app commands."""
        for command, keywords in self.command_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    self.latest_command = command
                    print(f"🎯 Command detected: {command}")
                    return command
        return None
        
    def _detect_basic_emotion(self, text):
        """Extremely basic heuristic for emotion based on text content as a placeholder."""
        # In Phase 2 this will be replaced by actual voice acoustic analysis
        excited_words = ["yay", "wow", "cool", "super", "awesome"]
        sad_words = ["oh no", "sad", "aww", "bad"]
        
        if any(word in text for word in excited_words) or text.endswith("!"):
            return "excited"
        elif any(word in text for word in sad_words):
            return "sad"
            
        return "neutral"

    def get_latest_data(self):
        """Returns the most recent transcription and commands. Clears the command once read."""
        data = {
            "transcription": self.latest_transcription,
            "command": self.latest_command
        }
        # Reset the command so it doesn't fire twice
        self.latest_command = None 
        return data


if __name__ == "__main__":
    print("Initializing AudioProcessor Test...")
    processor = AudioProcessor()
    
    if processor.start_listening():
        print("\n--- Audio Test Running ---")
        print("Speak into your microphone! Try saying 'start story' or 'choose left'.")
        print("Waiting for speech (will run for 15 seconds)...")
        
        try:
            # Keep the main thread alive while background thread listens
            for i in range(15):
                time.sleep(1)
                data = processor.get_latest_data()
                if data["command"]:
                    print(f"  -> Processed command: {data['command']}")
        except KeyboardInterrupt:
            print("Test interrupted by user.")
        finally:
            processor.stop_listening()
    else:
        print("Failed to start audio processor. Check your microphone access.")
