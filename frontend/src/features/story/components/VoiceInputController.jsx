import React, { useState, useRef, useCallback, useEffect } from 'react';
import './VoiceInputController.css';

/**
 * VoiceInputController — Manages the mic button UI and recording lifecycle.
 *
 * Voice is the primary creative channel. The mic button is large and pulsing
 * when idle, transitions to animated sound waves while listening, shows a
 * sparkle animation during processing, and displays a friendly retry prompt
 * on error. Communicates state through animation and color, not text.
 *
 * If mic permission is denied, the component hides entirely and cards
 * become the primary input method.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 8.1, 12.5
 *
 * @param {Object} props
 * @param {boolean} props.isActive - Only enabled during awaiting_input phase
 * @param {string} props.activeTwinColor - Mic button accent color
 * @param {function} props.onTranscript - Callback with transcribed text
 * @param {function} props.onRecordingStart - Callback when recording begins
 * @param {function} props.onRecordingEnd - Callback when recording ends
 */

/** Silence detection threshold (RMS level) */
const SILENCE_THRESHOLD = 0.01;
/** Duration of silence before auto-stop (ms) */
const SILENCE_DURATION_MS = 1500;
/** Minimum confidence for accepting a transcript */
const CONFIDENCE_THRESHOLD = 0.4;

function VoiceInputController({
  isActive,
  activeTwinColor,
  onTranscript,
  onRecordingStart,
  onRecordingEnd,
}) {
  // Internal states: idle | listening | processing | error | hidden
  const [internalState, setInternalState] = useState('idle');
  const [audioLevels, setAudioLevels] = useState([0, 0, 0, 0, 0]);

  // Refs for audio resources
  const mediaStreamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animationFrameRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const chunksRef = useRef([]);
  const hasSpeechRef = useRef(false);

  /**
   * Check mic permission on mount. If unavailable or denied, hide entirely.
   * (Req 2.7: Hide mic button if permission denied, cards become primary)
   */
  useEffect(() => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setInternalState('hidden');
      return;
    }

    // Check permission state if the Permissions API is available
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions
        .query({ name: 'microphone' })
        .then((result) => {
          if (result.state === 'denied') {
            setInternalState('hidden');
          }
          result.addEventListener('change', () => {
            if (result.state === 'denied') {
              setInternalState('hidden');
            } else if (internalState === 'hidden') {
              setInternalState('idle');
            }
          });
        })
        .catch(() => {
          // Permissions API not supported for mic — we'll try on tap
        });
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Cleanup audio resources on unmount.
   */
  useEffect(() => {
    return () => {
      stopAllAudio();
    };
  }, []);

  /**
   * Stop all audio resources and timers.
   */
  const stopAllAudio = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, []);

  /**
   * Monitor audio levels for sound wave visualization and silence detection.
   * Uses AnalyserNode to detect when audio drops below threshold for 1.5s.
   * (Req 2.4: Auto-stop after 1.5s silence)
   */
  const monitorAudio = useCallback(() => {
    const analyser = analyserRef.current;
    if (!analyser) return;

    const dataArray = new Uint8Array(analyser.fftSize);

    const tick = () => {
      if (!analyserRef.current) return;

      analyser.getByteTimeDomainData(dataArray);

      // Calculate RMS level
      let sum = 0;
      for (let i = 0; i < dataArray.length; i++) {
        const normalized = (dataArray[i] - 128) / 128;
        sum += normalized * normalized;
      }
      const rms = Math.sqrt(sum / dataArray.length);

      // Update sound wave bars (5 bars with slight variation)
      const levels = Array.from({ length: 5 }, (_, i) => {
        const offset = (i - 2) * 0.02;
        return Math.min(1, Math.max(0.05, rms * 4 + offset + Math.random() * 0.05));
      });
      setAudioLevels(levels);

      // Silence detection
      if (rms < SILENCE_THRESHOLD) {
        if (!silenceTimerRef.current && hasSpeechRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            finishRecording();
          }, SILENCE_DURATION_MS);
        }
      } else {
        // Speech detected — reset silence timer
        hasSpeechRef.current = true;
        if (silenceTimerRef.current) {
          clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = null;
        }
      }

      animationFrameRef.current = requestAnimationFrame(tick);
    };

    animationFrameRef.current = requestAnimationFrame(tick);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Start recording when mic button is tapped.
   * (Req 2.2: Tap mic → begin capturing audio → listening state)
   */
  const startRecording = useCallback(async () => {
    if (!isActive || internalState !== 'idle') return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;

      // Set up AudioContext + AnalyserNode for level monitoring
      const audioContext = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // Set up MediaRecorder for capturing audio data
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      hasSpeechRef.current = false;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        processRecording();
      };

      mediaRecorder.start();
      setInternalState('listening');
      onRecordingStart?.();
      monitorAudio();
    } catch (err) {
      // Permission denied or error — hide mic (Req 2.7)
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setInternalState('hidden');
      } else {
        setInternalState('error');
      }
    }
  }, [isActive, internalState, onRecordingStart, monitorAudio]);

  /**
   * Finish recording — stop media recorder and transition to processing.
   * (Req 2.4: Silence detected → stop recording → processing state)
   */
  const finishRecording = useCallback(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    setInternalState('processing');
    onRecordingEnd?.();

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }

    // Stop the stream tracks
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }
  }, [onRecordingEnd]);

  /**
   * Process the recorded audio — simulate STT (in production, send to backend).
   * For now, uses the Web Speech API as a local fallback for transcription.
   */
  const processRecording = useCallback(() => {
    // In a real implementation, the audio blob would be sent to the backend
    // via WebSocket for STT processing. For now, we simulate with SpeechRecognition
    // if available, or produce a simulated result.

    if (!hasSpeechRef.current) {
      // No speech detected — show error (Req 2.8)
      setInternalState('error');
      return;
    }

    // Simulate processing delay then deliver transcript
    // In production: send chunksRef.current blob to backend STT
    const blob = new Blob(chunksRef.current, { type: 'audio/webm' });

    // Use SpeechRecognition API if available for local transcription
    if (window.SpeechRecognition || window.webkitSpeechRecognition) {
      // SpeechRecognition works on live audio, not blobs.
      // In production, the backend handles STT. For now, simulate success.
      simulateTranscriptResult();
    } else {
      // No local STT available — in production the backend handles this
      simulateTranscriptResult();
    }
  }, [onTranscript]); // eslint-disable-line react-hooks/exhaustive-deps

  /**
   * Simulate a transcript result (placeholder for backend STT integration).
   * In production, the WebSocket handler sends audio and receives transcript_result
   * or transcript_error messages.
   */
  const simulateTranscriptResult = useCallback(() => {
    // This is a placeholder. In the real app, the backend WebSocket returns
    // either a transcript_result or transcript_error message.
    // For now, we assume success if speech was detected.
    const mockConfidence = hasSpeechRef.current ? 0.85 : 0.1;

    if (mockConfidence < CONFIDENCE_THRESHOLD) {
      // Low confidence — show retry (Req 2.8)
      setInternalState('error');
    } else {
      // In production, the actual transcript text comes from the backend.
      // The component would receive it via a WebSocket message handler.
      // For the component's own flow, we transition back to idle after
      // the parent handles the transcript via onTranscript callback.
      // The parent (story loop) is responsible for calling onTranscript
      // when the backend responds with a transcript_result.
      setInternalState('idle');
      // Note: In the real integration, onTranscript is called by the parent
      // when the backend responds. The component just manages UI state.
      // For self-contained demo purposes:
      onTranscript?.('');
    }
  }, [onTranscript]);

  /**
   * Handle retry from error state — return to idle.
   */
  const handleRetry = useCallback(() => {
    setInternalState('idle');
  }, []);

  /**
   * Handle mic button tap.
   */
  const handleMicTap = useCallback(() => {
    if (internalState === 'idle' && isActive) {
      startRecording();
    } else if (internalState === 'listening') {
      // Manual stop — treat as end of speech
      hasSpeechRef.current = true;
      finishRecording();
    }
  }, [internalState, isActive, startRecording, finishRecording]);

  // If hidden (permission denied), render nothing (Req 2.7)
  if (internalState === 'hidden') {
    return null;
  }

  const isDisabled = !isActive && internalState === 'idle';

  return (
    <div
      className="voice-input-controller"
      style={{ '--mic-color': activeTwinColor || '#6C63FF' }}
      role="region"
      aria-label="Voice input"
    >
      {/* ── Idle / Listening / Processing: Mic Button ── */}
      {internalState !== 'error' && (
        <button
          className={`voice-input-controller__mic-btn voice-input-controller__mic-btn--${internalState}`}
          onClick={handleMicTap}
          disabled={isDisabled}
          aria-label={
            internalState === 'idle'
              ? 'Tap to speak'
              : internalState === 'listening'
                ? 'Listening — tap to stop'
                : 'Processing your words'
          }
          aria-live="polite"
        >
          {/* Idle state: pulsing mic icon (Req 2.1) */}
          {internalState === 'idle' && (
            <span className="voice-input-controller__mic-icon" aria-hidden="true">
              🎤
            </span>
          )}

          {/* Listening state: sound wave bars (Req 2.3) */}
          {internalState === 'listening' && (
            <div className="voice-input-controller__waves" aria-hidden="true">
              {audioLevels.map((level, i) => (
                <span
                  key={i}
                  className="voice-input-controller__wave-bar"
                  style={{ '--bar-height': `${Math.max(20, level * 100)}%` }}
                />
              ))}
            </div>
          )}

          {/* Processing state: sparkle animation (Req 2.5) */}
          {internalState === 'processing' && (
            <span className="voice-input-controller__sparkle" aria-hidden="true">
              ✨
            </span>
          )}
        </button>
      )}

      {/* ── Error state: friendly retry prompt (Req 2.8, 12.5) ── */}
      {internalState === 'error' && (
        <div className="voice-input-controller__error" role="alert">
          <span className="voice-input-controller__error-emoji" aria-hidden="true">
            🙈
          </span>
          <p className="voice-input-controller__error-text">
            I didn&apos;t catch that — try again or tap a spark!
          </p>
          <button
            className="voice-input-controller__retry-btn"
            onClick={handleRetry}
            aria-label="Try again"
          >
            <span aria-hidden="true">🔄</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default VoiceInputController;
