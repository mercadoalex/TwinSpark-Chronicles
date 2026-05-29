# Implementation Plan: Interaction Model Redesign

## Overview

Incrementally transform TwinSpark Chronicles from a text-heavy, dual-perspective, gamepad-driven experience into a voice-first, turn-based, single-narrative storytelling engine. Start with backend data models and story beat generation, then build the frontend story loop state machine, voice input, suggestion cards, TTS integration, and finally the simplified setup flow. Remove legacy gamepad/dual-view code as the new system replaces it.

## Tasks

- [x] 1. Create backend data models for the new interaction model
  - [x] 1.1 Create `backend/app/models/story_beat.py`
    - Define `SuggestionData` model with `id`, `label` (max 4 words), `illustration_prompt`, `illustration_url`, `story_direction`
    - Define `StoryBeatResponse` model with `narration` (max 3 sentences), `illustration_prompt`, `illustration_url`, `suggestions` (2-3 items), `perspective`, `is_milestone`
    - Add Pydantic validators for narration sentence count, suggestion count, and label word count
    - _Requirements: 3.1, 3.2, 5.5, 9.5, 9.6_

  - [x] 1.2 Create `backend/app/models/input_event.py`
    - Define `InputType` enum (VOICE, CARD)
    - Define `StoryInputEvent` model with `session_id`, `active_twin`, `input_type`, `text`, `card_id`, `timestamp`
    - _Requirements: 2.6, 3.4_

  - [x] 1.3 Create `backend/app/models/session_state.py`
    - Define `SessionState` model with `session_id`, `active_twin`, `turn_count`, `last_beat_id`, `theme`, `story_context`
    - Implement `switch_turn()` method that alternates `active_twin` and increments `turn_count`
    - _Requirements: 1.2, 1.6_

  - [ ]* 1.4 Write property test: Turn alternation invariant (Property 1)
    - **Property 1: Turn alternation invariant**
    - Use Hypothesis to generate random starting twin + N switch operations, verify active_twin alternates correctly
    - **Validates: Requirements 1.2, 1.3**

  - [ ]* 1.5 Write property test: Session state round-trip (Property 2)
    - **Property 2: Session state round-trip**
    - Serialize `SessionState` to JSON and deserialize back, assert equivalence of all fields
    - **Validates: Requirements 1.6, 7.1**

  - [ ]* 1.6 Write property test: Suggestion count invariant (Property 5)
    - **Property 5: Suggestion count invariant**
    - Generate `StoryBeatResponse` objects with varying suggestion counts, verify validation rejects counts outside 2-3
    - **Validates: Requirements 3.1, 9.5**

  - [ ]* 1.7 Write property test: Narration sentence count limit (Property 6)
    - **Property 6: Narration sentence count limit**
    - Generate narration strings with varying sentence counts, verify validation rejects narrations with more than 3 sentences
    - **Validates: Requirements 4.6, 5.5, 9.6**

  - [ ]* 1.8 Write property test: Suggestion label brevity (Property 7)
    - **Property 7: Suggestion label brevity**
    - Generate labels with varying word counts, verify validation rejects labels with more than 4 words
    - **Validates: Requirements 3.2**

  - [ ]* 1.9 Write property test: StoryBeatResponse serialization round-trip (Property 12)
    - **Property 12: StoryBeatResponse serialization round-trip**
    - Serialize valid `StoryBeatResponse` to JSON and deserialize back, assert equivalence including nested `SuggestionData`
    - **Validates: Requirements 7.1**

  - [ ]* 1.10 Write property test: Turn state persistence (Property 10)
    - **Property 10: Turn state persistence across serialization**
    - Call `switch_turn()` then serialize/deserialize, verify `active_twin` is opposite and `turn_count` incremented by 1
    - **Validates: Requirements 1.6**

- [x] 2. Implement freeform input handler in the backend
  - [x] 2.1 Create `backend/app/services/freeform_input_handler.py`
    - Implement `interpret_input(input_text, session_id, active_twin, story_context) -> StoryBeatResponse`
    - Build storyteller prompt with "yes-and" instruction: accept any input, weave creatively into narrative
    - Include instruction to generate 2-3 contextual suggestions for next turn
    - Include instruction to limit narration to 3 sentences max
    - Never return rejection/error for creative input — always produce a valid beat
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [x] 2.2 Extend WebSocket handler for new message types
    - Add handling for `voice_input` message type (route audio to STT, then to freeform handler)
    - Add handling for `card_selection` message type (route story_direction text to freeform handler)
    - Send `story_beat` response with narration, illustration_url, suggestions, perspective, is_milestone
    - Send `transcript_result` and `transcript_error` feedback messages
    - _Requirements: 2.6, 3.4, 9.5_

  - [ ]* 2.3 Write property test: Input event normalization (Property 4)
    - **Property 4: Input event normalization**
    - Generate random voice/card inputs, verify both produce valid `StoryInputEvent` with non-empty text and valid active_twin
    - **Validates: Requirements 2.6, 3.4**

  - [ ]* 2.4 Write property test: No input rejection (Property 8)
    - **Property 8: No input rejection (freeform acceptance)**
    - Generate arbitrary non-empty strings (gibberish, fantastical, off-topic), verify backend produces valid `StoryBeatResponse` for each
    - **Validates: Requirements 9.1, 9.2, 9.3**

  - [ ]* 2.5 Write property test: Story beat response completeness (Property 9)
    - **Property 9: Story beat response completeness**
    - For valid `StoryInputEvent` objects, verify response has non-empty narration, non-empty illustration_prompt, 2-3 suggestions with non-empty labels and story_directions, and valid perspective
    - **Validates: Requirements 5.1, 5.5, 9.5**

  - [ ]* 2.6 Write property test: Low-confidence transcript triggers retry (Property 11)
    - **Property 11: Low-confidence transcript triggers retry**
    - Generate confidence values [0.0, 1.0], verify transcripts below 0.4 are not submitted as input and signal retry
    - **Validates: Requirements 2.8**

- [x] 3. Checkpoint — Verify backend models and services
  - Run all backend tests, ensure property tests pass. Ask user if questions arise.

- [x] 4. Build frontend story loop state machine
  - [x] 4.1 Create `frontend/src/stores/storyLoopStore.js`
    - Implement Zustand store with phases: `narrating`, `awaiting_input`, `recording`, `processing`, `error`
    - Track `activeTwin` (alternates each turn), `currentBeat`, `suggestions`, `ttsPlaying`, `highlightedSentence`
    - Track `isRecording`, `lastTranscript`, `error`, `turnCount`
    - Implement actions: `submitVoiceInput`, `submitCardSelection`, `onTTSComplete`, `startRecording`, `cancelRecording`, `switchTurn`, `retry`
    - Enforce valid state transitions (no recording during narrating, no input during processing)
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6_

  - [ ]* 4.2 Write property test: Voice input state machine validity (Property 3)
    - **Property 3: Voice input state machine validity**
    - Use fast-check to generate random sequences of events, verify state machine is always in a valid phase with no invalid transitions
    - **Validates: Requirements 1.5, 2.2, 2.3, 2.4**

- [x] 5. Build Narration View component
  - [x] 5.1 Create `frontend/src/features/story/components/NarrationView.jsx`
    - Layout: scene illustration (top 50-60%), narration text (middle 15-20%), interaction controls slot (bottom 25-30%)
    - Scene illustration with crossfade animation (300-500ms) on beat change
    - Narration text in large rounded font (22px minimum), with sentence highlighting during TTS
    - Active twin avatar as small overlay on scene illustration
    - Portrait-optimized, vertical stacking only
    - Apply CSS safe-area insets for iPad notch/home indicator
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.6, 11.1, 11.2, 11.3, 11.4, 11.6_

  - [x] 5.2 Create `frontend/src/features/story/components/NarrationView.css`
    - Warm, rounded visual aesthetic (border-radius, soft shadows, playful colors)
    - No glassmorphism or adult-oriented styles
    - Reduced-motion support: replace animations with opacity transitions
    - High-contrast mode: increased border widths and color differentiation
    - Safe-area insets via `env(safe-area-inset-*)`
    - _Requirements: 8.2, 8.7, 8.8, 11.6_

- [x] 6. Build Turn Indicator component
  - [x] 6.1 Create `frontend/src/features/story/components/TurnIndicator.jsx`
    - Display active twin's avatar, name, and pulsing glow animation in twin's assigned color
    - Position at top of screen, visible to both children
    - Communicate turn status through visual cues (avatar, color, animation) without relying on text
    - Show only during `awaiting_input` and `recording` phases
    - Minimum 72px height for the indicator area
    - _Requirements: 1.4, 8.1, 8.3, 11.5, 12.4_

- [x] 7. Build Voice Input Controller component
  - [x] 7.1 Create `frontend/src/features/story/components/VoiceInputController.jsx`
    - Large pulsing mic button (minimum 72px) at center-bottom of screen
    - States: idle (pulsing icon), listening (animated sound waves + twin avatar), processing (sparkle animation), error (retry prompt)
    - Tap to start recording, auto-stop after 1.5s silence
    - On successful transcript: submit to story loop
    - On low-confidence/empty: show "I didn't catch that — try again or tap a spark!" with retry animation
    - Hide mic button entirely if mic permission denied (cards become primary)
    - Communicate state through animation and color, not text
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 8.1, 12.5_

  - [x] 7.2 Create `frontend/src/features/story/components/VoiceInputController.css`
    - Pulsing animation for idle state
    - Sound wave animation for listening state
    - Sparkle/shimmer animation for processing state
    - Reduced-motion alternatives
    - _Requirements: 8.7_

- [x] 8. Build Suggestion Cards component
  - [x] 8.1 Create `frontend/src/features/story/components/SuggestionCards.jsx`
    - Display 2-3 illustrated cards in horizontal row below mic button
    - Each card: minimum 72px touch target, illustration image + short label (max 4 words)
    - Tap submits card's `storyDirection` as input (identical flow to voice)
    - Long-press (500ms) triggers TTS to read card label aloud
    - Only tappable during `awaiting_input` phase
    - Cards are optional — never required for progression
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 8.1, 12.3_

  - [x] 8.2 Create `frontend/src/features/story/components/SuggestionCards.css`
    - Warm rounded card style with soft shadows
    - Subtle entrance animation when cards appear
    - Tap feedback animation
    - Reduced-motion support
    - _Requirements: 8.2, 8.7_

- [x] 9. Integrate TTS Controller with story loop
  - [x] 9.1 Update TTS integration in story loop
    - Auto-play TTS when new story beat arrives (no user interaction required)
    - Use character-appropriate voice profile from existing voice system
    - Highlight currently spoken sentence in Narration View
    - Fire `onTTSComplete` event when narration finishes reading
    - Tap during TTS pauses narration, tap again resumes
    - Set TTS rate between 0.85x and 1.0x for child comprehension
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 10. Build Celebration Animator
  - [x] 10.1 Create `frontend/src/features/story/components/CelebrationAnimator.jsx`
    - Trigger sparkles/confetti/star burst on `is_milestone` story beats
    - Duration: 1-2 seconds per celebration
    - Fun loading animation (bouncing characters, swirling stars) during `processing` phase
    - Reduced-motion: replace with simple opacity fade
    - _Requirements: 8.4, 8.5, 8.7_

- [x] 11. Checkpoint — Verify core story loop
  - Run all frontend tests, verify story loop state machine, voice input, cards, TTS, and celebrations work together. Ask user if questions arise.

- [x] 12. Build simplified setup flow
  - [x] 12.1 Create `frontend/src/features/setup/components/SpiritAnimalPicker.jsx`
    - Horizontally swipeable gallery of large illustrated spirit animal cards (minimum 200px tall)
    - No reading required: TTS speaks animal name when card is in focus/center
    - Tap to confirm selection → celebration animation (sparkles + animal sound)
    - Minimum 6 spirit animal options
    - No virtual keyboard shown at any point
    - _Requirements: 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x] 12.2 Simplify parent setup flow
    - Reduce to maximum 3 screens: language selection, child names entry, confirmation
    - Standard on-screen keyboard for name entry (parent only)
    - After parent setup completes, transition to Spirit Animal Picker for each child
    - _Requirements: 6.1, 6.2_

- [x] 13. Build session continuity and theme picker
  - [x] 13.1 Create `frontend/src/features/story/components/ThemePicker.jsx`
    - Display 2-3 illustrated adventure theme cards (forest, space, ocean, etc.)
    - Each card: minimum 120px height, theme illustration, TTS reads name on focus
    - Tap triggers new session creation + launch celebration animation
    - _Requirements: 7.3, 7.4, 7.5_

  - [x] 13.2 Implement session continuity logic
    - Auto-resume from last beat within 2 seconds of app load when session exists
    - Display "Welcome back!" animation with both twins' avatars before resuming
    - Show Theme Picker when no active session or after story completion
    - No menus, back buttons, or text-based navigation required
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6_

- [x] 14. Remove legacy gamepad and dual-view code
  - [x] 14.1 Remove gamepad system
    - Remove `useGamepad` hook, `gamepadStore`, `FocusNavigator`, `VirtualKeyboard`, `ConnectionIndicator`
    - Remove gamepad-related imports and references from `App.jsx`
    - Remove text-based choice buttons from story interaction
    - _Requirements: 10.1, 10.2, 10.3, 10.5_

  - [x] 14.2 Remove dual-perspective split view
    - Remove `DualStoryDisplay` component and its CSS
    - Replace with new `NarrationView` in the story screen
    - Update `StoryScreen.jsx` to use the new story loop components
    - _Requirements: 10.4_

- [x] 15. Wire everything together in App shell
  - [x] 15.1 Update `App.jsx` and `StoryScreen.jsx`
    - Replace old story components with new: NarrationView, TurnIndicator, VoiceInputController, SuggestionCards, CelebrationAnimator
    - Integrate storyLoopStore as the central state machine
    - Connect session continuity (auto-resume or theme picker)
    - Ensure portrait layout with vertical stacking throughout
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 15.2 Implement accessibility features
    - Verify all interactive elements are 72px+ touch targets
    - Ensure TTS reads all UI labels and instructions automatically
    - Verify reduced-motion mode works across all animated components
    - Verify high-contrast mode increases visibility
    - Ensure no child-facing interaction requires reading ability
    - _Requirements: 8.1, 8.7, 8.8, 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 16. Final checkpoint — End-to-end verification
  - Run all tests (backend + frontend), verify complete flow: setup → spirit animal → theme pick → story loop (voice + cards + TTS + turns + celebrations) → session resume. Ask user if questions arise.

## Task Dependency Graph

```json
{
  "waves": [
    {
      "name": "Wave 1: Backend Data Models",
      "tasks": ["1"],
      "description": "Create Pydantic models for story beats, input events, and session state"
    },
    {
      "name": "Wave 2: Backend Services",
      "tasks": ["2"],
      "dependsOn": ["1"],
      "description": "Implement freeform input handler and WebSocket message types"
    },
    {
      "name": "Wave 3: Backend Checkpoint",
      "tasks": ["3"],
      "dependsOn": ["2"],
      "description": "Verify all backend models and services pass tests"
    },
    {
      "name": "Wave 4: Frontend State Machine",
      "tasks": ["4"],
      "dependsOn": ["3"],
      "description": "Build the story loop Zustand store with phase management"
    },
    {
      "name": "Wave 5: Core UI Components",
      "tasks": ["5", "6", "7", "8", "9", "10"],
      "dependsOn": ["4"],
      "description": "Build NarrationView, TurnIndicator, VoiceInputController, SuggestionCards, TTS integration, and CelebrationAnimator in parallel"
    },
    {
      "name": "Wave 6: Core Loop Checkpoint",
      "tasks": ["11"],
      "dependsOn": ["5", "6", "7", "8", "9", "10"],
      "description": "Verify the complete story loop works end-to-end"
    },
    {
      "name": "Wave 7: Setup and Session",
      "tasks": ["12", "13", "14"],
      "dependsOn": ["11"],
      "description": "Build simplified setup flow, session continuity, and remove legacy code in parallel"
    },
    {
      "name": "Wave 8: Integration",
      "tasks": ["15"],
      "dependsOn": ["12", "13", "14"],
      "description": "Wire all components together in App shell"
    },
    {
      "name": "Wave 9: Final Verification",
      "tasks": ["16"],
      "dependsOn": ["15"],
      "description": "End-to-end verification of the complete redesigned experience"
    }
  ]
}
```

## Notes

- Tasks marked with `*` are property-based tests (optional but recommended)
- Backend uses Python (FastAPI, Pydantic, Hypothesis for tests); frontend uses JavaScript (React, Zustand, fast-check for tests)
- Each task references specific requirements for traceability
- Checkpoints at tasks 3, 11, and 16 ensure incremental validation
- The gamepad removal (task 14) should happen after the new system is functional to avoid breaking the app mid-implementation
- Spirit animal illustrations and theme card illustrations will need to be generated or sourced as assets
- The existing TTS system and voice profiles are reused — this spec extends their integration, not replaces them
