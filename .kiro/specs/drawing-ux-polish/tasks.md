# Implementation Plan: Drawing UX Polish

## Overview

Bottom-up implementation: CSS theming and animations first, then JSX wiring for sounds/haptics/celebration, then integration. All changes are frontend-only across `DrawingToolbar.css/.jsx`, `DrawingCanvas.css/.jsx`, and `DrawingCountdown.css/.jsx`. Build verification via `npm run build` from `frontend/`.

## Tasks

- [x] 1. Dark theme and animation CSS for DrawingToolbar
  - [x] 1.1 Apply dark theme styles to DrawingToolbar.css
    - Replace `.drawing-toolbar` background `#f8f9fa` with `var(--color-glass)` + `backdrop-filter: blur(16px)` + border `1px solid var(--color-glass-border)`
    - Update `.drawing-toolbar__label` to `color: rgba(255,255,255,0.7)` and `font-family: var(--font-body)`
    - Update `.drawing-toolbar__color-swatch--selected` to use `box-shadow: var(--shadow-glow-violet)` instead of `#333` border
    - Update `.drawing-toolbar__color-swatch:hover` to use `box-shadow: 0 0 16px var(--swatch-color, rgba(167,139,250,0.4))` for per-color glow
    - Update `.drawing-toolbar__brush-btn`, `.drawing-toolbar__tool-btn`, `.drawing-toolbar__stamp-btn` backgrounds to `var(--color-glass)` / `var(--color-glass-hover)` on hover
    - Update `.drawing-toolbar__tool-text` color to `rgba(255,255,255,0.6)`
    - Update responsive `@media (max-width: 767px)` border-top to `var(--color-glass-border)`
    - Bump all interactive elements (`color-swatch`, `brush-btn`, `tool-btn`, `stamp-btn`) to `min-width: 56px; min-height: 56px` (was 44px)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 11.1, 11.2, 11.3, 11.4_

  - [x] 1.2 Add bounce-select and press animations to DrawingToolbar.css
    - Add `@keyframes bounce-select` (scale 1 → 1.25 → 0.92 → 1.1) with `animation-timing-function: var(--ease-bounce)`
    - Apply `bounce-select` animation on `--selected` modifier classes for color swatches, brush buttons, and stamp buttons
    - Add `.drawing-toolbar__tool-btn:active { transform: scale(0.88) }` press effect
    - Update `@media (prefers-reduced-motion: reduce)` block to suppress `bounce-select` animation and all transforms
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 11.8_

- [x] 2. Dark theme and animation CSS for DrawingCanvas
  - [x] 2.1 Apply dark theme styles to DrawingCanvas.css
    - Update `.drawing-canvas-overlay` background to `rgba(7, 11, 26, 0.85)`
    - Update `.drawing-canvas-layout` background to `var(--color-bg-mid)`, box-shadow to `var(--shadow-glow-violet)`, border-radius to `var(--radius-lg)`
    - Update `.drawing-canvas-header` gradient to `linear-gradient(135deg, var(--color-violet) 0%, var(--color-coral) 100%)`
    - Add decorative border to `.drawing-canvas-container`: `border: 1px solid var(--color-glass-border)`, `border-radius: var(--radius-md)`, `box-shadow: var(--shadow-glow-violet), var(--shadow-glow-gold)`, keep inner canvas `background: #FFFFFF`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 10.1, 10.2, 10.3, 10.4_

  - [x] 2.2 Style "We're Done!" button as btn-magic in DrawingCanvas.css
    - Replace `.drawing-canvas-done-btn` styles with gradient background `linear-gradient(135deg, var(--color-violet), var(--color-coral))`, `font-family: var(--font-display)`, remove border
    - Add hover: `transform: translateY(-3px) scale(1.04)` with `--ease-bounce`
    - Add active: `transform: scale(0.92)`
    - Set `min-height: 56px; min-width: 56px`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 11.5_

  - [x] 2.3 Add magical entrance animation to DrawingCanvas.css
    - Add `@keyframes magicalEntrance` (scale 0.85→1.02→1.0, opacity 0→1, glow pulse via box-shadow)
    - Replace `.drawing-canvas--entering` animation from `slideUp` to `magicalEntrance 600ms var(--ease-bounce) forwards`
    - Update `@media (prefers-reduced-motion: reduce)` to suppress `magicalEntrance`
    - _Requirements: 9.1, 9.2, 9.3, 9.5, 11.8_

- [x] 3. Dark theme and animation CSS for DrawingCountdown
  - [x] 3.1 Apply dark theme and urgent-state styles to DrawingCountdown.css
    - Update `.drawing-countdown-track` stroke to `rgba(255, 255, 255, 0.15)`
    - Update `.drawing-countdown-text` to `font-family: var(--font-display)`
    - Add `@keyframes pulse-glow-ring` (drop-shadow oscillation on red)
    - Add `.drawing-countdown--urgent .drawing-countdown-ring` with `pulse-glow-ring 1s ease-in-out infinite`
    - Add `.drawing-countdown--urgent .drawing-countdown-text` with `font-weight: 800; transform: scale(1.15)`
    - Add `@media (prefers-reduced-motion: reduce)` to suppress `pulse-glow-ring`, keep static color change
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 11.7, 11.8_

- [x] 4. Wire JSX for sounds, haptics, and celebration
  - [x] 4.1 Wire usePhotoUxEffects into DrawingToolbar.jsx
    - Import `usePhotoUxEffects` hook
    - Call `playSnap()` + `haptic(30)` in `handleColorClick`
    - Call `playWhoosh()` in `handleEraserClick`
    - Call `playSnap()` + `haptic(30)` in `handleStampClick`
    - Pass `style={{ '--swatch-color': color }}` to each color swatch button for CSS hover glow
    - _Requirements: 4.1, 4.3, 5.1_

  - [x] 4.2 Wire usePhotoUxEffects and CelebrationOverlay into DrawingCanvas.jsx
    - Import `usePhotoUxEffects` and `CelebrationOverlay`
    - Add `const [showCelebration, setShowCelebration] = useState(false)`
    - On entrance phase (`phase === 'entering'`): call `playWhoosh()`
    - On stamp placement in `handlePointerDown`: call `playChime()` + `haptic(50)`
    - In `handleDone`: call `playChime()`, `hapticPattern([50, 30, 80])`, `setShowCelebration(true)`
    - In `DRAWING_END` WebSocket handler: call `playChime()`, `hapticPattern([50, 30, 80])`, `setShowCelebration(true)`
    - Render `{showCelebration && <CelebrationOverlay type="star-shower" duration={2500} particleCount={60} colors={['#fbbf24', '#fb7185', '#a78bfa', '#f472b6']} />}` inside the overlay
    - _Requirements: 4.2, 4.4, 4.5, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 6.5, 9.4_

  - [x] 4.3 Add urgent class toggle to DrawingCountdown.jsx
    - Add conditional className: when `remainingTime < 10 && remainingTime > 0`, add `drawing-countdown--urgent` to the root div
    - _Requirements: 8.3, 8.4_

  - [x] 4.4 Verify ARIA live region announces tool changes
    - Confirm existing `setAnnouncement()` calls in DrawingCanvas.jsx cover color select, eraser toggle, stamp select, and brush size changes
    - Add announcement updates in DrawingToolbar if not already propagated (tool changes are already announced via the `useEffect` watching `selectedTool` and `selectedStamp` in DrawingCanvas)
    - _Requirements: 11.9_

- [x] 5. Build verification
  - Run `npm run build` from `frontend/` directory to verify no compile errors
  - Verify all CSS files parse correctly and no missing custom properties
  - _Requirements: all_

- [ ]* 6. Property-based tests for drawing UX polish
  - [ ]* 6.1 Write property test: Bounce animation on selectable toolbar items
    - **Property 1: Bounce animation on selectable toolbar items**
    - Use fast-check to generate random selections from color palette / brush sizes / stamp shapes
    - Verify the `bounce-select` animation class is applied on selected items
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [ ]* 6.2 Write property test: Color selection triggers snap sound and haptic
    - **Property 2: Color selection triggers snap sound and haptic**
    - Use fast-check to generate random color from PALETTE_COLORS, simulate selection
    - Verify `playSnap()` called once and `haptic(30)` called once
    - **Validates: Requirements 4.1, 5.1**

  - [ ]* 6.3 Write property test: Stamp placement triggers chime sound and haptic
    - **Property 3: Stamp placement triggers chime sound and haptic**
    - Use fast-check to generate random stamp shape + random canvas position
    - Verify `playChime()` called once and `haptic(50)` called once
    - **Validates: Requirements 4.2, 5.2**

  - [ ]* 6.4 Write property test: Audio suppression when feedback is disabled
    - **Property 4: Audio suppression when feedback is disabled**
    - Use fast-check to generate random interaction types with `audioFeedbackEnabled=false`
    - Verify no sound methods produce output
    - **Validates: Requirements 4.5**

  - [ ]* 6.5 Write property test: Session end triggers celebration, chime, and haptic
    - **Property 5: Session end triggers celebration, chime, and haptic**
    - Use fast-check to generate random end trigger (timer vs button)
    - Verify CelebrationOverlay rendered, `playChime()` called, `hapticPattern()` called
    - **Validates: Requirements 6.1, 6.2, 6.3**

  - [ ]* 6.6 Write property test: Countdown urgent state under 10 seconds
    - **Property 6: Countdown urgent state under 10 seconds**
    - Use fast-check to generate random `remainingTime` (0–120)
    - Verify `drawing-countdown--urgent` class present iff `0 < remainingTime < 10`
    - **Validates: Requirements 8.3, 8.4**

  - [ ]* 6.7 Write property test: Canvas painting surface remains white
    - **Property 7: Canvas painting surface remains white**
    - Use fast-check to generate random tool/color/session states
    - Verify canvas fill is `#FFFFFF`
    - **Validates: Requirements 10.4**

  - [ ]* 6.8 Write property test: All interactive elements meet 56px minimum touch target
    - **Property 8: All interactive elements meet 56px minimum touch target**
    - Use fast-check to generate random toolbar configurations (stamp mode on/off)
    - Verify all interactive elements have `min-width` and `min-height` >= 56px
    - **Validates: Requirements 7.5, 11.1, 11.2, 11.3, 11.4, 11.5**

  - [ ]* 6.9 Write property test: Selected swatch glow contrast ratio
    - **Property 9: Selected swatch glow contrast ratio**
    - For each of the 8 PALETTE_COLORS, compute luminance contrast of glow against dark background
    - Verify >= 3:1 contrast ratio
    - **Validates: Requirements 11.6**

  - [ ]* 6.10 Write property test: Reduced motion suppresses all decorative animations
    - **Property 10: Reduced motion suppresses all decorative animations**
    - Use fast-check to generate random interactions with `prefers-reduced-motion` active
    - Verify no decorative `animation-name` (`bounce-select`, `magicalEntrance`, `pulse-glow-ring`) is applied
    - **Validates: Requirements 3.6, 8.5, 11.8**

  - [ ]* 6.11 Write property test: ARIA live region announces tool changes
    - **Property 11: ARIA live region announces tool changes**
    - Use fast-check to generate random tool change sequences
    - Verify ARIA live region text updates after each change
    - **Validates: Requirements 11.9**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- All CSS changes use design system tokens from `index.css` — no hardcoded magic values
- `CelebrationOverlay` already handles `prefers-reduced-motion` internally (returns `null`)
- `usePhotoUxEffects` already gates sounds on `audioStore.audioFeedbackEnabled` and guards haptics on `navigator.vibrate`
- No store changes needed — `showCelebration` is local React state
- Build: `npm run build` from `frontend/` directory
