# Implementation Plan: Gamepad Controller Support

## Overview

Add gamepad/controller support to Twin Spark Chronicles as an additive input layer. Implementation follows the existing React/Zustand architecture: a Zustand store for connection state, a polling hook, a spatial navigation module, a virtual keyboard component, a connection indicator, and CSS focus styles. Each task builds incrementally — store first, then hook, then navigation, then UI components, then integration into App.jsx.

## Tasks

- [x] 1. Create gamepad Zustand store and CSS focus styles
  - [x] 1.1 Create `frontend/src/stores/gamepadStore.js` with Zustand store
    - State: `connected`, `gamepadIndex`, `gamepadId`, `virtualKeyboardOpen`, `virtualKeyboardTarget`
    - Actions: `connect(index, id)`, `disconnect()`, `openVirtualKeyboard(targetId)`, `closeVirtualKeyboard()`
    - _Requirements: 1.1, 1.2, 7.1_

  - [x] 1.2 Add `.gamepad-focus` styles to `frontend/src/index.css`
    - Add `.gamepad-focus` class with `outline: 3px solid var(--color-gold)`, `outline-offset: 3px`, `box-shadow: 0 0 20px rgba(251, 191, 36, 0.5)`, `border-radius: 8px`, and `gamepad-pulse` keyframe animation
    - Add `@media (prefers-reduced-motion: reduce)` rule to disable the pulse animation
    - _Requirements: 4.1, 4.2, 4.4, 4.6, 12.1_

  - [ ]* 1.3 Write property tests for gamepadStore
    - **Property 1: Connect/disconnect round trip**
    - **Validates: Requirements 1.1, 1.2**

- [x] 2. Implement FocusNavigator spatial navigation module
  - [x] 2.1 Create `frontend/src/shared/hooks/FocusNavigator.js`
    - Implement module-level singleton state: `currentFocusedElement`, `previousFocusBeforeModal`, `isGamepadActive`, `focusTrapContainer`
    - Implement `FOCUSABLE_SELECTOR` constant matching design spec selectors
    - Implement `activate()` / `deactivate()` — deactivate removes all `.gamepad-focus` classes
    - Implement `move(direction)` with 120-degree cone-based nearest-neighbor spatial search using Euclidean distance
    - Implement `confirm()` — dispatches click on focused element, or opens virtual keyboard if element is `<input>` or `<textarea>`
    - Implement `cancel()` — contextual back/close action
    - Implement `menu()` — toggles parent controls overlay
    - Implement `setInitialFocus()` — focuses first logical focusable element
    - Implement `trapFocus(containerEl)` / `releaseFocusTrap()` for modal focus management
    - Implement `syncToElement(el)` — updates gamepad focus to match mouse/touch click target
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.1, 4.3, 4.5, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 10.1, 10.2, 10.3, 10.4, 11.2, 11.3_

  - [ ]* 2.2 Write property test for cone-based spatial navigation
    - **Property 5: Cone-based spatial navigation**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]* 2.3 Write property test for focus state invariant
    - **Property 6: Focus state invariant**
    - **Validates: Requirements 3.6, 4.1, 4.3, 12.4**

  - [ ]* 2.4 Write property test for no gamepad-focus when disconnected
    - **Property 7: No gamepad-focus when disconnected**
    - **Validates: Requirements 4.5**

  - [ ]* 2.5 Write property test for confirm triggers click
    - **Property 8: Confirm triggers click**
    - **Validates: Requirements 5.1, 6.6, 8.4, 9.2**

  - [ ]* 2.6 Write property test for virtual keyboard opens for input elements
    - **Property 10: Virtual keyboard opens for input elements**
    - **Validates: Requirements 7.1**

  - [ ]* 2.7 Write property test for confirm disabled during loading
    - **Property 12: Confirm disabled during loading**
    - **Validates: Requirements 8.5**

  - [ ]* 2.8 Write property test for modal focus trap
    - **Property 13: Modal focus trap**
    - **Validates: Requirements 10.1**

  - [ ]* 2.9 Write property test for modal focus restore round trip
    - **Property 14: Modal focus restore round trip**
    - **Validates: Requirements 10.4**

  - [ ]* 2.10 Write property test for click sync updates gamepad focus
    - **Property 15: Click sync updates gamepad focus**
    - **Validates: Requirements 11.3**

- [x] 3. Implement useGamepad polling hook
  - [x] 3.1 Create `frontend/src/shared/hooks/useGamepad.js`
    - Listen for `gamepadconnected` / `gamepaddisconnected` window events, update gamepadStore
    - Start/stop `requestAnimationFrame` polling loop on connect/disconnect
    - Read `navigator.getGamepads()[index]` each frame, validate gamepad object exists
    - Normalize D-pad from both `axes[0]/axes[1]` (deadzone 0.5) and buttons 12-15
    - Track `prevButtons` array for edge detection (press transitions only)
    - Implement D-pad repeat: 400ms initial delay, then 150ms repeat interval
    - Call `FocusNavigator.move(direction)` on D-pad events
    - Call `FocusNavigator.confirm()` on A button (index 0) press edge
    - Call `FocusNavigator.cancel()` on B button (index 1) press edge
    - Call `FocusNavigator.menu()` on Start button (index 9) press edge
    - Check for Gamepad API support on mount; if absent, return immediately
    - Clean up rAF and event listeners on unmount
    - _Requirements: 1.1, 1.2, 1.5, 1.6, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 11.1, 11.4_

  - [ ]* 3.2 Write property test for no polling when disconnected
    - **Property 2: No polling when disconnected**
    - **Validates: Requirements 1.5**

  - [ ]* 3.3 Write property test for D-pad normalization
    - **Property 3: D-pad normalization**
    - **Validates: Requirements 2.2, 2.3**

  - [ ]* 3.4 Write property test for button edge detection
    - **Property 4: Button edge detection**
    - **Validates: Requirements 2.5, 2.6, 2.7, 2.8**

- [x] 4. Create VirtualKeyboard component
  - [x] 4.1 Create `frontend/src/features/setup/components/VirtualKeyboard.jsx`
    - Props: `targetValue`, `onCharacter`, `onBackspace`, `onDone`, `onCancel`
    - Render A-Z grid (7 columns × 4 rows) + bottom row with backspace (←), space (␣), done (✓)
    - Display current typed value above the grid
    - Use `role="grid"` with `role="row"` and `role="gridcell"`, `aria-label="Virtual keyboard"` on overlay
    - Each key: `min-width: 48px`, `min-height: 48px`, with `aria-label` for special keys
    - Style as overlay positioned over the app content
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9, 12.3_

  - [ ]* 4.2 Write property test for virtual keyboard character round trip
    - **Property 9: Virtual keyboard character round trip**
    - **Validates: Requirements 7.4, 7.5**

  - [ ]* 4.3 Write property test for B-cancel preserves value
    - **Property 11: B-cancel preserves virtual keyboard input value**
    - **Validates: Requirements 7.7**

  - [ ]* 4.4 Write unit tests for VirtualKeyboard
    - Test layout renders all 26 letters + backspace + space + done
    - Test accessibility: `role="grid"`, `aria-label`, correct key `aria-label`s
    - _Requirements: 7.2, 7.9, 12.3_

- [x] 5. Create ConnectionIndicator component
  - [x] 5.1 Create `frontend/src/shared/components/ConnectionIndicator.jsx`
    - Read `connected` and `gamepadId` from gamepadStore
    - Render a small fixed-position gamepad SVG icon (bottom-right corner) when connected
    - Include `aria-live="polite"` region announcing "Controller connected" / "Controller disconnected"
    - _Requirements: 1.3, 1.4, 12.2_

  - [ ]* 5.2 Write unit tests for ConnectionIndicator
    - Test renders icon when `connected=true`, hides when `false`
    - Test aria-live announcements on connect/disconnect
    - _Requirements: 1.3, 1.4, 12.2_

- [x] 6. Integrate into App.jsx and wire components together
  - [x] 6.1 Mount `useGamepad()` hook in App component
    - Import and call `useGamepad()` at the top of the App function body
    - _Requirements: 1.1, 2.1_

  - [x] 6.2 Render ConnectionIndicator in App
    - Import and render `<ConnectionIndicator />` inside AppContainer
    - _Requirements: 1.3, 1.4_

  - [x] 6.3 Wire VirtualKeyboard into the app
    - Read `virtualKeyboardOpen` and `virtualKeyboardTarget` from gamepadStore
    - Conditionally render `<VirtualKeyboard />` overlay when open
    - Connect `onCharacter`, `onBackspace`, `onDone`, `onCancel` callbacks to update the target input value and close the keyboard via gamepadStore actions
    - _Requirements: 7.1, 7.4, 7.5, 7.6, 7.7_

  - [x] 6.4 Add click-sync listener for mouse/touch coexistence
    - Add a document-level `click` listener that calls `FocusNavigator.syncToElement(e.target)` when a gamepad is connected, so mouse/touch clicks update the gamepad focus position
    - _Requirements: 11.2, 11.3_

  - [ ]* 6.5 Write unit tests for App integration
    - Test useGamepad hook is mounted (gamepadconnected event triggers store update)
    - Test ConnectionIndicator renders when gamepad connected
    - Test VirtualKeyboard overlay appears when `virtualKeyboardOpen` is true
    - _Requirements: 1.1, 1.3, 7.1_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use fast-check with `numRuns: 20` as specified in the design
- The implementation is frontend-only — no backend changes needed
- All new files use JavaScript/JSX consistent with the existing codebase
