# Requirements: Store Composition Hooks

## Requirement 1: Composition Hook Implementations

### 1.1 useStorySession hook
Create `useStorySession()` that composes sessionStore + storyStore + audioStore using individual field selectors. Returns `{ currentBeat, isGenerating, connected, connectionState, ttsEnabled, language }`.

**Acceptance Criteria:**
- Hook returns an object with exactly 6 fields
- `currentBeat` reads from `storyStore.currentBeat`
- `isGenerating` reads from `storyStore.isGenerating`
- `connected` reads from `sessionStore.isConnected`
- `connectionState` reads from `sessionStore.connectionState`
- `ttsEnabled` reads from `audioStore.ttsEnabled`
- `language` reads from `audioStore.ttsLanguage`
- Each field uses an individual selector (`s => s.field`), not a multi-field selector

### 1.2 useChildProfiles hook
Create `useChildProfiles()` that composes setupStore for profile access. Returns `{ child1, child2, profiles, language, isComplete }`.

**Acceptance Criteria:**
- Hook returns an object with exactly 5 fields
- `child1` reads from `setupStore.child1`
- `child2` reads from `setupStore.child2`
- `language` reads from `setupStore.language`
- `isComplete` reads from `setupStore.isComplete`
- `profiles` is derived via `useMemo` calling `setupStore.getState().getProfiles()` with dependencies `[child1, child2, language]`
- `profiles` returns the same object reference across renders when dependencies have not changed

### 1.3 useSessionControls hook
Create `useSessionControls()` that composes sessionStore + parentControlsStore + siblingStore. Returns `{ sessionId, connected, reconnecting, siblingScore, sessionSummary, timeLimitMinutes }`.

**Acceptance Criteria:**
- Hook returns an object with exactly 6 fields
- `sessionId` reads from `sessionStore.sessionId`
- `connected` reads from `sessionStore.isConnected`
- `reconnecting` reads from `sessionStore.isReconnecting`
- `siblingScore` reads from `siblingStore.siblingDynamicsScore`
- `sessionSummary` reads from `siblingStore.sessionSummary`
- `timeLimitMinutes` reads from `parentControlsStore.sessionTimeLimitMinutes`

### 1.4 useDrawingSession hook
Create `useDrawingSession()` that composes drawingStore. Returns `{ isActive, prompt, timeRemaining, strokes }`.

**Acceptance Criteria:**
- Hook returns an object with exactly 4 fields
- `isActive` reads from `drawingStore.isActive`
- `prompt` reads from `drawingStore.prompt`
- `timeRemaining` reads from `drawingStore.remainingTime`
- `strokes` reads from `drawingStore.strokes`

### 1.5 useMediaCapture hook
Create `useMediaCapture()` that composes multimodalStore + sceneAudioStore. Returns `{ audioUnlocked, cameraActive, lastEmotion }`.

**Acceptance Criteria:**
- Hook returns an object with exactly 3 fields
- `audioUnlocked` reads from `sceneAudioStore.audioUnlocked`
- `cameraActive` reads from `multimodalStore.cameraActive`
- `lastEmotion` reads from `multimodalStore.currentEmotions`

## Requirement 2: Selector Isolation and Re-render Prevention

### 2.1 Individual field selectors
Each composition hook must use individual field selectors (`useStore(s => s.field)`) rather than multi-field object selectors, so Zustand's built-in `Object.is` comparison prevents re-renders when unrelated fields change.

**Acceptance Criteria:**
- Changing `sessionStore.error` does NOT trigger a re-render in a component using `useStorySession()`
- Changing `sessionStore.reconnectAttempts` does NOT trigger a re-render in a component using `useStorySession()`
- Changing `setupStore.currentStep` does NOT trigger a re-render in a component using `useChildProfiles()`
- Changing `drawingStore.selectedColor` does NOT trigger a re-render in a component using `useDrawingSession()`
- Changing `multimodalStore.micActive` does NOT trigger a re-render in a component using `useMediaCapture()`

## Requirement 3: Module Structure and Exports

### 3.1 Single module file
All 5 composition hooks are defined in a single file at `frontend/src/stores/compositionHooks.js`.

**Acceptance Criteria:**
- File exists at `frontend/src/stores/compositionHooks.js`
- All 5 hooks are named exports: `useStorySession`, `useChildProfiles`, `useSessionControls`, `useDrawingSession`, `useMediaCapture`
- File imports only from existing store modules and React

### 3.2 Barrel export update
The stores barrel export (`frontend/src/stores/index.js`) re-exports all 5 composition hooks.

**Acceptance Criteria:**
- `frontend/src/stores/index.js` includes `export { useStorySession, useChildProfiles, useSessionControls, useDrawingSession, useMediaCapture } from './compositionHooks'`

## Requirement 4: Additive Refactor Constraints

### 4.1 No store modifications
No existing store file is modified. All 15 store files remain byte-identical.

**Acceptance Criteria:**
- `sessionStore.js`, `storyStore.js`, `audioStore.js`, `setupStore.js`, `siblingStore.js`, `parentControlsStore.js`, `drawingStore.js`, `multimodalStore.js`, `sceneAudioStore.js` are not modified
- All remaining store files are not modified

### 4.2 No new dependencies
No new npm packages are added to `package.json`.

**Acceptance Criteria:**
- `frontend/package.json` dependencies and devDependencies are unchanged

### 4.3 Build verification
The project builds successfully with the new hooks added.

**Acceptance Criteria:**
- `npm run build` from `frontend/` directory completes without errors
