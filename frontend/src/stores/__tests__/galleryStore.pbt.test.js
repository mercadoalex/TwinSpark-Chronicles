/**
 * Property-based tests for galleryStore (Task 5.2).
 *
 * Property 6: Local store deletion consistency —
 * removeStorybookLocally shrinks list by exactly 1 and the removed ID is gone.
 */

import { describe, it, expect, beforeEach } from 'vitest';
import fc from 'fast-check';
import { useGalleryStore } from '../galleryStore';

/** Generate a random storybook summary object. */
const storybookSummaryArb = fc.record({
  storybook_id: fc.string({ minLength: 8, maxLength: 12 }).filter((s) => s.trim().length >= 8),
  title: fc.string({ minLength: 1, maxLength: 40 }).filter((s) => s.trim().length > 0),
  cover_image_url: fc.oneof(fc.constant(null), fc.constant('/assets/scene.png')),
  beat_count: fc.integer({ min: 1, max: 20 }),
  duration_seconds: fc.integer({ min: 0, max: 3600 }),
  completed_at: fc.constant(new Date().toISOString()),
});

/** Generate a list of 1–10 summaries with unique IDs. */
const storybookListArb = fc
  .array(storybookSummaryArb, { minLength: 1, maxLength: 10 })
  .map((list) => {
    const seen = new Set();
    return list.filter((s) => {
      if (seen.has(s.storybook_id)) return false;
      seen.add(s.storybook_id);
      return true;
    });
  })
  .filter((list) => list.length >= 1);

describe('Property 6: Local store deletion consistency', () => {
  beforeEach(() => {
    useGalleryStore.setState({
      storybooks: [],
      selectedStorybook: null,
      isLoading: false,
      error: null,
    });
  });

  it('removeStorybookLocally shrinks list by 1 and removes the target ID', () => {
    fc.assert(
      fc.property(storybookListArb, (storybooks) => {
        // Pick a random index to remove
        const idx = Math.floor(Math.random() * storybooks.length);
        const targetId = storybooks[idx].storybook_id;

        // Set initial state
        useGalleryStore.setState({ storybooks: [...storybooks] });

        // Remove
        useGalleryStore.getState().removeStorybookLocally(targetId);

        const after = useGalleryStore.getState().storybooks;

        // List shrinks by exactly 1
        expect(after.length).toBe(storybooks.length - 1);

        // Removed ID is no longer present
        expect(after.find((s) => s.storybook_id === targetId)).toBeUndefined();

        // All other IDs still present
        const remainingIds = new Set(after.map((s) => s.storybook_id));
        for (const s of storybooks) {
          if (s.storybook_id !== targetId) {
            expect(remainingIds.has(s.storybook_id)).toBe(true);
          }
        }
      }),
      { numRuns: 20 },
    );
  });
});
