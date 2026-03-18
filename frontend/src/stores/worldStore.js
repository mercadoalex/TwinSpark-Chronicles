/**
 * World Store
 * Manages cross-session world state: locations, NPCs, items.
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useWorldStore = create(
  devtools(
    (set, get) => ({
      // State
      locations: [],
      npcs: [],
      items: [],
      isLoading: false,
      error: null,

      // Actions
      fetchWorldState: async (siblingPairId) => {
        set({ isLoading: true, error: null }, false, 'world/fetchStart');
        try {
          const res = await fetch(`${API_URL}/api/world/${encodeURIComponent(siblingPairId)}`);
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const data = await res.json();
          set({
            locations: data.locations || [],
            npcs: data.npcs || [],
            items: data.items || [],
            isLoading: false,
          }, false, 'world/fetchSuccess');
        } catch (e) {
          set({ isLoading: false, error: e.message }, false, 'world/fetchError');
        }
      },

      reset: () =>
        set({ locations: [], npcs: [], items: [], isLoading: false, error: null }, false, 'world/reset'),

      // Selectors
      getLocationCount: () => get().locations.length,
      getNpcCount: () => get().npcs.length,
      getItemCount: () => get().items.length,
      isEmpty: () => {
        const s = get();
        return s.locations.length === 0 && s.npcs.length === 0 && s.items.length === 0;
      },
    }),
    { name: 'WorldStore' }
  )
);
