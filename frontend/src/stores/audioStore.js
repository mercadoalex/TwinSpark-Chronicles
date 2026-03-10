/**
 * Audio Store
 * Manages audio settings and TTS state
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useAudioStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        ttsEnabled: true,
        ttsLanguage: 'en',
        ttsRate: 1.0,
        ttsPitch: 1.0,
        ttsVolume: 1.0,
        isSpeaking: false,
        isPaused: false,
        audioFeedbackEnabled: true,
        currentUtterance: null,

        // Actions
        setTTSEnabled: (enabled) => 
          set({ ttsEnabled: enabled }, false, 'audio/setTTSEnabled'),

        setTTSLanguage: (language) => 
          set({ ttsLanguage: language }, false, 'audio/setTTSLanguage'),

        setTTSRate: (rate) => 
          set({ ttsRate: rate }, false, 'audio/setTTSRate'),

        setTTSPitch: (pitch) => 
          set({ ttsPitch: pitch }, false, 'audio/setTTSPitch'),

        setTTSVolume: (volume) => 
          set({ ttsVolume: volume }, false, 'audio/setTTSVolume'),

        setIsSpeaking: (speaking) => 
          set({ isSpeaking: speaking }, false, 'audio/setIsSpeaking'),

        setIsPaused: (paused) => 
          set({ isPaused: paused }, false, 'audio/setIsPaused'),

        setAudioFeedbackEnabled: (enabled) => 
          set({ audioFeedbackEnabled: enabled }, false, 'audio/setAudioFeedbackEnabled'),

        setCurrentUtterance: (utterance) => 
          set({ currentUtterance: utterance }, false, 'audio/setCurrentUtterance'),

        toggleTTS: () => 
          set((state) => ({ 
            ttsEnabled: !state.ttsEnabled 
          }), false, 'audio/toggleTTS'),

        toggleAudioFeedback: () => 
          set((state) => ({ 
            audioFeedbackEnabled: !state.audioFeedbackEnabled 
          }), false, 'audio/toggleAudioFeedback'),

        reset: () => 
          set({
            ttsEnabled: true,
            ttsLanguage: 'en',
            ttsRate: 1.0,
            ttsPitch: 1.0,
            ttsVolume: 1.0,
            isSpeaking: false,
            isPaused: false,
            currentUtterance: null
          }, false, 'audio/reset'),

        // Selectors
        getTTSSettings: () => {
          const state = get();
          return {
            language: state.ttsLanguage,
            rate: state.ttsRate,
            pitch: state.ttsPitch,
            volume: state.ttsVolume
          };
        },

        isAudioEnabled: () => {
          return get().ttsEnabled || get().audioFeedbackEnabled;
        }
      }),
      {
        name: 'audio-storage',
        partialize: (state) => ({
          ttsEnabled: state.ttsEnabled,
          ttsLanguage: state.ttsLanguage,
          ttsRate: state.ttsRate,
          ttsPitch: state.ttsPitch,
          ttsVolume: state.ttsVolume,
          audioFeedbackEnabled: state.audioFeedbackEnabled
        })
      }
    ),
    { name: 'AudioStore' }
  )
);