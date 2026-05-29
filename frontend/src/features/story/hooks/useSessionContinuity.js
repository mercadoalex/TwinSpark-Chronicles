/**
 * useSessionContinuity Hook
 *
 * Manages session persistence and auto-resume logic for TwinSpark Chronicles.
 * On app load, checks localStorage for an existing session and auto-resumes
 * within 2 seconds. When no session exists, signals that the ThemePicker
 * should be shown.
 *
 * Requirements: 7.1, 7.2, 7.3, 7.5, 7.6
 */

import { useState, useEffect, useCallback, useRef } from 'react';

const STORAGE_KEY = 'twinspark_story_session';
const AUTO_RESUME_DELAY_MS = 2000;

/**
 * @typedef {Object} TwinConfig
 * @property {string} id - Twin identifier ('twin1' or 'twin2')
 * @property {string} name - Display name
 * @property {string} avatar - Avatar URL or emoji
 * @property {string} color - Assigned color hex
 */

/**
 * @typedef {Object} SessionData
 * @property {string} sessionId - Unique session identifier
 * @property {string} activeTwin - Current active twin ('twin1' or 'twin2')
 * @property {number} turnCount - Number of turns taken
 * @property {string} theme - Selected adventure theme ID
 * @property {string|null} lastBeatId - ID of the last completed story beat
 * @property {Object} twinConfig - Configuration for both twins
 * @property {TwinConfig} twinConfig.twin1 - First twin config
 * @property {TwinConfig} twinConfig.twin2 - Second twin config
 */

/**
 * Generate a simple unique session ID.
 * @returns {string}
 */
function generateSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

/**
 * Read session data from localStorage.
 * @returns {SessionData|null}
 */
function readSessionFromStorage() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Basic validation — ensure required fields exist
    if (parsed && parsed.sessionId && parsed.theme && parsed.twinConfig) {
      return parsed;
    }
    return null;
  } catch {
    return null;
  }
}

/**
 * Write session data to localStorage.
 * @param {SessionData} sessionData
 */
function writeSessionToStorage(sessionData) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessionData));
  } catch {
    // Silently fail — localStorage may be full or unavailable
  }
}

/**
 * Remove session data from localStorage.
 */
function removeSessionFromStorage() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // Silently fail
  }
}

/**
 * Hook for managing session continuity.
 *
 * @returns {Object} Session continuity state and actions
 * @returns {boolean} return.hasSession - Whether an active session exists
 * @returns {SessionData|null} return.sessionData - Current session data
 * @returns {boolean} return.isResuming - Whether auto-resume is in progress
 * @returns {boolean} return.showWelcomeBack - Whether to show the welcome back animation
 * @returns {(themeId: string, twinConfig?: Object) => SessionData} return.startNewSession - Create a new session
 * @returns {() => void} return.clearSession - Remove the current session
 * @returns {(sessionState: Partial<SessionData>) => void} return.saveSession - Persist session state updates
 * @returns {() => void} return.onWelcomeBackComplete - Signal that welcome animation finished
 */
export function useSessionContinuity() {
  const [hasSession, setHasSession] = useState(false);
  const [sessionData, setSessionData] = useState(null);
  const [isResuming, setIsResuming] = useState(false);
  const [showWelcomeBack, setShowWelcomeBack] = useState(false);

  const resumeTimerRef = useRef(null);

  // On mount: check for existing session and begin auto-resume (Req 7.1, 7.2)
  useEffect(() => {
    const existing = readSessionFromStorage();

    if (existing) {
      setSessionData(existing);
      setHasSession(true);
      setIsResuming(true);
      setShowWelcomeBack(true);

      // Auto-resume after 2 seconds (Req 7.1)
      resumeTimerRef.current = setTimeout(() => {
        setShowWelcomeBack(false);
        setIsResuming(false);
      }, AUTO_RESUME_DELAY_MS);
    } else {
      // No session — ThemePicker should be shown (Req 7.3)
      setHasSession(false);
      setSessionData(null);
      setIsResuming(false);
    }

    return () => {
      if (resumeTimerRef.current) {
        clearTimeout(resumeTimerRef.current);
      }
    };
  }, []);

  /**
   * Start a new session with the selected theme (Req 7.5).
   * @param {string} themeId - The adventure theme ID
   * @param {Object} [twinConfig] - Optional twin configuration override
   * @returns {SessionData} The newly created session data
   */
  const startNewSession = useCallback((themeId, twinConfig) => {
    const defaultTwinConfig = {
      twin1: { id: 'twin1', name: 'Ale', avatar: '🦊', color: '#FF6B6B' },
      twin2: { id: 'twin2', name: 'Sofi', avatar: '🦄', color: '#6B9FFF' },
    };

    const newSession = {
      sessionId: generateSessionId(),
      activeTwin: 'twin1',
      turnCount: 0,
      theme: themeId,
      lastBeatId: null,
      twinConfig: twinConfig || defaultTwinConfig,
    };

    writeSessionToStorage(newSession);
    setSessionData(newSession);
    setHasSession(true);
    setIsResuming(false);
    setShowWelcomeBack(false);

    return newSession;
  }, []);

  /**
   * Clear the current session (e.g., after story completion) (Req 7.3).
   * After clearing, ThemePicker should be shown for a new adventure.
   */
  const clearSession = useCallback(() => {
    removeSessionFromStorage();
    setSessionData(null);
    setHasSession(false);
    setIsResuming(false);
    setShowWelcomeBack(false);
  }, []);

  /**
   * Persist current session state updates (Req 7.1, 7.6).
   * Merges the provided state with existing session data.
   * @param {Partial<SessionData>} sessionState - Fields to update
   */
  const saveSession = useCallback((sessionState) => {
    setSessionData((prev) => {
      if (!prev) return prev;
      const updated = { ...prev, ...sessionState };
      writeSessionToStorage(updated);
      return updated;
    });
  }, []);

  /**
   * Signal that the welcome back animation has completed.
   * Allows manual dismissal before the 2s timer.
   */
  const onWelcomeBackComplete = useCallback(() => {
    if (resumeTimerRef.current) {
      clearTimeout(resumeTimerRef.current);
    }
    setShowWelcomeBack(false);
    setIsResuming(false);
  }, []);

  return {
    hasSession,
    sessionData,
    isResuming,
    showWelcomeBack,
    startNewSession,
    clearSession,
    saveSession,
    onWelcomeBackComplete,
  };
}
