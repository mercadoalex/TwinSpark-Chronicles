import { useCallback, useRef } from 'react';

const LIVE_REGION_ID = 'aria-live-announcer';
const CLEAR_DELAY = 150;

function getOrCreateLiveRegion() {
  let el = document.getElementById(LIVE_REGION_ID);
  if (el) return el;

  try {
    el = document.createElement('div');
    el.id = LIVE_REGION_ID;
    el.setAttribute('aria-live', 'polite');
    el.setAttribute('aria-atomic', 'true');
    el.setAttribute('role', 'status');
    Object.assign(el.style, {
      position: 'absolute',
      width: '1px',
      height: '1px',
      padding: '0',
      margin: '-1px',
      overflow: 'hidden',
      clip: 'rect(0, 0, 0, 0)',
      whiteSpace: 'nowrap',
      border: '0',
    });
    document.body.appendChild(el);
    return el;
  } catch {
    return null;
  }
}

/**
 * Returns an `announce(message, priority)` function that injects text
 * into a global ARIA live region for screen reader announcements.
 *
 * @returns {{ announce: (message: string, priority?: 'polite' | 'assertive') => void }}
 */
export function useAnnounce() {
  const timerRef = useRef(null);

  const announce = useCallback((message, priority = 'polite') => {
    const region = getOrCreateLiveRegion();
    if (!region) return;

    // Update priority if needed
    region.setAttribute('aria-live', priority);

    // Clear first so identical messages re-trigger announcement
    region.textContent = '';

    clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      region.textContent = message;
    }, CLEAR_DELAY);
  }, []);

  return { announce };
}
