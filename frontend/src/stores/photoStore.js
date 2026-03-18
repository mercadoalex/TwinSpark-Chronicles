/**
 * Photo Store — manages family photo state for the setup flow.
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const API_BASE = 'http://localhost:8000';

export const usePhotoStore = create(
  devtools(
    (set, get) => ({
      photos: [],
      stats: null,
      mappings: [],
      uploadResult: null,
      loading: false,
      error: null,

      loadPhotos: async (siblingPairId) => {
        if (!siblingPairId) return;
        set({ loading: true, error: null }, false, 'photo/loadPhotos');
        try {
          const [photosResp, statsResp] = await Promise.all([
            fetch(`${API_BASE}/api/photos/${siblingPairId}`),
            fetch(`${API_BASE}/api/photos/stats/${siblingPairId}`),
          ]);
          const photos = photosResp.ok ? await photosResp.json() : [];
          const stats = statsResp.ok ? await statsResp.json() : null;
          set({ photos, stats, loading: false }, false, 'photo/loadPhotos/done');
        } catch (err) {
          set({ loading: false, error: err.message }, false, 'photo/loadPhotos/error');
        }
      },

      setUploadResult: (result) =>
        set({ uploadResult: result }, false, 'photo/setUploadResult'),

      loadMappings: async (siblingPairId) => {
        if (!siblingPairId) return;
        try {
          const resp = await fetch(`${API_BASE}/api/photos/mappings/${siblingPairId}`);
          if (resp.ok) {
            set({ mappings: await resp.json() }, false, 'photo/loadMappings');
          }
        } catch (err) {
          console.error('Failed to load mappings:', err);
        }
      },

      approvePhoto: async (photoId) => {
        // Optimistic update — mark as safe locally first
        const prevPhotos = get().photos;
        set({
          photos: prevPhotos.map((p) =>
            p.photo_id === photoId ? { ...p, status: 'safe' } : p
          ),
        }, false, 'photo/approvePhoto');
        try {
          const resp = await fetch(`${API_BASE}/api/photos/${photoId}/approve`, {
            method: 'POST',
          });
          if (!resp.ok) {
            // Revert on failure
            set({ photos: prevPhotos }, false, 'photo/approvePhoto/revert');
            return { success: false, error: 'server' };
          }
          return { success: true };
        } catch (err) {
          set({ photos: prevPhotos }, false, 'photo/approvePhoto/error');
          console.error('Failed to approve photo:', err);
          return { success: false, error: 'network' };
        }
      },

      deletePhoto: async (photoId) => {
        // Optimistic update — remove locally first
        const prevPhotos = get().photos;
        set({
          photos: prevPhotos.filter((p) => p.photo_id !== photoId),
        }, false, 'photo/deletePhoto');
        try {
          const resp = await fetch(`${API_BASE}/api/photos/${photoId}`, {
            method: 'DELETE',
          });
          if (!resp.ok) {
            // Revert on failure
            set({ photos: prevPhotos }, false, 'photo/deletePhoto/revert');
            return { success: false, error: 'server' };
          }
          return { success: true };
        } catch (err) {
          set({ photos: prevPhotos }, false, 'photo/deletePhoto/error');
          console.error('Failed to delete photo:', err);
          return { success: false, error: 'network' };
        }
      },

      reset: () =>
        set({ photos: [], stats: null, mappings: [], uploadResult: null, loading: false, error: null },
          false, 'photo/reset'),
    }),
    { name: 'PhotoStore' }
  )
);
