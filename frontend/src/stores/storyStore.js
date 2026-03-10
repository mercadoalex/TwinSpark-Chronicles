/**
 * Story Store
 * Manages story progression, beats, and history
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

/**
 * @typedef {Object} StoryBeat
 * @property {string} narration
 * @property {string} child1_perspective
 * @property {string} child2_perspective
 * @property {string|null} scene_image_url
 * @property {string[]} choices
 * @property {Object} metadata
 */

export const useStoryStore = create(
  devtools(
    (set, get) => ({
      // State
      currentBeat: null,
      history: [],
      isGenerating: false,
      isComplete: false,
      currentAssets: {
        narration: '',
        child1_perspective: '',
        child2_perspective: '',
        image: null,
        choices: []
      },
      error: null,

      // Actions
      setCurrentBeat: (beat) => 
        set({ currentBeat: beat }, false, 'story/setCurrentBeat'),

      addAsset: (assetType, content, metadata = {}) => 
        set((state) => {
          const newAssets = { ...state.currentAssets };
          
          switch (assetType) {
            case 'text':
              if (metadata.child === 'c1') {
                newAssets.child1_perspective = content;
              } else if (metadata.child === 'c2') {
                newAssets.child2_perspective = content;
              } else {
                newAssets.narration = content;
              }
              break;
            case 'image':
              newAssets.image = content;
              break;
            case 'interactive':
              newAssets.choices = Array.isArray(content) ? content : [];
              break;
          }
          
          return { currentAssets: newAssets };
        }, false, 'story/addAsset'),

      completeBeat: (choice) => 
        set((state) => {
          if (!state.currentBeat) return state;

          return {
            history: [...state.history, {
              ...state.currentBeat,
              choiceMade: choice,
              timestamp: new Date().toISOString()
            }],
            currentBeat: null,
            currentAssets: {
              narration: '',
              child1_perspective: '',
              child2_perspective: '',
              image: null,
              choices: []
            }
          };
        }, false, 'story/completeBeat'),

      setGenerating: (isGenerating) => 
        set({ isGenerating }, false, 'story/setGenerating'),

      setComplete: (isComplete) => 
        set({ isComplete }, false, 'story/setComplete'),

      setError: (error) => 
        set({ error }, false, 'story/setError'),

      clearError: () => 
        set({ error: null }, false, 'story/clearError'),

      reset: () => 
        set({
          currentBeat: null,
          history: [],
          isGenerating: false,
          isComplete: false,
          currentAssets: {
            narration: '',
            child1_perspective: '',
            child2_perspective: '',
            image: null,
            choices: []
          },
          error: null
        }, false, 'story/reset'),

      // Selectors
      isAssetsComplete: () => {
        const { currentAssets } = get();
        return !!(
          currentAssets.narration &&
          currentAssets.child1_perspective &&
          currentAssets.child2_perspective &&
          currentAssets.choices.length > 0
        );
      },

      getBeatCount: () => {
        return get().history.length;
      },

      getLastChoice: () => {
        const { history } = get();
        if (history.length === 0) return null;
        return history[history.length - 1].choiceMade;
      }
    }),
    { name: 'StoryStore' }
  )
);