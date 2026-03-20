import { useState, useEffect, useRef } from 'react';

/**
 * Preloads an image and returns its load status.
 *
 * Creates an `Image()` object that races against a configurable timeout.
 * Cleans up on unmount or when `src` changes (aborts the in-flight load
 * and clears the timeout).
 *
 * @param {string|null|undefined} src  — URL of the image to preload
 * @param {number} [timeout=3000]      — max wait in ms before giving up
 * @returns {{ loaded: boolean, error: boolean }}
 */
export function useImagePreloader(src, timeout = 3000) {
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState(false);

  // Refs keep the cleanup function stable across renders.
  const imgRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    // Nothing to preload — stay in the initial state.
    if (!src) {
      setLoaded(false);
      setError(false);
      return;
    }

    // Reset for the new src.
    setLoaded(false);
    setError(false);

    let cancelled = false;

    const img = new Image();
    imgRef.current = img;

    const cleanup = () => {
      cancelled = true;
      // Abort the in-flight load by clearing the src.
      img.onload = null;
      img.onerror = null;
      img.src = '';
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
    };

    img.onload = () => {
      if (cancelled) return;
      clearTimeout(timerRef.current);
      timerRef.current = null;
      setLoaded(true);
    };

    img.onerror = () => {
      if (cancelled) return;
      clearTimeout(timerRef.current);
      timerRef.current = null;
      setError(true);
    };

    // Start the timeout race.
    timerRef.current = setTimeout(() => {
      if (cancelled) return;
      timerRef.current = null;
      // Treat timeout as an error — the transition should proceed anyway.
      img.onload = null;
      img.onerror = null;
      img.src = '';
      setError(true);
    }, timeout);

    // Kick off the load.
    img.src = src;

    return cleanup;
  }, [src, timeout]);

  return { loaded, error };
}
