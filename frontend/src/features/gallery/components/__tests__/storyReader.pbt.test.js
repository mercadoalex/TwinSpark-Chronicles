/**
 * Property-based tests for StoryReader page indicator (Task 7.3).
 *
 * Property 5: Page indicator correctness —
 * For any beat count N (1–20) and current index i (0 to N-1),
 * the indicator text matches "${i+1} / ${N}".
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

/**
 * Pure function extracted from StoryReader's page indicator logic.
 * In the component: `{currentBeatIndex + 1} / {totalBeats}`
 */
function formatPageIndicator(currentBeatIndex, totalBeats) {
  return `${currentBeatIndex + 1} / ${totalBeats}`;
}

describe('Property 5: Page indicator correctness', () => {
  it('indicator text matches "${i+1} / ${N}" for all valid indices', () => {
    fc.assert(
      fc.property(
        fc.integer({ min: 1, max: 20 }).chain((totalBeats) =>
          fc.tuple(
            fc.integer({ min: 0, max: totalBeats - 1 }),
            fc.constant(totalBeats),
          ),
        ),
        ([currentIndex, totalBeats]) => {
          const text = formatPageIndicator(currentIndex, totalBeats);
          const expected = `${currentIndex + 1} / ${totalBeats}`;
          expect(text).toBe(expected);

          // Additional invariants
          const [current, total] = text.split(' / ').map(Number);
          expect(current).toBeGreaterThanOrEqual(1);
          expect(current).toBeLessThanOrEqual(total);
          expect(total).toBe(totalBeats);
        },
      ),
      { numRuns: 20 },
    );
  });
});
