/**
 * Session Persistence Store
 * Manages save/load lifecycle for session snapshots.
 * Separate from sessionStore (which manages WebSocket connection state).
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { useSetupStore } from './setupStore';
import { useStoryStore } from './storyStore';
import { useSessionStore } from './sessionStore';

const API_BASE = 'http://localhost:8000';
const LS_KEY = 'twinspark_session_snapshot';

/**
 * Assemble a snapshot payload from the current store states.
 */
function assembleSnapshot() {
  const setup = useSetupStore.getState();
  const story = useStoryStore.getState();

  const siblingPairId = [setup.child1.name, setup.child2.name].sort().join(':');

  return {
    sibling_pair_id: siblingPairId,
    character_profiles: {
      c1_name: setup.child1.name,
      c1_gender: setup.child1.gender,
      c1_personality: setup.child1.personality,
      c1_spirit: setup.child1.spirit,
      c1_toy: setup.child1.toy,
      c2_name: setup.child2.name,
      c2_gender: setup.child2.gender,
      c2_personality: setup.child2.personality,
      c2_spirit: setup.child2.spirit,
      c2_toy: setup.child2.toy,
    },
    story_history: story.history,
    current_beat: story.currentBeat || null,
    session_metadata: {
      language: setup.language,
      story_beat_count: story.history.length,
      last_choice_made:
        story.history.length > 0
          ? story.history[story.history.length - 1].choiceMade
          : null,
      session_duration_seconds: 0,
    },
  };
}

/**
 * Helper: delay for ms milliseconds.
 */
function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const useSessionPersistenceStore = create(
  devtools(
    (set, get) => ({
      // State
      saveStatus: 'idle',
      availableSession: null,
      isRestoring: false,
      lastSaveError: null,

      /**
       * Save the current session snapshot to the server.
       * On failure: retry once after 2s, then fall back to localStorage.
       */
      saveSnapshot: async () => {
        set({ saveStatus: 'saving', lastSaveError: null }, false, 'persistence/saveSnapshot/start');

        const payload = assembleSnapshot();

        try {
          const resp = await fetch(`${API_BASE}/api/session/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });

          if (resp.ok) {
            set({ saveStatus: 'saved' }, false, 'persistence/saveSnapshot/saved');
            return;
          }

          throw new Error(`Save failed with status ${resp.status}`);
        } catch (err) {
          // Retry once after 2s
          try {
            await delay(2000);
            const retryResp = await fetch(`${API_BASE}/api/session/save`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(payload),
            });

            if (retryResp.ok) {
              set({ saveStatus: 'saved' }, false, 'persistence/saveSnapshot/retrySuccess');
              return;
            }

            throw new Error(`Retry failed with status ${retryResp.status}`);
          } catch (retryErr) {
            // Fall back to localStorage
            get().saveToLocalStorage();
            set(
              { saveStatus: 'error', lastSaveError: retryErr.message },
              false,
              'persistence/saveSnapshot/error'
            );
          }
        }
      },

      /**
       * Load a snapshot from the server for the given sibling pair.
       * Falls back to localStorage on 404 or network error.
       */
      loadSnapshot: async (siblingPairId) => {
        try {
          const resp = await fetch(
            `${API_BASE}/api/session/load/${encodeURIComponent(siblingPairId)}`
          );

          if (resp.ok) {
            const snapshot = await resp.json();
            set({ availableSession: snapshot }, false, 'persistence/loadSnapshot/loaded');
            return;
          }

          if (resp.status === 404) {
            // Fall back to localStorage
            get().restoreFromLocalStorage();
            return;
          }

          throw new Error(`Load failed with status ${resp.status}`);
        } catch (err) {
          // Network error — try localStorage
          get().restoreFromLocalStorage();
        }
      },

      /**
       * Restore session state from availableSession into the app stores.
       */
      restoreSession: () => {
        const { availableSession } = get();
        if (!availableSession) return;

        set({ isRestoring: true }, false, 'persistence/restoreSession/start');

        try {
          const snap = availableSession;

          // Hydrate setupStore
          const setupStore = useSetupStore.getState();
          setupStore.setChild1({
            name: snap.character_profiles.c1_name,
            gender: snap.character_profiles.c1_gender,
            personality: snap.character_profiles.c1_personality,
            spirit: snap.character_profiles.c1_spirit,
            toy: snap.character_profiles.c1_toy,
          });
          setupStore.setChild2({
            name: snap.character_profiles.c2_name,
            gender: snap.character_profiles.c2_gender,
            personality: snap.character_profiles.c2_personality,
            spirit: snap.character_profiles.c2_spirit,
            toy: snap.character_profiles.c2_toy,
          });
          if (snap.session_metadata && snap.session_metadata.language) {
            setupStore.setLanguage(snap.session_metadata.language);
          }
          setupStore.completeSetup();

          // Hydrate storyStore — bulk set for history and currentBeat
          useStoryStore.setState({
            history: snap.story_history || [],
            currentBeat: snap.current_beat || null,
          });

          // Hydrate sessionStore
          const sessionStore = useSessionStore.getState();
          sessionStore.setProfiles(snap.character_profiles);

          set({ isRestoring: false }, false, 'persistence/restoreSession/done');
        } catch (err) {
          console.error('Failed to restore session:', err);
          set({ isRestoring: false, availableSession: null }, false, 'persistence/restoreSession/error');
        }
      },

      /**
       * Delete a session snapshot on the server.
       */
      deleteSession: async (siblingPairId) => {
        try {
          await fetch(
            `${API_BASE}/api/session/${encodeURIComponent(siblingPairId)}`,
            { method: 'DELETE' }
          );
          set({ availableSession: null }, false, 'persistence/deleteSession');
        } catch (err) {
          console.error('Failed to delete session:', err);
        }
      },

      /**
       * Save the current snapshot to localStorage as a fallback.
       */
      saveToLocalStorage: () => {
        try {
          const payload = assembleSnapshot();
          localStorage.setItem(LS_KEY, JSON.stringify(payload));
        } catch (err) {
          console.error('Failed to save to localStorage:', err);
        }
      },

      /**
       * Restore a snapshot from localStorage into availableSession.
       */
      restoreFromLocalStorage: () => {
        try {
          const raw = localStorage.getItem(LS_KEY);
          if (raw) {
            const snapshot = JSON.parse(raw);
            set({ availableSession: snapshot }, false, 'persistence/restoreFromLocalStorage');
          }
        } catch (err) {
          console.error('Failed to restore from localStorage:', err);
          localStorage.removeItem(LS_KEY);
        }
      },

      /**
       * Push a localStorage snapshot to the server on reconnect.
       */
      syncLocalToServer: async () => {
        try {
          const raw = localStorage.getItem(LS_KEY);
          if (!raw) return;

          const payload = JSON.parse(raw);
          const resp = await fetch(`${API_BASE}/api/session/save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
          });

          if (resp.ok) {
            localStorage.removeItem(LS_KEY);
          }
        } catch (err) {
          console.error('Failed to sync localStorage to server:', err);
        }
      },
    }),
    { name: 'SessionPersistenceStore' }
  )
);
