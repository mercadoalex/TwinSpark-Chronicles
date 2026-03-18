# Implementation Plan: Content Safety System

## Overview

Implement a multi-layered content safety system for Twin Spark Chronicles. The plan starts with the backend content filter service and blocklist, integrates filtering into the orchestrator pipeline, hardens the Gemini safety settings, adds the emergency stop endpoint, then builds the frontend parent controls, session timer, and emergency stop components. Each backend task is followed by its tests; frontend components are wired in at the end.

## Tasks

- [x] 1. Create ContentFilter service and blocklist
  - [x] 1.1 Create the blocklist configuration file at `backend/app/config/blocklist.json`
    - Include `version`, `keywords`, and `phrases` arrays as defined in the design
    - _Requirements: 3.1, 3.3_

  - [x] 1.2 Implement `ContentFilter` class in `backend/app/services/content_filter.py`
    - Load blocklist from JSON file in `__init__`; fall back to hardcoded minimal blocklist if file is missing/malformed
    - Implement `scan(text, allowed_themes, custom_blocked_words)` returning a `FilterResult`
    - Scanning order: blocklist + custom words (case-insensitive) → BLOCKED; disallowed themes → REVIEW; otherwise → SAFE
    - Implement `reload_blocklist()` for hot-reload
    - Define `ContentRating` enum, `FilterResult` dataclass, and `ContentFilterLog` dataclass
    - Log every scan result with session ID, rating, reason, and text snippet
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5, 7.3, 8.4_

  - [ ]* 1.3 Write property tests for ContentFilter (`backend/tests/test_content_filter_properties.py`)
    - **Property 1: Filter rating completeness** — for any string input, `scan()` returns a `FilterResult` with rating in {SAFE, REVIEW, BLOCKED}
    - **Validates: Requirements 2.2, 4.1**

  - [ ]* 1.4 Write property test: blocklist case-insensitive detection
    - **Property 2: Blocklist detection is case-insensitive and includes custom words** — for any blocklist/custom word in any case variation embedded in text, `scan()` returns BLOCKED
    - **Validates: Requirements 3.2, 3.4, 4.2, 7.3**

  - [ ]* 1.5 Write property test: disallowed theme triggers REVIEW
    - **Property 3: Disallowed theme triggers REVIEW** — text with a theme keyword not in `allowed_themes` and no blocklist matches returns REVIEW
    - **Validates: Requirements 4.3**

  - [ ]* 1.6 Write property test: clean text is rated SAFE
    - **Property 4: Clean text is rated SAFE** — text with no blocklist matches and no disallowed themes returns SAFE
    - **Validates: Requirements 4.4**

  - [ ]* 1.7 Write property test: filter performance bound
    - **Property 7: Content filter performance bound** — for any text up to 10,000 chars, `scan()` completes within 500ms
    - **Validates: Requirements 8.4**

  - [ ]* 1.8 Write unit tests for ContentFilter (`backend/tests/test_content_filter.py`)
    - Test blocklist loading from JSON file
    - Test empty text input returns SAFE
    - Test exact blocklist word returns BLOCKED
    - Test blocklist phrase returns BLOCKED
    - Test theme check with no `allowed_themes` config skips theme check
    - Test logging of filter results with session ID
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.4, 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 2. Checkpoint — Ensure all content filter tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Harden Gemini safety settings in StorytellerAgent
  - [x] 3.1 Update safety settings in `backend/app/agents/storyteller_agent.py`
    - Change all four harm category thresholds to `BLOCK_LOW_AND_ABOVE`
    - Catch blocked-response exceptions from Gemini and return `_fallback_story()` instead of raising
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 3.2 Write unit tests for storyteller safety (`backend/tests/test_storyteller_safety.py`)
    - Verify safety settings are `BLOCK_LOW_AND_ABOVE` for all 4 categories
    - Verify blocked Gemini response returns fallback story, not an exception
    - _Requirements: 1.1, 1.2, 1.3_

- [x] 4. Integrate ContentFilter into AgentOrchestrator pipeline
  - [x] 4.1 Add content filtering to `backend/app/agents/orchestrator.py`
    - Instantiate `ContentFilter` in `__init__`
    - Add `_generate_safe_story_segment` method with retry logic (max 3 retries)
    - Call `_generate_safe_story_segment` in `generate_rich_story_moment` between story generation (Step 2) and image/voice generation (Step 3)
    - Also filter story choices and perspective text through `ContentFilter`
    - On `ContentFilter` exception, log error and return `_fallback_story()` (never deliver unfiltered content)
    - After 3 failed retries, return `_fallback_story()`
    - Accept `allowed_themes`, `complexity_level`, and `custom_blocked_words` from request and pass to filter
    - _Requirements: 2.1, 2.3, 2.4, 2.5, 8.1, 8.2, 8.3_

  - [x] 4.2 Extend `StoryRequest` model in `backend/app/main.py`
    - Add optional fields: `allowed_themes`, `complexity_level`, `custom_blocked_words`
    - Pass these fields through to the orchestrator in `generate_rich_story` and WebSocket handler
    - _Requirements: 7.1, 7.2, 7.3_

  - [ ]* 4.3 Write unit tests for orchestrator content filtering (`backend/tests/test_content_filter.py`)
    - Test retry logic: mock filter to return BLOCKED 3 times, verify fallback is used
    - Test ContentFilter unavailable: mock filter to raise exception, verify fallback
    - _Requirements: 2.4, 2.5, 8.3_

- [x] 5. Add emergency stop endpoint
  - [x] 5.1 Implement `cancel_session` in `AgentOrchestrator` (`backend/app/agents/orchestrator.py`)
    - Cancel all in-flight asyncio tasks for the given session
    - Return session state summary
    - _Requirements: 6.2, 6.5_

  - [x] 5.2 Add `POST /api/emergency-stop/{session_id}` endpoint in `backend/app/main.py`
    - Call `orchestrator.cancel_session(session_id)`
    - Return `{ status, session_id, session_saved }` response
    - Return 404 for unknown session
    - _Requirements: 6.2, 6.3, 6.5_

  - [ ]* 5.3 Write unit tests for emergency stop (`backend/tests/test_emergency_stop.py`)
    - Test cancellation of in-flight tasks
    - Test session state is returned
    - Test 404 for unknown session
    - _Requirements: 6.2, 6.3, 6.5_

- [x] 6. Checkpoint — Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Create parentControlsStore
  - [x] 7.1 Create `frontend/src/stores/parentControlsStore.js`
    - Zustand store with `allowedThemes`, `complexityLevel`, `customBlockedWords`, `sessionTimeLimitMinutes`
    - Default values: all themes allowed, `simple` complexity, empty custom words, 30-minute limit
    - Persist to localStorage using Zustand `persist` middleware
    - Actions: `setAllowedThemes`, `setComplexityLevel`, `addBlockedWord`, `removeBlockedWord`, `setSessionTimeLimit`
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 7.2 Write property test: preferences persistence round-trip (`frontend/src/__tests__/parentControls.property.test.js`)
    - **Property 6: Parent preferences persistence round-trip** — serialize to localStorage and deserialize produces equal object
    - **Validates: Requirements 7.5**

- [x] 8. Create ParentControls component
  - [x] 8.1 Create `frontend/src/components/ParentControls.jsx`
    - Settings panel with theme checkboxes, complexity selector, custom blocked words input, session time limit selector (15/30/45/60 min)
    - Read from and write to `parentControlsStore`
    - Changes apply immediately without session restart
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [ ]* 8.2 Write unit tests for ParentControls (`frontend/src/__tests__/ParentControls.test.jsx`)
    - Test theme selection updates store
    - Test complexity level selection
    - Test custom blocked words add/remove
    - Test preferences persist to localStorage
    - Test live update without restart
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 9. Create SessionTimer component
  - [x] 9.1 Create `frontend/src/components/SessionTimer.jsx`
    - Display remaining time in `MM:SS` format with child-friendly icon
    - Read `sessionTimeLimitMinutes` from `parentControlsStore`
    - Default to 30 minutes if not configured
    - Show warning overlay when ≤ 5 minutes remain
    - Trigger wrap-up sequence via WebSocket when time reaches 0; force-navigate to landing screen if no response in 5s
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

  - [ ]* 9.2 Write property test: session time display format (`frontend/src/__tests__/sessionTimer.property.test.js`)
    - **Property 5: Session time display format** — for any non-negative integer of seconds, display function produces `MM:SS` format
    - **Validates: Requirements 5.5**

  - [ ]* 9.3 Write unit tests for SessionTimer (`frontend/src/__tests__/SessionTimer.test.jsx`)
    - Test default timer is 30 minutes
    - Test warning appears at 5 minutes remaining
    - Test wrap-up triggers at 0 minutes
    - Test display for various time values
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 10. Create EmergencyStop component
  - [x] 10.1 Create `frontend/src/components/EmergencyStop.jsx`
    - Fixed-position red button, always visible during active sessions
    - On click: call `POST /api/emergency-stop/{session_id}`, save session state, navigate to safe landing screen within 2 seconds
    - Handle API failure gracefully: still navigate to safe screen, retry API call once in background
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 10.2 Write unit tests for EmergencyStop (`frontend/src/__tests__/EmergencyStop.test.jsx`)
    - Test button is visible during active session
    - Test click triggers API call and navigation
    - Test handles API failure gracefully
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 11. Wire frontend components into App
  - [x] 11.1 Integrate ParentControls, SessionTimer, and EmergencyStop into `frontend/src/App.jsx`
    - Add ParentControls accessible via a gear/settings icon
    - Render SessionTimer and EmergencyStop during active storytelling sessions
    - Pass parent preferences from `parentControlsStore` with story requests to backend
    - _Requirements: 5.5, 6.1, 7.4, 8.1, 8.2_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirement clauses for traceability
- Property tests use Hypothesis (Python) and fast-check (JavaScript)
- Checkpoints at tasks 2, 6, and 12 ensure incremental validation
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` (from `backend/` directory)
- Frontend build: `npm run build` (from `frontend/` directory)
