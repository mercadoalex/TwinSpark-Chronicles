/**
 * Session Store
 * Manages WebSocket connection state and session data
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/**
 * @typedef {Object} SessionState
 * @property {boolean} isConnected - WebSocket connection status
 * @property {string} connectionState - Current connection state
 * @property {Object|null} profiles - Character profiles
 * @property {string} sessionId - Current session ID
 * @property {string|null} error - Connection error message
 * @property {boolean} isReconnecting - Reconnection attempt status
 * @property {number} reconnectAttempts - Number of reconnection attempts
 */

export const useSessionStore = create(
  devtools(
    persist(
      (set, get) => ({
        // State
        isConnected: false,
        connectionState: 'DISCONNECTED',
        profiles: null,
        sessionId: '',
        error: null,
        isReconnecting: false,
        reconnectAttempts: 0,
        previousDurationSeconds: 0,

        // Actions
        setConnected: (connected) => 
          set({ isConnected: connected }, false, 'session/setConnected'),

        setConnectionState: (state) => 
          set({ connectionState: state }, false, 'session/setConnectionState'),

        setProfiles: (profiles) => 
          set({ profiles }, false, 'session/setProfiles'),

        setSessionId: (sessionId) => 
          set({ sessionId }, false, 'session/setSessionId'),

        setError: (error) => 
          set({ error }, false, 'session/setError'),

        setReconnecting: (isReconnecting, attempts = 0) => 
          set({ 
            isReconnecting, 
            reconnectAttempts: attempts 
          }, false, 'session/setReconnecting'),

        clearError: () => 
          set({ error: null }, false, 'session/clearError'),

        reset: () => 
          set({
            isConnected: false,
            connectionState: 'DISCONNECTED',
            profiles: null,
            sessionId: '',
            error: null,
            isReconnecting: false,
            reconnectAttempts: 0,
            previousDurationSeconds: 0
          }, false, 'session/reset'),

        // Selectors
        getConnectionStatus: () => {
          const state = get();
          return {
            isConnected: state.isConnected,
            state: state.connectionState,
            error: state.error,
            isReconnecting: state.isReconnecting,
            attempts: state.reconnectAttempts
          };
        },

        hasProfiles: () => {
          return get().profiles !== null;
        }
      }),
      {
        name: 'session-storage',
        partialize: (state) => ({
          profiles: state.profiles,
          sessionId: state.sessionId
        })
      }
    ),
    { name: 'SessionStore' }
  )
);