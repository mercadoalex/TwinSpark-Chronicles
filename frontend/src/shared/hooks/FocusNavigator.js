/**
 * FocusNavigator — spatial navigation module for gamepad support.
 * This is a plain JS module (NOT a React hook). It manages a visible
 * focus cursor that moves between focusable UI elements via D-pad input.
 */

import { useGamepadStore } from '../../stores/gamepadStore';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

export const FOCUSABLE_SELECTOR = [
  'button:not([disabled])',
  '[role="button"]:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'select:not([disabled])',
  '.wizard-card',
  '.dp-bubble:not([disabled])',
  '[data-gamepad-focusable]',
].join(', ');

const CONE_HALF_ANGLE_DEG = 60; // half of the 120-degree cone
const CONE_HALF_ANGLE_RAD = (CONE_HALF_ANGLE_DEG * Math.PI) / 180;

/** Unit direction vectors keyed by direction name. */
const DIRECTION_VECTORS = {
  up: { x: 0, y: -1 },
  down: { x: 0, y: 1 },
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
};

// ---------------------------------------------------------------------------
// Module-level state (singleton)
// ---------------------------------------------------------------------------

let currentFocusedElement = null;
let previousFocusBeforeModal = null;
let isGamepadActive = false;
let focusTrapContainer = null;

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

/**
 * Returns true if the element is visible in the viewport
 * (not hidden via display:none, visibility, or detached from layout).
 */
function _isVisible(el) {
  if (!el) return false;
  // offsetParent is null for display:none elements (and for <body>/<html>)
  if (el.offsetParent === null && el.tagName !== 'BODY' && el.tagName !== 'HTML') {
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    // Fixed-position elements also have null offsetParent but are visible
    if (style.position !== 'fixed') return false;
  }
  return true;
}

/**
 * Query all visible focusable elements, optionally scoped to a container.
 */
function _getVisibleFocusables(container) {
  const root = container || document;
  const all = root.querySelectorAll(FOCUSABLE_SELECTOR);
  return Array.from(all).filter(_isVisible);
}

/**
 * Get the center point of an element's bounding rect.
 */
function _getCenter(el) {
  const rect = el.getBoundingClientRect();
  return { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
}

/**
 * Move the visible gamepad focus highlight to `el`.
 * Removes .gamepad-focus from the previous element, adds it to the new one,
 * calls el.focus(), and updates module state.
 */
function _setFocus(el) {
  if (!el) return;

  // Remove highlight from previous element
  if (currentFocusedElement && currentFocusedElement !== el) {
    currentFocusedElement.classList.remove('gamepad-focus');
  }

  // Add highlight to new element
  el.classList.add('gamepad-focus');
  el.focus();
  currentFocusedElement = el;
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Activate gamepad navigation. Called when a gamepad connects.
 */
export function activate() {
  isGamepadActive = true;
  setInitialFocus();
}

/**
 * Deactivate gamepad navigation. Called when a gamepad disconnects.
 * Removes all .gamepad-focus classes from the DOM and clears state.
 */
export function deactivate() {
  isGamepadActive = false;

  // Remove all gamepad-focus highlights
  const highlighted = document.querySelectorAll('.gamepad-focus');
  highlighted.forEach((el) => el.classList.remove('gamepad-focus'));

  currentFocusedElement = null;
  previousFocusBeforeModal = null;
  focusTrapContainer = null;
}

/**
 * Spatial navigation — move focus in the given direction using a
 * 120-degree cone search and Euclidean nearest-neighbor selection.
 *
 * @param {'up'|'down'|'left'|'right'} direction
 */
export function move(direction) {
  if (!isGamepadActive) return;

  const dir = DIRECTION_VECTORS[direction];
  if (!dir) return;

  const focusables = _getVisibleFocusables(focusTrapContainer);
  if (focusables.length === 0) return;

  // If nothing is focused yet, focus the first element
  if (!currentFocusedElement || !document.body.contains(currentFocusedElement)) {
    _setFocus(focusables[0]);
    return;
  }

  const currentCenter = _getCenter(currentFocusedElement);
  let bestCandidate = null;
  let bestDistance = Infinity;

  for (const candidate of focusables) {
    if (candidate === currentFocusedElement) continue;

    const candidateCenter = _getCenter(candidate);
    const dx = candidateCenter.x - currentCenter.x;
    const dy = candidateCenter.y - currentCenter.y;
    const distance = Math.sqrt(dx * dx + dy * dy);

    if (distance === 0) continue;

    // Compute angle between direction vector and candidate vector
    // Using dot product: cos(angle) = (dir · vec) / |vec|
    const dot = dir.x * dx + dir.y * dy;
    const cosAngle = dot / distance;
    const angle = Math.acos(Math.min(1, Math.max(-1, cosAngle)));

    // Check if candidate is within the 120-degree cone (60 degrees each side)
    if (angle <= CONE_HALF_ANGLE_RAD) {
      if (distance < bestDistance) {
        bestDistance = distance;
        bestCandidate = candidate;
      }
    }
  }

  if (bestCandidate) {
    _setFocus(bestCandidate);
  }
}

/**
 * Confirm action — if the focused element is an input/textarea, open the
 * virtual keyboard. Otherwise dispatch a click event. Skip if disabled.
 */
export function confirm() {
  if (!isGamepadActive || !currentFocusedElement) return;

  const el = currentFocusedElement;

  // Skip disabled elements
  if (el.disabled || el.getAttribute('aria-disabled') === 'true') return;

  const tag = el.tagName.toLowerCase();

  if (tag === 'input' || tag === 'textarea') {
    // Open virtual keyboard via gamepadStore (non-React access)
    const store = useGamepadStore.getState();
    store.openVirtualKeyboard(el.id || el.name || 'unknown');
  } else {
    el.click();
  }
}

/**
 * Cancel action — contextual back/close.
 * If the virtual keyboard is open, close it.
 * Otherwise find the closest ancestor with [data-gamepad-cancel] and click it.
 */
export function cancel() {
  if (!isGamepadActive) return;

  // Check if virtual keyboard is open — close it first
  const store = useGamepadStore.getState();

  if (store.virtualKeyboardOpen) {
    store.closeVirtualKeyboard();
    return;
  }

  if (!currentFocusedElement) return;

  // Find closest ancestor with [data-gamepad-cancel] and click it
  const cancelTarget = currentFocusedElement.closest('[data-gamepad-cancel]');
  if (cancelTarget) {
    cancelTarget.click();
    return;
  }

  // Fallback: look anywhere in the document
  const cancelBtn = document.querySelector('[data-gamepad-cancel]');
  if (cancelBtn) {
    cancelBtn.click();
  }
}

/**
 * Menu action — find and click the element with [data-gamepad-menu].
 */
export function menu() {
  if (!isGamepadActive) return;

  const menuBtn = document.querySelector('[data-gamepad-menu]');
  if (menuBtn) {
    menuBtn.click();
  }
}

/**
 * Set initial focus to the first visible focusable element.
 */
export function setInitialFocus() {
  const focusables = _getVisibleFocusables(focusTrapContainer);
  if (focusables.length > 0) {
    _setFocus(focusables[0]);
  }
}

/**
 * Trap gamepad focus within a container element (e.g. a modal).
 * Saves the current focus so it can be restored later.
 */
export function trapFocus(containerEl) {
  if (!containerEl) return;

  previousFocusBeforeModal = currentFocusedElement;
  focusTrapContainer = containerEl;

  // Set initial focus inside the trap
  const focusables = _getVisibleFocusables(containerEl);
  if (focusables.length > 0) {
    _setFocus(focusables[0]);
  }
}

/**
 * Release the focus trap and restore focus to the previously focused element.
 */
export function releaseFocusTrap() {
  focusTrapContainer = null;

  if (previousFocusBeforeModal && document.body.contains(previousFocusBeforeModal)) {
    _setFocus(previousFocusBeforeModal);
  } else {
    setInitialFocus();
  }

  previousFocusBeforeModal = null;
}

/**
 * Sync gamepad focus to a specific element (e.g. after a mouse/touch click).
 * Only updates if the element matches the focusable selector.
 */
export function syncToElement(el) {
  if (!isGamepadActive || !el) return;

  if (el.matches && el.matches(FOCUSABLE_SELECTOR)) {
    _setFocus(el);
  }
}
