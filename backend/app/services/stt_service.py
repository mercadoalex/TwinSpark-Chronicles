"""
Speech-to-Text Service using Google Cloud Speech-to-Text.
Transcribes child voice input with child-optimized configuration.
Supports en-US and es-ES based on session language.
"""

import asyncio
import logging

from app.models.multimodal import TranscriptResult

logger = logging.getLogger(__name__)

# Child-friendly vocabulary for speech context boosting
_CHILD_VOCABULARY = [
    "dragon",
    "magic",
    "adventure",
    "let's go",
    "yes",
    "no",
    "unicorn",
    "brave",
    "help",
]

# Minimum confidence to accept a transcript
_CONFIDENCE_THRESHOLD = 0.4

# Maximum time to wait for the API response
_TIMEOUT_SECONDS = 3

# Supported languages
_SUPPORTED_LANGUAGES = {"en-US", "es-ES"}


class STTService:
    """
    Transcribes audio using Google Cloud Speech-to-Text.
    Gracefully degrades if the client fails to initialize.
    """

    def __init__(self):
        self._enabled = False
        self._client = None
        self._speech = None

        try:
            from google.cloud import speech_v1 as speech

            self._speech = speech
            self._client = speech.SpeechClient()
            self._enabled = True
            logger.info("✅ STT service initialized with Google Cloud Speech-to-Text")
        except Exception as e:
            logger.warning(
                f"⚠️  STT service disabled (Google Cloud Speech not configured): {e}"
            )
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def transcribe(
        self, audio_bytes: bytes, language: str = "en-US"
    ) -> TranscriptResult:
        """Transcribe audio bytes using Google Cloud Speech-to-Text.

        Args:
            audio_bytes: Raw PCM 16kHz mono audio bytes.
            language: BCP-47 language code ("en-US" or "es-ES").

        Returns:
            TranscriptResult with transcribed text and confidence.
            Returns empty result (is_empty=True) when:
            - Service is disabled
            - Confidence is below 0.4
            - API is unreachable (timeout after 3s)
            - Any processing error occurs
        """
        if not self._enabled:
            return TranscriptResult(
                text="", confidence=0.0, language=language, is_empty=True
            )

        if language not in _SUPPORTED_LANGUAGES:
            language = "en-US"

        try:
            recognition_audio = self._speech.RecognitionAudio(content=audio_bytes)

            speech_context = self._speech.SpeechContext(
                phrases=_CHILD_VOCABULARY,
            )

            config = self._speech.RecognitionConfig(
                encoding=self._speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language,
                enable_automatic_punctuation=True,
                speech_contexts=[speech_context],
            )

            # Run the synchronous API call in a thread with a timeout
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self._client.recognize(config=config, audio=recognition_audio),
                ),
                timeout=_TIMEOUT_SECONDS,
            )

            if not response.results:
                return TranscriptResult(
                    text="", confidence=0.0, language=language, is_empty=True
                )

            result = response.results[0].alternatives[0]
            confidence = result.confidence
            text = result.transcript

            # Discard low-confidence transcripts
            if confidence < _CONFIDENCE_THRESHOLD:
                return TranscriptResult(
                    text="", confidence=confidence, language=language, is_empty=True
                )

            return TranscriptResult(
                text=text, confidence=confidence, language=language, is_empty=False
            )

        except asyncio.TimeoutError:
            logger.error(
                f"STT transcription timed out after {_TIMEOUT_SECONDS}s — returning stt_unavailable"
            )
            return TranscriptResult(
                text="", confidence=0.0, language=language, is_empty=True
            )
        except Exception as e:
            logger.error(f"STT transcription failed: {e}")
            return TranscriptResult(
                text="", confidence=0.0, language=language, is_empty=True
            )
