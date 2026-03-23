/**
 * Gamepad Store — Dual gamepad support
 * Tracks up to 2 gamepads (one per child: Ale = pad 1, Sofi = pad 2)
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export const useGamepadStore = create(
  devtools(
    (set, get) => ({
      // Connection State — up to 2 gamepads
      // gamepads[0] = child 1's controller, gamepads[1] = child 2's controller
      gamepads: [null, null], // each: { index, id } or null
      connected: false,       // true if at least 1 gamepad connected
      connectedCount: 0,      // 0, 1, or 2

      // Virtual Keyboard State
      virtualKeyboardOpen: false,
      virtualKeyboardTarget: null,

      // Actions
      connectGamepad: (gamepadIndex, id) => {
        const { gamepads } = get();
        // Find first empty slot
        const slot = gamepads[0] === null ? 0 : gamepads[1] === null ? 1 : -1;
        if (slot === -1) return slot; // both slots full

        const updated = [...gamepads];
        updated[slot] = { index: gamepadIndex, id };
        const count = updated.filter(Boolean).length;
        set(
          { gamepads: updated, connected: true, connectedCount: count },
          false,
          'gamepad/connect'
        );
        return slot;
      },

      disconnectGamepad: (gamepadIndex) => {
        const { gamepads } = get();
        const updated = gamepads.map((g) =>
          g && g.index === gamepadIndex ? null : g
        );
        const count = updated.filter(Boolean).length;
        set(
          {
            gamepads: updated,
            connected: count > 0,
            connectedCount: count,
            ...(count === 0
              ? { virtualKeyboardOpen: false, virtualKeyboardTarget: null }
              : {}),
          },
          false,
          'gamepad/disconnect'
        );
      },

      disconnectAll: () =>
        set(
          {
            gamepads: [null, null],
            connected: false,
            connectedCount: 0,
            virtualKeyboardOpen: false,
            virtualKeyboardTarget: null,
          },
          false,
          'gamepad/disconnectAll'
        ),

      openVirtualKeyboard: (targetId) =>
        set(
          { virtualKeyboardOpen: true, virtualKeyboardTarget: targetId },
          false,
          'gamepad/openVirtualKeyboard'
        ),

      closeVirtualKeyboard: () =>
        set(
          { virtualKeyboardOpen: false, virtualKeyboardTarget: null },
          false,
          'gamepad/closeVirtualKeyboard'
        ),
    }),
    { name: 'GamepadStore' }
  )
);
