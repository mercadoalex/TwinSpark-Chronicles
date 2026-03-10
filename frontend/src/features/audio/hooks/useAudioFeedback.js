/**
 * useAudioFeedback Hook
 * Manages UI sound effects
 */

import { useCallback, useEffect, useState } from 'react';
import { audioFeedbackService } from '../services/audioFeedbackService';

/**
 * Hook for managing audio feedback
 * @returns {Object} Audio feedback utilities
 */
export function useAudioFeedback() {
  const [isEnabled, setIsEnabled] = useState(audioFeedbackService.getEnabled());

  /**
   * Initialize audio context on first user interaction
   */
  const init = useCallback(() => {
    audioFeedbackService.init();
  }, []);

  /**
   * Play success sound
   */
  const playSuccess = useCallback(() => {
    audioFeedbackService.playSuccess();
  }, []);

  /**
   * Play error sound
   */
  const playError = useCallback(() => {
    audioFeedbackService.playError();
  }, []);

  /**
   * Play notification sound
   */
  const playNotification = useCallback(() => {
    audioFeedbackService.playNotification();
  }, []);

  /**
   * Play choice sound
   */
  const playChoice = useCallback(() => {
    audioFeedbackService.playChoice();
  }, []);

  /**
   * Play custom beep
   */
  const playBeep = useCallback((frequency, duration, volume) => {
    audioFeedbackService.playBeep(frequency, duration, volume);
  }, []);

  /**
   * Toggle audio feedback
   */
  const toggle = useCallback(() => {
    const newState = !isEnabled;
    audioFeedbackService.setEnabled(newState);
    setIsEnabled(newState);
  }, [isEnabled]);

  /**
   * Set enabled state
   */
  const setEnabled = useCallback((enabled) => {
    audioFeedbackService.setEnabled(enabled);
    setIsEnabled(enabled);
  }, []);

  // Auto-init on mount
  useEffect(() => {
    // Initialize on first click anywhere
    const handleFirstClick = () => {
      init();
      document.removeEventListener('click', handleFirstClick);
    };

    document.addEventListener('click', handleFirstClick);

    return () => {
      document.removeEventListener('click', handleFirstClick);
    };
  }, [init]);

  return {
    playSuccess,
    playError,
    playNotification,
    playChoice,
    playBeep,
    isEnabled,
    toggle,
    setEnabled,
    init
  };
}