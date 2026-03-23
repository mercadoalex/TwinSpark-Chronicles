# Tasks: Wizard State Reducer

## Task 1: Create wizardReducer.js with initial state and action types
> Requirement(s): 1.1, 1.2, 1.3, 2.4

- [x] 1.1 Create `frontend/src/features/setup/reducers/wizardReducer.js` with `initialState` containing all 11 state fields and 12 formData fields
- [x] 1.2 Export `STEP_ORDER` array and `ActionTypes` object with all 14 action type constants
- [x] 1.3 Implement `wizardReducer` function skeleton with default case returning state unchanged

## Task 2: Implement step navigation and transition actions
> Requirement(s): 3.1, 3.2, 3.3, 6.6

- [x] 2.1 Implement `GO_TO_STEP` case — compute transition direction from step index comparison, set `wizardStep` and `transitionClass`
- [x] 2.2 Implement `SET_TRANSITION` case — set `transitionClass` to `action.className`

## Task 3: Implement form field and error actions
> Requirement(s): 4.1, 4.2, 4.3, 4.4

- [x] 3.1 Implement `SET_FIELD` case — update `formData[action.field]`, set `bounceCard`, clear `nameError` only when field matches `${prefix}name`
- [x] 3.2 Implement `SET_NAME_ERROR` and `SET_TOY_ERROR` cases

## Task 4: Implement character selection actions
> Requirement(s): 5.1, 5.2, 5.3, 5.4

- [x] 4.1 Implement `PICK_GENDER` case — set gender field using prefix, set `bounceCard` and `showSparkle: true`
- [x] 4.2 Implement `PICK_SPIRIT` case — set spirit_animal field using prefix, set `bounceCard` and `showSparkle: true`
- [x] 4.3 Implement `PICK_PRESET_TOY` case — set toy_type to `'preset'`, toy_image to value, clear toy photo state and error
- [x] 4.4 Implement `SET_TOY_PHOTO` case — set toy_type to `'photo'`, clear toy_image, set preview and file

## Task 5: Implement child transition and UI state actions
> Requirement(s): 6.1, 6.2, 6.3, 6.4, 6.5

- [x] 5.1 Implement `NEXT_CHILD` case — set `childNum: 2`, `wizardStep: 'name'`, `transitionClass: 'animation-fade-in'`, clear toy photo state
- [x] 5.2 Implement `CLEAR_BOUNCE`, `SHOW_SPARKLE`, `HIDE_SPARKLE`, `SET_PHOTO_REFRESH` cases

## Task 6: Refactor CharacterSetup.jsx to use useReducer
> Requirement(s): 7.1, 7.2, 7.3, 7.4

- [x] 6.1 Replace all `useState` calls with `useReducer(wizardReducer, initialState)` and destructure state
- [x] 6.2 Replace `set()` helper and all `setX()` calls with appropriate `dispatch()` calls
- [x] 6.3 Update `handleNameSubmit`, `handleGenderPick`, `handleSpiritPick`, `handleToyNext` to use dispatch
- [x] 6.4 Update toy step handlers (`handlePresetPick`, `handleToyPhoto`, `handleToyNextClick`) to use dispatch
- [x] 6.5 Update `goToStep` helper and photo refresh callback to use dispatch
- [x] 6.6 Verify refs (`nameRef`, `stepHeadingRef`, `toyFileRef`) and `useEffect` hooks remain unchanged

## Task 7: Write unit tests for wizardReducer
> Requirement(s): 2.1, 2.2, 2.3, 2.4, 3.1, 3.2, 5.1, 5.2, 6.1

- [x] 7.1 Create `frontend/src/features/setup/reducers/__tests__/wizardReducer.test.js`
- [x] 7.2 Test `GO_TO_STEP` forward produces `animation-slide-in-right`, backward produces `animation-slide-in-left`
- [x] 7.3 Test `PICK_GENDER` and `PICK_SPIRIT` set correct prefixed fields and enable sparkle
- [x] 7.4 Test `PICK_PRESET_TOY` and `SET_TOY_PHOTO` set correct toy fields and clear errors
- [x] 7.5 Test `NEXT_CHILD` resets to child 2, name step, fade-in, clears toy photo state
- [x] 7.6 Test `SET_FIELD` for name field clears `nameError`; non-name field does not
- [x] 7.7 Test unknown action returns same state reference
- [x] 7.8 Test immutability — deep-freeze state before dispatch, verify no mutation

## Task 8: Write property-based tests for wizardReducer (optional)
> Requirement(s): 2.1, 2.2, 2.3

- [ ] *8.1 Install fast-check as dev dependency if not present
- [ ] *8.2 Create `frontend/src/features/setup/reducers/__tests__/wizardReducer.property.test.js`
- [ ] *8.3 Property: for any sequence of valid actions, `wizardStep` is always in `STEP_ORDER`
- [ ] *8.4 Property: for any sequence of valid actions, `childNum` is always 1 or 2
- [ ] *8.5 Property: reducer never mutates input state (deep-freeze + arbitrary action sequences)

## Task 9: Build verification
> Requirement(s): 7.5

- [x] 9.1 Run `npm run build` from `frontend/` directory and verify zero errors
