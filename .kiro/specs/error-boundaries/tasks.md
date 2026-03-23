# Tasks: Error Boundaries

## Task 1: Create the reusable ErrorBoundary class component
- [x] 1.1 Create `frontend/src/shared/components/ErrorBoundary/ErrorBoundary.jsx` — class component with `getDerivedStateFromError`, `componentDidCatch`, `resetErrorBoundary`, and `componentDidUpdate` for resetKeys auto-reset [[1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10]]
- [x] 1.2 Create `frontend/src/shared/components/ErrorBoundary/ErrorBoundary.css` — CSS-only styling for fallback UIs with variant theming (story=purple, drawing=green, setup=gold), large emoji sizing, colorful buttons, gentle animations [[2.1, 2.5]]
- [x] 1.3 Create `frontend/src/shared/components/ErrorBoundary/FallbackUI.jsx` — functional component rendering emoji, message, and action button with variant CSS classes [[2.1, 2.2, 2.3, 2.4, 2.5]]
- [x] 1.4 Create `frontend/src/shared/components/ErrorBoundary/index.js` — barrel export for ErrorBoundary, FallbackUI, and domain wrappers
- [x] 1.5 Update `frontend/src/shared/components/index.js` — add ErrorBoundary exports to shared components barrel

## Task 2: Create domain-specific error boundary wrappers
- [x] 2.1 Add `StoryErrorBoundary` to `frontend/src/shared/components/ErrorBoundary/StoryErrorBoundary.jsx` — wraps story components with "Oops! The story got lost 📖" fallback and retry button [[3.1, 3.2]]
- [x] 2.2 Add `DrawingErrorBoundary` to `frontend/src/shared/components/ErrorBoundary/DrawingErrorBoundary.jsx` — wraps DrawingCanvas with "The crayons need a break 🖍️" fallback and retry button [[3.3, 3.4]]
- [x] 2.3 Add `CameraErrorBoundary` to `frontend/src/shared/components/ErrorBoundary/CameraErrorBoundary.jsx` — wraps camera components with `fallback={null}` for silent hide, still logs errors [[3.5, 3.6]]
- [x] 2.4 Add `SetupErrorBoundary` to `frontend/src/shared/components/ErrorBoundary/SetupErrorBoundary.jsx` — wraps CharacterSetup with "Let's start over! 🌟" fallback and reset button that calls onReset [[3.7, 3.8]]

## Task 3: Integrate error boundaries into App.jsx
- [x] 3.1 Wrap `CharacterSetup` in `SetupErrorBoundary` with `onReset={() => setup.reset()}` in `frontend/src/App.jsx` [[3.7, 3.8, 4.3]]
- [x] 3.2 Wrap `TransitionEngine` (story display section) in `StoryErrorBoundary` in `frontend/src/App.jsx` [[3.1, 3.2, 4.3]]
- [x] 3.3 Wrap `CameraPreview` and `MultimodalFeedback` in `CameraErrorBoundary` in `frontend/src/App.jsx` [[3.5, 3.6, 4.3]]
- [x] 3.4 Wrap `DrawingCanvas` in `DrawingErrorBoundary` in `frontend/src/App.jsx` [[3.3, 3.4, 4.3]]

## Task 4: Testing
- [x] 4.1 Create `frontend/src/shared/components/ErrorBoundary/__tests__/ErrorBoundary.test.jsx` — unit tests for core ErrorBoundary: error catching renders fallback, normal render passes through, static and function fallbacks, onError callback, console logging, reset clears state, onReset callback, resetKeys auto-reset, resetKeys no-op when not errored [[1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 1.10]]
- [x] 4.2 Create `frontend/src/shared/components/ErrorBoundary/__tests__/FallbackUI.test.jsx` — unit tests for FallbackUI: emoji rendering, message text, button with label and emoji, onAction callback, variant CSS classes [[2.1, 2.2, 2.3, 2.4, 2.5]]
- [x] 4.3 Create `frontend/src/shared/components/ErrorBoundary/__tests__/DomainBoundaries.test.jsx` — unit tests for domain wrappers: StoryErrorBoundary fallback content, DrawingErrorBoundary fallback content, CameraErrorBoundary silent hide, SetupErrorBoundary fallback and onReset, error isolation between sibling boundaries [[3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 4.1, 4.2]]
- [*] 4.4 Create `frontend/src/shared/components/ErrorBoundary/__tests__/ErrorBoundary.property.test.jsx` — property-based tests with fast-check: boundary state consistency under random error/reset/resetKey sequences [[1.7, 1.9, 1.10]]
