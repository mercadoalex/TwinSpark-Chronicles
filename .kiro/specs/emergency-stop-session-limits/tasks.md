# Implementation Plan: Emergency Stop & Session Limits

## Overview

Harden session time management by adding backend enforcement via `SessionTimeEnforcer`, enhancing the frontend `SessionTimer` with pause/resume and extension support, adding a press-and-hold confirmation gate to `EmergencyStop`, creating a `WindDownScreen` for graceful goodbyes, and wiring parent time-extension controls. All animations are CSS-only. Backend is Python 3.11, frontend is React/JSX with Zustand stores.

## Tasks

- [x] 1. Implement backend SessionTimeEnforcer
  - [x] 1.1 Create `backend/app/services/session_time_enforcer.py` with `SessionTimeEnforcer` class
    - Implement `_SessionTimeState` dataclass and `TimeCheckResult` dataclass
    - Implement `start_session(session_id, time_limit_minutes)` — records start timestamp via `time.monotonic()` and time limit
    - Implement `check_time(session_id)` — returns `TimeCheckResult` with `is_expired`, `elapsed_seconds` (wall-clock minus pauses), `remaining_seconds`
    - Implement `extend_time(session_id, additional_minutes)` — adds minutes to limit, returns new total
    - Implement `start_generation_pause(session_id)` and `end_generation_pause(session_id)` — tracks pause intervals
    - Implement `get_session_duration(session_id)` — total wall-clock duration
    - Implement `end_session(session_id)` — marks ended, returns duration
    - Implement `resume_session(session_id, previous_duration_seconds)` — resumes from snapshot
    - Implement `remove_session(session_id)` — cleanup
    - Handle missing session_id gracefully (return safe defaults, log warning)
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 2.2, 2.4, 2.5, 7.7_

  - [ ]* 1.2 Write property tests for SessionTimeEnforcer (`backend/tests/test_session_time_enforcer.py`)
    - **Property 1: Session initialization records correct state** — generate random time limits (1–120), verify `time_limit_seconds == minutes * 60`, `total_paused_seconds == 0`, `ended == False`
    - **Validates: Requirements 1.1, 2.1**
    - **Property 2: Time expiry detection is correct** — generate random limits and elapsed times, verify `is_expired` iff `elapsed_seconds >= total_limit_seconds`
    - **Validates: Requirements 1.2, 1.3, 1.4**
    - **Property 3: Time extension increases limit** — generate random limits and extensions, verify new limit equals original + extension * 60
    - **Validates: Requirements 1.6, 6.4**
    - **Property 4: Session duration equals wall-clock minus pauses** — generate random pause intervals, verify duration = (end - start) - total_paused
    - **Validates: Requirements 2.2, 7.7**
    - **Property 5: Duration resume from snapshot is additive** — generate random previous durations, verify reported duration >= previous
    - **Validates: Requirements 2.5**
    - **Property 6: Generation pause exclusion from elapsed time** — generate random pause durations, verify elapsed excludes paused time
    - **Validates: Requirements 7.7**
    - Use Hypothesis with `max_examples=20`


- [x] 2. Integrate SessionTimeEnforcer into backend WebSocket handler and Orchestrator
  - [x] 2.1 Wire SessionTimeEnforcer into WebSocket handler (`backend/app/main.py`)
    - Instantiate a global `SessionTimeEnforcer` instance alongside the orchestrator
    - On WebSocket connection: extract `time_limit_minutes` from query params, call `session_time_enforcer.start_session(session_id, time_limit_minutes)`
    - Handle incoming `TIME_EXTENSION` message: call `extend_time()`, send `TIME_EXTENSION_CONFIRMED` back with `new_limit_minutes` and `added_minutes`
    - Handle incoming `WRAP_UP` message: forward to orchestrator for story conclusion
    - On WebSocket disconnect (`_cleanup_session`): call `session_time_enforcer.end_session()` and `remove_session()`
    - _Requirements: 1.1, 1.6, 6.3, 6.4_

  - [x] 2.2 Add generation pause signals and time checks to Orchestrator (`backend/app/agents/orchestrator.py`)
    - Accept `session_time_enforcer` reference (passed from main.py or injected)
    - In `generate_rich_story_moment`: call `start_generation_pause()` at start, `end_generation_pause()` in `finally` block
    - In `generate_rich_story_moment`: send `GENERATION_STARTED` message over WebSocket at start, `GENERATION_COMPLETED` at end (success or failure)
    - Before generation: call `check_time()` — if expired, send `SESSION_TIME_EXPIRED` over WebSocket and skip generation
    - In `cancel_session`: call `session_time_enforcer.end_session()` before cancelling tasks
    - _Requirements: 1.2, 1.3, 1.4, 5.6, 7.1, 7.2, 7.7_

  - [ ]* 2.3 Write unit tests for WebSocket handler time integration
    - Test `TIME_EXTENSION` message flow: send extension, verify `TIME_EXTENSION_CONFIRMED` response
    - Test `GENERATION_STARTED`/`GENERATION_COMPLETED` messages sent around generation calls
    - Test `SESSION_TIME_EXPIRED` sent when time limit exceeded
    - _Requirements: 1.2, 1.3, 1.6, 7.1, 7.2_

- [x] 3. Enhance frontend SessionTimer with pause, extension, and backend sync
  - [x] 3.1 Add generation pause support to `SessionTimer.jsx`
    - Add `isPaused` state, toggled by `GENERATION_STARTED` / `GENERATION_COMPLETED` WebSocket messages
    - When paused, stop decrementing `secondsLeft`; resume on `GENERATION_COMPLETED`
    - Add 60-second safety timeout: if no `GENERATION_COMPLETED` within 60s, auto-resume
    - Add pulsing opacity CSS class (`session-timer--paused`) to `SessionTimer.css`
    - _Requirements: 7.3, 7.4, 7.5, 7.6_

  - [x] 3.2 Add time extension handling to `SessionTimer.jsx`
    - Listen for `TIME_EXTENSION_CONFIRMED` WebSocket message
    - Increase `secondsLeft` by `added_minutes * 60`
    - Reset warning state if new `secondsLeft > WARNING_THRESHOLD`
    - Add sparkle animation CSS class (`session-timer--sparkle`) to `SessionTimer.css`
    - _Requirements: 6.5, 6.6_

  - [x] 3.3 Add `TIME_LIMIT_REACHED` backend sync to `SessionTimer.jsx`
    - Listen for `TIME_LIMIT_REACHED` WebSocket message from backend
    - Force `secondsLeft` to 0 if not already expired
    - _Requirements: 1.4_

  - [x] 3.4 Add browser notification and session end event logging
    - On session end (time limit): trigger browser Notification with children's names from session profiles
    - If Notifications API not granted, skip silently
    - Store `session_ended` event (`{ reason, timestamp, child_names }`) to localStorage key `twinspark_last_session_end`
    - _Requirements: 8.1, 8.2, 8.3_

  - [ ]* 3.5 Write property tests for SessionTimer logic (frontend, fast-check)
    - **Property 9: Time extension increases timer and conditionally resets warning** — generate random `secondsLeft` and extension amounts, verify new value and warning state
    - **Validates: Requirements 6.5**
    - **Property 12: formatTime produces valid MM:SS strings** — generate random non-negative integers, verify output matches `\d{2}:\d{2}`
    - **Validates: Requirements 2.2**
    - Use fast-check with `numRuns: 100`

- [x] 4. Implement EmergencyStop confirmation gate with press-and-hold
  - [x] 4.1 Replace single-tap with press-and-hold confirmation gate in `EmergencyStop.jsx`
    - Add `holdProgress` state (0–1) and `isHolding` state
    - On `pointerdown`: start 2-second hold timer, animate progress ring via CSS `conic-gradient` transition
    - Show pulsing arrow indicator during hold (CSS animation, no text)
    - On `pointerup`/`pointerleave` before 2s: reset to initial state (progress 0, not holding)
    - On hold complete (2s): trigger stop sequence — save snapshot via `useSessionPersistenceStore`, call emergency stop endpoint, then show WindDownScreen
    - Add 10-second total timeout for the full stop sequence
    - Prevent re-entry while `stopping` is true
    - Update `EmergencyStop.css` with progress ring (`conic-gradient`), pulsing arrow, and hold animation styles
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 5.1, 5.2, 5.3, 5.5_

  - [ ]* 4.2 Write property tests for confirmation gate (frontend, fast-check)
    - **Property 7: Confirmation gate rejects holds shorter than threshold** — generate random durations < 2000ms, verify stop NOT triggered
    - **Validates: Requirements 4.1, 4.3**
    - **Property 8: Confirmation gate accepts holds at or above threshold** — generate random durations >= 2000ms, verify stop IS triggered
    - **Validates: Requirements 4.4**
    - Use fast-check with `numRuns: 100`

- [x] 5. Create WindDownScreen component
  - [x] 5.1 Create `frontend/src/shared/components/WindDownScreen.jsx` and `WindDownScreen.css`
    - Full-screen overlay (z-index above everything)
    - Display goodbye message with children's names and adventure summary
    - Star-trail particle animation reusing CelebrationOverlay's star particle CSS pattern
    - Gentle fade-to-dark: 8 seconds for normal end, 4 seconds for emergency stop (accept `duration` prop)
    - Block all story interaction controls while active
    - Navigate to landing screen after animation completes
    - Respect `prefers-reduced-motion` media query
    - CSS-only animations, no canvas or requestAnimationFrame
    - _Requirements: 3.3, 3.4, 3.5, 3.6, 5.4_

- [x] 6. Add parent time extension controls and session end display
  - [x] 6.1 Enhance `parentControlsStore.js` with time extension and session end tracking
    - Add `sendTimeExtension(minutes)` action that sends `{ type: "TIME_EXTENSION", additional_minutes }` via WebSocketService
    - Add `lastSessionEndEvent` state (loaded from localStorage `twinspark_last_session_end` on init)
    - Add `recordSessionEnd(reason, childNames)` action that writes to localStorage
    - _Requirements: 6.1, 6.3, 8.3_

  - [x] 6.2 Add "Add Time" section and session end display to `ParentControls.jsx`
    - Add "Add Time" section visible only during active session (check WebSocket connection state)
    - Three buttons: +10 min, +15 min, +30 min — each calls `sendTimeExtension()`
    - Display most recent session end event (reason + timestamp) from `lastSessionEndEvent` state
    - Style new section consistent with existing `pc-section` pattern in `ParentControls.css`
    - _Requirements: 6.1, 6.2, 8.4_

  - [ ]* 6.3 Write property test for session end event round-trip (frontend, fast-check)
    - **Property 10: Session end event round-trip to localStorage** — generate random reasons and child name pairs, verify round-trip
    - **Validates: Requirements 8.3**
    - Use fast-check with `numRuns: 100`

- [x] 7. Update session snapshot metadata with real duration
  - [x] 7.1 Update `sessionPersistenceStore.js` to include `session_duration_seconds`
    - In `assembleSnapshot()`: fetch real duration from backend (or accept it as a parameter) instead of hardcoded `0`
    - On restore: pass `previous_duration_seconds` to backend via WebSocket so `SessionTimeEnforcer` can resume tracking
    - _Requirements: 2.3, 2.4, 2.5_

  - [ ]* 7.2 Write property test for snapshot metadata (frontend, fast-check)
    - **Property 11: Snapshot metadata includes session duration** — generate random snapshot states, verify `session_duration_seconds` is a number >= 0
    - **Validates: Requirements 2.3**
    - Use fast-check with `numRuns: 100`

- [x] 8. Wire WindDownScreen into SessionTimer and EmergencyStop flows
  - [x] 8.1 Integrate WindDownScreen into session end flows
    - In `SessionTimer.jsx`: when `secondsLeft` reaches 0, render `WindDownScreen` with 8-second duration and children's names
    - In `EmergencyStop.jsx`: after stop sequence completes, render `WindDownScreen` with 4-second duration
    - Ensure WindDownScreen navigates to landing after animation
    - Pass `time_limit_minutes` as query param when connecting WebSocket in `websocketService.js` (read from `parentControlsStore`)
    - _Requirements: 3.3, 3.4, 5.4_

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (`max_examples=20`) on backend and fast-check (`numRuns: 100`) on frontend
- All animations are CSS-only following the existing CelebrationOverlay pattern
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/` directory, then `pkill -f "python.*pytest"`
- Frontend builds: `npm run build` from `frontend/` directory
