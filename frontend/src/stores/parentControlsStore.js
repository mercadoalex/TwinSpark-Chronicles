/**
 * Parent Controls Store
 * Manages content safety preferences: themes, complexity, blocked words, session time.
 * Persisted to localStorage so settings survive page reloads.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { websocketService } from '../features/session/services/websocketService';

const AVAILABLE_THEMES = [
  'friendship', 'nature', 'space', 'animals',
  'problem-solving', 'creativity', 'kindness', 'teamwork',
];

export const useParentControlsStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        allowedThemes: [...AVAILABLE_THEMES],
        complexityLevel: 'simple',
        customBlockedWords: [],
        sessionTimeLimitMinutes: 30,
        lastSessionEndEvent: (() => {
          try {
            const raw = localStorage.getItem('twinspark_last_session_end');
            return raw ? JSON.parse(raw) : null;
          } catch (_) { return null; }
        })(),

        // Actions
        setAllowedThemes: (themes) =>
          set({ allowedThemes: themes }, false, 'parentControls/setAllowedThemes'),

        toggleTheme: (theme) =>
          set((state) => {
            const has = state.allowedThemes.includes(theme);
            return {
              allowedThemes: has
                ? state.allowedThemes.filter((t) => t !== theme)
                : [...state.allowedThemes, theme],
            };
          }, false, 'parentControls/toggleTheme'),

        setComplexityLevel: (level) =>
          set({ complexityLevel: level }, false, 'parentControls/setComplexityLevel'),

        addBlockedWord: (word) =>
          set((state) => {
            const trimmed = word.trim().toLowerCase();
            if (!trimmed || state.customBlockedWords.includes(trimmed)) return state;
            return { customBlockedWords: [...state.customBlockedWords, trimmed] };
          }, false, 'parentControls/addBlockedWord'),

        removeBlockedWord: (word) =>
          set((state) => ({
            customBlockedWords: state.customBlockedWords.filter((w) => w !== word),
          }), false, 'parentControls/removeBlockedWord'),

        setSessionTimeLimit: (minutes) =>
          set({ sessionTimeLimitMinutes: minutes }, false, 'parentControls/setSessionTimeLimit'),

        sendTimeExtension: (minutes) => {
          websocketService.send({ type: 'TIME_EXTENSION', additional_minutes: minutes });
        },

        recordSessionEnd: (reason, childNames) => {
          const event = { reason, timestamp: new Date().toISOString(), child_names: childNames };
          try { localStorage.setItem('twinspark_last_session_end', JSON.stringify(event)); } catch (_) {}
          set({ lastSessionEndEvent: event }, false, 'parentControls/recordSessionEnd');
        },

        // Selectors
        getPreferencesPayload: () => {
          const s = get();
          return {
            allowed_themes: s.allowedThemes,
            complexity_level: s.complexityLevel,
            custom_blocked_words: s.customBlockedWords,
          };
        },
      }),
      {
        name: 'parent-controls-storage',
      }
    ),
    { name: 'ParentControlsStore' }
  )
);

export { AVAILABLE_THEMES };
