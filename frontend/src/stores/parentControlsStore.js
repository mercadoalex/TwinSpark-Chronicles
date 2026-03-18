/**
 * Parent Controls Store
 * Manages content safety preferences: themes, complexity, blocked words, session time.
 * Persisted to localStorage so settings survive page reloads.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

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
