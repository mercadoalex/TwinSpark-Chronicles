/**
 * Gallery Store — manages storybook gallery state for browsing and reading completed adventures.
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

const API_BASE = 'http://localhost:8000';

export const useGalleryStore = create(
  devtools(
    (set, get) => ({
      storybooks: [],
      selectedStorybook: null,
      isLoading: false,
      error: null,

      fetchStorybooks: async (siblingPairId) => {
        if (!siblingPairId) return;
        set({ isLoading: true, error: null }, false, 'gallery/fetchStorybooks');
        try {
          const resp = await fetch(`${API_BASE}/api/gallery/${siblingPairId}`);
          const storybooks = resp.ok ? await resp.json() : [];
          set({ storybooks, isLoading: false }, false, 'gallery/fetchStorybooks/done');
        } catch (err) {
          set({ isLoading: false, error: err.message }, false, 'gallery/fetchStorybooks/error');
        }
      },

      fetchStorybookDetail: async (storybookId) => {
        if (!storybookId) return;
        set({ isLoading: true, error: null }, false, 'gallery/fetchStorybookDetail');
        try {
          const resp = await fetch(`${API_BASE}/api/gallery/detail/${storybookId}`);
          if (!resp.ok) {
            set({ isLoading: false, error: 'Storybook not found' }, false, 'gallery/fetchStorybookDetail/error');
            return;
          }
          const selectedStorybook = await resp.json();
          set({ selectedStorybook, isLoading: false }, false, 'gallery/fetchStorybookDetail/done');
        } catch (err) {
          set({ isLoading: false, error: err.message }, false, 'gallery/fetchStorybookDetail/error');
        }
      },

      deleteStorybook: async (storybookId, pin) => {
        const prevStorybooks = get().storybooks;
        set({
          storybooks: prevStorybooks.filter((s) => s.storybook_id !== storybookId),
        }, false, 'gallery/deleteStorybook');
        try {
          const resp = await fetch(`${API_BASE}/api/gallery/${storybookId}`, {
            method: 'DELETE',
            headers: { 'X-Parent-Pin': pin },
          });
          if (!resp.ok) {
            set({ storybooks: prevStorybooks }, false, 'gallery/deleteStorybook/revert');
            const body = await resp.json().catch(() => ({}));
            return { success: false, error: body.detail || 'Delete failed' };
          }
          const result = await resp.json();
          return { success: true, data: result };
        } catch (err) {
          set({ storybooks: prevStorybooks }, false, 'gallery/deleteStorybook/error');
          return { success: false, error: err.message };
        }
      },

      removeStorybookLocally: (storybookId) =>
        set(
          (state) => ({
            storybooks: state.storybooks.filter((s) => s.storybook_id !== storybookId),
          }),
          false,
          'gallery/removeStorybookLocally',
        ),

      clearSelectedStorybook: () =>
        set({ selectedStorybook: null }, false, 'gallery/clearSelectedStorybook'),

      reset: () =>
        set({
          storybooks: [],
          selectedStorybook: null,
          isLoading: false,
          error: null,
        }, false, 'gallery/reset'),
    }),
    { name: 'GalleryStore' },
  ),
);
