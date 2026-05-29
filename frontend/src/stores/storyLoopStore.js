/**
 * Story Loop Store
 * Manages the core story loop state machine for the voice-first,
 * turn-based interaction model.
 *
 * Phases: narrating → awaiting_input → recording → processing → error
 * Requirements: 1.1, 1.2, 1.3, 1.5, 1.6
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

/**
 * Valid phases for the story loop state machine.
 * @typedef {'narrating' | 'awaiting_input' | 'recording' | 'processing' | 'error'} StoryLoopPhase
 */

/**
 * @typedef {Object} StoryBeat
 * @property {string} narration - Max 3 sentences
 * @property {string} illustrationUrl - Scene image URL
 * @property {Array<SuggestionCard>} suggestions - 2-3 suggestion cards
 * @property {string} perspective - Which twin's POV
 * @property {boolean} isMilestone - Triggers celebration animation
 */

/**
 * @typedef {Object} SuggestionCard
 * @property {string} id
 * @property {string} label - Max 4 words
 * @property {string} illustrationUrl - Card illustration
 * @property {string} storyDirection - Full text sent to backend
 */

const initialState = {
  // Story loop state machine
  phase: 'processing', // Start in processing — waiting for first beat from backend
  activeTwin: 'twin1',

  // Current beat data
  currentBeat: null,
  suggestions: [],

  // TTS state
  ttsPlaying: false,
  highlightedSentence: 0,

  // Voice input state
  isRecording: false,
  lastTranscript: null,

  // Error state
  error: null,

  // Session
  turnCount: 0,
};

export const useStoryLoopStore = create(
  devtools(
    (set, get) => ({
      ...initialState,

      // --- Actions ---

      /**
       * Submit voice input transcript.
       * Transitions to 'processing' phase and stores the transcript.
       * Only allowed during 'awaiting_input' or 'recording' phases.
       * The actual WebSocket call is handled by a separate hook.
       */
      submitVoiceInput: (transcript) => {
        const { phase } = get();
        if (phase !== 'awaiting_input' && phase !== 'recording') return;

        set({
          phase: 'processing',
          lastTranscript: transcript,
          isRecording: false,
        }, false, 'storyLoop/submitVoiceInput');
      },

      /**
       * Submit a suggestion card selection.
       * Finds the card in suggestions and transitions to 'processing'.
       * Only allowed during 'awaiting_input' phase.
       */
      submitCardSelection: (cardId) => {
        const { phase, suggestions } = get();
        if (phase !== 'awaiting_input') return;

        const card = suggestions.find((c) => c.id === cardId);
        if (!card) return;

        set({
          phase: 'processing',
          lastTranscript: card.storyDirection,
        }, false, 'storyLoop/submitCardSelection');
      },

      /**
       * Called when TTS finishes reading the current narration.
       * Transitions from 'narrating' to 'awaiting_input'.
       */
      onTTSComplete: () => {
        const { phase } = get();
        if (phase !== 'narrating') return;

        set({
          phase: 'awaiting_input',
          ttsPlaying: false,
          highlightedSentence: 0,
        }, false, 'storyLoop/onTTSComplete');
      },

      /**
       * Start recording voice input.
       * Only allowed during 'awaiting_input' phase.
       */
      startRecording: () => {
        const { phase } = get();
        if (phase !== 'awaiting_input') return;

        set({
          phase: 'recording',
          isRecording: true,
        }, false, 'storyLoop/startRecording');
      },

      /**
       * Cancel an active recording and return to awaiting_input.
       */
      cancelRecording: () => {
        const { phase } = get();
        if (phase !== 'recording') return;

        set({
          phase: 'awaiting_input',
          isRecording: false,
        }, false, 'storyLoop/cancelRecording');
      },

      /**
       * Switch the active twin and increment turn count.
       * Alternates between 'twin1' and 'twin2'.
       */
      switchTurn: () => {
        const { activeTwin, turnCount } = get();
        set({
          activeTwin: activeTwin === 'twin1' ? 'twin2' : 'twin1',
          turnCount: turnCount + 1,
        }, false, 'storyLoop/switchTurn');
      },

      /**
       * Receive a new story beat from the backend.
       * Sets current beat, suggestions, transitions to 'narrating',
       * and switches the turn.
       */
      receiveBeat: (beat) => {
        set({
          phase: 'narrating',
          currentBeat: beat,
          suggestions: beat.suggestions || [],
          ttsPlaying: true,
          highlightedSentence: 0,
          error: null,
        }, false, 'storyLoop/receiveBeat');

        // Switch turn after receiving a new beat
        get().switchTurn();
      },

      /**
       * Set the highlighted sentence index during TTS playback.
       */
      setHighlightedSentence: (index) => {
        set({ highlightedSentence: index }, false, 'storyLoop/setHighlightedSentence');
      },

      /**
       * Set an error state with a message.
       * Transitions to 'error' phase.
       */
      setError: (msg) => {
        set({
          phase: 'error',
          error: msg,
          isRecording: false,
        }, false, 'storyLoop/setError');
      },

      /**
       * Retry after an error.
       * Clears the error and returns to 'awaiting_input'.
       */
      retry: () => {
        set({
          phase: 'awaiting_input',
          error: null,
        }, false, 'storyLoop/retry');
      },

      /**
       * Reset all state to initial values.
       */
      reset: () => {
        set({ ...initialState }, false, 'storyLoop/reset');
      },
    }),
    { name: 'StoryLoopStore' }
  )
);
