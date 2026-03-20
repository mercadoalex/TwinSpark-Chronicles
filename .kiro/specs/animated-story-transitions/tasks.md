# Implementation Plan: Animated Story Transitions

## Overview

Build a CSS-first animated transition system for TwinSpark Chronicles that wraps DualStoryDisplay with a TransitionEngine component. The engine orchestrates page-turn and cinematic-fade effects between story scenes using a state machine, sparkle bursts via CelebrationOverlay, and full prefers-reduced-motion support. Implementation follows the design's component structure: registry → hooks → CSS → component → integration → mobile → tests.

## Tasks

- [x] 1. Create transition type registry
  - [x] 1.1 Create `frontend/src/features/story/transitions/transitionTypes.js`
    - Define `TRANSITION_TYPES` array with `page-turn` and `cinematic-fade` entries (name, outClass, inClass, duration, minViewport)
    - Implement `getNextTransition(currentIndex, viewportWidth)` that cycles through types, skipping any whose `minViewport > viewportWidth`
    - Export both `TRANSITION_TYPES` and `getNextTransition`
    - _Requirements: 4.1, 4.2, 4.3, 10.2_

  - [ ]* 1.2 Write property tests for transition type registry
    - **Property 2: Transition durations are within bounds**
    - **Property 5: Consecutive transitions use different types**
    - **Property 10: Small viewports exclude page-turn effect**
    - Create `frontend/src/features/story/components/__tests__/transitionTypes.test.js` using fast-check
    - **Validates: Requirements 1.2, 4.2, 10.2**

- [x] 2. Create useReducedMotion hook
  - [x] 2.1 Create `frontend/src/shared/hooks/useReducedMotion.js`
    - Implement hook that reads `window.matchMedia('(prefers-reduced-motion: reduce)')` on mount
    - Add `change` event listener for real-time detection without page reload
    - Clean up listener on unmount
    - Return boolean `prefersReducedMotion`
    - _Requirements: 6.4_

  - [ ]* 2.2 Write unit tests for useReducedMotion
    - Create `frontend/src/features/story/components/__tests__/useReducedMotion.test.js`
    - Test initial value detection, real-time change response, and cleanup
    - **Validates: Requirements 6.4**

- [x] 3. Create useImagePreloader hook
  - [x] 3.1 Create `frontend/src/shared/hooks/useImagePreloader.js`
    - Implement hook that accepts `src` and `timeout` (default 3000ms)
    - Create an `Image()` object, set `onload`/`onerror`, start timeout race
    - Return `{ loaded: boolean, error: boolean }`
    - Clean up on unmount (abort image load, clear timeout)
    - _Requirements: 1.5_

  - [ ]* 3.2 Write unit tests for useImagePreloader
    - Create `frontend/src/features/story/components/__tests__/useImagePreloader.test.js`
    - Test successful load, failed load, timeout behavior, and cleanup
    - **Property 4: Image preloader resolves within timeout**
    - **Validates: Requirements 1.5**

- [x] 4. Create TransitionEngine CSS
  - [x] 4.1 Create `frontend/src/features/story/components/TransitionEngine.css`
    - Define `.transition-container` (relative, overflow hidden, full width)
    - Define `.transition-scene`, `.transition-scene--outgoing`, `.transition-scene--incoming` with z-index layering
    - Define `@keyframes page-turn-out` with `perspective(1000px) rotateY(0deg → -90deg)`, `transform-origin: left center`, ease-in timing, 900ms
    - Define `@keyframes page-turn-in` with `perspective(1000px) rotateY(90deg → 0deg)`, `transform-origin: right center`, ease-out timing, 900ms
    - Add gradient shadow pseudo-element on turning edge for page thickness illusion
    - Define `@keyframes cinematic-fade-out` with `opacity 1→0`, `scale(1.0→1.04)`, ease-in-out, 800ms
    - Define `@keyframes cinematic-fade-in` with `opacity 0→1`, `scale(0.97→1.0)`, ease-in-out, 800ms
    - Define `.transition-scene--will-change` with `will-change: transform, opacity`
    - Define `.transition-scene--no-interaction` with `pointer-events: none`
    - Add `@media (prefers-reduced-motion: reduce)` overrides that disable all transition animations
    - Add mobile responsive rules: scale perspective proportionally below 768px viewport
    - Use CSS custom properties from the design system (`--ease-smooth`, `--ease-bounce`, `--radius-lg`, etc.)
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 3.3, 6.1, 7.1, 7.2, 7.3, 7.4, 8.2, 10.1, 10.3_

- [x] 5. Implement TransitionEngine component
  - [x] 5.1 Create `frontend/src/features/story/components/TransitionEngine.jsx`
    - Import `DualStoryDisplay`, `CelebrationOverlay`, `useReducedMotion`, `useImagePreloader`, `getNextTransition`, `TRANSITION_TYPES`
    - Implement state machine with states: `idle`, `preparing`, `animating`, `cleanup`
    - Track `transitionState`, `transitionIndex`, `showSparkle`, `currentBeat`, `incomingBeat` in state/refs
    - On new `storyBeat` prop change (while in `idle`): transition to `preparing`, render incoming scene at opacity 0, start image preload
    - On image loaded or 3s timeout: transition to `animating`, apply exit/enter CSS classes, set `will-change`, block interactions
    - At 50% of transition duration: trigger `CelebrationOverlay` sparkle burst (type "sparkle", 15-30 particles, gold/coral/violet colors)
    - On `animationend` or 2s safety timeout: transition to `cleanup`, remove CSS classes and `will-change` within 100ms, promote incoming scene to current
    - When `prefersReducedMotion` is true: skip animations, no sparkle, instant opacity swap within 200ms
    - Render two scene slots wrapping `DualStoryDisplay` — pass `onChoice` only to the active (non-transitioning) scene
    - Block `onChoice` propagation during non-idle states
    - Clean up all timeouts and listeners on unmount
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 8.3, 8.4, 9.1, 9.2, 9.3, 9.4_

  - [ ]* 5.2 Write property tests for TransitionEngine state machine
    - Create `frontend/src/features/story/components/__tests__/TransitionEngine.property.test.js` using fast-check
    - **Property 1: State machine follows valid transitions**
    - **Property 3: Interactions blocked during non-idle states**
    - **Property 6: Sparkle burst timing fits within transition**
    - **Property 7: Reduced motion suppresses all animation and sparkles**
    - **Property 8: Cleanup completes within 100ms and removes all transition artifacts**
    - **Property 9: Safety timeout force-completes stuck transitions**
    - **Validates: Requirements 1.1, 1.2, 1.3, 5.1, 5.4, 6.1, 6.2, 6.3, 7.4, 8.3, 8.4, 9.2**

- [x] 6. Integrate TransitionEngine into App.jsx
  - [x] 6.1 Update `frontend/src/App.jsx` to use TransitionEngine
    - Import `TransitionEngine` from story components
    - Replace `<DualStoryDisplay storyBeat={story.currentBeat} ...>` with `<TransitionEngine storyBeat={story.currentBeat} t={t} profiles={session.profiles} onChoice={handleChoice} />`
    - Ensure existing focus management (narrationRef) still works through TransitionEngine
    - Verify shimmer sweep on new scene image is preserved (handled inside DualStoryDisplay)
    - Export TransitionEngine from `frontend/src/features/story/index.js` if barrel file exists
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [x] 7. Add mobile responsive adaptations
  - [x] 7.1 Add viewport-aware transition selection in TransitionEngine
    - Read `window.innerWidth` (or use a resize listener) to pass viewport width to `getNextTransition`
    - Below 480px: `getNextTransition` automatically skips page-turn (handled by registry's `minViewport`)
    - Below 768px: scale perspective values proportionally in CSS (already in task 4.1)
    - Use relative units (%, vw, vh) for transition positioning in CSS
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 8. Final checkpoint
  - Run `npm run build` from `frontend/` to verify no build errors
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use fast-check and validate universal correctness properties from the design document
- The TransitionEngine wraps DualStoryDisplay without modifying its internals
- All animations are CSS-only (transform + opacity) for 60fps performance
- CelebrationOverlay is reused for sparkle bursts — no new particle system needed
