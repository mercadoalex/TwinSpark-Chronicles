/**
 * usePhotoUxEffects — shared hook for haptic and sound effects across photo components.
 * Reads audioStore.audioFeedbackEnabled to gate sound playback.
 * Haptic calls are independent of the mute setting.
 */

import { useCallback, useRef } from 'react';
import { useAudioStore } from '../../stores/audioStore';
import { audioFeedbackService } from '../../features/audio/services/audioFeedbackService';

/**
 * @returns {{ haptic, hapticPattern, playShutter, playChime, playWhoosh, playSnap }}
 */
export function usePhotoUxEffects() {
  const audioFeedbackEnabled = useAudioStore((s) => s.audioFeedbackEnabled);
  const initializedRef = useRef(false);

  const ensureAudioInit = useCallback(() => {
    if (!initializedRef.current) {
      audioFeedbackService.init();
      initializedRef.current = true;
    }
  }, []);

  /** Trigger a single vibration pulse (no-op if unsupported). */
  const haptic = useCallback((durationMs = 30) => {
    if (navigator.vibrate) {
      navigator.vibrate(durationMs);
    }
  }, []);

  /** Trigger a pattern vibration (no-op if unsupported). */
  const hapticPattern = useCallback((pattern) => {
    if (navigator.vibrate) {
      navigator.vibrate(pattern);
    }
  }, []);

  const playShutter = useCallback(() => {
    if (!audioFeedbackEnabled) return;
    ensureAudioInit();
    audioFeedbackService.playShutter();
  }, [audioFeedbackEnabled, ensureAudioInit]);

  const playChime = useCallback(() => {
    if (!audioFeedbackEnabled) return;
    ensureAudioInit();
    audioFeedbackService.playChime();
  }, [audioFeedbackEnabled, ensureAudioInit]);

  const playWhoosh = useCallback(() => {
    if (!audioFeedbackEnabled) return;
    ensureAudioInit();
    audioFeedbackService.playWhoosh();
  }, [audioFeedbackEnabled, ensureAudioInit]);

  const playSnap = useCallback(() => {
    if (!audioFeedbackEnabled) return;
    ensureAudioInit();
    audioFeedbackService.playSnap();
  }, [audioFeedbackEnabled, ensureAudioInit]);

  return { haptic, hapticPattern, playShutter, playChime, playWhoosh, playSnap };
}
