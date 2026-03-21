# Requirements Document

## Introduction

The collaborative drawing feature is the most visually disconnected feature in Twin Spark Chronicles. While the rest of the app uses the "Living Storybook" dark theme with glassmorphism, glow effects, and animations, the drawing feature uses a plain light gray toolbar (#f8f9fa), a white canvas box with no decorative theming, and lacks micro-interactions, sound effects, haptic feedback, and celebration moments. This polish pass brings the drawing experience up to the same premium, immersive quality as the rest of the app — delivering the "WOOOAW factor" for 6-year-old twins Ale and Sofi.

## Glossary

- **Drawing_Toolbar**: The sidebar component (`DrawingToolbar.jsx`) containing color palette, brush size, eraser, undo, and stamp tool controls for the drawing session.
- **Drawing_Canvas**: The main drawing overlay component (`DrawingCanvas.jsx`) that renders the HTML5 canvas, header bar, prompt, countdown, and "We're Done!" button.
- **Drawing_Countdown**: The circular SVG countdown timer component (`DrawingCountdown.jsx`) displayed in the drawing header.
- **Celebration_Overlay**: The existing shared particle animation component (`CelebrationOverlay.jsx`) used for confetti, sparkle, star-shower, and shimmer effects.
- **Audio_Feedback_Service**: The existing synthesized sound service (`audioFeedbackService`) providing `playSequence()` for generating audio cues.
- **Photo_UX_Effects_Hook**: The existing shared hook (`usePhotoUxEffects`) providing `haptic()`, `hapticPattern()`, `playShutter()`, `playChime()`, `playWhoosh()`, and `playSnap()` methods.
- **Design_System**: The "Living Storybook" CSS custom property system defined in `index.css`, including night-sky backgrounds, glassmorphism, glow shadows, accent colors, child signature colors, Fredoka/Quicksand fonts, and animation easings.
- **Reduced_Motion_Mode**: The user accessibility preference detected via `prefers-reduced-motion: reduce` media query, which disables decorative animations.

## Requirements

### Requirement 1: Dark Theme Toolbar

**User Story:** As a child user, I want the drawing toolbar to match the dark, magical theme of the rest of the app, so that the drawing experience feels immersive and consistent.

#### Acceptance Criteria

1. THE Drawing_Toolbar SHALL use a background derived from the Design_System night-sky palette (--color-bg-surface or equivalent glassmorphism) instead of the current #f8f9fa light gray.
2. THE Drawing_Toolbar SHALL apply glassmorphism styling (backdrop-filter blur, semi-transparent background, --color-glass-border) consistent with the Design_System glass-panel pattern.
3. THE Drawing_Toolbar section labels SHALL use the Design_System body font (--font-body) with a light text color (rgba(255, 255, 255, 0.7) or equivalent) instead of the current #666 dark gray.
4. THE Drawing_Toolbar selected-state indicators (color swatch, brush button, stamp button, active tool) SHALL use Design_System glow shadows (--shadow-glow-violet or --shadow-glow-gold) instead of the current #667eea solid borders.
5. THE Drawing_Toolbar border separating it from the canvas SHALL use --color-glass-border instead of the current #e0e0e0.
6. THE Drawing_Toolbar tool button backgrounds SHALL use --color-glass or --color-glass-hover instead of the current #fff and #f0f0f0.
7. THE Drawing_Toolbar tool text labels SHALL use a light color (rgba(255, 255, 255, 0.6) or equivalent) instead of the current #555.

### Requirement 2: Dark Theme Canvas Layout

**User Story:** As a child user, I want the drawing canvas area to feel like a magical portal rather than a plain white box, so that I feel excited to draw.

#### Acceptance Criteria

1. THE Drawing_Canvas layout container SHALL use a Design_System dark background (--color-bg-mid or --color-bg-surface) instead of the current #fff white background.
2. THE Drawing_Canvas layout container SHALL apply a decorative border using Design_System glow shadows (--shadow-glow-violet or --shadow-glow-gold) instead of the current plain box-shadow.
3. THE Drawing_Canvas header gradient SHALL use Design_System accent colors (--color-violet, --color-coral, or equivalent) and remain visually consistent with the dark theme.
4. THE Drawing_Canvas overlay background SHALL use a darker scrim (rgba(7, 11, 26, 0.85) or equivalent derived from --color-bg-deep) instead of the current rgba(0, 0, 0, 0.6).
5. THE Drawing_Canvas layout container border-radius SHALL remain at 16px or use --radius-lg from the Design_System for consistency.

### Requirement 3: Micro-Interactions on Tool Selection

**User Story:** As a child user, I want playful bounce and scale animations when I select colors, brushes, and stamps, so that the tools feel alive and responsive.

#### Acceptance Criteria

1. WHEN a color swatch is selected, THE Drawing_Toolbar SHALL apply a bounce-scale animation (using --ease-bounce) to the selected swatch.
2. WHEN a brush size button is selected, THE Drawing_Toolbar SHALL apply a bounce-scale animation (using --ease-bounce) to the selected button.
3. WHEN a stamp shape button is selected, THE Drawing_Toolbar SHALL apply a bounce-scale animation (using --ease-bounce) to the selected button.
4. WHEN a tool button (eraser, undo, stamps toggle) is tapped, THE Drawing_Toolbar SHALL apply a brief scale-down-then-up press animation.
5. WHEN a color swatch is hovered, THE Drawing_Toolbar SHALL display a glow effect using the swatch's own color as the glow source.
6. WHILE Reduced_Motion_Mode is active, THE Drawing_Toolbar SHALL suppress all bounce, scale, and glow animations and display static selected states only.

### Requirement 4: Sound Effects on Drawing Interactions

**User Story:** As a child user, I want to hear playful sounds when I pick tools and draw, so that the experience feels magical and multi-sensory.

#### Acceptance Criteria

1. WHEN a color swatch is selected, THE Drawing_Canvas component SHALL play a short snap sound via the Photo_UX_Effects_Hook `playSnap()` method.
2. WHEN a stamp is placed on the canvas, THE Drawing_Canvas component SHALL play a chime sound via the Photo_UX_Effects_Hook `playChime()` method.
3. WHEN the eraser tool is toggled on, THE Drawing_Canvas component SHALL play a whoosh sound via the Photo_UX_Effects_Hook `playWhoosh()` method.
4. WHEN the drawing session entrance animation begins, THE Drawing_Canvas component SHALL play a whoosh sound via the Photo_UX_Effects_Hook `playWhoosh()` method.
5. WHILE the audio feedback toggle in the audio store is disabled, THE Drawing_Canvas component SHALL suppress all sound effects.

### Requirement 5: Haptic Feedback on Drawing Interactions

**User Story:** As a child user on a touch device, I want to feel a vibration when I select tools and place stamps, so that the drawing feels tactile and real.

#### Acceptance Criteria

1. WHEN a color swatch is selected, THE Drawing_Canvas component SHALL trigger a short haptic pulse (30ms) via the Photo_UX_Effects_Hook `haptic()` method.
2. WHEN a stamp is placed on the canvas, THE Drawing_Canvas component SHALL trigger a haptic pulse (50ms) via the Photo_UX_Effects_Hook `haptic()` method.
3. WHEN the "We're Done!" button is pressed, THE Drawing_Canvas component SHALL trigger a haptic pattern via the Photo_UX_Effects_Hook `hapticPattern()` method.
4. IF the device does not support the Vibration API, THEN THE Drawing_Canvas component SHALL skip haptic calls without errors.

### Requirement 6: Celebration on Drawing Completion

**User Story:** As a child user, I want a magical celebration when the drawing session ends, so that finishing feels rewarding and exciting.

#### Acceptance Criteria

1. WHEN the drawing session ends (timer expiry or "We're Done!" button press), THE Drawing_Canvas component SHALL display the Celebration_Overlay with a confetti or star-shower particle effect.
2. WHEN the drawing session ends, THE Drawing_Canvas component SHALL play a chime sound via the Photo_UX_Effects_Hook `playChime()` method.
3. WHEN the drawing session ends, THE Drawing_Canvas component SHALL trigger a haptic pattern via the Photo_UX_Effects_Hook `hapticPattern()` method.
4. THE Celebration_Overlay displayed on drawing completion SHALL use Design_System accent colors (gold, coral, violet, pink) for particle colors.
5. WHILE Reduced_Motion_Mode is active, THE Drawing_Canvas component SHALL suppress the Celebration_Overlay particle animations (the Celebration_Overlay component already handles this internally).

### Requirement 7: Styled "We're Done!" Button

**User Story:** As a child user, I want the "We're Done!" button to look playful and magical like other buttons in the app, so that it feels inviting to press.

#### Acceptance Criteria

1. THE Drawing_Canvas "We're Done!" button SHALL use the Design_System `btn-magic` gradient styling (linear-gradient of --color-violet to --color-coral) instead of the current plain transparent/white-border style.
2. THE Drawing_Canvas "We're Done!" button SHALL use the Design_System display font (--font-display: Fredoka) for its label text.
3. THE Drawing_Canvas "We're Done!" button SHALL apply the Design_System bounce hover effect (translateY(-3px) scale(1.04) with --ease-bounce) on hover.
4. THE Drawing_Canvas "We're Done!" button SHALL apply a scale-down press effect (scale(0.92)) on active/tap.
5. THE Drawing_Canvas "We're Done!" button SHALL maintain a minimum touch target of 56px (--touch-min) in both width and height.

### Requirement 8: Enhanced Countdown Timer

**User Story:** As a child user, I want the countdown timer to feel more magical and urgent as time runs low, so that I stay engaged and aware of the remaining time.

#### Acceptance Criteria

1. THE Drawing_Countdown SHALL use the Design_System display font (--font-display: Fredoka) for the seconds text instead of the default body font.
2. THE Drawing_Countdown track circle SHALL use a semi-transparent light stroke (rgba(255, 255, 255, 0.15)) instead of the current rgba(0, 0, 0, 0.1) to match the dark theme header.
3. WHEN the remaining time drops below 10 seconds, THE Drawing_Countdown SHALL apply a CSS pulse-glow animation to the countdown ring to create visual urgency.
4. WHEN the remaining time drops below 10 seconds, THE Drawing_Countdown text SHALL increase in font-weight or scale slightly to draw attention.
5. WHILE Reduced_Motion_Mode is active, THE Drawing_Countdown SHALL suppress the pulse-glow animation and display a static color change only.

### Requirement 9: Magical Entrance Animation

**User Story:** As a child user, I want the drawing session to appear with a magical reveal animation, so that starting to draw feels like an exciting event.

#### Acceptance Criteria

1. WHEN the drawing session starts, THE Drawing_Canvas overlay SHALL use a scale-and-fade entrance animation (scaling from 0.85 to 1.0 with opacity 0 to 1) instead of the current simple slide-up.
2. WHEN the drawing session starts, THE Drawing_Canvas layout container SHALL apply a glow-pulse effect (using --shadow-glow-violet or --shadow-glow-gold) during the entrance animation to create a magical reveal.
3. THE Drawing_Canvas entrance animation duration SHALL be between 500ms and 800ms using the Design_System --ease-bounce easing.
4. WHEN the drawing session starts, THE Drawing_Canvas component SHALL play a whoosh sound via the Photo_UX_Effects_Hook during the entrance reveal.
5. WHILE Reduced_Motion_Mode is active, THE Drawing_Canvas SHALL skip the scale-and-glow entrance animation and display the overlay immediately with no animation.

### Requirement 10: Canvas Area Decorative Border

**User Story:** As a child user, I want the canvas drawing area to have a magical glowing border, so that it feels like I'm drawing inside a special portal.

#### Acceptance Criteria

1. THE Drawing_Canvas container (the element wrapping the HTML5 canvas) SHALL display a decorative border using a Design_System glow shadow (--shadow-glow-violet, --shadow-glow-gold, or a combination).
2. THE Drawing_Canvas container border SHALL use a rounded corner radius consistent with the Design_System (--radius-md or --radius-sm).
3. THE Drawing_Canvas container SHALL maintain a 1px solid border using --color-glass-border for definition against the dark layout background.
4. THE Drawing_Canvas container inner background (the actual canvas painting surface) SHALL remain white (#FFFFFF) to preserve drawing visibility and color contrast for the 8-color child palette.

### Requirement 11: Accessibility and Touch Target Compliance

**User Story:** As a parent, I want the polished drawing UI to remain fully accessible and easy to use for young children, so that the visual upgrades do not compromise usability.

#### Acceptance Criteria

1. THE Drawing_Toolbar color swatches SHALL maintain a minimum touch target size of 56px (--touch-min-child) in both width and height.
2. THE Drawing_Toolbar brush size buttons SHALL maintain a minimum touch target size of 56px (--touch-min-child) in both width and height.
3. THE Drawing_Toolbar tool buttons (eraser, undo, stamps) SHALL maintain a minimum touch target size of 56px (--touch-min-child) in both width and height.
4. THE Drawing_Toolbar stamp shape buttons SHALL maintain a minimum touch target size of 56px (--touch-min-child) in both width and height.
5. THE Drawing_Canvas "We're Done!" button SHALL maintain a minimum touch target size of 56px (--touch-min) in both dimensions.
6. THE Drawing_Toolbar selected color swatch SHALL maintain a minimum contrast ratio of 3:1 for the selected-state indicator (glow border) against the dark toolbar background.
7. THE Drawing_Countdown text SHALL maintain readable contrast against the header gradient background.
8. WHILE Reduced_Motion_Mode is active, THE Drawing_Canvas and Drawing_Toolbar SHALL suppress all decorative animations (bounce, glow-pulse, entrance scale) and display static visual states.
9. THE Drawing_Canvas ARIA live region SHALL continue to announce tool changes and session state transitions for screen reader users.
