/**
 * useMultimodalInput Hook
 * Coordinates Camera_Service and Audio_Input_Service, sends data over WebSocket,
 * listens for backend feedback, and manages capture lifecycle with buffering.
 *
 * Requirements: 8.1, 8.2, 8.3, 8.6, 10.3, 10.4
 */

import { useCallback, useEffect, useRef } from 'react';
import { cameraService } from '../services/cameraService.js';
import { audioInputService } from '../services/audioInputService.js';
import { useMultimodalStore } from '../../../stores/multimodalStore.js';
import { websocketService } from '../../session/services/websocketService.js';

/**
 * Generate a unique ID for each audio segment.
 * @returns {string}
 */
function generateSpeechId() {
  return `speech_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Hook that coordinates camera and audio capture, sends multimodal data
 * over WebSocket, and manages feedback from the backend.
 *
 * @returns {import('./useMultimodalInput').UseMultimodalInput}
 */
export function useMultimodalInput() {
  const cleanupRef = useRef([]);
  const capturingRef = useRef(false);

  const cameraActive = useMultimodalStore((s) => s.cameraActive);
  const micActive = useMultimodalStore((s) => s.micActive);
  const currentEmotions = useMultimodalStore((s) => s.currentEmotions);
  const lastTranscript = useMultimodalStore((s) => s.lastTranscript);
  const isSpeaking = useMultimodalStore((s) => s.isSpeaking);
  const cameraError = useMultimodalStore((s) => s.cameraError);
  const micError = useMultimodalStore((s) => s.micError);

  const {
    setCameraActive,
    setMicActive,
    setCurrentEmotions,
    setLastTranscript,
    setIsSpeaking,
    setCameraError,
    setMicError,
    setPrivacyConsented,
    addToInputBuffer,
    flushInputBuffer,
  } = useMultimodalStore.getState();

  // ─── Send or buffer a message ──────────────────────────────
  const sendOrBuffer = useCallback((message) => {
    if (websocketService.isConnected()) {
      websocketService.send(message);
    } else {
      addToInputBuffer(message);
    }
  }, [addToInputBuffer]);

  // ─── Flush buffered messages on reconnect ──────────────────
  const flushBuffer = useCallback(() => {
    const buffered = flushInputBuffer();
    for (const item of buffered) {
      const { bufferedAt, ...msg } = item;
      websocketService.send(msg);
    }
  }, [flushInputBuffer]);

  // ─── Start capture ─────────────────────────────────────────
  const startCapture = useCallback(async (privacyConsented) => {
    if (capturingRef.current) return;

    if (!privacyConsented) {
      console.warn('🎬 Cannot start capture without privacy consent');
      return;
    }

    setPrivacyConsented(true);
    capturingRef.current = true;

    // --- Camera ---
    try {
      cameraService.setPrivacyConsent(true);
      await cameraService.start();
      cameraService.startCapturing();
      setCameraActive(true);
    } catch {
      setCameraActive(false);
      setCameraError('camera_unavailable');
    }

    // --- Microphone ---
    try {
      await audioInputService.start();
      setMicActive(true);
    } catch {
      setMicActive(false);
      setMicError('mic_unavailable');
    }
  }, [setCameraActive, setMicActive, setCameraError, setMicError, setPrivacyConsented]);

  // ─── Stop capture ──────────────────────────────────────────
  const stopCapture = useCallback(() => {
    capturingRef.current = false;

    cameraService.stopCapturing();
    cameraService.stop();
    setCameraActive(false);

    audioInputService.stop();
    setMicActive(false);
    setIsSpeaking(false);
  }, [setCameraActive, setMicActive, setIsSpeaking]);

  // ─── Wire up event listeners on mount / tear down on unmount ─
  useEffect(() => {
    const unsubs = [];

    // --- Camera frame → WebSocket ---
    unsubs.push(
      cameraService.onFrame((base64Frame) => {
        sendOrBuffer({
          type: 'camera_frame',
          data: base64Frame,
          timestamp: new Date().toISOString(),
        });
      })
    );

    // --- Camera error events ---
    unsubs.push(
      cameraService.onUnavailable(() => {
        setCameraActive(false);
        setCameraError('camera_unavailable');
      })
    );
    unsubs.push(
      cameraService.onLost(() => {
        setCameraActive(false);
        setCameraError('camera_lost');
      })
    );
    unsubs.push(
      cameraService.onReconnected(() => {
        setCameraActive(true);
        setCameraError(null);
      })
    );

    // --- Audio segment → WebSocket ---
    unsubs.push(
      audioInputService.onSpeechSegment((base64Audio) => {
        const speechId = generateSpeechId();
        sendOrBuffer({
          type: 'audio_segment',
          data: base64Audio,
          timestamp: new Date().toISOString(),
          speech_id: speechId,
        });
        setIsSpeaking(false);
      })
    );

    // --- Audio error events ---
    unsubs.push(
      audioInputService.onUnavailable(() => {
        setMicActive(false);
        setMicError('mic_unavailable');
      })
    );
    unsubs.push(
      audioInputService.onLost(() => {
        setMicActive(false);
        setMicError('mic_lost');
      })
    );

    // --- VAD speaking state (poll via interval) ---
    const vadInterval = setInterval(() => {
      if (capturingRef.current) {
        setIsSpeaking(audioInputService.isSpeechDetected);
      }
    }, 200);

    // --- WebSocket feedback listeners ---
    unsubs.push(
      websocketService.on('emotion_feedback', (data) => {
        if (data.emotions) {
          setCurrentEmotions(data.emotions);
        }
      })
    );
    unsubs.push(
      websocketService.on('transcript_feedback', (data) => {
        if (data.text != null) {
          setLastTranscript({ text: data.text, confidence: data.confidence ?? 0 });
        }
      })
    );
    unsubs.push(
      websocketService.on('input_status', (data) => {
        if (data.camera != null) setCameraActive(data.camera);
        if (data.mic != null) setMicActive(data.mic);
      })
    );

    // --- Reconnect → flush buffer ---
    unsubs.push(
      websocketService.on('connected', () => {
        flushBuffer();
      })
    );

    cleanupRef.current = unsubs;

    return () => {
      unsubs.forEach((fn) => typeof fn === 'function' && fn());
      clearInterval(vadInterval);
      cleanupRef.current = [];
    };
  }, [
    sendOrBuffer,
    flushBuffer,
    setCameraActive,
    setMicActive,
    setCameraError,
    setMicError,
    setCurrentEmotions,
    setLastTranscript,
    setIsSpeaking,
  ]);

  return {
    startCapture,
    stopCapture,
    cameraActive,
    micActive,
    currentEmotion: currentEmotions.length > 0
      ? currentEmotions.reduce((best, e) => (e.confidence > best.confidence ? e : best)).emotion
      : null,
    lastTranscript: lastTranscript?.text ?? null,
    isSpeaking,
    cameraError,
    micError,
  };
}
