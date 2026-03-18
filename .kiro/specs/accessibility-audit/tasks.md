# Implementation Plan: Accessibility Audit

## Overview

Systematic accessibility remediation of the Twin Spark Chronicles React frontend. Work proceeds in layers: shared accessibility utilities first, then component-by-component remediation, then integration and wiring. All changes are frontend-only (React components + CSS).

## Tasks

- [x] 1. Create shared accessibility hooks and utilities
  - [x] 1.1 Create `useFocusTrap` hook
    - Create `frontend/src/shared/hooks/useFocusTrap.js`
    - Implement focus trapping logic: store `document.activeElement` on activate, focus first focusable child, cycle Tab/Shift+Tab within container, handle Escape to call `onClose`, restore focus on deactivate
    - Export from `frontend/src/shared/hooks/index.js`
    - _Requirements: 2.2, 2.3, 2.4_

  - [x] 1.2 Create `useAnnounce` hook
    - Create `frontend/src/shared/hooks/useAnnounce.js`
    - Implement global ARIA live region: render a visually hidden `<div>` with `aria-live` at document root, return `announce(message, priority)` function, clear messages after short delay to allow re-announcement
    - Export from `frontend/src/shared/hooks/index.js`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 1.3 Create `SkipLink` component
    - Create `frontend/src/shared/components/SkipLink.jsx`
    - Render `<a href="#main-content" className="skip-link">Skip to main content</a>` as a visually hidden anchor visible on focus
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 1.4 Create `a11y.css` and update `index.css`
    - Create `frontend/src/a11y.css` with skip-link styles, `.sr-only` utility class, `.touch-target-min` utility
    - Import `a11y.css` in `frontend/src/main.jsx`
    - Update `frontend/src/index.css` to refine `prefers-reduced-motion` rule: preserve essential transitions at ≤200ms, kill purely decorative animations (`.logo-animation`, `body::before`, `body::after`, `.app-container::before`)
    - _Requirements: 8.1, 11.1, 11.2, 12.2_

  - [ ]* 1.5 Write property tests for `useFocusTrap` hook
    - **Property 4: Modal focus trap** — For any open modal with N focusable elements (N ≥ 1), Tab N times from first element cycles back to first; Shift+Tab from first moves to last
    - **Validates: Requirements 2.2, 2.3**

  - [ ]* 1.6 Write property test for modal escape restores focus
    - **Property 5: Modal escape restores focus** — For any modal opened by a trigger element, Escape closes modal and returns `document.activeElement` to the trigger
    - **Validates: Requirements 2.4, 9.5**

- [x] 2. Remediate App shell and landmark structure
  - [x] 2.1 Add semantic landmarks and SkipLink to `App.jsx`
    - Add `<SkipLink />` as first child in `frontend/src/App.jsx`
    - Wrap story stage area in `<main id="main-content" aria-label="Story experience">`
    - Wrap session controls in `<nav aria-label="Session controls">`
    - Ensure single `<h1>` and sequential heading levels (no skipped levels)
    - Manage focus on setup → story transition: focus the `<main>` element
    - Set `aria-hidden="true"` on background content when modals are open
    - _Requirements: 1.1, 1.2, 1.4, 1.5, 3.4, 9.2, 12.1_

  - [ ]* 2.2 Write property test for heading hierarchy
    - **Property 1: Heading hierarchy invariant** — For any render state, DOM contains exactly one `<h1>` and no heading level is skipped
    - **Validates: Requirements 1.2**

- [x] 3. Remediate modal components with dialog semantics and focus trap
  - [x] 3.1 Update `AlertModal` with dialog role and focus trap
    - Modify `frontend/src/shared/components/Modal/AlertModal.jsx`
    - Add `role="dialog"`, `aria-modal="true"`, `aria-labelledby` pointing to heading
    - Integrate `useFocusTrap` hook
    - Add Escape key dismissal via the hook
    - Ensure `aria-hidden="true"` on sibling content when open
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.2 Update `ExitModal` with dialog role and focus trap
    - Modify `frontend/src/shared/components/Modal/ExitModal.jsx`
    - Same pattern as AlertModal: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `useFocusTrap`, Escape dismissal, background `aria-hidden`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 3.3 Update `PrivacyModal` with dialog role and focus trap
    - Modify `frontend/src/features/setup/components/PrivacyModal.jsx`
    - Same pattern: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, `useFocusTrap`, Escape dismissal, background `aria-hidden`
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [ ]* 3.4 Write property test for modal dialog attributes
    - **Property 3: Modal dialog attributes** — For any modal component in open state, container has `role="dialog"` and `aria-modal="true"`
    - **Validates: Requirements 2.1**

  - [ ]* 3.5 Write property test for modal background aria-hidden
    - **Property 6: Modal background aria-hidden** — For any open modal, all sibling elements have `aria-hidden="true"`
    - **Validates: Requirements 2.5**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Remediate Setup Wizard accessibility
  - [x] 5.1 Update `CharacterSetup.jsx` with landmarks, focus management, and form accessibility
    - Modify `frontend/src/components/CharacterSetup.jsx`
    - Wrap each wizard step in `<section aria-label="Step: {stepName}">`
    - Move focus to heading or first interactive element on step transition (name → gender → spirit → photos)
    - Add `<label htmlFor>` on name input with matching `id`
    - Add `aria-describedby` for validation errors, `aria-invalid="true"` on empty name submission
    - Ensure wizard cards (gender, spirit) are keyboard-activatable with Enter/Space (verify existing `<button>` elements)
    - _Requirements: 1.3, 3.1, 6.1, 6.2, 6.5, 9.1_

  - [ ]* 5.2 Write property test for wizard step section labeling
    - **Property 2: Wizard step section labeling** — For any wizard step, rendered output is wrapped in `<section>` with `aria-label` describing the step
    - **Validates: Requirements 1.3**

  - [ ]* 5.3 Write property test for wizard cards keyboard activation
    - **Property 7: Wizard cards keyboard activation** — For any wizard card, the element responds to Enter and Space key presses triggering the same action as click
    - **Validates: Requirements 3.1**

  - [ ]* 5.4 Write property test for form error aria-describedby
    - **Property 15: Form error aria-describedby association** — For any input with an error message, `aria-describedby` matches the error element's `id`
    - **Validates: Requirements 6.2, 6.4**

  - [ ]* 5.5 Write property test for wizard step focus management
    - **Property 16: Wizard step focus management** — For any step transition, `document.activeElement` is within the new step's content
    - **Validates: Requirements 9.1**

- [x] 6. Remediate Story Stage and dynamic content announcements
  - [x] 6.1 Update `DualStoryDisplay.jsx` with live regions and descriptive alt text
    - Modify `frontend/src/features/story/components/DualStoryDisplay.jsx` (and `frontend/src/components/DualStoryDisplay.jsx` if both exist)
    - Add `aria-live="polite"` region for story narration text
    - Replace generic `alt="Story scene"` with descriptive alt from `scene_description` data or fallback "Illustration for the current story scene"
    - Wrap in `<section aria-label="Story experience">`
    - Move focus to narration text when a new story beat loads and replaces loading animation
    - _Requirements: 1.4, 4.1, 5.1, 9.3_

  - [x] 6.2 Update `SessionStatus.jsx` with live region
    - Modify `frontend/src/features/session/components/SessionStatus.jsx`
    - Add `aria-live="assertive"` and `role="status"` to the status text element
    - _Requirements: 4.2_

  - [x] 6.3 Update `SessionTimer.jsx` with live announcements
    - Modify `frontend/src/components/SessionTimer.jsx`
    - Use `useAnnounce` hook for programmatic announcements
    - Announce remaining time via `aria-live="assertive"` at 5-minute warning
    - Announce session ended via `aria-live="assertive"` when timer reaches zero
    - Ensure countdown text meets 4.5:1 contrast ratio in normal and warning states
    - _Requirements: 4.3, 4.4, 7.3_

  - [ ]* 6.4 Write property test for story beat narration announcement
    - **Property 9: Story beat narration announcement** — For any story beat with narration, Story_Stage contains `aria-live="polite"` region with the narration text
    - **Validates: Requirements 4.1**

  - [ ]* 6.5 Write property test for connection status live announcement
    - **Property 10: Connection status live announcement** — For any connection state, SessionStatus renders status text inside `aria-live="assertive"` element
    - **Validates: Requirements 4.2**

  - [ ]* 6.6 Write property test for story image descriptive alt text
    - **Property 13: Story image descriptive alt text** — For any story beat with scene image, `alt` is not generic "Story scene" but contains descriptive content
    - **Validates: Requirements 5.1**

  - [ ]* 6.7 Write property test for story choice buttons keyboard activation
    - **Property 18: Story choice buttons keyboard activation** — For any set of choice buttons, each is focusable via Tab and activatable via Enter
    - **Validates: Requirements 3.2**

  - [ ]* 6.8 Write property test for story beat focus management
    - **Property 17: Story beat focus management** — After a story beat loads, `document.activeElement` is the narration text or within story content area
    - **Validates: Requirements 9.3**

- [x] 7. Remediate Photo Flow components
  - [x] 7.1 Update `PhotoUploader.jsx` with upload announcements and error associations
    - Modify `frontend/src/features/setup/components/PhotoUploader.jsx`
    - Add `aria-live="polite"` announcement on upload success/failure using `useAnnounce`
    - Associate error messages (wrong file type, file too large, upload failed) with interactive elements via `aria-describedby`
    - _Requirements: 4.5, 6.4_

  - [x] 7.2 Update `PhotoGallery.jsx` with descriptive alt text and form labels
    - Modify `frontend/src/features/setup/components/PhotoGallery.jsx`
    - Update photo thumbnail `alt` text to include face count and labeled family member names
    - Add `<label htmlFor>` on face name input
    - Associate error messages via `aria-describedby`
    - Ensure face bounding boxes use border style variation (dashed vs solid) in addition to color
    - Ensure face bounding box tap targets meet 44×44px minimum
    - _Requirements: 5.2, 6.3, 6.4, 7.5, 8.3_

  - [x] 7.3 Update `CharacterMapping.jsx` with keyboard support and live announcements
    - Modify `frontend/src/features/setup/components/CharacterMapping.jsx`
    - Add `tabIndex={0}`, `role="button"`, `aria-label` to each face chip
    - Add `onKeyDown` handler for Enter/Space to trigger tap-to-assign
    - Add `tabIndex={0}`, `role="button"` to role slots for keyboard activation
    - Use `useAnnounce` to announce assignment changes (e.g., "Dragon assigned to protagonist 1")
    - Ensure clear button on assigned role slot is keyboard-accessible
    - _Requirements: 3.3, 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ]* 7.4 Write property test for character mapping keyboard assign and announce
    - **Property 8: Character mapping keyboard assign and announce** — For any face chip activated via Enter/Space, face is assigned to first available slot and live region announces the assignment
    - **Validates: Requirements 3.3, 10.1, 10.2, 10.3, 10.5**

  - [ ]* 7.5 Write property test for upload result announcement
    - **Property 11: Upload result announcement** — For any upload outcome, PhotoUploader triggers `aria-live="polite"` announcement with result message
    - **Validates: Requirements 4.5**

  - [ ]* 7.6 Write property test for photo thumbnail descriptive alt text
    - **Property 14: Photo thumbnail descriptive alt text** — For any photo with faces, thumbnail `alt` includes face count and labeled names
    - **Validates: Requirements 5.2**

- [x] 8. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Remediate Camera, Session, and remaining components
  - [x] 9.1 Update `CameraPreview.jsx` with descriptive aria-label
    - Modify `frontend/src/features/camera/components/CameraPreview.jsx`
    - Update video element `aria-label` to "Live camera preview showing your face"
    - _Requirements: 5.5_

  - [x] 9.2 Update `MultimodalFeedback.jsx` — verify transcript live region
    - Verify `frontend/src/features/camera/components/MultimodalFeedback.jsx` has `aria-live="polite"` on transcript bubble
    - Ensure transcript text is announced (confirm `role="status"` usage)
    - _Requirements: 4.6_

  - [x] 9.3 Update `MagicMirror.jsx` with accessible gesture prompt
    - Modify `frontend/src/features/session/components/MagicMirror.jsx`
    - Ensure gesture prompt text has accessible labeling for screen readers
    - _Requirements: 5.6_

  - [x] 9.4 Update `ContinueScreen.jsx` with focus management and reduced motion
    - Modify `frontend/src/features/session/components/ContinueScreen.jsx`
    - Move focus to greeting heading on mount
    - Disable sparkle glow and bounce animations when `prefers-reduced-motion: reduce` is active
    - _Requirements: 9.4, 11.3_

  - [x] 9.5 Update `EmergencyStop.jsx` and `ParentControls.jsx` keyboard accessibility
    - Ensure `frontend/src/components/EmergencyStop.jsx` button is keyboard-reachable and meets 44×44px touch target
    - Ensure `frontend/src/components/ParentControls.jsx` toggle is keyboard-reachable
    - _Requirements: 3.6, 8.4_

  - [ ]* 9.6 Write property test for transcript live region announcement
    - **Property 12: Transcript live region announcement** — For any speech transcript, MultimodalFeedback renders text inside `aria-live="polite"` element
    - **Validates: Requirements 4.6**

- [x] 10. Remediate Parent Gate accessibility
  - [x] 10.1 Update `ParentApprovalScreen.jsx` with keyboard hold and announcements
    - Modify `frontend/src/features/setup/components/ParentApprovalScreen.jsx`
    - Add `onKeyDown`/`onKeyUp` handlers for Enter/Space hold (start timer on keydown, clear on keyup)
    - Announce hold progress at 1-second intervals via `useAnnounce` ("1 of 3 seconds", "2 of 3 seconds")
    - Announce "Parent review unlocked" on gate open
    - Move focus to first review item or completion message after unlock
    - Announce instruction "Hold for 3 seconds to unlock parent review" on focus
    - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 11. Touch targets and contrast verification pass
  - [x] 11.1 Audit and fix touch target sizes across all interactive elements
    - Apply `.touch-target-min` or explicit `min-width`/`min-height: 44px` to any interactive elements below threshold
    - Verify camera capture, gallery pick, confirm, retake buttons in Photo_Flow
    - Verify modal action buttons (OK, Save, Exit, Cancel)
    - Ensure interactive state changes (hover, focus, active, disabled) don't rely solely on color
    - _Requirements: 8.1, 8.2, 8.5, 7.4_

  - [x] 11.2 Verify and fix color contrast for story text and controls
    - Ensure story narration text, choice button labels, and child name labels meet 4.5:1 contrast ratio
    - Ensure all text content meets WCAG 2.1 AA contrast minimums
    - _Requirements: 7.1, 7.2_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use `fast-check` with React Testing Library, minimum 100 iterations per property
- All changes are frontend-only — no backend modifications needed
- Checkpoints ensure incremental validation between major phases
