# Requirements Document

## Introduction

Twin Spark Chronicles is an interactive storytelling app for young siblings (ages 6–12). The app already uses some `aria-label` attributes across its React components, but has never been systematically audited for screen reader compatibility, keyboard navigation, focus management, or WCAG 2.1 AA compliance. This feature covers a comprehensive accessibility audit and remediation across all frontend components, with special attention to the young user base and the app's reliance on voice, camera, touch, and drag-and-drop interactions.

## Glossary

- **App_Shell**: The root `App.jsx` component that orchestrates routing between setup, story, and session screens.
- **Setup_Wizard**: The multi-step character creation flow including `CharacterSetup`, `LanguageSelector`, and `PrivacyModal` components.
- **Story_Stage**: The active storytelling area containing `DualStoryDisplay`, `DualPrompt`, loading states, and choice buttons.
- **Photo_Flow**: The photo upload, gallery, face labeling, character mapping, and parent approval components (`PhotoUploader`, `PhotoGallery`, `CharacterMapping`, `ParentApprovalScreen`).
- **Modal_System**: Overlay dialogs including `AlertModal`, `ExitModal`, `PrivacyModal`, and confirmation dialogs.
- **Session_Controls**: Components for session management including `SessionTimer`, `EmergencyStop`, `SessionStatus`, `SiblingDashboard`, and `ParentControls`.
- **Camera_Components**: The `CameraPreview`, `MagicMirror`, and `MultimodalFeedback` components.
- **Screen_Reader**: Assistive technology that reads aloud on-screen content and interactive elements for visually impaired users.
- **Focus_Trap**: A pattern that constrains keyboard focus within a modal or overlay so users cannot tab to hidden background content.
- **Live_Region**: An ARIA live region (`aria-live`) that announces dynamic content changes to screen readers without requiring focus.
- **Skip_Link**: A hidden-until-focused link at the top of the page that allows keyboard users to jump past navigation to main content.

## Requirements

### Requirement 1: Semantic HTML and ARIA Landmark Structure

**User Story:** As a screen reader user, I want the app to use proper semantic HTML landmarks and heading hierarchy, so that I can navigate between major sections of the app efficiently.

#### Acceptance Criteria

1. THE App_Shell SHALL wrap the main storytelling area in a `<main>` landmark element with an accessible name.
2. THE App_Shell SHALL use a single `<h1>` for the app title and sequential heading levels (`h2`, `h3`) for subsections without skipping levels.
3. WHEN the Setup_Wizard is active, THE Setup_Wizard SHALL be contained within a `<section>` element with an `aria-label` describing the current wizard step.
4. WHEN the Story_Stage is active, THE Story_Stage SHALL be contained within a `<section>` element with an `aria-label` of "Story experience".
5. THE Session_Controls SHALL use a `<nav>` or `<aside>` landmark with an accessible name to distinguish parent-facing controls from child-facing content.

### Requirement 2: Modal Focus Trap and Accessible Dialog Pattern

**User Story:** As a keyboard-only user, I want modals and overlays to trap focus and be dismissible with the Escape key, so that I can interact with dialogs without losing my place.

#### Acceptance Criteria

1. WHEN the Modal_System displays an overlay (AlertModal, ExitModal, or PrivacyModal), THE Modal_System SHALL apply `role="dialog"` and `aria-modal="true"` to the dialog container.
2. WHEN a modal opens, THE Modal_System SHALL move keyboard focus to the first focusable element inside the dialog.
3. WHILE a modal is open, THE Modal_System SHALL trap Tab and Shift+Tab cycling within the dialog content.
4. WHEN the user presses the Escape key while a modal is open, THE Modal_System SHALL close the modal and return focus to the element that triggered the modal.
5. WHEN a modal opens, THE Modal_System SHALL set `aria-hidden="true"` on all background content outside the dialog.

### Requirement 3: Keyboard Navigation for Interactive Elements

**User Story:** As a user who cannot use a mouse, I want all interactive elements to be operable via keyboard, so that I can fully use the app without a pointing device.

#### Acceptance Criteria

1. THE Setup_Wizard SHALL make all wizard cards (language, gender, spirit animal) focusable and activatable with Enter or Space keys.
2. THE Story_Stage SHALL make all story choice buttons reachable and activatable via Tab and Enter keys.
3. THE Photo_Flow SHALL provide a keyboard-accessible alternative for the drag-and-drop character mapping interaction in CharacterMapping.
4. WHEN a user presses Tab, THE App_Shell SHALL move focus in a logical reading order through all interactive elements on the current screen.
5. THE App_Shell SHALL display a visible focus indicator on all focusable elements that meets a minimum 3:1 contrast ratio against adjacent colors.
6. THE Session_Controls SHALL make the EmergencyStop button, SessionTimer warning dismiss button, and ParentControls toggle reachable via keyboard.

### Requirement 4: Dynamic Content Announcements via Live Regions

**User Story:** As a screen reader user, I want dynamic content changes to be announced automatically, so that I am aware of story updates, connection status changes, and timer warnings without needing to manually search the page.

#### Acceptance Criteria

1. WHEN a new story beat arrives, THE Story_Stage SHALL announce the narration text via an `aria-live="polite"` region.
2. WHEN the connection status changes (connected, disconnected, reconnecting, error), THE SessionStatus component SHALL announce the new status via an `aria-live="assertive"` region.
3. WHEN the SessionTimer reaches the 5-minute warning threshold, THE SessionTimer SHALL announce the remaining time via an `aria-live="assertive"` region.
4. WHEN the SessionTimer reaches zero, THE SessionTimer SHALL announce that the session has ended via an `aria-live="assertive"` region.
5. WHEN a photo upload completes (success or failure), THE Photo_Flow SHALL announce the result via an `aria-live="polite"` region.
6. WHEN the MultimodalFeedback displays a speech transcript, THE MultimodalFeedback component SHALL announce the transcribed text via an `aria-live="polite"` region.

### Requirement 5: Image and Media Accessibility

**User Story:** As a screen reader user, I want all images, icons, and media elements to have meaningful alternative text or be properly hidden from assistive technology, so that I understand the visual content or am not confused by decorative elements.

#### Acceptance Criteria

1. THE Story_Stage SHALL provide descriptive `alt` text on story scene images that conveys the scene content rather than generic text like "Story scene".
2. THE Photo_Flow SHALL provide descriptive `alt` text on photo thumbnails that includes the number of detected faces and any labeled family member names.
3. WHEN an emoji or icon serves a purely decorative purpose, THE component SHALL mark the element with `aria-hidden="true"`.
4. WHEN an emoji or icon conveys meaningful information (e.g., the emergency stop icon, the mic status icon), THE component SHALL provide an accessible label via `aria-label` or visually hidden text.
5. THE Camera_Components SHALL provide `alt` text or `aria-label` on the video preview element that describes the camera feed purpose (e.g., "Live camera preview showing your face").
6. THE MagicMirror component SHALL label the gesture prompt text accessibly so screen readers announce the instruction.

### Requirement 6: Form Input Accessibility

**User Story:** As a screen reader user, I want all form inputs to have associated labels and clear error messages, so that I know what information is expected and what went wrong.

#### Acceptance Criteria

1. THE Setup_Wizard SHALL associate a visible or visually-hidden `<label>` with the name input field using `htmlFor` and matching `id` attributes.
2. WHEN a form validation error occurs (e.g., empty name field), THE Setup_Wizard SHALL associate the error message with the input using `aria-describedby`.
3. THE Photo_Flow SHALL associate a visible or visually-hidden `<label>` with the face name input field in PhotoGallery.
4. THE Photo_Flow SHALL associate error messages (wrong file type, file too large, upload failed) with the relevant interactive element using `aria-describedby`.
5. IF a required form field is empty on submission, THEN THE Setup_Wizard SHALL set `aria-invalid="true"` on the field and announce the error.

### Requirement 7: Color Contrast and Visual Accessibility

**User Story:** As a user with low vision, I want all text and interactive elements to have sufficient color contrast, so that I can read content and identify controls.

#### Acceptance Criteria

1. THE App_Shell SHALL ensure all text content meets a minimum contrast ratio of 4.5:1 against its background for normal text and 3:1 for large text (18px+ or 14px+ bold), per WCAG 2.1 AA.
2. THE Story_Stage SHALL ensure story narration text, choice button labels, and child name labels meet the 4.5:1 contrast ratio.
3. THE Session_Controls SHALL ensure the SessionTimer countdown text meets a 4.5:1 contrast ratio in both normal and warning states.
4. THE App_Shell SHALL ensure that interactive state changes (hover, focus, active, disabled) do not rely solely on color to convey meaning.
5. THE Photo_Flow SHALL ensure face bounding box overlays in PhotoGallery use a combination of color and border style (not color alone) to distinguish faces.

### Requirement 8: Touch Target Sizing

**User Story:** As a young child using a touchscreen, I want all interactive elements to be large enough to tap accurately, so that I do not accidentally trigger the wrong action.

#### Acceptance Criteria

1. THE App_Shell SHALL ensure all interactive elements (buttons, links, tappable cards) have a minimum touch target size of 44×44 CSS pixels, per WCAG 2.1 AA.
2. THE Photo_Flow SHALL ensure the camera capture, gallery pick, confirm, and retake buttons maintain a minimum touch target of 44×44 CSS pixels.
3. THE Photo_Flow SHALL ensure face bounding box tap targets in PhotoGallery detail view have a minimum touch target of 44×44 CSS pixels.
4. THE Session_Controls SHALL ensure the EmergencyStop button has a minimum touch target of 44×44 CSS pixels.
5. THE Modal_System SHALL ensure all modal action buttons (OK, Save, Exit, Cancel) have a minimum touch target of 44×44 CSS pixels.

### Requirement 9: Focus Management During Screen Transitions

**User Story:** As a keyboard or screen reader user, I want focus to be managed correctly when the app transitions between screens, so that I am not lost or disoriented after a navigation change.

#### Acceptance Criteria

1. WHEN the Setup_Wizard transitions between steps (name → gender → spirit → photos), THE Setup_Wizard SHALL move focus to the heading or first interactive element of the new step.
2. WHEN the app transitions from setup to the Story_Stage, THE App_Shell SHALL move focus to the Story_Stage heading or the first story content element.
3. WHEN a story beat loads and replaces the loading animation, THE Story_Stage SHALL move focus to the new story narration text.
4. WHEN the ContinueScreen is displayed, THE ContinueScreen SHALL move focus to the greeting heading or the "Continue Story" button.
5. IF a confirmation dialog is dismissed, THEN THE component SHALL return focus to the element that triggered the dialog.

### Requirement 10: Accessible Drag-and-Drop with Keyboard Alternative

**User Story:** As a keyboard-only user, I want an alternative to drag-and-drop for assigning faces to character roles, so that I can complete the character mapping without a mouse or touch.

#### Acceptance Criteria

1. THE CharacterMapping component SHALL provide a tap-to-assign interaction as an alternative to drag-and-drop for all face-to-role assignments.
2. THE CharacterMapping component SHALL make each face chip and each role slot focusable and activatable via Enter or Space keys.
3. WHEN a face chip is focused and activated via keyboard, THE CharacterMapping component SHALL assign the face to the first available role slot and announce the assignment via a Live_Region.
4. WHEN a role slot has an assigned face, THE CharacterMapping component SHALL allow keyboard users to activate the clear button to remove the assignment.
5. THE CharacterMapping component SHALL announce the current mapping state (e.g., "Dragon assigned to protagonist 1") via a Live_Region after each assignment change.

### Requirement 11: Reduced Motion Support

**User Story:** As a user with vestibular sensitivity, I want the app to respect my operating system's reduced motion preference, so that animations do not cause discomfort.

#### Acceptance Criteria

1. WHEN the user has enabled `prefers-reduced-motion: reduce` in their OS settings, THE App_Shell SHALL disable or minimize all non-essential CSS animations (bounces, sparkles, floating effects, confetti).
2. WHEN the user has enabled `prefers-reduced-motion: reduce`, THE App_Shell SHALL preserve essential state-change transitions (e.g., screen transitions) but reduce their duration to under 200ms.
3. WHEN the user has enabled `prefers-reduced-motion: reduce`, THE ContinueScreen SHALL disable the sparkle glow and bounce animations on the "Continue Story" button.

### Requirement 12: Skip Navigation Link

**User Story:** As a keyboard user, I want a skip navigation link at the top of the page, so that I can bypass repeated controls and jump directly to the main content area.

#### Acceptance Criteria

1. THE App_Shell SHALL render a Skip_Link as the first focusable element in the DOM that targets the main content area.
2. THE Skip_Link SHALL be visually hidden by default and become visible when focused via keyboard.
3. WHEN the Skip_Link is activated, THE App_Shell SHALL move focus to the main content landmark.

### Requirement 13: Parent Gate Accessibility

**User Story:** As a parent using assistive technology, I want the parent gate (long-press to unlock) to have a keyboard-accessible alternative, so that I can access the parent review screen without a touch gesture.

#### Acceptance Criteria

1. THE ParentApprovalScreen SHALL provide a keyboard-accessible alternative to the 3-second long-press gate (e.g., holding Enter or Space for 3 seconds).
2. WHEN the parent gate is focused, THE ParentApprovalScreen SHALL announce the instruction "Hold for 3 seconds to unlock parent review" to screen readers.
3. WHILE the parent gate hold is in progress, THE ParentApprovalScreen SHALL announce progress at 1-second intervals (e.g., "1 of 3 seconds", "2 of 3 seconds") via a Live_Region.
4. WHEN the parent gate unlocks, THE ParentApprovalScreen SHALL announce "Parent review unlocked" and move focus to the first review item or the completion message.
