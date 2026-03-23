# Requirements: Error Boundaries

## Requirement 1: Reusable ErrorBoundary Class Component

### Acceptance Criteria

1.1. Given a child component that throws during render, when the ErrorBoundary catches the error, then it renders the fallback UI instead of the children.

1.2. Given a child component that renders without errors, when the ErrorBoundary wraps it, then the children render normally with no visual or behavioral difference.

1.3. Given a static ReactNode passed as the `fallback` prop, when an error is caught, then that ReactNode is rendered as the fallback.

1.4. Given a render function passed as the `fallback` prop, when an error is caught, then the function is called with `(error, resetFn)` and its return value is rendered.

1.5. Given an `onError` callback prop, when an error is caught, then `onError` is called with the Error object and React errorInfo (including componentStack).

1.6. Given any error caught by the boundary, when `componentDidCatch` fires, then the error and component stack are logged to `console.error`.

1.7. Given the boundary is in error state, when `resetErrorBoundary()` is called (e.g., via retry button), then `hasError` becomes false and children are re-rendered.

1.8. Given an `onReset` callback prop, when the boundary resets (manual or auto), then `onReset` is called.

1.9. Given a `resetKeys` array prop, when the boundary is in error state and any value in `resetKeys` changes between renders, then the boundary auto-resets without user interaction.

1.10. Given a `resetKeys` array prop, when the boundary is NOT in error state and `resetKeys` values change, then nothing happens and children continue rendering normally.

## Requirement 2: Child-Friendly FallbackUI Component

### Acceptance Criteria

2.1. Given a FallbackUI is rendered, then it displays a large emoji (minimum 64px) as the primary visual element so non-reading children can understand the state.

2.2. Given a FallbackUI with a `message` prop, then the message text is displayed in a large, friendly font below the emoji.

2.3. Given a FallbackUI with `buttonLabel` and optional `buttonEmoji` props, then a colorful action button is rendered with the label and emoji.

2.4. Given a user clicks the action button, then the `onAction` callback is invoked.

2.5. Given a `variant` prop (story | drawing | setup | default), then the FallbackUI applies variant-specific color theming via CSS classes (purple for story, green for drawing, gold for setup).

## Requirement 3: Domain-Specific Error Boundary Wrappers

### Acceptance Criteria

3.1. Given the StoryErrorBoundary wraps story components, when a render error occurs, then it displays "Oops! The story got lost" with a 📖 emoji and a retry button.

3.2. Given the StoryErrorBoundary is showing its fallback, when the user clicks the retry button, then the story components are re-rendered.

3.3. Given the DrawingErrorBoundary wraps the DrawingCanvas, when a render error occurs, then it displays "The crayons need a break" with a 🖍️ emoji and a retry button.

3.4. Given the DrawingErrorBoundary is showing its fallback, when the user clicks the retry button, then the DrawingCanvas is re-rendered.

3.5. Given the CameraErrorBoundary wraps CameraPreview and MultimodalFeedback, when a render error occurs, then it renders nothing (null) — the camera UI silently disappears.

3.6. Given the CameraErrorBoundary catches an error, then the error is still logged to console with the component stack even though no fallback UI is shown.

3.7. Given the SetupErrorBoundary wraps CharacterSetup, when a render error occurs, then it displays "Let's start over!" with a 🌟 emoji and a reset button.

3.8. Given the SetupErrorBoundary is showing its fallback, when the user clicks the reset button, then `onReset` is called (to reset setup state) and the boundary clears its error state.

## Requirement 4: Error Isolation and Non-Regression

### Acceptance Criteria

4.1. Given multiple error boundaries in the component tree, when one boundary catches an error, then sibling boundaries and their children continue to render and function normally.

4.2. Given an error is caught by any domain boundary, then the root App component does not crash and non-errored sections remain interactive.

4.3. Given error boundaries are added around existing feature components, when no errors occur, then all existing functionality works identically to before the boundaries were added.
