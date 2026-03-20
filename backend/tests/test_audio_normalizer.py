"""Tests for AudioNormalizer: property-based and unit tests.

Property tests use Hypothesis with pydub-generated audio segments.
Unit tests cover edge cases: empty audio, corrupt bytes, boundary durations, silence-only.
"""

import io
import struct
import wave

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck
from pydub import AudioSegment
from pydub.generators import Sine

from app.services.audio_normalizer import AudioNormalizer, AudioNormalizationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_wav_bytes(audio: AudioSegment) -> bytes:
    """Export an AudioSegment to WAV bytes."""
    buf = io.BytesIO()
    audio.export(buf, format="wav")
    return buf.getvalue()


def _parse_wav_params(wav_bytes: bytes):
    """Read WAV header params from bytes."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wf:
        return {
            "channels": wf.getnchannels(),
            "sample_width": wf.getsampwidth(),
            "frame_rate": wf.getframerate(),
            "n_frames": wf.getnframes(),
        }


def _make_tone(duration_ms: int = 3000, freq: int = 440, sample_rate: int = 44100) -> bytes:
    """Generate a sine tone as WAV bytes."""
    tone = Sine(freq, sample_rate=sample_rate).to_audio_segment(duration=duration_ms)
    return _make_wav_bytes(tone)


def _make_silence_padded_tone(
    leading_silence_ms: int,
    tone_duration_ms: int,
    trailing_silence_ms: int,
    freq: int = 440,
) -> bytes:
    """Generate WAV with silence + tone + silence."""
    leading = AudioSegment.silent(duration=leading_silence_ms)
    tone = Sine(freq).to_audio_segment(duration=tone_duration_ms)
    trailing = AudioSegment.silent(duration=trailing_silence_ms)
    combined = leading + tone + trailing
    return _make_wav_bytes(combined)


# ---------------------------------------------------------------------------
# Hypothesis strategies
# ---------------------------------------------------------------------------

@st.composite
def audio_with_varied_params(draw):
    """Generate WAV audio with varied sample rates, channels, and durations.

    Produces audio between 1.5s and 10s to stay within normalizer bounds.
    """
    duration_ms = draw(st.integers(min_value=1500, max_value=10000))
    freq = draw(st.integers(min_value=200, max_value=2000))
    sample_rate = draw(st.sampled_from([8000, 16000, 22050, 44100, 48000]))
    channels = draw(st.sampled_from([1, 2]))

    tone = Sine(freq, sample_rate=sample_rate).to_audio_segment(duration=duration_ms)
    if channels == 2:
        tone = tone.set_channels(2)
    return _make_wav_bytes(tone)


@st.composite
def silence_padded_audio(draw):
    """Generate audio with variable leading/trailing silence and a tone core."""
    leading_ms = draw(st.integers(min_value=0, max_value=3000))
    trailing_ms = draw(st.integers(min_value=0, max_value=3000))
    tone_ms = draw(st.integers(min_value=1500, max_value=5000))
    freq = draw(st.integers(min_value=300, max_value=1500))
    return leading_ms, trailing_ms, _make_silence_padded_tone(leading_ms, tone_ms, trailing_ms, freq)


@st.composite
def audio_for_fade(draw):
    """Generate canonical WAV audio suitable for fade testing."""
    duration_ms = draw(st.integers(min_value=1500, max_value=8000))
    freq = draw(st.integers(min_value=200, max_value=2000))
    tone = Sine(freq, sample_rate=16000).to_audio_segment(duration=duration_ms)
    tone = tone.set_sample_width(2).set_channels(1)
    return _make_wav_bytes(tone)


# ---------------------------------------------------------------------------
# Property Tests
# ---------------------------------------------------------------------------

class TestNormalizationOutputInvariant:
    """Property 1: Normalization output invariant.

    For any valid input audio (regardless of original format, sample rate,
    or channel count), normalize() output SHALL produce:
    (a) WAV at exactly 16 kHz, 16-bit, mono
    (b) peak amplitude within ±0.5 dB of -3 dBFS
    (c) a valid decodable MP3
    (d) voice sample WAV at exactly 22.05 kHz, 16-bit, mono

    **Validates: Requirements 1.6, 3.1, 3.2, 3.5, 8.1, 8.2**
    """

    @given(audio_bytes=audio_with_varied_params())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_normalization_output_invariant(self, audio_bytes):
        normalizer = AudioNormalizer()
        result = normalizer.normalize(audio_bytes)

        # (a) WAV at 16kHz, 16-bit, mono
        wav_params = _parse_wav_params(result.wav_bytes)
        assert wav_params["frame_rate"] == 16000
        assert wav_params["sample_width"] == 2
        assert wav_params["channels"] == 1

        # (b) Peak amplitude within ±0.5 dB of -3 dBFS
        wav_audio = AudioSegment.from_file(io.BytesIO(result.wav_bytes), format="wav")
        if wav_audio.max_dBFS != float("-inf"):
            assert abs(wav_audio.max_dBFS - (-3.0)) <= 0.5

        # (c) Valid decodable MP3
        mp3_audio = AudioSegment.from_file(io.BytesIO(result.mp3_bytes), format="mp3")
        assert len(mp3_audio) > 0

        # (d) Voice sample at 22.05kHz, 16-bit, mono
        sample_params = _parse_wav_params(result.sample_bytes)
        assert sample_params["frame_rate"] == 22050
        assert sample_params["sample_width"] == 2
        assert sample_params["channels"] == 1


class TestSilenceTrimming:
    """Property 2: Silence trimming.

    For any input audio with leading silence of L ms and trailing silence
    of T ms, after normalization the output SHALL have at most 500ms of
    leading/trailing silence while preserving non-silent content.

    **Validates: Requirements 3.3**
    """

    @given(data=silence_padded_audio())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_silence_trimming(self, data):
        leading_ms, trailing_ms, audio_bytes = data
        normalizer = AudioNormalizer()
        result = normalizer.normalize(audio_bytes)

        wav_audio = AudioSegment.from_file(io.BytesIO(result.wav_bytes), format="wav")

        # Measure remaining leading silence
        from pydub.silence import detect_leading_silence
        remaining_leading = detect_leading_silence(
            wav_audio, silence_threshold=-40, chunk_size=10
        )
        remaining_trailing = detect_leading_silence(
            wav_audio.reverse(), silence_threshold=-40, chunk_size=10
        )

        # At most 500ms + tolerance for chunk-based detection
        tolerance_ms = 50
        assert remaining_leading <= 500 + tolerance_ms
        assert remaining_trailing <= 500 + tolerance_ms


class TestFadePreservesDuration:
    """Property 19: Fade-in/fade-out preserves duration.

    For any audio passed through _apply_fade(audio_bytes, fade_ms=500),
    the output duration SHALL equal the input duration (within ±10ms).

    **Validates: Requirements 6.6**
    """

    @given(audio_bytes=audio_for_fade())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_fade_preserves_duration(self, audio_bytes):
        normalizer = AudioNormalizer()

        input_audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")
        input_duration_ms = len(input_audio)

        faded_bytes = normalizer._apply_fade(audio_bytes, fade_ms=500)
        output_audio = AudioSegment.from_file(io.BytesIO(faded_bytes), format="wav")
        output_duration_ms = len(output_audio)

        assert abs(input_duration_ms - output_duration_ms) <= 10


# ---------------------------------------------------------------------------
# Unit Tests — Edge Cases (Task 2.6)
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Unit tests for edge cases: empty audio, corrupt bytes, boundary durations, silence-only."""

    def test_empty_audio_raises(self):
        """Empty bytes should raise AudioNormalizationError."""
        normalizer = AudioNormalizer()
        with pytest.raises(AudioNormalizationError, match="Empty audio data"):
            normalizer.normalize(b"")

    def test_corrupt_bytes_raises(self):
        """Random corrupt bytes should raise AudioNormalizationError."""
        normalizer = AudioNormalizer()
        with pytest.raises(AudioNormalizationError, match="Could not process audio"):
            normalizer.normalize(b"this is not audio data at all!!!")

    def test_exactly_1s_audio_accepted(self):
        """Audio of exactly 1 second (after trim) should be accepted."""
        normalizer = AudioNormalizer()
        # Generate a 1.1s tone (slight buffer since trimming may shave a tiny bit)
        tone = Sine(440).to_audio_segment(duration=1100)
        audio_bytes = _make_wav_bytes(tone)
        result = normalizer.normalize(audio_bytes)
        assert result.duration_seconds >= 1.0

    def test_exactly_60s_audio_accepted(self):
        """Audio of exactly 60 seconds should be accepted."""
        normalizer = AudioNormalizer()
        tone = Sine(440).to_audio_segment(duration=60000)
        audio_bytes = _make_wav_bytes(tone)
        result = normalizer.normalize(audio_bytes)
        assert result.duration_seconds <= 60.0
        assert result.duration_seconds >= 59.0  # allow minor trim

    def test_audio_over_60s_rejected(self):
        """Audio over 60 seconds should be rejected."""
        normalizer = AudioNormalizer()
        tone = Sine(440).to_audio_segment(duration=61000)
        audio_bytes = _make_wav_bytes(tone)
        with pytest.raises(AudioNormalizationError, match="60-second maximum"):
            normalizer.normalize(audio_bytes)

    def test_audio_only_silence_rejected(self):
        """Audio that is only silence should be rejected as too short after trimming."""
        normalizer = AudioNormalizer()
        silence = AudioSegment.silent(duration=5000)
        audio_bytes = _make_wav_bytes(silence)
        with pytest.raises(AudioNormalizationError, match="too short"):
            normalizer.normalize(audio_bytes)

    def test_truncated_wav_header_raises(self):
        """A truncated WAV header (valid start but incomplete) should raise."""
        normalizer = AudioNormalizer()
        # First 20 bytes of a valid WAV — enough to look like WAV but not decodable
        partial_header = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00"
        with pytest.raises(AudioNormalizationError, match="Could not process audio"):
            normalizer.normalize(partial_header)

    def test_stereo_input_converted_to_mono(self):
        """Stereo input should be converted to mono output."""
        normalizer = AudioNormalizer()
        tone = Sine(440).to_audio_segment(duration=2000).set_channels(2)
        audio_bytes = _make_wav_bytes(tone)
        result = normalizer.normalize(audio_bytes)
        wav_params = _parse_wav_params(result.wav_bytes)
        assert wav_params["channels"] == 1

    def test_high_sample_rate_downsampled(self):
        """48kHz input should be downsampled to 16kHz."""
        normalizer = AudioNormalizer()
        tone = Sine(440, sample_rate=48000).to_audio_segment(duration=2000)
        audio_bytes = _make_wav_bytes(tone)
        result = normalizer.normalize(audio_bytes)
        wav_params = _parse_wav_params(result.wav_bytes)
        assert wav_params["frame_rate"] == 16000

    def test_apply_fade_on_short_audio(self):
        """Fade on very short audio should clamp fade duration without error."""
        normalizer = AudioNormalizer()
        tone = Sine(440, sample_rate=16000).to_audio_segment(duration=600)
        tone = tone.set_sample_width(2).set_channels(1)
        audio_bytes = _make_wav_bytes(tone)
        faded = normalizer._apply_fade(audio_bytes, fade_ms=500)
        faded_audio = AudioSegment.from_file(io.BytesIO(faded), format="wav")
        # Duration should be preserved
        assert abs(len(faded_audio) - 600) <= 10
