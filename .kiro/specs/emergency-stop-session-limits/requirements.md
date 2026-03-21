# Requirements Document

## Introduction

Twin Spark Chronicles currently has a frontend-only session timer and a bare-bones emergency stop button. For 6-year-old twins Ale and Sofi, abruptly killing a story session is jarring — and the backend has zero awareness of time limits, meaning a clever browser hack or stale tab can bypass them entirely. This spec hardens session time enforcement on the server, adds graceful wind-down and goodbye experiences that feel magical rather than punitive, makes the emergency stop safe from accidental taps, tracks real session duration, lets parents extend time mid-session, and ensures the timer is fair by pausing during AI generation. The goal: safety and parental control that still feels like part of the adventure.

## Glossary

- **Session_Timer**: The frontend countdown component (`SessionTimer.jsx`) that displays remaining session time and triggers wrap-up events.
- **Session_Time_Enforcer**: The backend module that tracks elapsed session time per active WebSocket connection and rejects content generation requests when the time limit has been exceeded.
- **Emergency_Stop**: The frontend component (`EmergencyStop.jsx`) that provides a fixed-position button to immediately end a session.
- **Emergency_Stop_Endpoint**: The backend POST `/api/emergency-stop/{session_id}` route that cancels all in-flight tasks via the Orchestrator.
- **Orchestrator**: The backend agent (`orchestrator.py`) that manages story generation pipelines and tracks asyncio tasks per session.
- **Session_Persistence_Store**: The frontend Zustand store (`sessionPersistenceStore.js`) that assembles and saves/loads session snapshots.
- **Parent_Controls_Store**: The frontend Zustand store (`parentControlsStore.js`) that persists parent preferences including `sessionTimeLimitMinutes`.
- **WebSocket_Service**: The frontend singleton (`websocketService.js`) that manages the WebSocket connection, reconnection, and message routing.
- **Wind_Down_Screen**: A child-friendly animated overlay that plays when a session is ending, providing a gentle narrative conclusion and goodbye.
- **Confirmation_Gate**: A two-step UI interaction required before the Emergency_Stop action executes, preventing accidental activation by young children.
- **Time_Extension**: A parent-initiated action that adds additional minutes to an active session's time limit.
- **Generation_Pause**: A state during which the Session_Timer countdown is suspended because the backend is actively generating content (AI inference in progress).

## Requirements

### Requirement 1: Backend Session Time Enforcement

**User Story:** As a parent, I want the server to enforce session time limits so that my children cannot bypass the timer by refreshing the browser or manipulating the frontend.

#### Acceptance Criteria

1. WHEN a WebSocket session is established, THE Session_Time_Enforcer SHALL record the session start timestamp and the configured time limit (received from the frontend as a connection parameter) on the server.
2. WHEN the Orchestrator receives a content generation request for a session, THE Session_Time_Enforcer SHALL verify that the elapsed session time has not exceeded the configured time limit before allowing generation to proceed.
3. IF the elapsed session time exceeds the configured time limit and a content generation request is received, THEN THE Session_Time_Enforcer SHALL reject the request and send a `SESSION_TIME_EXPIRED` message over the WebSocket connection.
4. WHEN the elapsed session time reaches the configured time limit, THE Session_Time_Enforcer SHALL send a `TIME_LIMIT_REACHED` message over the WebSocket connection to notify the frontend.
5. THE Session_Time_Enforcer SHALL track elapsed time using server-side wall-clock time, independent of any frontend timer state.
6. WHEN a Time_Extension is granted, THE Session_Time_Enforcer SHALL update the stored time limit for the active session to reflect the additional minutes.

### Requirement 2: Session Duration Tracking

**User Story:** As a parent, I want accurate session duration recorded for each story session so that I can understand how much time my children spend in the app.

#### Acceptance Criteria

1. WHEN a WebSocket session is established, THE Session_Time_Enforcer SHALL begin tracking the session duration in seconds using the server-side clock.
2. WHEN a session ends (via time expiry, emergency stop, or normal completion), THE Session_Time_Enforcer SHALL compute the total duration as the difference between the session end timestamp and the session start timestamp.
3. WHEN a session snapshot is saved, THE Session_Persistence_Store SHALL include the computed `session_duration_seconds` value in the `session_metadata` field.
4. THE Session_Time_Enforcer SHALL update the `session_duration_seconds` field in the session snapshot at save time, replacing the current hardcoded value of 0.
5. WHEN a session is restored from a snapshot, THE Session_Time_Enforcer SHALL resume duration tracking from the previously recorded `session_duration_seconds` value rather than resetting to zero.

### Requirement 3: Graceful Session Wind-Down

**User Story:** As a 6-year-old child, I want the story to end with a magical goodbye instead of suddenly disappearing so that I feel happy about the adventure even when time is up.

#### Acceptance Criteria

1. WHEN the Session_Timer reaches 5 minutes remaining, THE Session_Timer SHALL send a `WRAP_UP` message via the WebSocket_Service to signal the Orchestrator to begin concluding the current story arc.
2. WHEN the Orchestrator receives a `WRAP_UP` message, THE Orchestrator SHALL instruct the Storyteller_Agent to generate a concluding story beat that wraps up the current narrative thread within the next 1-2 story beats.
3. WHEN the Session_Timer reaches zero, THE Wind_Down_Screen SHALL appear as a full-screen animated overlay displaying a child-friendly goodbye message with the children's character names and a summary of the adventure.
4. THE Wind_Down_Screen SHALL display a star-trail animation and a gentle fade-to-dark transition lasting 8 seconds before navigating to the landing screen.
5. WHILE the Wind_Down_Screen is active, THE Wind_Down_Screen SHALL prevent all story interaction controls (choice buttons, text input) from being accessible.
6. THE Wind_Down_Screen SHALL be implemented using CSS animations and the existing CelebrationOverlay pattern, without introducing new animation library dependencies.

### Requirement 4: Emergency Stop Confirmation Gate

**User Story:** As a parent, I want the emergency stop to require a confirmation step so that my 6-year-old children cannot accidentally end their story session by tapping the button.

#### Acceptance Criteria

1. WHEN a user taps the Emergency_Stop button, THE Confirmation_Gate SHALL display a slide-to-confirm interaction (swipe gesture or press-and-hold for 2 seconds) instead of immediately triggering the stop action.
2. WHILE the Confirmation_Gate is displayed, THE Emergency_Stop SHALL show a clear visual instruction using an animated arrow or pulsing indicator (no text-heavy instructions, suitable for pre-readers).
3. IF the user releases the Confirmation_Gate interaction before the 2-second hold threshold, THEN THE Emergency_Stop SHALL cancel the stop action and reset the Confirmation_Gate to its initial state.
4. WHEN the Confirmation_Gate interaction is completed (2-second hold fulfilled), THE Emergency_Stop SHALL proceed with the stop sequence.
5. THE Confirmation_Gate SHALL be implemented using CSS transitions and touch/pointer events, without introducing new gesture library dependencies.

### Requirement 5: Emergency Stop with Snapshot Save and Gentle Exit

**User Story:** As a parent, I want the emergency stop to save the current session before ending it and show a gentle goodbye so that story progress is preserved and my children are not startled.

#### Acceptance Criteria

1. WHEN the Emergency_Stop action is confirmed via the Confirmation_Gate, THE Session_Persistence_Store SHALL save a session snapshot before the Emergency_Stop_Endpoint is called.
2. WHEN the snapshot save completes (or fails after one retry), THE Emergency_Stop SHALL call the Emergency_Stop_Endpoint to cancel all in-flight backend tasks.
3. IF the snapshot save fails after one retry, THEN THE Emergency_Stop SHALL proceed with the stop action and save the snapshot to localStorage as a fallback.
4. WHEN the Emergency_Stop_Endpoint responds (or after a 3-second timeout), THE Wind_Down_Screen SHALL appear with a shortened goodbye animation lasting 4 seconds before navigating to the landing screen.
5. THE Emergency_Stop SHALL complete the full sequence (snapshot save, API call, goodbye animation, navigation) within 10 seconds of the Confirmation_Gate being fulfilled.
6. WHEN the Emergency_Stop is activated, THE Orchestrator.cancel_session method SHALL wait for any in-progress snapshot save to complete (up to 2 seconds) before cancelling asyncio tasks.

### Requirement 6: Parent Time Extension

**User Story:** As a parent, I want to add more time to an active session without interrupting the story so that I can let my children continue playing when they are deeply engaged.

#### Acceptance Criteria

1. WHILE a story session is active, THE Parent_Controls_Store SHALL provide a "Add Time" action accessible from the Parent Controls panel.
2. WHEN a parent selects the "Add Time" action, THE Parent Controls panel SHALL present options to add 10, 15, or 30 additional minutes to the current session.
3. WHEN a time extension is selected, THE Parent_Controls_Store SHALL send a `TIME_EXTENSION` message via the WebSocket_Service containing the additional minutes value.
4. WHEN the Session_Time_Enforcer receives a `TIME_EXTENSION` message, THE Session_Time_Enforcer SHALL add the specified minutes to the session's configured time limit.
5. WHEN a time extension is applied, THE Session_Timer SHALL increase the `secondsLeft` countdown by the extended amount and reset any active warning state if the new remaining time exceeds the warning threshold.
6. THE Session_Timer SHALL display a brief sparkle animation on the timer display when a time extension is applied, providing visual feedback to the children that more time has been added.

### Requirement 7: Timer Fairness — Pause During AI Generation

**User Story:** As a child, I want the session timer to pause while the app is thinking so that I get the full play time my parents set for me.

#### Acceptance Criteria

1. WHEN the Orchestrator begins generating content for a session (story beat, image, or audio), THE Orchestrator SHALL send a `GENERATION_STARTED` message over the WebSocket connection.
2. WHEN the Orchestrator completes or fails content generation for a session, THE Orchestrator SHALL send a `GENERATION_COMPLETED` message over the WebSocket connection.
3. WHEN the Session_Timer receives a `GENERATION_STARTED` message, THE Session_Timer SHALL pause the countdown and enter the Generation_Pause state.
4. WHEN the Session_Timer receives a `GENERATION_COMPLETED` message, THE Session_Timer SHALL resume the countdown from the paused value.
5. WHILE in the Generation_Pause state, THE Session_Timer SHALL display a distinct visual indicator (pulsing opacity on the timer) to show that the timer is paused.
6. IF no `GENERATION_COMPLETED` message is received within 60 seconds of a `GENERATION_STARTED` message, THEN THE Session_Timer SHALL automatically resume the countdown to prevent indefinite pausing.
7. THE Session_Time_Enforcer SHALL exclude Generation_Pause durations from the elapsed time calculation when checking whether the session time limit has been exceeded.

### Requirement 8: Parent Notification on Session End

**User Story:** As a parent, I want to be notified when my children's session ends due to a time limit so that I know the app did its job even if I am not watching the screen.

#### Acceptance Criteria

1. WHEN a session ends due to the time limit being reached, THE Session_Timer SHALL trigger a browser notification (via the Notifications API) with the message "Story time is over — Ale and Sofi's adventure has ended" (using the actual children's names from the session profiles).
2. IF the browser Notifications API permission has not been granted, THEN THE Session_Timer SHALL skip the browser notification without displaying an error.
3. WHEN a session ends due to the time limit, THE Session_Timer SHALL store a `session_ended` event with the end reason ("time_limit") and timestamp in localStorage for the parent to review in the Parent Controls panel.
4. WHEN a parent opens the Parent Controls panel, THE Parent Controls panel SHALL display the most recent session end event (reason and timestamp) if one exists.
