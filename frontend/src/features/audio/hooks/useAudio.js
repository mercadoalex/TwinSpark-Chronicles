/**
 * useAudio Hook
 * Manages Text-to-Speech functionality
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { ttsService } from '../services/ttsService';

/**
 * Hook for managing TTS audio
 * @param {string} [defaultLanguage='en'] - Default language
 * @returns {Object} Audio utilities
 */
export function useAudio(defaultLanguage = 'en') {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const checkIntervalRef = useRef(null);

  /**
   * Start speaking interval checker
   */
  const startSpeakingCheck = useCallback(() => {
    if (checkIntervalRef.current) return;

    checkIntervalRef.current = setInterval(() => {
      setIsSpeaking(ttsService.isSpeaking());
      setIsPaused(ttsService.isPaused());
    }, 100);
  }, []);

  /**
   * Stop speaking interval checker
   */
  const stopSpeakingCheck = useCallback(() => {
    if (checkIntervalRef.current) {
      clearInterval(checkIntervalRef.current);
      checkIntervalRef.current = null;
    }
  }, []);

  /**
   * Speak text
   */
  const speak = useCallback(async (text, language = defaultLanguage, options = {}) => {
    if (!text) {
      console.warn('⚠️ No text provided to speak');
      return;
    }

    startSpeakingCheck();
    
    try {
      await ttsService.speak(text, language, options);
    } finally {
      stopSpeakingCheck();
      setIsSpeaking(false);
      setIsPaused(false);
    }
  }, [defaultLanguage, startSpeakingCheck, stopSpeakingCheck]);

  /**
   * Stop speaking
   */
  const stop = useCallback(() => {
    ttsService.stop();
    stopSpeakingCheck();
    setIsSpeaking(false);
    setIsPaused(false);
  }, [stopSpeakingCheck]);

  /**
   * Pause speaking
   */
  const pause = useCallback(() => {
    ttsService.pause();
    setIsPaused(true);
  }, []);

  /**
   * Resume speaking
   */
  const resume = useCallback(() => {
    ttsService.resume();
    setIsPaused(false);
  }, []);

  /**
   * Get available voices
   */
  const getVoices = useCallback((language) => {
    return ttsService.getVoicesForLanguage(language || defaultLanguage);
  }, [defaultLanguage]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  return {
    speak,
    stop,
    pause,
    resume,
    isSpeaking,
    isPaused,
    getVoices,
    isAvailable: ttsService.isEnabled
  };
}