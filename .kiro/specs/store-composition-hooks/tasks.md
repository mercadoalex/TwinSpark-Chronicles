# Tasks: Store Composition Hooks

## Task 1: Create composition hooks module
- [x] 1.1 Create `frontend/src/stores/compositionHooks.js` with `useStorySession` hook that uses individual selectors from sessionStore, storyStore, and audioStore
- [x] 1.2 Add `useChildProfiles` hook with `useMemo`-derived profiles from setupStore
- [x] 1.3 Add `useSessionControls` hook composing sessionStore, parentControlsStore, and siblingStore
- [x] 1.4 Add `useDrawingSession` hook composing drawingStore with `remainingTime` → `timeRemaining` mapping
- [x] 1.5 Add `useMediaCapture` hook composing multimodalStore and sceneAudioStore with `currentEmotions` → `lastEmotion` mapping

## Task 2: Update barrel exports
- [x] 2.1 Add composition hooks re-exports to `frontend/src/stores/index.js`

## Task 3: Unit tests for composition hooks
- [x] 3.1 Create `frontend/src/stores/__tests__/compositionHooks.test.js` with tests for `useStorySession` — verify returned shape and value equivalence with store state
- [x] 3.2 Add tests for `useChildProfiles` — verify returned shape, value equivalence, and `profiles` memoization stability
- [x] 3.3 Add tests for `useSessionControls` — verify returned shape and value equivalence with 3 stores
- [x] 3.4 Add tests for `useDrawingSession` — verify returned shape and `remainingTime` → `timeRemaining` mapping
- [x] 3.5 Add tests for `useMediaCapture` — verify returned shape and `currentEmotions` → `lastEmotion` mapping
- [x] 3.6 Add selector isolation tests — verify unrelated store field changes do NOT trigger re-renders

## Task 4: Build verification
- [x] 4.1 Run `npm run build` from `frontend/` and verify no errors
