# Requirements Document

## Introduction

This specification defines a comprehensive child-friendly UI redesign for TwinSpark Chronicles — an AI-powered interactive storytelling app for 6-year-old twins Ale and Sofi. The redesign transforms every screen and interaction into a magical, immersive experience with oversized touch targets, playful animations, celebration moments, and age-appropriate visual design. The goal is a premium "WOOOAW" factor that makes the app feel like a living storybook, not a generic kids' app.

## Glossary

- **App_Shell**: The root layout container (`App.jsx`) including the title, settings buttons, floating mic, and overall page structure.
- **Design_System**: The set of CSS custom properties, shared tokens, and reusable style primitives (colors, radii, shadows, typography, spacing) defined globally.
- **Setup_Wizard**: The multi-step character creation flow including LanguageSelector, CharacterSetup (name, spirit, tool, outfit, toy, place, review steps), and PrivacyModal.
- **Story_Stage**: The main story experience area including DualStoryDisplay, choice cards, narration, scene images, and perspective cards.
- **Session_Controls**: The collection of session-related UI elements: SessionStatus, SessionTimer, EmergencyStop, DualPrompt, and ContinueScreen.
- **Celebration_System**: A new subsystem responsible for rendering confetti, sparkles, particle bursts, and sound effects in response to achievement events.
- **Animation_Engine**: The collection of CSS keyframe animations, transitions, and motion utilities used across all components.
- **Touch_Target**: Any interactive element (button, card, link, input) that a child taps or clicks.
- **Shared_Components**: Reusable UI primitives in `shared/components/` — AlertModal, ExitModal, LoadingAnimation, LazyImage, SkipLink.
- **Parent_Surfaces**: UI areas intended for parents — ParentDashboard, ParentControls, SiblingDashboard — which receive a lighter touch in the redesign.
- **Micro_Interaction**: A small, delightful animation triggered by a user action (tap, hover, focus) that provides immediate visual feedback.

## Requirements

### Requirement 1: Global Design System Overhaul

**User Story:** As a 6-year-old child, I want the entire app to feel like a magical storybook world, so that every screen feels immersive and delightful.

#### Acceptance Criteria

1. THE Design_System SHALL define a child-friendly color palette using CSS custom properties with at least 8 vibrant, high-contrast accent colors (pink, violet, coral, gold, emerald, sky-blue, amber, magenta) each with light, base, and glow variants.
2. THE Design_System SHALL define border-radius tokens where all child-facing containers use a minimum radius of 20px and interactive cards use a minimum radius of 24px.
3. THE Design_System SHALL define a typography scale using rounded, playful display fonts (e.g., Nunito, Baloo 2, or Fredoka) with a minimum body text size of 18px and a minimum heading size of 28px for child-facing content.
4. THE Design_System SHALL define shadow tokens that include a "glow" variant with colored, soft box-shadows to make interactive elements appear to float.
5. THE Design_System SHALL define spacing tokens with a minimum interactive element gap of 16px to prevent accidental taps on adjacent targets.
6. THE Design_System SHALL define a background system with animated gradient layers and floating particle effects (stars, sparkles) that create a living storybook atmosphere.

### Requirement 2: Touch Target Sizing

**User Story:** As a 6-year-old child with developing motor skills, I want all buttons and interactive elements to be large and easy to tap, so that I never feel frustrated by missing a target.

#### Acceptance Criteria

1. THE App_Shell SHALL render all child-facing Touch_Target elements with a minimum tappable area of 56x56 pixels.
2. THE Setup_Wizard SHALL render wizard cards (spirit, tool, outfit, toy, place selections) with a minimum tappable area of 120x120 pixels.
3. THE Story_Stage SHALL render choice cards with a minimum tappable area of 160x140 pixels on desktop and 100 pixels tall on mobile.
4. THE Session_Controls SHALL render the EmergencyStop button with a minimum tappable area of 64x64 pixels.
5. THE App_Shell SHALL render the floating microphone button with a minimum tappable area of 80x80 pixels.
6. WHILE a Touch_Target is adjacent to another Touch_Target, THE Design_System SHALL enforce a minimum gap of 12px between their tappable areas.
7. THE Setup_Wizard SHALL render the name input field with a minimum height of 64px and a font size of at least 24px.

### Requirement 3: Playful Animations Across All Screens

**User Story:** As a 6-year-old child, I want everything on screen to move and feel alive, so that the app feels like a magical world rather than a static page.

#### Acceptance Criteria

1. WHEN a new screen or step loads, THE Animation_Engine SHALL play an entrance animation (fade-in combined with scale or slide) lasting between 300ms and 600ms with an ease-out or spring easing curve.
2. WHEN a child taps a Touch_Target, THE Animation_Engine SHALL play a tactile feedback animation (scale-down to 0.92 on press, bounce-back to 1.0 on release) within 250ms.
3. WHILE the Story_Stage is visible, THE Animation_Engine SHALL continuously animate background elements (floating stars, drifting sparkles, gentle parallax) at a frame rate that does not degrade scrolling performance.
4. WHEN a wizard step transitions to the next step in the Setup_Wizard, THE Animation_Engine SHALL play a directional slide animation (slide-out-left for the current step, slide-in-right for the next step) lasting 350ms.
5. WHEN a story scene image loads in the Story_Stage, THE Animation_Engine SHALL play a Ken Burns effect (slow zoom and pan) cycling over 20 seconds.
6. THE Animation_Engine SHALL apply a gentle floating animation (vertical oscillation of 4-8px over 3-4 seconds) to decorative emoji elements and avatar badges.
7. WHEN a child hovers over or focuses on a wizard card, THE Animation_Engine SHALL scale the card to 1.05-1.08 and apply a colored glow border within 250ms.

### Requirement 4: Celebration System

**User Story:** As a 6-year-old child, I want to see confetti, sparkles, and hear fun sounds when I do something great, so that I feel proud and excited to keep playing.

#### Acceptance Criteria

1. WHEN a child selects a story choice, THE Celebration_System SHALL play a "choice pop" animation consisting of a scale burst (1.0 → 1.15 → 0.95 → 1.02) and a radial sparkle particle effect around the selected card.
2. WHEN a child completes the character setup (review step), THE Celebration_System SHALL trigger a full-screen confetti burst lasting 2-3 seconds with at least 50 particles in the app's accent colors.
3. WHEN a new story beat loads with a scene image, THE Celebration_System SHALL play a "magic reveal" animation with a shimmer sweep across the image lasting 800ms.
4. WHEN the Setup_Wizard transitions from one step to the next, THE Celebration_System SHALL emit a small sparkle burst (8-12 particles) from the completed element.
5. WHEN a child taps the floating microphone button to start recording, THE Celebration_System SHALL play a pulsing ring animation with expanding colored rings radiating outward.
6. WHEN a voice recording is saved successfully, THE Celebration_System SHALL trigger a star-shower animation (15-20 falling star particles) lasting 1.5 seconds.
7. IF the Celebration_System detects that the `prefers-reduced-motion` media query is active, THEN THE Celebration_System SHALL disable all particle effects and replace burst animations with simple opacity fades.

### Requirement 5: Setup Wizard Visual Enhancement

**User Story:** As a 6-year-old child, I want the character creation screens to feel like I'm building a real hero, so that I'm excited before the story even starts.

#### Acceptance Criteria

1. THE Setup_Wizard SHALL render each spirit animal option as an illustrated card with a large emoji (minimum 48px font-size), a glowing colored border matching the spirit's theme color, and a floating animation on the emoji.
2. WHEN a child selects a spirit animal, tool, outfit, toy, or place, THE Setup_Wizard SHALL play a bounce animation on the selected card and apply a persistent glow border in the selection's theme color.
3. THE Setup_Wizard SHALL render the review step ("Meet Your Heroes") with animated character summary cards that slide in from opposite sides (child 1 from left, child 2 from right) with a staggered delay of 200ms.
4. THE Setup_Wizard SHALL render a progress indicator showing the current step as an animated trail of glowing dots or stars, where completed steps pulse gently and the current step glows brightly.
5. THE LanguageSelector SHALL render each language option as a card with a minimum size of 140x140 pixels, a flag emoji at 56px, and a hover/focus glow effect.
6. THE PrivacyModal SHALL render action buttons with a minimum height of 56px, rounded corners of at least 16px, and a gradient background matching the app's accent palette.

### Requirement 6: Story Stage Immersive Redesign

**User Story:** As a 6-year-old child, I want the story screen to feel like I'm inside the adventure, so that I'm fully immersed in the magical world.

#### Acceptance Criteria

1. THE Story_Stage SHALL render choice cards with a glowing gradient border, a large icon (minimum 48px), a radial glow background layer, and a hover lift effect (translateY -8px with colored shadow).
2. THE Story_Stage SHALL render the narration text area with a glassmorphism background, a minimum font size of 20px, generous line-height (1.8), and a tap-to-expand interaction for perspective details.
3. THE Story_Stage SHALL render child avatar badges on the scene image with a frosted-glass pill shape, a floating animation with staggered delays between the two children, and a colored border matching each child's theme color.
4. WHEN a new story beat arrives, THE Story_Stage SHALL animate the narration text in with a fade-up entrance (opacity 0 → 1, translateY 20px → 0) over 500ms.
5. THE Story_Stage SHALL render perspective cards (child 1 and child 2 views) with slide-in animations from opposite sides and a colored top-border accent matching each child's theme.
6. WHEN a story choice is selected, THE Story_Stage SHALL animate the non-selected cards fading out (opacity to 0.3, scale to 0.95) while the selected card plays the choice-pop celebration.

### Requirement 7: Session Controls Child-Friendly Redesign

**User Story:** As a 6-year-old child, I want the timer and status indicators to look friendly and not scary, so that I feel safe and happy while playing.

#### Acceptance Criteria

1. THE SessionTimer SHALL render as a playful pill-shaped badge with an icon (hourglass or clock emoji), rounded corners (999px radius), and a minimum height of 44px.
2. WHEN the SessionTimer enters the warning state (5 minutes remaining), THE SessionTimer SHALL transition its background to a warm amber glow and display a gentle pulsing animation rather than an alarming flash.
3. THE EmergencyStop SHALL render as a circular button with a minimum diameter of 64px, a soft red gradient background, and a friendly icon (door or wave emoji instead of a stop sign).
4. THE DualPrompt SHALL render each child's turn indicator as a bubble with a minimum tappable area of 90x80 pixels, a colored pulsing glow when it is that child's turn, and a celebratory checkmark animation when the child responds.
5. THE SessionStatus SHALL render connection state as a friendly animated icon (spinning sparkle for connecting, steady glow for connected) rather than technical text.
6. THE ContinueScreen SHALL render the "Continue Adventure" and "New Adventure" options as large illustrated cards (minimum 200px wide) with playful icons and hover-lift animations.

### Requirement 8: Shared Components Visual Upgrade

**User Story:** As a 6-year-old child, I want popups and loading screens to feel magical too, so that nothing in the app breaks the storybook feeling.

#### Acceptance Criteria

1. THE LoadingAnimation SHALL render as an animated character or magical object (spinning wand, bouncing star, orbiting sparkles) rather than a generic spinner, with a minimum animation element size of 64px.
2. THE AlertModal SHALL render with rounded corners (minimum 24px), a glassmorphism background, a large friendly emoji header, and action buttons with a minimum height of 56px.
3. THE ExitModal SHALL render with a warm, non-threatening visual style using soft gradients, a friendly illustration or emoji, and clearly differentiated "Save" (green gradient) and "Exit" (muted) action buttons with a minimum height of 56px.
4. WHEN a modal opens, THE Animation_Engine SHALL play a scale-up entrance animation (0.85 → 1.0) combined with a backdrop fade-in over 300ms.
5. WHEN a modal closes, THE Animation_Engine SHALL play a scale-down exit animation (1.0 → 0.9) combined with an opacity fade-out over 200ms.
6. THE LazyImage component SHALL render a shimmer placeholder animation (gradient sweep from left to right) while the image is loading, using the app's accent colors.

### Requirement 9: Micro-Interactions and Feedback

**User Story:** As a 6-year-old child, I want to see something fun happen every time I touch something, so that the app feels responsive and alive.

#### Acceptance Criteria

1. WHEN a child taps any Touch_Target, THE Animation_Engine SHALL play a ripple or sparkle effect originating from the tap point within 100ms of the touch event.
2. WHEN a child successfully submits their name in the Setup_Wizard, THE Animation_Engine SHALL play a "name sparkle" effect — a brief shimmer across the input field lasting 400ms.
3. WHEN a child navigates between wizard steps using the next-arrow button, THE Animation_Engine SHALL animate the arrow with a forward-thrust motion (translateX 8px and back) over 300ms.
4. WHEN the floating microphone button transitions from inactive to active (recording), THE Animation_Engine SHALL smoothly transition the button's gradient from violet-coral to emerald-green over 400ms with expanding pulse rings.
5. WHEN a voice recording badge appears during story playback, THE Animation_Engine SHALL slide the badge in from below with a bounce easing and pulse the indicator dot rhythmically.
6. THE App_Shell SHALL animate the "TwinSpark Chronicles" title with a continuous subtle shimmer effect (gradient text color shifting) that loops every 4-6 seconds.

### Requirement 10: Responsive and Adaptive Layout

**User Story:** As a child using a tablet or phone, I want the app to look great and be easy to use on my device, so that the magic works everywhere.

#### Acceptance Criteria

1. WHEN the viewport width is 767px or less, THE Story_Stage SHALL switch choice cards from a horizontal flex layout to a vertical stack layout with full-width cards and a minimum height of 80px per card.
2. WHEN the viewport width is 767px or less, THE Setup_Wizard SHALL maintain a minimum card size of 100x100 pixels and reduce grid gaps to 10px while keeping emoji sizes at a minimum of 36px.
3. WHEN the viewport width is 767px or less, THE DualPrompt SHALL reduce bubble padding but maintain a minimum tappable area of 72x64 pixels per child bubble.
4. THE App_Shell SHALL use CSS `clamp()` for the main title font size with a range of 2.2rem to 3.5rem scaling with viewport width.
5. WHEN the viewport width is 767px or less, THE Story_Stage SHALL stack perspective cards vertically (single column) instead of the two-column grid layout.

### Requirement 11: Parent Surface Styling Consistency

**User Story:** As a parent, I want the dashboard and controls to feel polished and consistent with the app's magical theme, so that the whole experience feels premium.

#### Acceptance Criteria

1. THE ParentDashboard SHALL use the same glassmorphism card style, border-radius tokens, and color palette as the child-facing components while maintaining a more subdued, professional tone.
2. THE ParentControls modal SHALL render with the same modal entrance/exit animations and rounded-corner styling as the child-facing AlertModal and ExitModal.
3. THE SiblingDashboard SHALL render score bars and stat cards with smooth gradient fills using the Design_System accent colors and animated transitions when values change.
4. THE ParentDashboard navigation buttons SHALL have a minimum tappable area of 48x48 pixels and use the Design_System's hover-glow interaction pattern.

### Requirement 12: Accessibility Preservation

**User Story:** As a child or parent using assistive technology, I want the redesigned UI to remain fully accessible, so that the visual enhancements do not break screen reader or keyboard navigation.

#### Acceptance Criteria

1. THE Design_System SHALL maintain a minimum color contrast ratio of 4.5:1 for all text content against its background, as measured by WCAG 2.1 AA standards.
2. THE Animation_Engine SHALL respect the `prefers-reduced-motion: reduce` media query by replacing all transform and particle animations with simple opacity transitions or disabling them entirely.
3. THE App_Shell SHALL preserve all existing `aria-label`, `aria-live`, `aria-hidden`, and `role` attributes on interactive and decorative elements after the redesign.
4. THE App_Shell SHALL preserve keyboard focus order and the existing SkipLink functionality after the redesign.
5. WHEN a celebration animation (confetti, sparkles) plays, THE Celebration_System SHALL not trap keyboard focus or block interaction with underlying content.
6. THE Design_System SHALL ensure all decorative emoji elements retain the `aria-hidden="true"` attribute.
