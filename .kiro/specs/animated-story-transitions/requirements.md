# Requirements Document

## Introduction

Animated Story Transitions adds cinematic, immersive scene-change animations to TwinSpark Chronicles. When Ale & Sofi (age 6) make a story choice and a new scene loads, the transition between the outgoing and incoming scene should feel like turning a page in a magical storybook or watching a cinematic movie cut — not a generic fade. The feature is CSS-first (no heavy animation libraries), integrates with the existing Living Storybook design system, and respects `prefers-reduced-motion`.

## Glossary

- **Transition_Engine**: The React component and CSS module responsible for orchestrating animated transitions between story scenes inside DualStoryDisplay.
- **Scene**: A single story beat rendered by DualStoryDisplay, consisting of a scene image, narration text, child perspective cards, and choice cards.
- **Outgoing_Scene**: The Scene currently visible that is about to be replaced.
- **Incoming_Scene**: The new Scene that will appear after a story choice is made.
- **Page_Turn_Effect**: A 3D CSS perspective-based animation that simulates a physical page being turned in a storybook, revealing the Incoming_Scene beneath.
- **Cinematic_Fade**: A cross-fade transition where the Outgoing_Scene dissolves while the Incoming_Scene materializes, optionally combined with a subtle zoom or parallax shift.
- **Sparkle_Burst**: A particle overlay (using the existing CelebrationOverlay component) that fires during the midpoint of a transition to add a magical punctuation.
- **Transition_Type**: One of the available transition styles: Page_Turn_Effect, Cinematic_Fade, or any future additions.
- **Reduced_Motion_Mode**: The operating state when the user's system has `prefers-reduced-motion: reduce` enabled, requiring all decorative animations to be suppressed.
- **DualStoryDisplay**: The main React component (`DualStoryDisplay.jsx`) that renders story scenes, narration, perspectives, and choices.

## Requirements

### Requirement 1: Scene Transition Orchestration

**User Story:** As Ale or Sofi, I want scene changes to play a smooth animated transition, so that the story feels like a magical storybook coming to life.

#### Acceptance Criteria

1. WHEN a story choice is made and a new story beat arrives, THE Transition_Engine SHALL animate the Outgoing_Scene out and the Incoming_Scene in using the active Transition_Type.
2. THE Transition_Engine SHALL complete each transition animation within 600ms to 1200ms.
3. WHILE a transition animation is playing, THE Transition_Engine SHALL prevent additional choice interactions until the Incoming_Scene is fully visible.
4. THE Transition_Engine SHALL render the Incoming_Scene off-screen or at zero opacity before the transition begins, so that no layout flash occurs.
5. WHEN the Incoming_Scene has no scene image loaded yet, THE Transition_Engine SHALL delay the transition start until the image has loaded or 3 seconds have elapsed, whichever comes first.

### Requirement 2: Page Turn Effect

**User Story:** As Ale or Sofi, I want some scene changes to look like a storybook page turning, so that the app feels like a real magical book.

#### Acceptance Criteria

1. WHEN the active Transition_Type is Page_Turn_Effect, THE Transition_Engine SHALL apply a CSS 3D perspective transform that rotates the Outgoing_Scene along the vertical axis to simulate a page turning from right to left.
2. THE Page_Turn_Effect SHALL use a CSS `perspective` value between 800px and 1200px to create a convincing depth illusion.
3. THE Page_Turn_Effect SHALL include a subtle gradient shadow on the turning edge to simulate page thickness and light.
4. THE Page_Turn_Effect SHALL reveal the Incoming_Scene progressively as the Outgoing_Scene rotates away.

### Requirement 3: Cinematic Fade Effect

**User Story:** As Ale or Sofi, I want some scene changes to dissolve like a movie, so that dramatic story moments feel epic.

#### Acceptance Criteria

1. WHEN the active Transition_Type is Cinematic_Fade, THE Transition_Engine SHALL cross-fade the Outgoing_Scene opacity from 1 to 0 while simultaneously fading the Incoming_Scene opacity from 0 to 1.
2. THE Cinematic_Fade SHALL apply a subtle scale transform (from 1.0 to 1.04) on the Outgoing_Scene during fade-out to create a parallax depth effect.
3. THE Cinematic_Fade SHALL apply a subtle scale transform (from 0.97 to 1.0) on the Incoming_Scene during fade-in to create an approaching motion.

### Requirement 4: Transition Type Selection

**User Story:** As Ale or Sofi, I want different scene changes to use different transition styles, so that the story feels varied and surprising.

#### Acceptance Criteria

1. THE Transition_Engine SHALL support at least two Transition_Types: Page_Turn_Effect and Cinematic_Fade.
2. WHEN a new transition is triggered, THE Transition_Engine SHALL select the Transition_Type by cycling through available types in sequence, so that consecutive scenes use different effects.
3. THE Transition_Engine SHALL expose a mechanism for future Transition_Types to be registered without modifying existing transition logic.

### Requirement 5: Sparkle Burst During Transitions

**User Story:** As Ale or Sofi, I want magical sparkles to appear during scene changes, so that every transition feels enchanted.

#### Acceptance Criteria

1. WHEN a transition animation reaches its midpoint (approximately 50% of the total duration), THE Transition_Engine SHALL trigger a Sparkle_Burst using the existing CelebrationOverlay component with type "sparkle".
2. THE Sparkle_Burst SHALL use the design system accent palette colors (gold, coral, violet) for particle colors.
3. THE Sparkle_Burst SHALL display between 15 and 30 particles.
4. THE Sparkle_Burst SHALL complete within the remaining duration of the transition animation.

### Requirement 6: Accessibility — Reduced Motion Support

**User Story:** As a parent of a child with motion sensitivity, I want transitions to be suppressed when reduced motion is enabled, so that the app remains comfortable for all children.

#### Acceptance Criteria

1. WHILE Reduced_Motion_Mode is active, THE Transition_Engine SHALL replace all animated transitions with an instant crosscut (opacity swap with no animation).
2. WHILE Reduced_Motion_Mode is active, THE Transition_Engine SHALL suppress the Sparkle_Burst entirely.
3. WHILE Reduced_Motion_Mode is active, THE Transition_Engine SHALL complete the scene swap within 200ms.
4. THE Transition_Engine SHALL detect Reduced_Motion_Mode changes in real time using a `matchMedia` listener, without requiring a page reload.

### Requirement 7: CSS-First Implementation

**User Story:** As a developer, I want transitions built with CSS animations and minimal JavaScript, so that the app stays lightweight and consistent with the existing design system.

#### Acceptance Criteria

1. THE Transition_Engine SHALL implement all visual transition effects using CSS `@keyframes`, `transform`, and `opacity` properties.
2. THE Transition_Engine SHALL use CSS custom properties (variables) from the existing design system for timing functions, colors, and radii.
3. THE Transition_Engine SHALL add no new external animation library dependencies to the project.
4. THE Transition_Engine SHALL use `will-change` on transitioning elements to hint GPU compositing, and remove the hint after the transition completes.

### Requirement 8: Performance and Rendering Quality

**User Story:** As Ale or Sofi, I want scene changes to be smooth without any stuttering, so that the magic is never broken.

#### Acceptance Criteria

1. THE Transition_Engine SHALL maintain 60 frames per second during transition animations on mid-range tablet hardware.
2. THE Transition_Engine SHALL animate only composite-friendly CSS properties (transform, opacity) to avoid layout thrashing.
3. THE Transition_Engine SHALL clean up all transition-related CSS classes and inline styles from the DOM within 100ms after a transition completes.
4. IF a transition animation fails to complete within 2000ms, THEN THE Transition_Engine SHALL force-complete the transition by immediately showing the Incoming_Scene and removing the Outgoing_Scene.

### Requirement 9: Integration with DualStoryDisplay

**User Story:** As a developer, I want the transition system to integrate cleanly with DualStoryDisplay, so that existing story rendering logic remains unchanged.

#### Acceptance Criteria

1. THE Transition_Engine SHALL operate as a wrapper or sibling component to DualStoryDisplay, without modifying the internal rendering logic of DualStoryDisplay.
2. WHEN a new story beat is set via the story store, THE Transition_Engine SHALL intercept the scene change and apply the transition before DualStoryDisplay renders the new content.
3. THE Transition_Engine SHALL preserve the existing focus management behavior where narration text receives focus after a new scene loads.
4. THE Transition_Engine SHALL preserve the existing shimmer sweep effect that fires when a new scene image appears.

### Requirement 10: Mobile Responsiveness

**User Story:** As Ale or Sofi using a tablet, I want transitions to look great on any screen size, so that the experience is magical everywhere.

#### Acceptance Criteria

1. THE Transition_Engine SHALL adapt the Page_Turn_Effect perspective value proportionally to the viewport width on screens narrower than 768px.
2. WHEN the viewport width is below 480px, THE Transition_Engine SHALL default to Cinematic_Fade instead of Page_Turn_Effect to avoid 3D distortion on small screens.
3. THE Transition_Engine SHALL use relative units (%, vw, vh) for transition positioning to maintain visual consistency across screen sizes.
