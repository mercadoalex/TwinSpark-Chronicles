# Requirements Document

## Introduction

This document defines the requirements for the Interaction Model Redesign of TwinSpark Chronicles. The redesign overhauls the UX/UI to be optimized for 6-8 year old twins (Ale & Sofi) sharing a single iPad in portrait mode. The core shift replaces the current text-heavy, dual-perspective split view with a voice-first, turn-based interaction model where children speak their imagination freely into the story. Illustrated suggestion cards serve as gentle inspiration (not required choices), TTS reads all content aloud automatically, and the AI adapts to anything the children say — creating a freeform imagination engine with no dead ends.

## Glossary

- **Story_Engine**: The frontend module that orchestrates the core story loop including narration display, turn management, voice input capture, and suggestion card presentation.
- **Turn_Indicator**: The UI component that displays which twin's turn it is, showing the active child's avatar, name, and a pulsing glow animation in their assigned color.
- **Voice_Input_Controller**: The frontend module that manages the microphone button, captures speech, displays listening/processing states, and delivers transcribed text to the backend.
- **Suggestion_Card**: An illustrated touch target (minimum 72px) that presents a story direction idea as an image with a short label, serving as optional inspiration the child may tap instead of speaking.
- **Narration_View**: The single-narrative display area that shows the current story beat with a scene illustration and text, replacing the previous dual-perspective split view.
- **TTS_Controller**: The module that automatically reads all story narration aloud using text-to-speech, making text a secondary reinforcement rather than the primary channel.
- **Spirit_Animal_Picker**: The setup component that lets each child choose their spirit animal from a swipeable gallery of large illustrated cards without requiring reading ability.
- **Theme_Picker**: The component that presents 2-3 illustrated adventure theme cards (e.g., forest, space, ocean) for starting a new story session.
- **Session_Continuity_Manager**: The module that handles automatic session resumption and offers the "new adventure" option when children return to the app.
- **Celebration_Animator**: The module that triggers sparkle, confetti, and other delight animations on story progression milestones.
- **Parent_Setup_Flow**: The initial configuration screens where a parent enters children's names and selects language using a standard keyboard.
- **Active_Twin**: The child whose turn it currently is to provide story input.
- **Spark**: A synonym for Suggestion_Card, used in the UI to describe the illustrated inspiration options shown to children.

## Requirements

### Requirement 1: Turn-Based Story Loop

**User Story:** As a child user, I want to take turns with my twin telling the story, so that we both get to shape the adventure equally.

#### Acceptance Criteria

1. WHEN a story beat narration completes (TTS finishes reading), THE Story_Engine SHALL activate the Turn_Indicator for the Active_Twin.
2. THE Story_Engine SHALL alternate the Active_Twin between the two configured children after each story input is submitted.
3. WHEN the Active_Twin submits input (via voice or suggestion card tap), THE Story_Engine SHALL send the input to the backend, switch the Active_Twin to the other child, and request the next story beat.
4. THE Turn_Indicator SHALL display the Active_Twin's avatar, name, and a pulsing glow animation in the Active_Twin's assigned color.
5. WHILE a story beat is being narrated, THE Story_Engine SHALL disable all input controls (microphone button and suggestion cards).
6. THE Story_Engine SHALL persist the current Active_Twin in session state so that turn order is preserved across app backgrounding and resumption.

### Requirement 2: Voice Input as Primary Creative Channel

**User Story:** As a child user, I want to say what happens next in the story, so that I can use my imagination freely without needing to read or type.

#### Acceptance Criteria

1. WHEN the Active_Twin's turn begins, THE Voice_Input_Controller SHALL display a large pulsing microphone button (minimum 72px touch target) at center-bottom of the screen.
2. WHEN the child taps the microphone button, THE Voice_Input_Controller SHALL begin capturing audio from the device microphone and transition to the listening state.
3. WHILE the Voice_Input_Controller is in the listening state, THE Voice_Input_Controller SHALL display an animated sound wave visualization and the Active_Twin's avatar in a "listening" pose.
4. WHEN the Voice_Input_Controller detects 1.5 seconds of silence after speech, THE Voice_Input_Controller SHALL stop recording and transition to the processing state.
5. WHILE the Voice_Input_Controller is in the processing state, THE Voice_Input_Controller SHALL display a sparkle animation indicating the AI is thinking.
6. WHEN the backend returns a transcription, THE Story_Engine SHALL send the transcript as freeform story input to the AI — the AI SHALL interpret any input and weave it into the narrative without rejecting or invalidating the child's idea.
7. IF the Voice_Input_Controller fails to obtain microphone permission, THEN THE Voice_Input_Controller SHALL hide the microphone button and display only the suggestion cards as the input method.
8. IF the transcription result is empty or below confidence threshold, THEN THE Voice_Input_Controller SHALL display a gentle "I didn't catch that — try again or tap a spark!" message with a retry animation.

### Requirement 3: Illustrated Suggestion Cards (Sparks)

**User Story:** As a child user, I want to see picture ideas for what could happen next, so that I have inspiration if I don't know what to say.

#### Acceptance Criteria

1. WHEN the Active_Twin's turn begins, THE Story_Engine SHALL display 2-3 Suggestion_Cards alongside the microphone button.
2. THE Story_Engine SHALL present each Suggestion_Card as an illustrated image with a short text label (maximum 4 words) readable by TTS on long-press.
3. Each Suggestion_Card SHALL have a minimum touch target size of 72px in both width and height.
4. WHEN the child taps a Suggestion_Card, THE Story_Engine SHALL submit the card's associated story direction text as input to the backend, identical in flow to voice input submission.
5. THE Story_Engine SHALL generate contextually relevant Suggestion_Card content based on the current story state, requested from the backend alongside each story beat.
6. THE Story_Engine SHALL NOT require the child to use a Suggestion_Card — cards are optional inspiration that children can ignore in favor of voice input.
7. WHEN a Suggestion_Card is long-pressed (500ms), THE TTS_Controller SHALL read the card's label aloud to assist non-reading children.

### Requirement 4: Automatic TTS Narration

**User Story:** As a child user, I want the story read aloud to me automatically, so that I can enjoy the adventure without needing to read.

#### Acceptance Criteria

1. WHEN a new story beat arrives from the backend, THE TTS_Controller SHALL automatically begin reading the narration text aloud without requiring user interaction.
2. THE TTS_Controller SHALL use the character-appropriate voice profile for narration (matching the existing voice system).
3. WHILE the TTS_Controller is reading narration, THE Narration_View SHALL highlight the currently spoken sentence to provide visual text tracking as secondary reinforcement.
4. WHEN the TTS narration completes, THE Story_Engine SHALL transition to the Active_Twin's input phase (showing turn indicator, mic button, and suggestion cards).
5. IF the child taps the screen during TTS narration, THEN THE TTS_Controller SHALL pause narration and display a "tap to continue" indicator, resuming on the next tap.
6. THE TTS_Controller SHALL read narration at a pace appropriate for 6-8 year old comprehension (rate between 0.85x and 1.0x normal speed).

### Requirement 5: Single Narrative View with Scene Illustration

**User Story:** As a child user, I want to see one big picture of the story, so that I can focus on what's happening without confusion.

#### Acceptance Criteria

1. THE Narration_View SHALL display a single scene illustration occupying the top 50-60% of the portrait viewport for each story beat.
2. THE Narration_View SHALL display the narration text below the scene illustration in a large, rounded font (minimum 18px, recommended 22px) suitable for emerging readers.
3. THE Narration_View SHALL replace the previous dual-perspective split view with a single unified narrative perspective.
4. WHEN a new story beat arrives, THE Narration_View SHALL transition the scene illustration with a gentle crossfade animation (300-500ms duration).
5. THE Narration_View SHALL use minimal text — the AI backend SHALL generate concise narration (maximum 3 sentences per beat) optimized for listening rather than reading.
6. THE Narration_View SHALL display the Active_Twin's avatar as a small overlay on the scene illustration to indicate story perspective.

### Requirement 6: Simplified Visual Setup Flow

**User Story:** As a parent, I want to quickly set up the app for my kids, and as a child, I want to pick my spirit animal from fun pictures without needing to read.

#### Acceptance Criteria

1. THE Parent_Setup_Flow SHALL consist of a maximum of 3 screens: language selection, child names entry, and confirmation.
2. THE Parent_Setup_Flow SHALL use a standard on-screen keyboard for text entry (names only), restricted to the parent setup phase.
3. WHEN the parent setup is complete, THE Spirit_Animal_Picker SHALL present each child with a horizontally swipeable gallery of large illustrated spirit animal cards (minimum 200px tall).
4. THE Spirit_Animal_Picker SHALL require no reading — each card SHALL display only the animal illustration with the animal name spoken aloud by TTS when the card is in focus.
5. WHEN a child swipes to a spirit animal card and taps it, THE Spirit_Animal_Picker SHALL confirm the selection with a celebration animation (sparkles and the animal's sound).
6. THE Spirit_Animal_Picker SHALL present a minimum of 6 spirit animal options per child.
7. THE setup flow SHALL NOT present a virtual keyboard to children at any point.

### Requirement 7: Frictionless Session Continuity

**User Story:** As a child user, I want to jump right back into my story when I open the app, so that I don't have to figure out menus or buttons.

#### Acceptance Criteria

1. WHEN the app launches with an existing session, THE Session_Continuity_Manager SHALL automatically resume the story from the last completed beat within 2 seconds of app load.
2. WHEN the app launches with an existing session, THE Session_Continuity_Manager SHALL display a brief "Welcome back!" animation with both children's avatars before resuming.
3. WHEN the app launches without an existing session (or after a story completes), THE Theme_Picker SHALL present 2-3 illustrated adventure theme cards for starting a new story.
4. Each Theme_Picker card SHALL have a minimum touch target of 120px height, display a theme illustration, and speak the theme name aloud via TTS when focused.
5. WHEN a child taps a theme card, THE Session_Continuity_Manager SHALL initiate a new story session with the selected theme and display a launch celebration animation.
6. THE Session_Continuity_Manager SHALL NOT require navigation through menus, back buttons, or text-based options to start or resume play.

### Requirement 8: Child-Appropriate Visual Design System

**User Story:** As a child user, I want the app to look fun and colorful with big buttons I can easily tap, so that I can play without getting confused or frustrated.

#### Acceptance Criteria

1. THE Story_Engine SHALL render all interactive elements (buttons, cards, controls) with a minimum touch target size of 72px in both dimensions.
2. THE Story_Engine SHALL use a warm, rounded visual aesthetic with soft shadows and playful colors — not glassmorphism, flat design, or other adult-oriented styles.
3. THE Story_Engine SHALL assign each twin a distinct color (used in turn indicator, avatar border, and UI accents) that persists throughout the session.
4. WHEN a story beat progresses successfully, THE Celebration_Animator SHALL trigger a brief celebration effect (sparkles, confetti, or star burst) lasting 1-2 seconds.
5. WHILE the AI is generating the next story beat, THE Story_Engine SHALL display a fun loading animation (e.g., bouncing characters, swirling stars) instead of a standard spinner.
6. THE Story_Engine SHALL minimize on-screen text, preferring icons and illustrations for navigation and status communication.
7. THE Story_Engine SHALL support a reduced-motion mode that replaces animations with simple opacity transitions for accessibility.
8. THE Story_Engine SHALL support a high-contrast mode that increases border widths and color differentiation for visibility.

### Requirement 9: AI Freeform Interpretation

**User Story:** As a child user, I want the story to go wherever my imagination takes it, so that I never feel like I said the wrong thing.

#### Acceptance Criteria

1. WHEN the backend receives voice input from a child, THE backend SHALL interpret the input as a creative story direction regardless of grammar, coherence, or relevance to the current scene.
2. THE backend SHALL NOT return "invalid choice", "I don't understand", or any rejection of the child's input — every input SHALL produce a valid next story beat.
3. WHEN the child's input is tangential or fantastical (e.g., "make it rain candy" during a forest scene), THE backend SHALL creatively weave the input into the narrative while maintaining story continuity.
4. WHEN the child references the other twin by name (e.g., "Sofi should find a secret door"), THE backend SHALL incorporate the referenced twin into the narrative action.
5. THE backend SHALL generate 2-3 contextually relevant suggestion texts alongside each story beat response, to be displayed as Suggestion_Cards on the next turn.
6. THE backend SHALL generate concise narration (maximum 3 sentences per beat) optimized for TTS delivery to young children.

### Requirement 10: Gamepad and Legacy Input Removal

**User Story:** As a developer, I want to remove the archived gamepad system and text-based choice buttons, so that the codebase reflects the new voice-first interaction model.

#### Acceptance Criteria

1. THE Story_Engine SHALL NOT render text-based choice buttons for story progression — all choice input flows through voice or Suggestion_Cards.
2. THE Story_Engine SHALL NOT initialize, reference, or depend on the gamepad input system (useGamepad hook, gamepadStore, FocusNavigator, VirtualKeyboard).
3. THE Story_Engine SHALL NOT present a virtual keyboard to children during story interaction.
4. THE Story_Engine SHALL NOT render the dual-perspective split view (DualStoryDisplay component) — replaced by the single Narration_View.
5. WHEN the redesign is complete, THE frontend SHALL remove or archive all gamepad-related code (useGamepad, gamepadStore, FocusNavigator, VirtualKeyboard, ConnectionIndicator).

### Requirement 11: Portrait iPad Layout Optimization

**User Story:** As a child user sharing an iPad with my twin, I want the app to work perfectly in portrait mode, so that we can both see and reach the screen comfortably.

#### Acceptance Criteria

1. THE Story_Engine SHALL render all UI in portrait orientation, optimized for iPad screen dimensions (approximately 810x1080 logical points).
2. THE Narration_View SHALL stack content vertically: scene illustration (top 50-60%), narration text (middle 15-20%), and interaction controls (bottom 25-30%).
3. THE interaction controls area (mic button + suggestion cards) SHALL be positioned in the lower third of the screen within comfortable thumb-reach for children holding the iPad.
4. THE Story_Engine SHALL NOT use horizontal split layouts, side-by-side panels, or landscape-optimized arrangements.
5. THE Turn_Indicator SHALL be positioned at the top of the screen, clearly visible to both children simultaneously.
6. THE Story_Engine SHALL use CSS safe-area insets to avoid content being obscured by iPad notch or home indicator areas.

### Requirement 12: Accessibility for Non-Readers

**User Story:** As a child who is still learning to read, I want to use the app entirely through pictures and voice, so that I can play independently without needing a parent to read for me.

#### Acceptance Criteria

1. THE Story_Engine SHALL NOT require reading ability for any child-facing interaction — all text content SHALL be accompanied by TTS audio or iconographic representation.
2. THE TTS_Controller SHALL automatically read all UI labels, instructions, and story content without requiring the child to initiate playback.
3. THE Suggestion_Cards SHALL communicate their meaning primarily through illustration, with text labels serving only as secondary reinforcement.
4. THE Turn_Indicator SHALL communicate turn status through visual cues (avatar, color, animation) without relying on text comprehension.
5. THE Voice_Input_Controller SHALL communicate its state (ready, listening, processing, error) through animation and color changes rather than text messages.
6. All error states and system messages directed at children SHALL use simple illustrations and TTS audio rather than text-only notifications.
