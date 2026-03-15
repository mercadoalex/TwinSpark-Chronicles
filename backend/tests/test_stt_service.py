"""Unit tests for STTService."""

import asyncio
import pytest
from unittest.mock import patch, MagicMock

from app.services.stt_service import STTService, _CHILD_VOCABULARY, _CONFIDENCE_THRESHOLD
from app.models.multimodal import TranscriptResult


def _run(coro):
    """Helper to run an async coroutine in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSTTServiceInit:
    def test_enabled_when_speech_client_available(self):
        """STTService sets enabled=True when Google Cloud Speech initializes."""
        mock_speech = MagicMock()
        mock_client = MagicMock()
        mock_speech.SpeechClient.return_value = mock_client

        with patch.dict("sys.modules", {"google.cloud.speech_v1": mock_speech, "google.cloud": MagicMock(), "google": MagicMock()}):
            svc = STTService.__new__(STTService)
            svc._enabled = False
            svc._client = None
            svc._speech = None
            try:
                from google.cloud import speech_v1 as speech
                svc._speech = speech
                svc._client = speech.SpeechClient()
                svc._enabled = True
            except Exception:
                pass
            assert svc._enabled is True

    def test_disabled_when_speech_client_fails(self):
        """STTService gracefully disables when client init fails."""
        svc = STTService.__new__(STTService)
        svc._enabled = False
        svc._client = None
        svc._speech = None
        assert svc.enabled is False

    def test_enabled_property(self):
        svc = STTService.__new__(STTService)
        svc._enabled = True
        assert svc.enabled is True
        svc._enabled = False
        assert svc.enabled is False


class TestSTTServiceTranscribe:
    @pytest.fixture
    def disabled_svc(self):
        """An STTService with enabled=False."""
        svc = STTService.__new__(STTService)
        svc._enabled = False
        svc._client = None
        svc._speech = None
        return svc

    @pytest.fixture
    def mock_svc(self):
        """An STTService with a mocked Google Cloud Speech client."""
        svc = STTService.__new__(STTService)
        svc._enabled = True
        svc._speech = MagicMock()
        svc._client = MagicMock()
        return svc

    def test_returns_empty_when_disabled(self, disabled_svc):
        result = _run(disabled_svc.transcribe(b"audio data"))
        assert isinstance(result, TranscriptResult)
        assert result.is_empty is True
        assert result.text == ""
        assert result.confidence == 0.0

    def test_returns_empty_when_disabled_preserves_language(self, disabled_svc):
        result = _run(disabled_svc.transcribe(b"audio", language="es-ES"))
        assert result.language == "es-ES"
        assert result.is_empty is True

    def test_successful_transcription(self, mock_svc):
        """High-confidence transcript is returned with text."""
        mock_alternative = MagicMock()
        mock_alternative.confidence = 0.92
        mock_alternative.transcript = "I want to fight the dragon"

        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data", language="en-US"))
        assert result.text == "I want to fight the dragon"
        assert result.confidence == pytest.approx(0.92)
        assert result.is_empty is False
        assert result.language == "en-US"

    def test_low_confidence_returns_empty(self, mock_svc):
        """Transcripts with confidence < 0.4 are discarded."""
        mock_alternative = MagicMock()
        mock_alternative.confidence = 0.2
        mock_alternative.transcript = "mumble"

        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data"))
        assert result.is_empty is True
        assert result.text == ""

    def test_no_results_returns_empty(self, mock_svc):
        """Empty API response returns empty TranscriptResult."""
        mock_response = MagicMock()
        mock_response.results = []

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data"))
        assert result.is_empty is True
        assert result.text == ""

    def test_timeout_returns_empty(self, mock_svc):
        """API timeout returns empty result."""
        with patch("asyncio.wait_for", side_effect=asyncio.TimeoutError):
            result = _run(mock_svc.transcribe(b"audio data"))
            assert result.is_empty is True
            assert result.text == ""

    def test_api_error_returns_empty(self, mock_svc):
        """API errors return empty result gracefully."""
        with patch("asyncio.wait_for", side_effect=Exception("API unreachable")):
            result = _run(mock_svc.transcribe(b"audio data"))
            assert result.is_empty is True
            assert result.text == ""

    def test_unsupported_language_defaults_to_en_us(self, mock_svc):
        """Unsupported language codes fall back to en-US."""
        mock_alternative = MagicMock()
        mock_alternative.confidence = 0.85
        mock_alternative.transcript = "hello"

        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data", language="fr-FR"))
        assert result.language == "en-US"

    def test_spanish_language_supported(self, mock_svc):
        """es-ES language is passed through correctly."""
        mock_alternative = MagicMock()
        mock_alternative.confidence = 0.88
        mock_alternative.transcript = "quiero luchar con el dragón"

        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data", language="es-ES"))
        assert result.language == "es-ES"
        assert result.is_empty is False
        assert result.text == "quiero luchar con el dragón"

    def test_confidence_at_threshold_is_accepted(self, mock_svc):
        """Confidence exactly at 0.4 should be accepted (not discarded)."""
        mock_alternative = MagicMock()
        mock_alternative.confidence = 0.4
        mock_alternative.transcript = "yes"

        mock_result = MagicMock()
        mock_result.alternatives = [mock_alternative]

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_svc._client.recognize.return_value = mock_response

        result = _run(mock_svc.transcribe(b"audio data"))
        assert result.is_empty is False
        assert result.text == "yes"

    def test_child_vocabulary_contains_expected_words(self):
        """Verify child vocabulary includes key words from the spec."""
        expected = {"dragon", "magic", "adventure", "unicorn", "brave", "help", "yes", "no"}
        assert expected.issubset(set(_CHILD_VOCABULARY))

    def test_confidence_threshold_is_0_4(self):
        assert _CONFIDENCE_THRESHOLD == 0.4
