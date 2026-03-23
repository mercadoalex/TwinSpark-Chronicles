# Requirements: App Component Split

## Requirement 1: Thin App Router Shell

### Description
Replace the monolithic App.jsx with a thin router shell (~80-100 lines) that switches between SetupScreen and StoryScreen based on `setupStore.isComplete`. The shell owns only global cross-cutting concerns: modals, gamepad, skip links, celebration overlay, and connection indicator.

### Acceptance Criteria
- 1.1 App.jsx renders SetupScreen when `setupStore.isComplete === false` and `setupStore.privacyAccepted === true`
- 1.2 App.jsx renders StoryScreen when `setupStore.isComplete === true`
- 1.3 Exactly one screen (SetupScreen or StoryScreen) is mounted at any time — never both
- 1.4 PrivacyModal renders when `privacyAccepted === false`, outside any `aria-hidden` wrapper
- 1.5 Global modals (AlertModal, ExitModal, VoiceCommandToast, CelebrationOverlay) remain in App shell
- 1.6 `useGamepad()` hook is called in App shell; VirtualKeyboard overlay renders in App shell
- 1.7 ConnectionIndicator renders in App shell
- 1.8 SkipLink renders as the first focusable element in App shell
- 1.9 Click-sync effect for gamepad focus (`FocusNavigator.syncToElement`) remains in App shell
- 1.10 App.jsx is reduced to under 150 lines (from 1127)

## Requirement 2: SetupScreen Container

### Description
Create a SetupScreen container component that owns the entire setup flow: privacy acceptance → language selection → character setup (or session continue). It encapsulates all setup-related event handlers and store interactions.

### Acceptance Criteria
- 2.1 SetupScreen renders LanguageSelector when `setup.currentStep === 'language'`
- 2.2 SetupScreen renders ContinueScreen when `setup.currentStep === 'characters'` and `persistence.availableSession` exists
- 2.3 SetupScreen renders CharacterSetup when `setup.currentStep === 'characters'` and no available session
- 2.4 `handleLanguageSelect` sets language in setupStore and plays success audio feedback
- 2.5 `handleSetupComplete` enriches profiles with spiritToPersonality mapping, sets child1/child2 in setupStore, calls `completeSetup()`, sets profiles in sessionStore, and triggers WebSocket connection
- 2.6 `handleContinueStory` restores session from persistence, builds profiles from restored setup state, and connects to AI
- 2.7 `handleNewAdventure` deletes existing session snapshot and clears `availableSession`
- 2.8 SetupScreen renders the "TwinSpark Chronicles" title heading
- 2.9 Session existence check effect fires when `privacyAccepted && language && currentStep === 'characters'`
- 2.10 SetupScreen is located at `frontend/src/features/setup/components/SetupScreen.jsx`

## Requirement 3: StoryScreen Container

### Description
Create a StoryScreen container component that owns the active story experience: session controls, story rendering, DualPrompt, drawing overlay, and all overlay panels (world map, gallery, parent controls, sibling dashboard).

### Acceptance Criteria
- 3.1 StoryScreen renders SessionStatus, SessionTimer, and EmergencyStop in a nav element with `aria-label="Session controls"`
- 3.2 StoryScreen renders DualPrompt when `story.currentBeat` exists and both child profiles are available
- 3.3 StoryScreen renders TransitionEngine when `story.currentBeat` exists, otherwise renders LoadingAnimation
- 3.4 StoryScreen renders DrawingCanvas overlay when `drawingStore.isActive === true`
- 3.5 StoryScreen manages overlay toggles: WorldMap, Gallery, ParentControls, ParentDashboard, SiblingDashboard, ParentApprovalScreen
- 3.6 `handleChoice` sends `MAKE_CHOICE` message via websocketService, sets `currentBeat` to null and `isGenerating` to true; on failure sets alert and resets generating
- 3.7 `handleDrawingComplete` sends `DRAWING_COMPLETE` message and calls `drawingStore.endSession()`
- 3.8 `handleSaveAndExit` saves snapshot, ends sibling session, resets all stores, disconnects WebSocket, and returns to setup
- 3.9 `handleExitWithoutSaving` disconnects WebSocket, resets all stores without saving
- 3.10 `handleEmergencyExit` disconnects WebSocket, clears localStorage snapshot, resets all stores
- 3.11 Drawing tick interval (1s) runs while `drawingStore.isActive` and cleans up on deactivation
- 3.12 Audio unlock button renders when `audioUnlocked === false`
- 3.13 Floating mic button toggles `isListening` state
- 3.14 MagicMirror, CameraPreview, and MultimodalFeedback render within story stage
- 3.15 Multimodal capture starts when component mounts (setup complete + connected)
- 3.16 StoryScreen is located at `frontend/src/features/story/components/StoryScreen.jsx`

## Requirement 4: useStoryConnection Hook

### Description
Extract WebSocket connection logic from App.jsx into a custom hook that manages connection lifecycle, event subscriptions, and reconnection. The hook encapsulates all 11 WebSocket event handlers.

### Acceptance Criteria
- 4.1 Hook accepts `{ lang, profiles, onVoiceCommand, onMechanics }` parameters
- 4.2 Hook returns `{ connectToAI, disconnect, isConnected }` interface
- 4.3 `connectToAI` builds connection params from profiles (including `time_limit_minutes` and optional `previous_duration_seconds`) and calls `websocketService.connect()`
- 4.4 Hook subscribes to all 11 events: `connected`, `disconnected`, `CREATIVE_ASSET`, `STORY_COMPLETE`, `STATUS`, `MECHANIC_WARNING`, `error`, `story_segment`, `VOICE_COMMAND_MATCH`, `DRAWING_PROMPT`, `DRAWING_END`
- 4.5 On `connected`: sets session connected, syncs localStorage snapshot, flushes drawing sync queue
- 4.6 On `disconnected` with code 1006 during story: sets reconnecting and retries after 3s
- 4.7 On `STORY_COMPLETE`: assembles beat from currentAssets, sets currentBeat, triggers TTS if enabled
- 4.8 On `DRAWING_PROMPT`: starts drawing session with prompt and duration
- 4.9 All subscriptions are cleaned up (unsubscribed) when hook unmounts
- 4.10 Hook is located at `frontend/src/features/session/hooks/useStoryConnection.js`

## Requirement 5: Session Persistence Preservation

### Description
All session persistence behaviors (auto-save, beforeunload beacon, visibilitychange save, session restore) must continue working after the split.

### Acceptance Criteria
- 5.1 Auto-save triggers on `story.history.length` change when `setup.isComplete`
- 5.2 `beforeunload` event sends session snapshot via `navigator.sendBeacon`
- 5.3 `visibilitychange` event saves snapshot when tab goes hidden and setup is complete
- 5.4 Story completion deletes session snapshot for the sibling pair
- 5.5 These effects live in StoryScreen (they only apply when story is active)

## Requirement 6: Accessibility Preservation

### Description
All existing accessibility features must be preserved after the component split.

### Acceptance Criteria
- 6.1 Focus moves to `main` element (via ref) when transitioning from setup to story screen
- 6.2 `aria-hidden` is applied to background content when any modal is open
- 6.3 SkipLink remains the first focusable element in the DOM
- 6.4 Story stage `<main>` has `id="main-content"`, `aria-label="Story experience"`, and `tabIndex={-1}`
- 6.5 Session controls nav has `aria-label="Session controls"`
- 6.6 Mic button has appropriate `aria-label` toggling between "Stop recording" and "Start recording"

## Requirement 7: Build and Compatibility

### Description
The refactored code must build successfully and maintain all existing behavior.

### Acceptance Criteria
- 7.1 `npm run build` from `frontend/` directory completes without errors
- 7.2 No new dependencies are added to `package.json`
- 7.3 All existing CSS classes and styles continue to apply (no CSS changes needed)
- 7.4 All existing imports in other files that reference App.jsx continue to work
