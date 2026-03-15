/**
 * Multimodal Store
 * Manages camera, microphone, emotion, transcript, and input pipeline state
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

/** Max age (ms) for buffered messages during WebSocket disconnect */
const INPUT_BUFFER_MAX_AGE_MS = 5000;

let transcriptTimer = null;

export const useMultimodalStore = create(
  devtools(
    (set, get) => ({
      // State
      cameraActive: false,
      micActive: false,
      currentEmotions: [],        // [{face_id, emotion, confidence}]
      lastTranscript: null,       // {text, confidence}
      transcriptVisible: false,   // controls 3-second speech bubble
      isSpeaking: false,          // VAD speech detection active
      cameraError: null,          // 'camera_unavailable' | 'camera_lost' | null
      micError: null,             // 'mic_unavailable' | 'mic_lost' | null
      allInputsUnavailable: false,
      privacyConsented: false,
      inputBuffer: [],            // buffered messages during disconnect (max 5s)

      // Actions
      setCameraActive: (active) =>
        set((state) => {
          const allUnavailable = !active && !state.micActive;
          return {
            cameraActive: active,
            cameraError: active ? null : state.cameraError,
            allInputsUnavailable: allUnavailable,
          };
        }, false, 'multimodal/setCameraActive'),

      setMicActive: (active) =>
        set((state) => {
          const allUnavailable = !state.cameraActive && !active;
          return {
            micActive: active,
            micError: active ? null : state.micError,
            allInputsUnavailable: allUnavailable,
          };
        }, false, 'multimodal/setMicActive'),

      setCurrentEmotions: (emotions) =>
        set({ currentEmotions: emotions }, false, 'multimodal/setCurrentEmotions'),

      setLastTranscript: (transcript) => {
        // Clear any existing timer
        if (transcriptTimer) {
          clearTimeout(transcriptTimer);
          transcriptTimer = null;
        }

        set(
          { lastTranscript: transcript, transcriptVisible: true },
          false,
          'multimodal/setLastTranscript'
        );

        // Auto-hide after 3 seconds
        transcriptTimer = setTimeout(() => {
          set({ transcriptVisible: false }, false, 'multimodal/hideTranscript');
          transcriptTimer = null;
        }, 3000);
      },

      setTranscriptVisible: (visible) =>
        set({ transcriptVisible: visible }, false, 'multimodal/setTranscriptVisible'),

      setIsSpeaking: (speaking) =>
        set({ isSpeaking: speaking }, false, 'multimodal/setIsSpeaking'),

      setCameraError: (error) =>
        set((state) => {
          const cameraDown = error != null;
          const allUnavailable = cameraDown && (state.micError != null || !state.micActive);
          return {
            cameraError: error,
            cameraActive: cameraDown ? false : state.cameraActive,
            allInputsUnavailable: allUnavailable,
          };
        }, false, 'multimodal/setCameraError'),

      setMicError: (error) =>
        set((state) => {
          const micDown = error != null;
          const allUnavailable = (state.cameraError != null || !state.cameraActive) && micDown;
          return {
            micError: error,
            micActive: micDown ? false : state.micActive,
            allInputsUnavailable: allUnavailable,
          };
        }, false, 'multimodal/setMicError'),

      setAllInputsUnavailable: (unavailable) =>
        set({ allInputsUnavailable: unavailable }, false, 'multimodal/setAllInputsUnavailable'),

      setPrivacyConsented: (consented) =>
        set({ privacyConsented: consented }, false, 'multimodal/setPrivacyConsented'),

      addToInputBuffer: (message) =>
        set((state) => {
          const now = Date.now();
          // Drop messages older than 5 seconds
          const filtered = state.inputBuffer.filter(
            (m) => now - m.bufferedAt < INPUT_BUFFER_MAX_AGE_MS
          );
          return {
            inputBuffer: [...filtered, { ...message, bufferedAt: now }],
          };
        }, false, 'multimodal/addToInputBuffer'),

      flushInputBuffer: () => {
        const buffer = get().inputBuffer;
        set({ inputBuffer: [] }, false, 'multimodal/flushInputBuffer');
        return buffer;
      },

      clearInputBuffer: () =>
        set({ inputBuffer: [] }, false, 'multimodal/clearInputBuffer'),

      reset: () => {
        if (transcriptTimer) {
          clearTimeout(transcriptTimer);
          transcriptTimer = null;
        }
        set({
          cameraActive: false,
          micActive: false,
          currentEmotions: [],
          lastTranscript: null,
          transcriptVisible: false,
          isSpeaking: false,
          cameraError: null,
          micError: null,
          allInputsUnavailable: false,
          privacyConsented: false,
          inputBuffer: [],
        }, false, 'multimodal/reset');
      },
    }),
    { name: 'MultimodalStore' }
  )
);
