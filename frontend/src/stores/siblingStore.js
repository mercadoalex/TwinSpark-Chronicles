/**
 * Sibling Dynamics Store
 * Manages sibling dynamics score, session summary, parent suggestions,
 * child roles, and waiting-for-child state
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export const useSiblingStore = create(
  devtools(
    (set) => ({
      // State
      siblingDynamicsScore: null,                        // 0.0-1.0
      sessionSummary: null,                              // plain-language string
      parentSuggestion: null,                            // string or null
      childRoles: { child1: null, child2: null },        // current prompt roles
      waitingForChild: null,                             // child ID if one hasn't responded

      // Actions
      setSiblingScore: (score) =>
        set({ siblingDynamicsScore: score }, false, 'sibling/setSiblingScore'),

      setSessionSummary: (summary) =>
        set({ sessionSummary: summary }, false, 'sibling/setSessionSummary'),

      setParentSuggestion: (suggestion) =>
        set({ parentSuggestion: suggestion }, false, 'sibling/setParentSuggestion'),

      setChildRoles: (roles) =>
        set({ childRoles: roles }, false, 'sibling/setChildRoles'),

      setWaitingForChild: (childId) =>
        set({ waitingForChild: childId }, false, 'sibling/setWaitingForChild'),

      reset: () =>
        set({
          siblingDynamicsScore: null,
          sessionSummary: null,
          parentSuggestion: null,
          childRoles: { child1: null, child2: null },
          waitingForChild: null,
        }, false, 'sibling/reset'),
    }),
    { name: 'SiblingStore' }
  )
);
