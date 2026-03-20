import { useState, useEffect } from 'react';

const MEDIA_QUERY = '(prefers-reduced-motion: reduce)';

/**
 * Detects whether the user prefers reduced motion via the
 * `prefers-reduced-motion: reduce` media query.
 *
 * Listens for real-time changes so the UI adapts without a page reload.
 *
 * @returns {boolean} `true` when reduced motion is preferred
 */
export function useReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(
    () => window.matchMedia(MEDIA_QUERY).matches
  );

  useEffect(() => {
    const mql = window.matchMedia(MEDIA_QUERY);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, []);

  return prefersReducedMotion;
}
