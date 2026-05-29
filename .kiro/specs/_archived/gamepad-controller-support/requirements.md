# Requirements Document

## Introduction

Twin Spark Chronicles is a touch-first interactive storytelling app for 6-year-old twin siblings (Ale & Sofi). This feature adds gamepad/controller support as an additional input method alongside existing keyboard, mouse, and touch inputs. The implementation uses the browser Gamepad API (`navigator.getGamepads()`) and targets standard HID gamepads (SNES-style USB controllers, 8BitDo, generic USB gamepads). The gamepad enables spatial D-pad navigation between focusable UI elements, A/B button confirm/cancel, and an on-screen virtual keyboard for text entry — making the app fully playable from the couch without a keyboard.

## Glossary

- **Gamepad_Manager**: The singleton module responsible for detecting gamepad connections, polling gamepad state via `requestAnimationFrame`, and dispatching normalized input events to the Focus_Navigator
- **Focus_Navigator**: The module that maintains a spatial map of focusable UI elements and moves a visible focus cursor between them in response to D-pad directional inputs
- **Gamepad_Cursor**: The visible highlight ring rendered around the currently focused UI element when a gamepad is connected, distinct from the browser's native `:focus-visible` outline
- **Virtual_Keyboard**: An on-screen letter picker overlay displayed when a text input field receives gamepad focus, allowing character-by-character name entry via D-pad navigation and A-button selection
- **Focusable_Element**: Any interactive UI element (buttons, cards, inputs, links) that the Focus_Navigator can target, identified by CSS selectors matching `.btn-magic`, `.wizard-card`, `.dp-bubble`, `.drawing-tool-btn`, and similar interactive classes
- **Connection_Indicator**: A small non-intrusive icon displayed when a gamepad is connected, confirming to the user that controller input is active
- **D-pad**: The directional pad on a standard gamepad, mapped to `axes[0]` and `axes[1]` or buttons 12-15 in the standard gamepad mapping
- **A_Button**: Button index 0 in the standard gamepad mapping, used for select/confirm actions (equivalent to Enter/tap)
- **B_Button**: Button index 1 in the standard gamepad mapping, used for back/cancel actions (equivalent to Escape)
- **Start_Button**: Button index 9 in the standard gamepad mapping, used to open the parent controls overlay

## Requirements

### Requirement 1: Gamepad Connection Detection

**User Story:** As a parent, I want the app to automatically detect when a USB gamepad is plugged in, so that my children can start using the controller without any configuration.

#### Acceptance Criteria

1. WHEN a gamepad is connected via the `gamepadconnected` browser event, THE Gamepad_Manager SHALL register the gamepad and begin polling its state via `requestAnimationFrame`
2. WHEN a gamepad is disconnected via the `gamepaddisconnected` browser event, THE Gamepad_Manager SHALL stop polling for that gamepad and remove it from the active gamepad registry
3. WHEN a gamepad is connected, THE Connection_Indicator SHALL display a controller icon in a fixed screen position within 500ms of the connection event
4. WHEN a gamepad is disconnected, THE Connection_Indicator SHALL hide the controller icon within 500ms of the disconnection event
5. WHILE no gamepad is connected, THE Gamepad_Manager SHALL not run any polling loop or consume requestAnimationFrame cycles
6. IF the browser does not support the Gamepad API, THEN THE Gamepad_Manager SHALL silently degrade without errors and without affecting existing input methods

### Requirement 2: Gamepad Input Polling

**User Story:** As a child using a controller, I want my button presses and D-pad movements to be recognized reliably, so that I can navigate the app without frustration.

#### Acceptance Criteria

1. WHILE a gamepad is connected, THE Gamepad_Manager SHALL poll gamepad state once per `requestAnimationFrame` cycle using `navigator.getGamepads()`
2. THE Gamepad_Manager SHALL normalize D-pad input by reading both `axes[0]`/`axes[1]` (analog) and buttons 12-15 (digital D-pad) from the standard gamepad mapping
3. WHEN a D-pad direction is first pressed (axis value exceeds a deadzone threshold of 0.5 or digital button pressed), THE Gamepad_Manager SHALL emit a single directional event immediately
4. WHILE a D-pad direction is held continuously beyond 400ms, THE Gamepad_Manager SHALL emit repeated directional events at a rate of one event every 150ms
5. WHEN the A_Button transitions from released to pressed, THE Gamepad_Manager SHALL emit a single confirm event
6. WHEN the B_Button transitions from released to pressed, THE Gamepad_Manager SHALL emit a single cancel event
7. WHEN the Start_Button transitions from released to pressed, THE Gamepad_Manager SHALL emit a single menu event
8. THE Gamepad_Manager SHALL track previous frame button states to detect press-edge transitions and prevent repeated firing on held buttons (except D-pad repeat as specified in criterion 4)

### Requirement 3: Spatial Focus Navigation

**User Story:** As a 6-year-old child, I want to move a visible highlight between buttons and cards using the D-pad, so that I can pick story choices and navigate the wizard without reading text.

#### Acceptance Criteria

1. WHEN a directional event is received from the Gamepad_Manager, THE Focus_Navigator SHALL move focus to the nearest Focusable_Element in the pressed direction (up, down, left, right) relative to the currently focused element's screen position
2. THE Focus_Navigator SHALL calculate the nearest element using the geometric center of each Focusable_Element's bounding rectangle and selecting the closest element within a 120-degree cone in the pressed direction
3. WHEN no Focusable_Element exists in the pressed direction, THE Focus_Navigator SHALL keep focus on the current element without wrapping
4. WHEN the set of visible Focusable_Elements changes (screen transition, modal open/close, wizard step change), THE Focus_Navigator SHALL rebuild its spatial map and set initial focus to the first logical Focusable_Element on the new screen
5. THE Focus_Navigator SHALL identify Focusable_Elements by querying the DOM for elements matching the selectors: `button:not([disabled])`, `[role="button"]:not([disabled])`, `a[href]`, `input:not([disabled])`, `select:not([disabled])`, `.wizard-card`, `.dp-bubble:not([disabled])`, and `[data-gamepad-focusable]`
6. WHEN a Focusable_Element receives gamepad focus, THE Focus_Navigator SHALL call the native `.focus()` method on that element so that existing keyboard and screen reader focus behavior is preserved

### Requirement 4: Gamepad Cursor Visual Highlight

**User Story:** As a 6-year-old child, I want to see a bright glowing ring around the button I'm pointing at with the controller, so that I know which one I'm about to pick.

#### Acceptance Criteria

1. WHILE a gamepad is connected and a Focusable_Element has gamepad focus, THE Gamepad_Cursor SHALL render a visible highlight ring around the focused element using a CSS class `gamepad-focus`
2. THE Gamepad_Cursor highlight SHALL use a 3px solid ring with color `var(--color-gold)` and a glow box-shadow of `0 0 20px rgba(251, 191, 36, 0.5)` to be clearly visible against the dark app background
3. WHEN focus moves from one element to another, THE Gamepad_Cursor SHALL remove the `gamepad-focus` class from the previous element and add it to the new element within the same animation frame
4. THE Gamepad_Cursor SHALL include a subtle pulsing animation (opacity oscillation between 0.7 and 1.0 over 1.5 seconds) to draw the child's attention to the focused element
5. WHILE no gamepad is connected, THE Gamepad_Cursor highlight SHALL not appear on any element, preserving the existing touch/mouse/keyboard focus styles
6. WHEN the user prefers reduced motion (`prefers-reduced-motion: reduce`), THE Gamepad_Cursor SHALL display the highlight ring without the pulsing animation

### Requirement 5: Confirm and Cancel Actions

**User Story:** As a child using a controller, I want to press the A button to pick a choice and the B button to go back, so that I can play the story without needing a keyboard.

#### Acceptance Criteria

1. WHEN a confirm event is received from the Gamepad_Manager, THE Focus_Navigator SHALL trigger a `click` event on the currently focused Focusable_Element
2. WHEN a cancel event is received from the Gamepad_Manager while a modal or overlay is open (exit modal, parent controls, world map, gallery), THE Focus_Navigator SHALL trigger the modal's close/back action
3. WHEN a cancel event is received while on the Character Setup wizard gender or spirit step, THE Focus_Navigator SHALL navigate back to the previous wizard step
4. WHEN a cancel event is received on a screen with no back action available (language selection, name step for child 1), THE Focus_Navigator SHALL take no action
5. WHEN a menu event is received from the Gamepad_Manager, THE Focus_Navigator SHALL toggle the parent controls overlay open or closed
6. THE Focus_Navigator SHALL not interfere with existing keyboard Enter and Escape key handlers — both input paths SHALL coexist

### Requirement 6: Character Setup Wizard Gamepad Navigation

**User Story:** As a parent setting up the app with a controller, I want to navigate through the character wizard (name, gender, spirit animal, photos) using the gamepad, so that my kids can help pick their characters from the couch.

#### Acceptance Criteria

1. WHEN the name step is displayed and a gamepad is connected, THE Focus_Navigator SHALL set initial focus on the name text input field
2. WHEN the name input receives gamepad confirm (A_Button), THE Virtual_Keyboard SHALL open to allow character-by-character text entry
3. WHEN the gender step is displayed, THE Focus_Navigator SHALL set initial focus on the first gender card and allow D-pad left/right navigation between the three gender cards
4. WHEN the spirit animal step is displayed, THE Focus_Navigator SHALL set initial focus on the first spirit animal card and allow D-pad navigation across the 3-column grid of six spirit cards
5. WHEN the photos step is displayed, THE Focus_Navigator SHALL set initial focus on the primary action button (Skip or Go)
6. WHEN a wizard card receives a confirm event, THE Focus_Navigator SHALL trigger the card's click handler identically to a touch tap

### Requirement 7: Virtual Keyboard for Text Entry

**User Story:** As a 6-year-old child using a controller, I want to pick letters from an on-screen keyboard to type my name, so that I don't need a real keyboard.

#### Acceptance Criteria

1. WHEN a text input field receives a confirm event via gamepad while the Virtual_Keyboard is not open, THE Virtual_Keyboard SHALL display an on-screen letter grid overlay
2. THE Virtual_Keyboard SHALL display uppercase letters A-Z arranged in a grid, plus a backspace key, a space key, and a done/confirm key
3. WHEN D-pad directional events are received while the Virtual_Keyboard is open, THE Focus_Navigator SHALL move the highlight between letter keys in the grid spatially
4. WHEN the A_Button is pressed on a letter key, THE Virtual_Keyboard SHALL append that letter to the associated text input field's value
5. WHEN the A_Button is pressed on the backspace key, THE Virtual_Keyboard SHALL remove the last character from the associated text input field's value
6. WHEN the A_Button is pressed on the done key, THE Virtual_Keyboard SHALL close and return focus to the text input field
7. WHEN the B_Button is pressed while the Virtual_Keyboard is open, THE Virtual_Keyboard SHALL close without additional changes and return focus to the text input field
8. THE Virtual_Keyboard SHALL display the current input value above the letter grid so the child can see what has been typed
9. THE Virtual_Keyboard letter keys SHALL have a minimum touch target size of 48px to remain consistent with the app's child-friendly design

### Requirement 8: Story Experience Gamepad Navigation

**User Story:** As a child playing the story with a controller, I want to pick story choices and press the voice button using the D-pad and A button, so that I can play the whole adventure with just the gamepad.

#### Acceptance Criteria

1. WHEN a story beat is displayed with choice buttons, THE Focus_Navigator SHALL set initial focus on the first choice button
2. WHEN the DualPrompt component is displayed, THE Focus_Navigator SHALL include the child response bubbles (`.dp-bubble`) in the focusable element set
3. WHEN the voice recording button is displayed, THE Focus_Navigator SHALL include the voice button in the focusable element set and allow D-pad navigation to reach it
4. WHEN a confirm event is received on a story choice button, THE Focus_Navigator SHALL trigger the choice selection handler identically to a touch tap
5. WHILE story content is generating (loading state), THE Focus_Navigator SHALL disable confirm events on choice buttons to prevent duplicate submissions

### Requirement 9: Drawing Canvas Gamepad Navigation

**User Story:** As a child in a drawing session, I want to use the controller to pick colors and tools, so that I can draw without switching to touch for the toolbar.

#### Acceptance Criteria

1. WHILE a drawing session is active, THE Focus_Navigator SHALL include the drawing toolbar buttons (color picker, brush size, tool selector, stamp selector) in the focusable element set
2. WHEN D-pad navigation moves focus to a toolbar button and the A_Button is pressed, THE Focus_Navigator SHALL trigger the toolbar button's click handler
3. WHEN the B_Button is pressed during a drawing session, THE Focus_Navigator SHALL trigger the "We're Done!" action to end the drawing session
4. THE Focus_Navigator SHALL not intercept D-pad events while the canvas element itself has pointer focus (to avoid interfering with future D-pad drawing controls)

### Requirement 10: Modal and Overlay Gamepad Navigation

**User Story:** As a parent, I want to navigate modals and overlays (exit confirmation, parent controls, gallery) using the gamepad, so that I can manage the app without switching to mouse.

#### Acceptance Criteria

1. WHEN a modal or overlay opens, THE Focus_Navigator SHALL trap gamepad focus within the modal's Focusable_Elements until the modal is closed
2. WHEN a modal opens, THE Focus_Navigator SHALL set initial focus on the modal's primary action button or first Focusable_Element
3. WHEN the B_Button is pressed while a modal is open, THE Focus_Navigator SHALL trigger the modal's dismiss/cancel action
4. WHEN a modal closes, THE Focus_Navigator SHALL restore gamepad focus to the element that was focused before the modal opened

### Requirement 11: Coexistence with Existing Input Methods

**User Story:** As a parent, I want keyboard, mouse, and touch input to continue working exactly as before when a gamepad is connected, so that adding a controller doesn't break anything.

#### Acceptance Criteria

1. THE Gamepad_Manager SHALL operate as an additive input layer that does not modify, intercept, or disable any existing keyboard, mouse, or touch event handlers
2. WHEN a keyboard or mouse event occurs while a gamepad is connected, THE Focus_Navigator SHALL defer to the browser's native focus management for that interaction
3. WHEN a touch or mouse click occurs on a Focusable_Element while the Gamepad_Cursor is visible on a different element, THE Focus_Navigator SHALL update the gamepad focus position to match the touched element
4. THE Gamepad_Manager SHALL not add any global event listeners that call `preventDefault()` or `stopPropagation()` on keyboard, mouse, or touch events

### Requirement 12: Accessibility and Reduced Motion

**User Story:** As a parent of a child with motion sensitivity, I want the gamepad cursor animations to respect reduced motion preferences, so that the controller feature is comfortable for all children.

#### Acceptance Criteria

1. WHEN the user has `prefers-reduced-motion: reduce` enabled, THE Gamepad_Cursor SHALL display the highlight ring as a static border without pulsing animation
2. THE Connection_Indicator SHALL include an `aria-live="polite"` announcement when a gamepad connects or disconnects, stating "Controller connected" or "Controller disconnected"
3. THE Virtual_Keyboard SHALL be announced to screen readers via `aria-label` on the overlay container and `role="grid"` on the letter grid
4. THE Gamepad_Cursor focus changes SHALL be reflected in the DOM focus state so that screen readers announce the newly focused element
