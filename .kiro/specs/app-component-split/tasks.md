# Tasks: App Component Split

## Task 1: Create useStoryConnection hook
Extract WebSocket connection logic from App.jsx into a reusable hook.

- [x] 1.1 Create `frontend/src/features/session/hooks/useStoryConnection.js` with the hook skeleton accepting `{ lang, profiles, onVoiceCommand, onMechanics }` and returning `{ connectToAI, disconnect, isConnected }` [Requirement 4.1, 4.2]
- [x] 1.2 Move `connectToAI` function body from App.jsx into the hook — build connection params, call `websocketService.connect()`, include `time_limit_minutes` and optional `previous_duration_seconds` [Requirement 4.3]
- [x] 1.3 Move all 11 WebSocket event subscriptions (`connected`, `disconnected`, `CREATIVE_ASSET`, `STORY_COMPLETE`, `STATUS`, `MECHANIC_WARNING`, `error`, `story_segment`, `VOICE_COMMAND_MATCH`, `DRAWING_PROMPT`, `DRAWING_END`) into the hook [Requirement 4.4, 4.5, 4.6, 4.7, 4.8]
- [x] 1.4 Add cleanup effect that unsubscribes all listeners on unmount [Requirement 4.9]
- [x] 1.5 Export hook from `frontend/src/features/session/index.js` barrel file [Requirement 4.10]
- [ ] *1.6 Write property test: for any valid profiles input, `connectToAI` registers exactly 11 subscriptions and returns 11 unsubscribe functions [Requirement 4.4]

## Task 2: Create SetupScreen container
Build the setup flow container that owns privacy→language→character setup.

- [x] 2.1 Create `frontend/src/features/setup/components/SetupScreen.jsx` with props `{ t, onSetupCelebration }` [Requirement 2.10]
- [x] 2.2 Move `handleLanguageSelect` from App.jsx into SetupScreen — sets language in setupStore, plays success feedback [Requirement 2.4]
- [x] 2.3 Move `handleSetupComplete` from App.jsx into SetupScreen — enriches profiles with spiritToPersonality mapping, sets child stores, calls completeSetup, sets session profiles, triggers connection via `useStoryConnection` [Requirement 2.5]
- [x] 2.4 Move `handleContinueStory` and `handleNewAdventure` from App.jsx into SetupScreen [Requirement 2.6, 2.7]
- [x] 2.5 Move session existence check effect (`setup.privacyAccepted && setup.language && currentStep === 'characters'`) into SetupScreen [Requirement 2.9]
- [x] 2.6 Render LanguageSelector, ContinueScreen, CharacterSetup, and title heading based on `setup.currentStep` [Requirement 2.1, 2.2, 2.3, 2.8]
- [x] 2.7 Export SetupScreen from `frontend/src/features/setup/index.js` barrel file [Requirement 2.10]
- [ ] *2.8 Write property test: for any valid profile input, `enrichProfiles` always produces output with all required fields populated [Requirement 2.5]

## Task 3: Create StoryScreen container
Build the story experience container that owns WebSocket subscriptions, story rendering, and overlays.

- [x] 3.1 Create `frontend/src/features/story/components/StoryScreen.jsx` with props `{ t, onExit, onAlert, onVoiceCommand }` [Requirement 3.16]
- [x] 3.2 Wire up `useStoryConnection` hook and move story-related useState calls (`isListening`, `hasCamera`, `showDashboard`, `showParentControls`, `showWorldMap`, `showGallery`, `showPhotoReview`, `mechanics`, `child1Responded`, `child2Responded`, `audioUnlocked`) into StoryScreen [Requirement 3.5, 3.12, 3.13]
- [x] 3.3 Move `handleChoice`, `handleDrawingComplete`, `handleSaveAndExit`, `handleExitWithoutSaving`, `handleEmergencyExit`, `handleUnlockAudio` from App.jsx into StoryScreen [Requirement 3.6, 3.7, 3.8, 3.9, 3.10]
- [x] 3.4 Move story lifecycle effects: multimodal capture start, child response reset on new beat, drawing tick interval, sceneAudio unlock tracking [Requirement 3.11, 3.15]
- [x] 3.5 Move session persistence effects: auto-save on history change, beforeunload beacon, visibilitychange save, story completion cleanup [Requirement 5.1, 5.2, 5.3, 5.4, 5.5]
- [x] 3.6 Move accessibility focus effect: focus `mainRef` on mount with 100ms delay [Requirement 6.1]
- [x] 3.7 Render session controls nav, DualPrompt, TransitionEngine/LoadingAnimation, DrawingCanvas, overlays (WorldMap, Gallery, ParentControls, ParentDashboard, SiblingDashboard, ParentApprovalScreen), MagicMirror, CameraPreview, MultimodalFeedback, audio unlock button, floating mic [Requirement 3.1, 3.2, 3.3, 3.4, 3.5, 3.12, 3.13, 3.14]
- [x] 3.8 Export StoryScreen from `frontend/src/features/story/index.js` barrel file [Requirement 3.16]

## Task 4: Refactor App.jsx into router shell
Slim down App.jsx to a thin screen switcher with only global concerns.

- [x] 4.1 Remove all moved useState calls, event handlers, effects, and store subscriptions from App.jsx [Requirement 1.10]
- [x] 4.2 Import and render SetupScreen when `!setup.isComplete`, StoryScreen when `setup.isComplete` [Requirement 1.1, 1.2, 1.3]
- [x] 4.3 Keep global concerns in App: SkipLink, AppContainer, useGamepad, VirtualKeyboard, ConnectionIndicator, click-sync effect [Requirement 1.6, 1.7, 1.8, 1.9]
- [x] 4.4 Keep modal layer in App: PrivacyModal (outside aria-hidden), AlertModal, ExitModal, VoiceCommandToast, CelebrationOverlay, FeedbackComponent [Requirement 1.4, 1.5]
- [x] 4.5 Wire callback props between App shell and screen containers (`onAlert`, `onExit`, `onVoiceCommand`, `onSetupCelebration`) [Requirement 1.3]
- [x] 4.6 Verify `aria-hidden` is applied to background content when modals are open [Requirement 6.2]

## Task 5: Verify build and integration
Ensure the refactored code builds and all behavior is preserved.

- [x] 5.1 Run `npm run build` from `frontend/` directory and verify zero errors [Requirement 7.1]
- [x] 5.2 Verify no new dependencies in `package.json` [Requirement 7.2]
- [x] 5.3 Verify all existing CSS classes apply without changes [Requirement 7.3]
- [x] 5.4 Run getDiagnostics on all new and modified files to verify no type/lint errors [Requirement 7.1]
- [x] 5.5 Verify SkipLink is first focusable element, story main has correct aria attributes, session nav has correct aria-label [Requirement 6.3, 6.4, 6.5, 6.6]
