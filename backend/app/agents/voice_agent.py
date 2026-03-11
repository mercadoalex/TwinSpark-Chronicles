"""
Voice Personality Agent using Google Cloud Text-to-Speech
Creates unique character voices for immersive storytelling
"""

from typing import Dict, Optional
import base64
import os

class VoicePersonalityAgent:
    """
    Generates character-specific voice audio for story dialogue
    """
    
    def __init__(self):
        self.enabled = False
        self.client = None
        
        # Try to initialize Google TTS
        try:
            from google.cloud import texttospeech_v1 as tts
            self.tts = tts
            self.client = tts.TextToSpeechClient()
            self.enabled = True
            print("✅ Voice agent initialized with Google Cloud TTS")
        except Exception as e:
            print(f"ℹ️  Voice agent using fallback mode (Google Cloud TTS not configured)")
            print(f"   To enable voice: Set up Application Default Credentials")
            print(f"   See: https://cloud.google.com/docs/authentication/provide-credentials-adc")
        
        # Character voice profiles
        self.voice_profiles = {
            "narrator": {
                "language_code": "en-US",
                "name": "en-US-Studio-O",
                "pitch": 0.0,
                "speaking_rate": 0.9,
                "description": "Warm narrator"
            },
            "dragon": {
                "language_code": "en-US",
                "name": "en-US-Studio-M",
                "pitch": -8.0,
                "speaking_rate": 0.85,
                "description": "Powerful dragon"
            },
            "owl": {
                "language_code": "en-US",
                "name": "en-US-Wavenet-B",
                "pitch": 2.0,
                "speaking_rate": 0.8,
                "description": "Wise owl"
            },
            "phoenix": {
                "language_code": "en-US",
                "name": "en-US-Neural2-F",
                "pitch": 3.0,
                "speaking_rate": 0.9,
                "description": "Mystical phoenix"
            },
            "unicorn": {
                "language_code": "en-US",
                "name": "en-US-Neural2-C",
                "pitch": 4.0,
                "speaking_rate": 0.95,
                "description": "Gentle unicorn"
            },
            "lion": {
                "language_code": "en-US",
                "name": "en-US-Studio-M",
                "pitch": -4.0,
                "speaking_rate": 0.9,
                "description": "Brave lion"
            },
            "child_hero": {
                "language_code": "en-US",
                "name": "en-US-Neural2-E",
                "pitch": 4.0,
                "speaking_rate": 1.05,
                "description": "Child hero"
            }
        }
        
        # Emotion adjustments
        self.emotion_adjustments = {
            "excited": {"pitch": 2.0, "rate": 1.1},
            "scared": {"pitch": -2.0, "rate": 0.85},
            "happy": {"pitch": 1.5, "rate": 1.05},
            "sad": {"pitch": -1.5, "rate": 0.8},
            "surprised": {"pitch": 3.0, "rate": 1.15},
            "calm": {"pitch": 0.0, "rate": 0.9},
            "neutral": {"pitch": 0.0, "rate": 1.0}
        }
    
    async def generate_narration(
        self,
        text: str,
        language: str = "en"
    ) -> Optional[str]:
        """
        Generate narrator voice for story text
        Returns: Base64 encoded MP3 audio or None if disabled
        """
        if not self.enabled:
            return None
        
        try:
            return await self.generate_dialogue(
                text=text,
                character_type="narrator",
                emotion="neutral",
                language=language
            )
        except Exception as e:
            print(f"❌ Narration generation error: {e}")
            return None
    
    async def generate_dialogue(
        self,
        text: str,
        character_type: str,
        emotion: str = "neutral",
        language: str = "en"
    ) -> Optional[str]:
        """
        Generate character-specific voice audio
        """
        if not self.enabled:
            return None
        
        try:
            # Get voice profile
            profile = self.voice_profiles.get(
                character_type,
                self.voice_profiles["narrator"]
            )
            
            # Adjust for language
            if language == "es":
                profile = profile.copy()
                profile["language_code"] = "es-ES"
                profile["name"] = "es-ES-Neural2-A"
            elif language == "hi":
                profile = profile.copy()
                profile["language_code"] = "hi-IN"
                profile["name"] = "hi-IN-Neural2-A"
            
            # Adjust for emotion
            emotion_adjust = self.emotion_adjustments.get(emotion, {"pitch": 0, "rate": 1.0})
            
            # Build synthesis request
            synthesis_input = self.tts.SynthesisInput(text=text)
            
            voice = self.tts.VoiceSelectionParams(
                language_code=profile["language_code"],
                name=profile["name"]
            )
            
            audio_config = self.tts.AudioConfig(
                audio_encoding=self.tts.AudioEncoding.MP3,
                pitch=profile["pitch"] + emotion_adjust["pitch"],
                speaking_rate=profile["speaking_rate"] * emotion_adjust["rate"]
            )
            
            # Generate audio
            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )
            
            # Convert to base64
            audio_base64 = base64.b64encode(response.audio_content).decode('utf-8')
            
            print(f"🎤 Generated {character_type} voice ({emotion})")
            
            return f"data:audio/mp3;base64,{audio_base64}"
            
        except Exception as e:
            print(f"❌ Voice generation error: {e}")
            return None
    
    def get_character_voice_for_spirit_animal(self, spirit_animal: str) -> str:
        """
        Map spirit animal to voice profile
        """
        mapping = {
            "dragon": "dragon",
            "owl": "owl",
            "phoenix": "phoenix",
            "unicorn": "unicorn",
            "lion": "lion",
            "wolf": "lion",
            "bear": "lion",
            "eagle": "owl",
            "fox": "owl"
        }
        
        return mapping.get(spirit_animal.lower(), "child_hero")


# Global instance
voice_agent = VoicePersonalityAgent()