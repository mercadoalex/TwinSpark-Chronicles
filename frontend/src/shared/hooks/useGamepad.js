/**
 * useGamepad — React hook for dual gamepad support.
 *
 * Polls up to 2 connected gamepads. Both controllers share the same
 * FocusNavigator (merged input) — either child can navigate the UI.
 * The store tracks which slot (0 or 1) each gamepad occupies so that
 * game logic can distinguish child 1 vs child 2 inputs when needed.
 */

import { useEffect, useRef } from 'react';
import { useGamepadStore } from '../../stores/gamepadStore';
import * as FocusNavigator from './FocusNavigator';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DEADZONE = 0.5;
const DPAD_INITIAL_DELAY = 400;
const DPAD_REPEAT_INTERVAL = 150;
const MAX_GAMEPADS = 2;

// Button indices (standard gamepad mapping)
const BTN_A = 0;
const BTN_B = 1;
const BTN_START = 9;
const BTN_DPAD_UP = 12;
const BTN_DPAD_DOWN = 13;
const BTN_DPAD_LEFT = 14;
const BTN_DPAD_RIGHT = 15;

// ---------------------------------------------------------------------------
// D-pad normalization helper
// ---------------------------------------------------------------------------

function normalizeDpad(gamepad) {
  const axes0 = gamepad.axes[0] || 0;
  const axes1 = gamepad.axes[1] || 0;
  const buttons = gamepad.buttons;

  return {
    up:    axes1 < -DEADZONE || (buttons[BTN_DPAD_UP]    && buttons[BTN_DPAD_UP].pressed),
    down:  axes1 >  DEADZONE || (buttons[BTN_DPAD_DOWN]  && buttons[BTN_DPAD_DOWN].pressed),
    left:  axes0 < -DEADZONE || (buttons[BTN_DPAD_LEFT]  && buttons[BTN_DPAD_LEFT].pressed),
    right: axes0 >  DEADZONE || (buttons[BTN_DPAD_RIGHT] && buttons[BTN_DPAD_RIGHT].pressed),
  };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useGamepad() {
  // Per-gamepad state: prevButtons and dpadRepeat for each slot
  const stateRef = useRef([
    { prevButtons: [], dpadRepeat: { up: null, down: null, left: null, right: null } },
    { prevButtons: [], dpadRepeat: { up: null, down: null, left: null, right: null } },
  ]);
  const rafIdRef = useRef(null);

  useEffect(() => {
    if (typeof navigator === 'undefined' || !navigator.getGamepads) return;

    // ------------------------------------------------------------------
    // Process a single gamepad's input for one frame
    // ------------------------------------------------------------------
    function processGamepad(gamepad, slotState) {
      const now = performance.now();
      const currentButtons = Array.from(gamepad.buttons, (b) => b.pressed);

      // --- D-pad with repeat ---
      const dpad = normalizeDpad(gamepad);
      const directions = ['up', 'down', 'left', 'right'];

      for (const dir of directions) {
        const isPressed = dpad[dir];
        const repeat = slotState.dpadRepeat[dir];

        if (isPressed) {
          if (!repeat) {
            FocusNavigator.move(dir);
            slotState.dpadRepeat[dir] = { startTime: now, lastRepeatTime: now };
          } else {
            const elapsed = now - repeat.startTime;
            if (elapsed >= DPAD_INITIAL_DELAY) {
              const sinceLast = now - repeat.lastRepeatTime;
              if (sinceLast >= DPAD_REPEAT_INTERVAL) {
                FocusNavigator.move(dir);
                repeat.lastRepeatTime = now;
              }
            }
          }
        } else {
          slotState.dpadRepeat[dir] = null;
        }
      }

      // --- Edge-detected buttons ---
      const prev = slotState.prevButtons;

      if (currentButtons[BTN_A] && !prev[BTN_A]) FocusNavigator.confirm();
      if (currentButtons[BTN_B] && !prev[BTN_B]) FocusNavigator.cancel();
      if (currentButtons[BTN_START] && !prev[BTN_START]) FocusNavigator.menu();

      slotState.prevButtons = currentButtons;
    }

    // ------------------------------------------------------------------
    // Polling loop — reads all connected gamepads
    // ------------------------------------------------------------------
    function poll() {
      const store = useGamepadStore.getState();
      const browserGamepads = navigator.getGamepads();
      let anyAlive = false;

      for (let slot = 0; slot < MAX_GAMEPADS; slot++) {
        const entry = store.gamepads[slot];
        if (!entry) continue;

        const gamepad = browserGamepads[entry.index];
        if (!gamepad) {
          // Gamepad disappeared — disconnect this slot
          store.disconnectGamepad(entry.index);
          stateRef.current[slot] = {
            prevButtons: [],
            dpadRepeat: { up: null, down: null, left: null, right: null },
          };
          continue;
        }

        anyAlive = true;
        processGamepad(gamepad, stateRef.current[slot]);
      }

      // If all gamepads gone, deactivate navigation
      if (!anyAlive && store.connectedCount === 0) {
        FocusNavigator.deactivate();
        stopPolling();
        return;
      }

      rafIdRef.current = requestAnimationFrame(poll);
    }

    function startPolling() {
      if (rafIdRef.current === null) {
        rafIdRef.current = requestAnimationFrame(poll);
      }
    }

    function stopPolling() {
      if (rafIdRef.current !== null) {
        cancelAnimationFrame(rafIdRef.current);
        rafIdRef.current = null;
      }
    }

    // ------------------------------------------------------------------
    // Connection handlers
    // ------------------------------------------------------------------
    function handleConnect(e) {
      const store = useGamepadStore.getState();
      const slot = store.connectGamepad(e.gamepad.index, e.gamepad.id);

      if (slot === -1) return; // both slots full, ignore

      // Reset slot state
      stateRef.current[slot] = {
        prevButtons: [],
        dpadRepeat: { up: null, down: null, left: null, right: null },
      };

      // Activate navigation if not already active
      FocusNavigator.activate();

      startPolling();
    }

    function handleDisconnect(e) {
      const store = useGamepadStore.getState();
      store.disconnectGamepad(e.gamepad.index);

      // Find and reset the slot
      for (let i = 0; i < MAX_GAMEPADS; i++) {
        stateRef.current[i] = stateRef.current[i] || {
          prevButtons: [],
          dpadRepeat: { up: null, down: null, left: null, right: null },
        };
      }

      // If no gamepads left, deactivate
      const updated = useGamepadStore.getState();
      if (updated.connectedCount === 0) {
        FocusNavigator.deactivate();
        stopPolling();
      }
    }

    // ------------------------------------------------------------------
    // Register
    // ------------------------------------------------------------------
    window.addEventListener('gamepadconnected', handleConnect);
    window.addEventListener('gamepaddisconnected', handleDisconnect);

    return () => {
      window.removeEventListener('gamepadconnected', handleConnect);
      window.removeEventListener('gamepaddisconnected', handleDisconnect);
      stopPolling();
    };
  }, []);
}
