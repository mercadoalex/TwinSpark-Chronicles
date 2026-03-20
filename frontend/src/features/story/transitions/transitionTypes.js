/**
 * Transition type registry for animated story transitions.
 *
 * Each entry defines a CSS-based transition effect with viewport constraints.
 * New types can be added by appending to the array — no existing logic changes needed.
 */

export const TRANSITION_TYPES = [
  {
    name: 'page-turn',
    outClass: 'transition-page-turn-out',
    inClass: 'transition-page-turn-in',
    duration: 900,
    minViewport: 480,
  },
  {
    name: 'cinematic-fade',
    outClass: 'transition-cinematic-fade-out',
    inClass: 'transition-cinematic-fade-in',
    duration: 800,
    minViewport: 0,
  },
];

/**
 * Default fallback when no transition types match the current viewport.
 */
const DEFAULT_TRANSITION = {
  type: {
    name: 'instant-swap',
    outClass: '',
    inClass: '',
    duration: 0,
    minViewport: 0,
  },
  nextIndex: 0,
};

/**
 * Selects the next transition type by cycling through the registry,
 * skipping any type whose minViewport exceeds the current viewport width.
 *
 * @param {number} currentIndex - Index of the last-used transition type
 * @param {number} viewportWidth - Current viewport width in pixels
 * @returns {{ type: object, nextIndex: number }}
 */
export function getNextTransition(currentIndex, viewportWidth) {
  const len = TRANSITION_TYPES.length;
  if (len === 0) return DEFAULT_TRANSITION;

  for (let i = 0; i < len; i++) {
    const candidateIndex = (currentIndex + 1 + i) % len;
    const candidate = TRANSITION_TYPES[candidateIndex];
    if (candidate.minViewport <= viewportWidth) {
      return { type: candidate, nextIndex: candidateIndex };
    }
  }

  return DEFAULT_TRANSITION;
}
