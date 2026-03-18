# Implementation Plan: Session Resumption

## Overview

Build the session persistence layer bottom-up: database migration → Pydantic models → SessionService → API endpoints → frontend sessionPersistenceStore → ContinueScreen UI → auto-save/restore wiring into App.jsx and existing stores. Each task builds on the previous, with property tests alongside implementation.

## Tasks

- [x] 1. Database schema and data models
  - [x] 1.1 Create database migration `backend/app/db/migrations/003_session_snapshots.sql`
    - Create `session_snapshots` table with columns: id (TEXT PRIMARY KEY), sibling_pair_id (TEXT NOT NULL), character_profiles (TEXT NOT NULL), story_history (TEXT NOT NULL), current_beat (TEXT), session_metadata (TEXT NOT NULL), created_at (TEXT NOT NULL), updated_at (TEXT NOT NULL)
    - Create unique index `idx_session_snapshots_pair` on `sibling_pair_id`
    - Use `IF NOT EXISTS` for idempotency
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [x] 1.2 Create Pydantic models in `backend/app/models/session.py`
    - Define `SessionSnapshotPayload` (sibling_pair_id, character_profiles, story_history, current_beat optional, session_metadata)
    - Define `SessionSnapshotResponse` (all payload fields + id, created_at, updated_at)
    - Define `SessionSaveResult` (id, updated_at)
    - _Requirements: 1.1, 1.2, 5.1, 5.2, 5.4, 5.6_

- [x] 2. SessionService backend implementation
  - [x] 2.1 Implement `SessionService` in `backend/app/services/session_service.py`
    - Follow the `WorldDB` pattern: constructor takes `DatabaseConnection`, all methods async
    - Implement `save_snapshot(snapshot: dict) -> dict` — upsert via INSERT ... ON CONFLICT UPDATE, return `{id, updated_at}`
    - Implement `load_snapshot(sibling_pair_id: str) -> dict | None` — SELECT by sibling_pair_id, parse JSON columns, return None if not found
    - Implement `delete_snapshot(sibling_pair_id: str) -> bool` — DELETE by sibling_pair_id, return True if row deleted
    - Implement `cleanup_stale(max_age_days: int = 30) -> int` — DELETE where updated_at older than threshold, return count
    - Handle corrupted JSON gracefully: catch `json.JSONDecodeError`, log, delete corrupt row, return None
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 8.1, 8.2, 8.3, 8.4_

  - [ ]* 2.2 Write property test for save/load round-trip
    - **Property 1: Save/Load Round-Trip**
    - Generate random valid snapshots with Hypothesis (arbitrary character profiles, 0–50 story beats, optional current beat, valid metadata), save then load, assert deep equality on all JSON fields
    - **Validates: Requirements 1.1, 1.2, 5.1, 5.2, 5.4, 5.8**

  - [ ]* 2.3 Write property test for upsert invariant
    - **Property 2: Upsert Preserves One Snapshot Per Pair**
    - Generate N≥2 snapshots for the same sibling_pair_id, save all sequentially, load once, assert result matches last saved snapshot and exactly one DB row exists
    - **Validates: Requirements 1.3, 1.4, 6.3**

  - [ ]* 2.4 Write property test for delete then load
    - **Property 4: Delete Then Load Returns Nothing**
    - Generate snapshot, save, delete, load, assert None returned
    - **Validates: Requirements 5.3**

  - [ ]* 2.5 Write property test for stale cleanup precision
    - **Property 8: Stale Session Cleanup Precision**
    - Generate snapshots with varying updated_at timestamps (1–60 days ago), run cleanup_stale(30), assert exactly those older than 30 days are deleted
    - **Validates: Requirements 8.2**

- [x] 3. FastAPI session endpoints
  - [x] 3.1 Add session API routes to `backend/app/main.py`
    - `POST /api/session/save` — accept `SessionSnapshotPayload`, call `SessionService.save_snapshot`, return `SessionSaveResult` (200) or validation error (422) or server error (500)
    - `GET /api/session/load/{sibling_pair_id}` — call `SessionService.load_snapshot`, return `SessionSnapshotResponse` (200) or 404
    - `DELETE /api/session/{sibling_pair_id}` — call `SessionService.delete_snapshot`, return `{deleted: true}` (200) or 404
    - Initialize `SessionService` with existing `DatabaseConnection` and run stale cleanup as background task on startup
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 8.4_

  - [ ]* 3.2 Write property test for invalid payload rejection
    - **Property 5: Invalid Payload Rejection**
    - Generate JSON payloads with random required fields removed, POST to save endpoint, assert 422 returned and database unchanged
    - **Validates: Requirements 5.6**

  - [ ]* 3.3 Write unit tests for session API endpoints
    - Test save with all fields → 200 with id and updated_at
    - Test load non-existent pair → 404
    - Test save with missing sibling_pair_id → 422
    - Test save with empty story_history → success
    - Test delete existing → 200
    - Test delete non-existent → 404
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 3.4 Write property test for migration idempotency
    - **Property 7: Migration Idempotency**
    - Run migration on fresh DB, insert data, run migration again, assert no error and data preserved
    - **Validates: Requirements 6.4**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Frontend sessionPersistenceStore
  - [x] 5.1 Create `frontend/src/stores/sessionPersistenceStore.js`
    - Implement Zustand store with state: `saveStatus` ('idle'|'saving'|'saved'|'error'), `availableSession` (null or snapshot), `isRestoring` (bool), `lastSaveError` (null or string)
    - Implement `saveSnapshot()` — read state from setupStore, storyStore, sessionStore; derive sibling_pair_id as sorted names joined by ':'; POST to `/api/session/save`; track saveStatus transitions (idle→saving→saved or idle→saving→error)
    - Implement `loadSnapshot(siblingPairId)` — GET from `/api/session/load/{siblingPairId}`; set availableSession on success; fall back to localStorage on 404
    - Implement `restoreSession()` — hydrate setupStore (isComplete=true, currentStep='complete'), storyStore (history, currentBeat), sessionStore (profiles, sessionId) from availableSession
    - Implement `deleteSession(siblingPairId)` — DELETE via API
    - Implement `saveToLocalStorage()` / `restoreFromLocalStorage()` — fallback persistence
    - Implement `syncLocalToServer()` — push localStorage snapshot to server on reconnect
    - On save failure: retry once after 2s delay; if retry fails, fall back to localStorage and set saveStatus to 'error'
    - _Requirements: 2.1, 2.4, 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 7.1, 7.2, 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

  - [ ]* 5.2 Write property test for save status state machine
    - **Property 3: Save Status State Machine**
    - Mock API success/failure with fast-check booleans, trigger save, record status transitions, assert valid sequence (idle→saving→saved or idle→saving→error)
    - **Validates: Requirements 2.7**

  - [ ]* 5.3 Write property test for frontend store round-trip
    - **Property 10: Frontend Store Round-Trip**
    - Generate random setupStore, storyStore, sessionStore states with fast-check; serialize to snapshot, restore, assert deep equality across all three stores
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.6**

- [x] 6. ContinueScreen UI component
  - [x] 6.1 Create `frontend/src/features/session/components/ContinueScreen.jsx`
    - Display last scene image from story_history as visual preview background
    - Display sibling names and spirit animal icons from character_profiles
    - Display friendly greeting: "Welcome back, {name1} & {name2}"
    - Large animated "Continue Story" button with sparkle/glow CSS effect
    - Secondary "New Adventure" button with confirmation prompt before deleting existing session
    - Play welcoming sound effect on mount via audioFeedbackService
    - Minimal text, visual-first design for 6-year-olds
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_

  - [ ]* 6.2 Write property test for ContinueScreen preview rendering
    - **Property 6: Continue Screen Displays Snapshot Preview Data**
    - Generate random profiles (c1_name, c2_name, c1_spirit, c2_spirit) and story_history with fast-check; render component; assert both names, spirit references, last scene image, and greeting are present in output
    - **Validates: Requirements 4.1, 4.2, 4.8**

  - [ ]* 6.3 Write unit tests for ContinueScreen
    - Test "Continue Story" button renders when session available
    - Test "New Adventure" shows confirmation dialog before delete
    - Test welcome sound plays on mount
    - Test greeting contains both sibling names
    - _Requirements: 4.3, 4.4, 4.5, 4.7_

- [x] 7. Auto-save and interrupted session handling wiring
  - [x] 7.1 Wire auto-save triggers into `frontend/src/App.jsx`
    - On story beat completion → trigger `sessionPersistenceStore.saveSnapshot()` (non-blocking)
    - On Exit Modal save → trigger `saveSnapshot()` before WebSocket disconnect
    - On `beforeunload` → use `navigator.sendBeacon('/api/session/save', payload)` for fire-and-forget save
    - On `visibilitychange` (hidden) → trigger `saveSnapshot()`
    - On WebSocket disconnect → trigger `saveToLocalStorage()` immediately
    - On WebSocket reconnect → trigger `syncLocalToServer()`
    - Display child-friendly warning icon (no text) when both server and localStorage saves fail
    - _Requirements: 2.1, 2.2, 2.3, 2.6, 7.1, 7.2, 7.3, 7.4, 7.5_

  - [x] 7.2 Wire session load and restore into app startup flow
    - On app start (after privacy + language), check for existing session via `loadSnapshot(siblingPairId)`
    - If session found, show ContinueScreen on landing screen
    - On "Continue Story" tap, call `restoreSession()` → skip character setup → proceed to story experience
    - On corrupted/unparseable snapshot, discard, log error, show normal setup flow
    - If localStorage fallback exists and no server snapshot, restore from localStorage and sync to server
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] 8. Session cleanup integration
  - [x] 8.1 Wire session deletion into story lifecycle
    - On "New Adventure" confirmed → delete existing snapshot before starting new session
    - On story natural completion → delete snapshot for the sibling pair
    - Stale cleanup (30-day TTL) runs as background task on backend startup (already wired in task 3.1)
    - _Requirements: 8.1, 8.2, 8.3_

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python, backend) and fast-check (JavaScript, frontend) with minimum 100 examples per property
- Checkpoints ensure incremental validation
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- Frontend builds: `npm run build` from `frontend/`
