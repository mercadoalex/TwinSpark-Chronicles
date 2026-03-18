import { useEffect, useRef, useCallback } from 'react';

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Traps keyboard focus within a container element.
 * On activate: stores document.activeElement, focuses first focusable child.
 * On Tab/Shift+Tab: cycles within container.
 * On Escape: calls onClose.
 * On deactivate: restores previously focused element.
 *
 * @param {React.RefObject} containerRef - Ref to the container element
 * @param {boolean} isActive - Whether the focus trap is active
 * @param {Function} onClose - Callback when Escape is pressed
 */
export function useFocusTrap(containerRef, isActive, onClose) {
  const previousFocusRef = useRef(null);

  const handleKeyDown = useCallback(
    (e) => {
      const container = containerRef.current;
      if (!container) return;

      if (e.key === 'Escape') {
        e.stopPropagation();
        onClose?.();
        return;
      }

      if (e.key !== 'Tab') return;

      const focusable = Array.from(container.querySelectorAll(FOCUSABLE_SELECTOR));
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    },
    [containerRef, onClose]
  );

  useEffect(() => {
    if (!isActive) return;

    const container = containerRef.current;
    if (!container) return;

    // Store the currently focused element to restore later
    previousFocusRef.current = document.activeElement;

    // Focus the first focusable child
    const focusable = container.querySelectorAll(FOCUSABLE_SELECTOR);
    if (focusable.length > 0) {
      focusable[0].focus();
    }

    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);

      // Restore focus on deactivate
      const prev = previousFocusRef.current;
      if (prev && typeof prev.focus === 'function') {
        try {
          prev.focus();
        } catch {
          // Element may have been removed from DOM
        }
      }
    };
  }, [isActive, containerRef, handleKeyDown]);
}
