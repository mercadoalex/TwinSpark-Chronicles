"""Audio normalization service using pydub (ffmpeg wrapper).

Converts uploaded audio to canonical WAV format, normalizes levels,
trims silence, generates MP3 for streaming, and produces voice samples
for future cloning preparation.
"""

import io
import struct
import wave

from pydub import AudioSegment
from pydub.silence import detect_leading_silence

from app.models.voice_recording import NormalizedAudio


class AudioNormalizationError(Exception):
    """Raised when audio cannot be processed."""


class AudioNormalizer:
    """Stateless audio processing using pydub (wraps ffmpeg)."""

    CANONICAL_SAMPLE_RATE = 16000       # 16 kHz
    CANONICAL_CHANNELS = 1              # mono
    CANONICAL_SAMPLE_WIDTH = 2          # 16-bit
    PEAK_TARGET_DBFS = -3.0
    SILENCE_THRESHOLD_MS = 500
    MIN_DURATION_S = 1.0
    MAX_DURATION_S = 60.0
    VOICE_SAMPLE_RATE = 22050           # for cloning prep
    SILENCE_THRESH_DB = -40             # dBFS threshold for silence detection

    def normalize(self, audio_bytes: bytes) -> NormalizedAudio:
        """Normalize audio bytes to canonical format.

        Converts to WAV 16kHz/16-bit/mono, normalizes peak to -3 dBFS,
        trims silence >500ms, rejects <1s or >60s, generates MP3,
        and generates a voice sample at 22.05kHz.

        Args:
            audio_bytes: Raw audio bytes in any ffmpeg-supported format.

        Returns:
            NormalizedAudio with wav_bytes, mp3_bytes, sample_bytes, duration_seconds.

        Raises:
            AudioNormalizationError: If audio is invalid, too short, or too long.
        """
        if not audio_bytes:
            raise AudioNormalizationError("Empty audio data")

        # Decode input audio
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as exc:
            raise AudioNormalizationError(
                f"Could not process audio — unsupported or corrupt format: {exc}"
            ) from exc

        # Convert to canonical format: 16kHz, 16-bit, mono
        audio = audio.set_frame_rate(self.CANONICAL_SAMPLE_RATE)
        audio = audio.set_sample_width(self.CANONICAL_SAMPLE_WIDTH)
        audio = audio.set_channels(self.CANONICAL_CHANNELS)

        # Normalize peak amplitude to -3 dBFS
        if audio.max_dBFS != float("-inf"):
            gain = self.PEAK_TARGET_DBFS - audio.max_dBFS
            audio = audio.apply_gain(gain)

        # Trim silence
        audio = self._trim_silence(audio)

        # Duration validation
        duration_s = len(audio) / 1000.0
        if duration_s < self.MIN_DURATION_S:
            raise AudioNormalizationError(
                "Recording too short — must be at least 1 second after silence trimming"
            )
        if duration_s > self.MAX_DURATION_S:
            raise AudioNormalizationError(
                "Recording exceeds 60-second maximum"
            )

        # Export canonical WAV
        wav_buf = io.BytesIO()
        audio.export(wav_buf, format="wav")
        wav_bytes = wav_buf.getvalue()

        # Export MP3 for streaming
        mp3_buf = io.BytesIO()
        audio.export(mp3_buf, format="mp3", bitrate="128k")
        mp3_bytes = mp3_buf.getvalue()

        # Generate voice sample at 22.05kHz
        sample_bytes = self._generate_voice_sample(audio)

        return NormalizedAudio(
            wav_bytes=wav_bytes,
            mp3_bytes=mp3_bytes,
            sample_bytes=sample_bytes,
            duration_seconds=duration_s,
        )

    def _trim_silence(self, audio: AudioSegment) -> AudioSegment:
        """Trim leading and trailing silence exceeding 500ms.

        Uses pydub's silence detection to find leading/trailing silent
        portions and trims them down to at most SILENCE_THRESHOLD_MS.

        Args:
            audio: AudioSegment to trim.

        Returns:
            Trimmed AudioSegment with at most 500ms of leading/trailing silence.
        """
        if len(audio) == 0:
            return audio

        # detect_leading_silence returns ms of silence at the start
        leading_ms = detect_leading_silence(
            audio, silence_threshold=self.SILENCE_THRESH_DB, chunk_size=10
        )
        # For trailing silence, reverse the audio and detect leading silence
        trailing_ms = detect_leading_silence(
            audio.reverse(), silence_threshold=self.SILENCE_THRESH_DB, chunk_size=10
        )

        # Calculate trim points: keep at most 500ms of silence on each end
        trim_start = max(0, leading_ms - self.SILENCE_THRESHOLD_MS)
        trim_end = max(0, trailing_ms - self.SILENCE_THRESHOLD_MS)

        if trim_start == 0 and trim_end == 0:
            return audio

        end_point = len(audio) - trim_end
        if end_point <= trim_start:
            # All silence — return empty
            return AudioSegment.empty()

        return audio[trim_start:end_point]

    def _generate_voice_sample(self, audio: AudioSegment) -> bytes:
        """Generate a voice sample at 22.05kHz/16-bit/mono WAV.

        Resamples the canonical audio to the voice cloning standard
        format for future model training.

        Args:
            audio: Canonical AudioSegment (already 16-bit mono).

        Returns:
            WAV bytes at 22.05kHz, 16-bit, mono.
        """
        sample_audio = audio.set_frame_rate(self.VOICE_SAMPLE_RATE)
        sample_audio = sample_audio.set_sample_width(self.CANONICAL_SAMPLE_WIDTH)
        sample_audio = sample_audio.set_channels(self.CANONICAL_CHANNELS)

        buf = io.BytesIO()
        sample_audio.export(buf, format="wav")
        return buf.getvalue()

    def _apply_fade(self, audio_bytes: bytes, fade_ms: int = 500) -> bytes:
        """Apply fade-in and fade-out to audio for smooth playback blending.

        Args:
            audio_bytes: WAV audio bytes to apply fades to.
            fade_ms: Duration of fade in milliseconds (default 500ms).

        Returns:
            WAV bytes with fade-in and fade-out applied.

        Raises:
            AudioNormalizationError: If audio cannot be decoded.
        """
        try:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
        except Exception as exc:
            raise AudioNormalizationError(
                f"Could not apply fade — invalid audio: {exc}"
            ) from exc

        # Clamp fade duration to half the audio length
        max_fade = len(audio) // 2
        effective_fade = min(fade_ms, max_fade)

        if effective_fade > 0:
            audio = audio.fade_in(effective_fade).fade_out(effective_fade)

        buf = io.BytesIO()
        audio.export(buf, format="wav")
        return buf.getvalue()
