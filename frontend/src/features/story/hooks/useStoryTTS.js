/**
 * useStoryTTS Hook
 * Manages sentence-by-sentence TTS narration for the story loop.
 * Auto-plays when narration changes, tracks current sentence for highlighting,
 * and supports pause/resume via tap.
 *
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6
 */

import { useState, useCallback, useEffect, useRef } from 'react';

/** TTS rate for child comprehension (between 0.85x and 1.0x) */
const CHILD_TTS_RATE = 0.9;

/**
 * Split narration text into sentences on sentence-ending punctuation.
 * @param {string} text
 * @returns {string[]}
 */
function splitIntoSentences(text) {
  if (!text) return [];
  // Split on sentence-ending punctuation, keeping the delimiter attached
  const parts = text.match(/[^.!?]+[.!?]+/g);
  if (!parts) {
    // No sentence-ending punctuation found — treat entire text as one sentence
    return [text.trim()].filter(Boolean);
  }
  return parts.map((s) => s.trim()).filter(Boolean);
}

/**
 * Hook for managing story narration TTS with sentence-by-sentence tracking.
 *
 * @param {Object} params
 * @param {string} params.narration - The narration text to speak
 * @param {() => void} params.onComplete - Called when all sentences have been read
 * @param {(index: number) => void} params.onSentenceChange - Called with the index of the sentence currently being spoken
 * @returns {{ isSpeaking: boolean, isPaused: boolean, currentSentenceIndex: number, sentences: string[], pause: () => void, resume: () => void, cancel: () => void }}
 */
export function useStoryTTS({ narration, onComplete, onSentenceChange }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [sentences, setSentences] = useState([]);

  // Refs to track mutable state across async speech callbacks
  const sentenceIndexRef = useRef(0);
  const sentencesRef = useRef([]);
  const isCancelledRef = useRef(false);
  const onCompleteRef = useRef(onComplete);
  const onSentenceChangeRef = useRef(onSentenceChange);
  const narrationRef = useRef(narration);

  // Keep callback refs up to date
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    onSentenceChangeRef.current = onSentenceChange;
  }, [onSentenceChange]);

  /**
   * Speak a single sentence and return a promise that resolves when done.
   * @param {string} sentence
   * @returns {Promise<void>}
   */
  const speakSentence = useCallback((sentence) => {
    return new Promise((resolve) => {
      if (!window.speechSynthesis) {
        resolve();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(sentence);
      utterance.rate = CHILD_TTS_RATE;
      utterance.pitch = 1.1;
      utterance.volume = 0.8;

      utterance.onend = () => {
        resolve();
      };

      utterance.onerror = () => {
        // Resolve on error to avoid blocking the sequence
        resolve();
      };

      window.speechSynthesis.speak(utterance);
    });
  }, []);

  /**
   * Speak all sentences sequentially, calling onSentenceChange for each.
   * @param {string[]} sentenceList
   */
  const speakAll = useCallback(async (sentenceList) => {
    isCancelledRef.current = false;
    sentenceIndexRef.current = 0;

    for (let i = 0; i < sentenceList.length; i++) {
      if (isCancelledRef.current) return;

      sentenceIndexRef.current = i;
      setCurrentSentenceIndex(i);
      if (onSentenceChangeRef.current) {
        onSentenceChangeRef.current(i);
      }

      await speakSentence(sentenceList[i]);

      if (isCancelledRef.current) return;
    }

    // All sentences spoken
    setIsSpeaking(false);
    setIsPaused(false);
    if (onCompleteRef.current) {
      onCompleteRef.current();
    }
  }, [speakSentence]);

  /**
   * Pause the current narration.
   */
  const pause = useCallback(() => {
    if (window.speechSynthesis && window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
      setIsPaused(true);
    }
  }, []);

  /**
   * Resume paused narration.
   */
  const resume = useCallback(() => {
    if (window.speechSynthesis && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      setIsPaused(false);
    }
  }, []);

  /**
   * Cancel all narration.
   */
  const cancel = useCallback(() => {
    isCancelledRef.current = true;
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setIsPaused(false);
    setCurrentSentenceIndex(0);
  }, []);

  // Auto-start speaking when narration changes
  useEffect(() => {
    // Skip if narration hasn't actually changed
    if (narration === narrationRef.current && sentencesRef.current.length > 0) {
      return;
    }
    narrationRef.current = narration;

    if (!narration) {
      setSentences([]);
      sentencesRef.current = [];
      return;
    }

    // If speechSynthesis is not available, call onComplete immediately
    if (!window.speechSynthesis) {
      const parsed = splitIntoSentences(narration);
      setSentences(parsed);
      sentencesRef.current = parsed;
      if (onCompleteRef.current) {
        onCompleteRef.current();
      }
      return;
    }

    // Cancel any ongoing speech
    isCancelledRef.current = true;
    window.speechSynthesis.cancel();

    const parsed = splitIntoSentences(narration);
    setSentences(parsed);
    sentencesRef.current = parsed;

    if (parsed.length === 0) {
      if (onCompleteRef.current) {
        onCompleteRef.current();
      }
      return;
    }

    // Start speaking
    setIsSpeaking(true);
    setIsPaused(false);
    setCurrentSentenceIndex(0);
    speakAll(parsed);
  }, [narration, speakAll]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      isCancelledRef.current = true;
      if (window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  return {
    isSpeaking,
    isPaused,
    currentSentenceIndex,
    sentences,
    pause,
    resume,
    cancel,
  };
}
