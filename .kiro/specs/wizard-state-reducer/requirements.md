# Requirements: Wizard State Reducer

## Overview

Refactor CharacterSetup.jsx from 12+ individual `useState` calls to a single `useReducer` pattern with an extracted pure reducer function, preserving all existing functionality.

## Requirements

### Requirement 1: Extract Reducer to Dedicated File

The wizard reducer function and initial state must be extracted into `frontend/src/features/setup/reducers/wizardReducer.js`.

#### Acceptance Criteria

1.1 Given the reducer file exists at `frontend/src/features/setup/reducers/wizardReducer.js`, it must export `wizardReducer` (function) and `initialState` (object).

1.2 Given `initialState` is exported, it must contain all 11 state fields: `childNum`, `wizardStep`, `formData`, `bounceCard`, `photoRefreshKey`, `transitionClass`, `nameError`, `showSparkle`, `toyPhotoPreview`, `toyPhotoFile`, `toyError`.

1.3 Given `initialState.formData` is accessed, it must contain all 12 form fields: `c1_name`, `c1_gender`, `c1_spirit_animal`, `c1_toy_name`, `c1_toy_type`, `c1_toy_image`, `c2_name`, `c2_gender`, `c2_spirit_animal`, `c2_toy_name`, `c2_toy_type`, `c2_toy_image`.

### Requirement 2: Reducer Purity and Immutability

The reducer must be a pure function that never mutates its input state.

#### Acceptance Criteria

2.1 Given any valid state and action, when `wizardReducer(state, action)` is called, then the input `state` object is never mutated.

2.2 Given the same state and action inputs, when `wizardReducer` is called multiple times, then it always returns the same output.

2.3 Given an action that changes state, when `wizardReducer` returns, then the returned object is a new reference (not the same object as input).

2.4 Given an unknown action type, when `wizardReducer` is called, then it returns the exact same state reference (referential equality).

### Requirement 3: Step Navigation Actions

The reducer must handle step transitions with correct directional animations.

#### Acceptance Criteria

3.1 Given `wizardStep` is `'name'` and a `GO_TO_STEP` action with `step: 'gender'` is dispatched, then `wizardStep` becomes `'gender'` and `transitionClass` becomes `'animation-slide-in-right'`.

3.2 Given `wizardStep` is `'spirit'` and a `GO_TO_STEP` action with `step: 'name'` is dispatched, then `wizardStep` becomes `'name'` and `transitionClass` becomes `'animation-slide-in-left'`.

3.3 Given any `GO_TO_STEP` action, when the target step index is >= current step index, then `transitionClass` is `'animation-slide-in-right'`; otherwise `'animation-slide-in-left'`.

### Requirement 4: Form Field Actions

The reducer must handle setting form fields with appropriate side effects (bounce, error clearing).

#### Acceptance Criteria

4.1 Given a `SET_FIELD` action with `field: 'c1_name'` and `value: 'Luna'`, when dispatched with `childNum: 1`, then `formData.c1_name` becomes `'Luna'`, `bounceCard` becomes `'Luna'`, and `nameError` is cleared to `''`.

4.2 Given a `SET_FIELD` action for a non-name field, when dispatched, then `nameError` is not cleared.

4.3 Given a `SET_NAME_ERROR` action with `error: 'Please enter a name'`, then `nameError` becomes `'Please enter a name'`.

4.4 Given a `SET_TOY_ERROR` action with `error: 'Photo is too big!'`, then `toyError` becomes `'Photo is too big!'`.

### Requirement 5: Character Selection Actions

The reducer must handle gender, spirit, and toy selection with bounce and sparkle effects.

#### Acceptance Criteria

5.1 Given `childNum` is 1 and a `PICK_GENDER` action with `value: 'girl'` is dispatched, then `formData.c1_gender` becomes `'girl'`, `bounceCard` becomes `'girl'`, and `showSparkle` becomes `true`.

5.2 Given `childNum` is 2 and a `PICK_SPIRIT` action with `value: 'dragon'` is dispatched, then `formData.c2_spirit_animal` becomes `'dragon'`, `bounceCard` becomes `'dragon'`, and `showSparkle` becomes `true`.

5.3 Given a `PICK_PRESET_TOY` action with `value: 'teddy'`, then `formData[prefix+'toy_type']` becomes `'preset'`, `formData[prefix+'toy_image']` becomes `'teddy'`, `toyPhotoPreview` becomes `null`, `toyPhotoFile` becomes `null`, and `toyError` becomes `''`.

5.4 Given a `SET_TOY_PHOTO` action with `preview` and `file`, then `formData[prefix+'toy_type']` becomes `'photo'`, `formData[prefix+'toy_image']` becomes `''`, `toyPhotoPreview` is set to `preview`, `toyPhotoFile` is set to `file`, and `toyError` becomes `''`.

### Requirement 6: Child Transition and UI State Actions

The reducer must handle transitioning between children and managing UI animation state.

#### Acceptance Criteria

6.1 Given `childNum` is 1 and a `NEXT_CHILD` action is dispatched, then `childNum` becomes 2, `wizardStep` becomes `'name'`, `transitionClass` becomes `'animation-fade-in'`, `toyPhotoPreview` becomes `null`, `toyPhotoFile` becomes `null`, and `toyError` becomes `''`.

6.2 Given a `CLEAR_BOUNCE` action is dispatched, then `bounceCard` becomes `null`.

6.3 Given a `SHOW_SPARKLE` action is dispatched, then `showSparkle` becomes `true`.

6.4 Given a `HIDE_SPARKLE` action is dispatched, then `showSparkle` becomes `false`.

6.5 Given a `SET_PHOTO_REFRESH` action is dispatched, then `photoRefreshKey` increments by 1.

6.6 Given a `SET_TRANSITION` action with `className: 'animation-fade-in'`, then `transitionClass` becomes `'animation-fade-in'`.

### Requirement 7: Component Integration

CharacterSetup.jsx must use `useReducer` with the extracted reducer, replacing all `useState` calls.

#### Acceptance Criteria

7.1 Given CharacterSetup.jsx is loaded, it must call `useReducer(wizardReducer, initialState)` instead of individual `useState` calls.

7.2 Given the component renders, all existing JSX output, CSS classes, ARIA attributes, and accessibility features must remain identical to the pre-refactor version.

7.3 Given the component uses refs (`nameRef`, `stepHeadingRef`, `toyFileRef`), these must remain as `useRef` calls — not moved into reducer state.

7.4 Given the component has side effects (focus management via `useEffect`, photo loading, timeouts for animations), these must remain in the component — not in the reducer.

7.5 Given the project is built with `npm run build` from the `frontend/` directory, the build must succeed with no errors.
