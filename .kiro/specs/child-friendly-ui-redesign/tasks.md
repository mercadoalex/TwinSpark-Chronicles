# Implementation Plan: Child-Friendly UI Redesign

## Overview

CSS-first visual overhaul of TwinSpark Chronicles. Starts with design system token expansion in `index.css`, then builds the CelebrationOverlay shared component, then applies component-by-component CSS updates, and finishes with property-based tests using fast-check + Vitest. Each task builds on the previous — no orphaned code.

## Tasks

- [x] 1. Expand design system tokens and shared keyframes in index.css
  - [x] 1.1 Add extended accent color palette tokens to `:root`
    - Add `--color-pink`, `--color-pink-light`, `--color-pink-glow`, `--color-magenta`, `--color-magenta-light`, `--color-magenta-glow`, `--color-violet-light`, `--color-violet-glow`, `--color-coral-light`, `--color-coral-glow`, `--color-gold-glow`, `--color-emerald-light`, `--color-emerald-glow`, `--color-sky-light`, `--color-sky-glow`, `--color-amber-light`, `--color-amber-glow`
    - _Requirements: 1.1, 1.4_

  - [x] 1.2 Add spacing, touch target, typography, and glow shadow tokens to `:root`
    - Add `--space-xs` through `--space-2xl`, `--touch-min-child` (56px), `--touch-min-card` (120px), `--touch-min-choice` (160px), `--touch-gap` (12px), `--text-body` (18px), `--text-heading` (28px), `--text-hero` (clamp), `--text-card` (1.1rem), `--shadow-glow-gold`, `--shadow-glow-violet`, `--shadow-glow-pink`, `--shadow-glow-emerald`, `--shadow-glow-coral`
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 2.1, 2.6_

  - [x] 1.3 Add celebration and micro-interaction keyframes to index.css
    - Add `@keyframes confetti-fall`, `sparkle-burst`, `star-fall`, `shimmer-sweep`, `tap-ripple`, `name-sparkle`, `arrow-thrust`, `title-shimmer`, `check-pop`, `pulse-ring-gentle`
    - Wrap all new animations in `@media (prefers-reduced-motion: reduce)` block to disable or replace with opacity fades
    - _Requirements: 3.1, 3.2, 4.7, 12.2_

- [x] 2. Create CelebrationOverlay component
  - [x] 2.1 Create CelebrationOverlay.css with particle animation styles
    - Define `.celebration-overlay` container with `pointer-events: none`, `position: fixed`, `inset: 0`, `z-index: 1000`
    - Define `.celebration-particle` base class and type-specific variants (confetti, sparkle, star, shimmer)
    - Each particle uses CSS custom properties (`--x`, `--y`, `--delay`, `--rotation`, `--color`, `--scale`) to drive the shared keyframes
    - Add `prefers-reduced-motion` override that hides all particles
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 12.2, 12.5_

  - [x] 2.2 Create CelebrationOverlay.jsx React component
    - Accept props: `type` ("confetti" | "sparkle" | "star-shower" | "shimmer"), `duration` (ms), `particleCount`, `origin` (optional {x,y}), `colors` (optional array)
    - On mount, generate particle array with randomized CSS custom properties via `Array.from`
    - Render particles as `<span>` elements with inline `style` setting `--x`, `--y`, `--delay`, `--rotation`, `--color`, `--scale`
    - Auto-cleanup via `useEffect` returning a cleanup function; use `setTimeout` to set a `visible` state to false after `duration` ms
    - Check `window.matchMedia('(prefers-reduced-motion: reduce)')` — if active, render nothing
    - Clamp `particleCount` to max 100
    - Ensure overlay has no focusable elements (no buttons, links, inputs) and container has `aria-hidden="true"`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.6, 4.7, 12.5, 12.6_

- [x] 3. Update App Shell (App.jsx / App.css)
  - [x] 3.1 Add title shimmer animation and floating mic size increase
    - In `App.css`, add `title-shimmer` animation to `.app-title` (continuous gradient-shift, 4–6s loop)
    - Increase `.floating-mic` to 80×80px, add pulse rings on `.floating-mic--active`
    - Enhance `.app-container::before` particle layer with more varied radial gradients
    - _Requirements: 2.5, 9.6, 1.6, 3.3_

  - [x] 3.2 Wire CelebrationOverlay into App.jsx for setup-complete confetti
    - Import `CelebrationOverlay` in `App.jsx`
    - Add state `showSetupCelebration` — set to true in `handleSetupComplete`, auto-clear after 2500ms
    - Render `<CelebrationOverlay type="confetti" duration={2500} particleCount={60} />` when active
    - _Requirements: 4.2_

- [x] 4. Update Setup Wizard (CharacterSetup.jsx / CharacterSetup.css)
  - [x] 4.1 Add wizard progress indicator and enhance spirit card styling
    - Add a `.wizard-progress` element (row of dots/stars) rendered above the wizard content in `CharacterSetup.jsx`
    - Style completed steps with a gentle pulse, current step with a bright glow
    - Increase `.wizard-card__emoji--big` to minimum 48px, add floating animation
    - Add glow border on hover/focus using `--spirit-color` token
    - _Requirements: 5.1, 5.2, 5.4, 3.7_

  - [x] 4.2 Enhance name input, review step animations, and selection bounce
    - Increase `.wizard-name-input` to 64px height, 24px font-size
    - Add review step slide-in from opposite sides with 200ms stagger for child 1 (left) and child 2 (right)
    - Add sparkle burst (CelebrationOverlay type="sparkle") on spirit/gender selection
    - Ensure all wizard cards have `aria-hidden="true"` on decorative emoji spans
    - _Requirements: 2.7, 5.2, 5.3, 4.4, 12.6_

- [x] 5. Update Story Stage (DualStoryDisplay.jsx / DualStoryDisplay.css)
  - [x] 5.1 Enhance choice cards with glow, sizing, and non-selected fade
    - Add radial glow layer to `.story-choice-card`, increase min-size to 160×140px desktop
    - Add non-selected card fade: when a card is selected, siblings get `opacity: 0.3` and `scale(0.95)` via a new `.story-choice-card--dimmed` class
    - Apply the class in `DualStoryDisplay.jsx` to non-selected cards when `selectedIdx !== null`
    - _Requirements: 6.1, 6.6, 2.3_

  - [x] 5.2 Enhance narration text, scene image shimmer, and perspective cards
    - Increase `.story-narration__text` font-size to 20px, line-height to 1.8
    - Add shimmer sweep on scene image load via CelebrationOverlay type="shimmer" triggered in `DualStoryDisplay.jsx`
    - Ensure perspective cards have colored top-border accent and slide-in animations
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 4.3_

- [x] 6. Update Session Controls CSS
  - [x] 6.1 Restyle SessionTimer, EmergencyStop, and DualPrompt
    - In `SessionTimer.css`: pill badge with emoji icon, `border-radius: 999px`, min-height 44px, amber glow on warning state with gentle pulse (not alarming flash)
    - In `EmergencyStop.css`: 64px diameter circle, soft red gradient, friendly emoji icon (door/wave)
    - In `DualPrompt.css`: bubbles min 90×80px desktop, 72×64px mobile, colored pulsing glow on active turn, celebratory checkmark animation on response
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 6.2 Restyle SessionStatus and ContinueScreen
    - SessionStatus: animated icon (spinning sparkle connecting, steady glow connected) instead of text
    - ContinueScreen: large illustrated cards (200px+ wide), hover-lift animation
    - _Requirements: 7.5, 7.6_

- [x] 7. Update Shared Components CSS
  - [x] 7.1 Restyle LoadingAnimation and LazyImage
    - LoadingAnimation: replace spinner with animated magical object (bouncing star + orbiting sparkles), min 64px element size
    - LazyImage: update shimmer placeholder to use accent colors from design system
    - _Requirements: 8.1, 8.6_

  - [x] 7.2 Restyle AlertModal, ExitModal, and modal animations
    - AlertModal: 24px radius, glassmorphism, large emoji header, 56px buttons
    - ExitModal: warm gradients, friendly emoji, differentiated Save (green) / Exit (muted) buttons, 56px height
    - Modal entrance: `scale(0.85) → scale(1.0)` + backdrop fade over 300ms
    - Modal exit: `scale(1.0) → scale(0.9)` + opacity fade over 200ms
    - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [x] 8. Update Parent Surfaces CSS
  - [x] 8.1 Restyle ParentDashboard, ParentControls, and SiblingDashboard
    - ParentDashboard: glassmorphism card style, design system radii and colors, 48px min nav buttons
    - ParentControls: same modal animations as child-facing modals
    - SiblingDashboard: gradient fills on score bars using accent colors, animated value transitions
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] 9. Responsive layout adjustments
  - [x] 9.1 Add/update mobile breakpoint rules across all updated CSS files
    - Story choice cards: vertical stack at ≤767px, full-width, min-height 80px
    - Perspective cards: single-column grid at ≤767px
    - Wizard cards: min 100×100px, emoji ≥36px, gap 10px at ≤767px
    - DualPrompt bubbles: min 72×64px at ≤767px
    - Title: `clamp(2.2rem, 6vw, 3.5rem)` already in place — verify
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 10. Micro-interactions and tap feedback
  - [x] 10.1 Add tap ripple utility and micro-interaction CSS classes
    - Add `.tap-ripple` CSS class using `::after` pseudo-element with `tap-ripple` keyframe
    - Add `.name-sparkle` class for input shimmer effect
    - Add `.arrow-thrust` class for next-button forward motion
    - Ensure all child-facing `:active` states apply `transform: scale(0.92)` with ≤250ms transition
    - _Requirements: 9.1, 9.2, 9.3, 3.2_

- [x] 11. Property-based tests
  - [ ]* 11.1 Write property test: touch target minimum dimensions
    - **Property 1: Touch target minimum dimensions by category**
    - Generate random element categories, render components, query computed min-width/min-height
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.7**

  - [ ]* 11.2 Write property test: adjacent touch target gap
    - **Property 2: Adjacent touch target gap enforcement**
    - Generate random card grid configurations, verify computed gap ≥ 12px
    - **Validates: Requirements 2.6**

  - [ ]* 11.3 Write property test: typography minimum sizes
    - **Property 3: Typography minimum sizes by element role**
    - Generate random text element roles, verify computed font-size meets minimums
    - **Validates: Requirements 1.3, 5.1, 6.1, 6.2**

  - [ ]* 11.4 Write property test: animation durations in range
    - **Property 4: Animation durations fall within specified ranges**
    - Parse CSS animation classes, verify duration values fall within specified ranges
    - **Validates: Requirements 3.1, 3.4, 3.5, 3.6, 3.7, 8.4, 8.5, 9.6**

  - [ ]* 11.5 Write property test: tactile press feedback
    - **Property 5: Tactile press feedback on all child-facing touch targets**
    - Verify `:active` state applies `scale(0.92)` ±0.02 with ≤250ms transition
    - **Validates: Requirements 3.2**

  - [ ]* 11.6 Write property test: CelebrationOverlay particle count
    - **Property 6: CelebrationOverlay renders correct particle count**
    - Generate random `particleCount` (1–100), render component, assert exactly N `<span>` particles; assert 0 when reduced-motion is simulated
    - **Validates: Requirements 4.2, 4.7, 12.2**

  - [ ]* 11.7 Write property test: non-selected choice card fade
    - **Property 7: Non-selected choice cards fade out on selection**
    - Generate random choice arrays and selected index, verify non-selected cards have dimmed class
    - **Validates: Requirements 6.6**

  - [ ]* 11.8 Write property test: responsive layout at mobile breakpoint
    - **Property 8: Responsive layout adaptation at mobile breakpoint**
    - Verify layout changes at ≤767px: vertical stack, single-column grid, reduced bubble sizes
    - **Validates: Requirements 10.1, 10.2, 10.3, 10.5**

  - [ ]* 11.9 Write property test: celebration overlay non-blocking
    - **Property 9: Celebration overlay does not trap focus or block interaction**
    - Render CelebrationOverlay, verify `pointer-events: none` and zero focusable elements
    - **Validates: Requirements 12.5**

  - [ ]* 11.10 Write property test: decorative emoji aria-hidden
    - **Property 10: Decorative emoji elements have aria-hidden**
    - Render components, query emoji elements, verify `aria-hidden="true"`
    - **Validates: Requirements 12.6**

  - [ ]* 11.11 Write property test: wizard progress indicator reflects step
    - **Property 11: Wizard progress indicator reflects current step**
    - Generate random step index k out of T, verify T dots rendered, k completed, 1 current
    - **Validates: Requirements 5.4**

  - [ ]* 11.12 Write property test: wizard card interaction states
    - **Property 12: Wizard card interaction states (hover glow and selection bounce)**
    - Verify hover applies scale 1.05–1.08 with glow border, selection applies bounce class
    - **Validates: Requirements 3.7, 5.2**

  - [ ]* 11.13 Write property test: reduced motion disables animations
    - **Property 13: Reduced motion disables all transform and particle animations**
    - Simulate `prefers-reduced-motion: reduce`, verify animation-duration ≤ 1ms or replaced with opacity
    - **Validates: Requirements 4.7, 12.2**

  - [ ]* 11.14 Write property test: color contrast ratio
    - **Property 14: Color contrast ratio for text content**
    - Verify computed foreground/background contrast ratio ≥ 4.5:1 for text elements
    - **Validates: Requirements 12.1**

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use fast-check with Vitest (`fc.assert` with `{ numRuns: 100 }`)
- Test files go in `frontend/src/__tests__/child-friendly-ui-redesign/`
- Run frontend build after each task: `npm run build` (cwd: `frontend/`)