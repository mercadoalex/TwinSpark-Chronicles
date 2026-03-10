/**
 * Setup Store
 * Manages character setup flow and form state
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

export const useSetupStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        currentStep: 'privacy',
        privacyAccepted: false,
        language: 'en',
        child1: {
          name: '',
          gender: '',
          personality: '',
          spirit: '',
          toy: ''
        },
        child2: {
          name: '',
          gender: '',
          personality: '',
          spirit: '',
          toy: ''
        },
        isComplete: false,

        // Actions
        setStep: (step) => 
          set({ currentStep: step }, false, 'setup/setStep'),

        acceptPrivacy: () => 
          set({ 
            privacyAccepted: true,
            currentStep: 'language'
          }, false, 'setup/acceptPrivacy'),

        setLanguage: (language) => 
          set({ 
            language,
            currentStep: 'characters'
          }, false, 'setup/setLanguage'),

        setChild1: (data) => 
          set((state) => ({
            child1: { ...state.child1, ...data }
          }), false, 'setup/setChild1'),

        setChild2: (data) => 
          set((state) => ({
            child2: { ...state.child2, ...data }
          }), false, 'setup/setChild2'),

        completeSetup: () => 
          set({ 
            isComplete: true,
            currentStep: 'complete'
          }, false, 'setup/completeSetup'),

        reset: () => 
          set({
            currentStep: 'privacy',
            privacyAccepted: false,
            language: 'en',
            child1: {
              name: '',
              gender: '',
              personality: '',
              spirit: '',
              toy: ''
            },
            child2: {
              name: '',
              gender: '',
              personality: '',
              spirit: '',
              toy: ''
            },
            isComplete: false
          }, false, 'setup/reset'),

        // Selectors
        getProfiles: () => {
          const { language, child1, child2 } = get();
          return {
            lang: language,
            c1_name: child1.name,
            c1_gender: child1.gender,
            c1_personality: child1.personality,
            c1_spirit: child1.spirit,
            c1_toy: child1.toy,
            c2_name: child2.name,
            c2_gender: child2.gender,
            c2_personality: child2.personality,
            c2_spirit: child2.spirit,
            c2_toy: child2.toy
          };
        },

        isChild1Complete: () => {
          const { child1 } = get();
          return !!(
            child1.name &&
            child1.gender &&
            child1.personality &&
            child1.spirit &&
            child1.toy
          );
        },

        isChild2Complete: () => {
          const { child2 } = get();
          return !!(
            child2.name &&
            child2.gender &&
            child2.personality &&
            child2.spirit &&
            child2.toy
          );
        },

        canProceed: () => {
          const state = get();
          return (
            state.privacyAccepted &&
            state.isChild1Complete() &&
            state.isChild2Complete()
          );
        }
      }),
      {
        name: 'setup-storage',
        partialize: (state) => ({
          privacyAccepted: state.privacyAccepted,
          language: state.language,
          child1: state.child1,
          child2: state.child2
        })
      }
    ),
    { name: 'SetupStore' }
  )
);