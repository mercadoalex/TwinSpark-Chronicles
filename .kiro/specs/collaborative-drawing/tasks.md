# Implementation Plan: Collaborative Drawing

## Overview

Add a shared HTML5 Canvas drawing experience to Twin Spark Chronicles. Both siblings draw together during story moments with real-time stroke sync over the existing WebSocket connection. Completed drawings are rendered to PNG, persisted, and woven into the AI narrative. Backend is Python 3.11 / FastAPI, frontend is React JSX with Zustand stores. CSS-first animations, no new heavy dependencies. Pillow is used for server-side PNG rendering.

## Tasks

- [x] 1. Create database migration and data models
  - [x] 1.1 Create migration `backend/app/db/migrations/007_collaborative_drawing.sql`
    - Create `drawings` table with columns: `drawing_id TEXT PRIMARY KEY`, `session_id TEXT NOT NULL`, `sibling_pair_id TEXT NOT NULL`, `prompt TEXT NOT NULL`, `stroke_count INTEGER NOT NULL DEFAULT 0`, `duration_seconds INTEGER NOT NULL DEFAULT 0`, `image_path TEXT NOT NULL`, `beat_index INTEGER NOT NULL DEFAULT 0`, `created_at TEXT NOT NULL`
    - Create index `idx_drawings_session` on `session_id`
    - Create index `idx_drawings_pair` on `(sibling_pair_id, created_at DESC)`
    - _Requirements: 4.2, 4.3_

  - [x] 1.2 Create `backend/app/models/drawing.py` with `StrokeMessage` and `DrawingRecord` dataclasses
    - `StrokeMessage`: `session_id`, `sibling_id`, `points` (list of `{x, y}` dicts), `color` (hex string), `brush_size` (int), `timestamp` (ISO 8601), `tool` (default `"brush"`), `stamp_shape` (optional)
    - Define `REQUIRED_FIELDS = {"session_id", "sibling_id", "points", "color", "brush_size", "timestamp"}`
    - `DrawingRecord`: `drawing_id`, `session_id`, `sibling_pair_id`, `prompt`, `stroke_count`, `duration_seconds`, `image_path`, `beat_index`, `created_at`
    - _Requirements: 7.1, 4.2, 4.3_


- [x] 2. Implement DrawingSyncService (backend stroke validation and serialization)
  - [x] 2.1 Create `backend/app/services/drawing_sync_service.py` with `DrawingSyncService` class
    - Implement `validate_stroke(data: dict) -> StrokeMessage | None` — checks all required fields present, `points` is non-empty list of `{x, y}` dicts, `sibling_id` is `"child1"` or `"child2"`, `color` is valid hex string, `brush_size` is positive int. Returns `None` on failure without raising exceptions
    - Implement `serialize_stroke(stroke: StrokeMessage) -> str` — converts to JSON string
    - Implement `deserialize_stroke(json_str: str) -> StrokeMessage | None` — parses JSON, validates, returns `None` on failure
    - Implement `clamp_duration(requested: int, remaining_session_time: int | None = None) -> int` — clamps duration to [30, 120] range, further clamps to remaining session time if provided
    - Implement `get_default_color(sibling_id: str) -> str` — returns distinct default colors for child1 vs child2
    - _Requirements: 2.5, 7.1, 7.2, 7.4, 1.5, 3.2, 9.3_

  - [ ]* 2.2 Write property tests for DrawingSyncService (`backend/tests/test_drawing_properties.py`)
    - **Property 1: Distinct default colors per sibling** — verify `get_default_color("child1") != get_default_color("child2")`
    - **Validates: Requirements 1.5**
    - **Property 4: Stroke validation rejects incomplete data** — generate stroke dicts with random missing required fields or empty points, verify `validate_stroke` returns `None`
    - **Validates: Requirements 2.5, 7.4**
    - **Property 5: Drawing duration clamped to valid range** — generate random ints, verify result is in [30, 120]
    - **Validates: Requirements 3.2**
    - **Property 7: Stroke serialization round-trip** — generate valid StrokeMessage objects, verify `serialize(deserialize(serialize(s))) == serialize(s)`
    - **Validates: Requirements 7.1, 7.2, 7.3**
    - **Property 13: Palette colors meet contrast ratio against canvas background** — verify all palette colors have >= 3.0:1 contrast ratio against `#FFFFFF`
    - **Validates: Requirements 8.3**
    - **Property 15: Drawing duration reduced to fit remaining session time** — generate random remaining times R and durations D where R < D, verify result == R
    - **Validates: Requirements 9.3**
    - Use Hypothesis with `max_examples=20`

  - [ ]* 2.3 Write unit tests for DrawingSyncService (`backend/tests/test_drawing_sync_service.py`)
    - Test validate well-formed stroke returns StrokeMessage
    - Test reject stroke missing `session_id`
    - Test reject stroke with empty `points` array
    - Test reject stroke with invalid `sibling_id` (not child1/child2)
    - Test `clamp_duration` with values below 30, above 120, and within range
    - _Requirements: 2.5, 7.1, 7.4, 3.2_

- [x] 3. Implement DrawingPersistenceService (backend PNG rendering and DB storage)
  - [x] 3.1 Create `backend/app/services/drawing_persistence_service.py` with `DrawingPersistenceService` class
    - Constructor accepts `DatabaseConnection` instance
    - Implement `render_composite(strokes: list[dict], width: int, height: int) -> bytes` — uses Pillow to render strokes onto a white canvas, scales normalized [0.0, 1.0] coordinates to pixel dimensions, draws lines for brush strokes, fills background-color lines for eraser strokes, returns PNG bytes
    - Implement `async save_drawing(session_id, sibling_pair_id, strokes, prompt, duration_seconds, beat_index) -> DrawingRecord` — calls `render_composite`, saves PNG to `assets/generated_images/drawing_{unix_timestamp}.png`, inserts metadata row into `drawings` table, returns `DrawingRecord`. On render failure: logs warning, saves record with `image_path=""`
    - Implement `async get_drawing(drawing_id) -> DrawingRecord | None`
    - Implement `async get_drawings_for_session(session_id) -> list[DrawingRecord]`
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 3.2 Write property tests for DrawingPersistenceService (`backend/tests/test_drawing_properties.py`)
    - **Property 8: Render produces valid PNG for any strokes** — generate non-empty lists of valid strokes with normalized coordinates, verify output starts with PNG magic bytes `\x89PNG\r\n\x1a\n`
    - **Validates: Requirements 4.1**
    - **Property 9: Persistence stores all required metadata with correct filename** — generate drawing records, verify non-empty fields and `image_path` matches `assets/generated_images/drawing_\d+\.png`
    - **Validates: Requirements 4.2, 4.3**
    - Use Hypothesis with `max_examples=20`

  - [ ]* 3.3 Write unit tests for DrawingPersistenceService (`backend/tests/test_drawing_persistence_service.py`)
    - Test render composite with zero strokes returns minimal valid PNG
    - Test save drawing writes file to correct path pattern
    - Test save drawing inserts correct metadata into DB
    - Test render failure logs warning and returns record with empty `image_path`
    - _Requirements: 4.1, 4.2, 4.4_


- [x] 4. Integrate drawing messages into WebSocket handler and Orchestrator
  - [x] 4.1 Add drawing message routing to WebSocket handler (`backend/app/main.py`)
    - Import `DrawingSyncService` and instantiate alongside existing services
    - Handle incoming `DRAWING_STROKE` message: validate via `DrawingSyncService.validate_stroke()`, broadcast to same session via `manager.send_story()` as `DRAWING_STROKE` type
    - Handle incoming `DRAWING_COMPLETE` message: create task to persist drawing via `DrawingPersistenceService.save_drawing()`, send `DRAWING_END` with `reason: "manual"` to session
    - Handle incoming `DRAWING_EARLY_END` message: send `DRAWING_END` with `reason: "manual"` to session
    - Add `send_drawing_prompt` helper: sends `DRAWING_PROMPT` message with `prompt`, `duration`, `session_id` to client
    - _Requirements: 2.1, 2.2, 2.5, 3.5, 7.4_

  - [x] 4.2 Add drawing prompt injection to Orchestrator (`backend/app/agents/orchestrator.py`)
    - In `_do_generate_rich_story_moment`: after story segment generation, check if `story_segment` contains a `drawing_prompt` field
    - If present: compute effective duration via `DrawingSyncService.clamp_duration()` using remaining session time from `session_time_enforcer.check_time()`
    - Send `DRAWING_PROMPT` message via `ws_manager.send_story()` with prompt text and clamped duration
    - Add `drawing_context` to next story beat generation when a drawing was just completed (prompt text + sibling names)
    - If session time expires during drawing: send `DRAWING_END` with `reason: "session_expired"`
    - _Requirements: 5.1, 5.2, 5.3, 9.1, 9.2, 9.3_

- [x] 5. Create frontend drawingStore (Zustand)
  - [x] 5.1 Create `frontend/src/stores/drawingStore.js`
    - State: `isActive`, `prompt`, `duration`, `remainingTime`, `strokes` (all local + remote), `undoStacks: { child1: [], child2: [] }`, `selectedColor`, `selectedBrushSize` (`"medium"`), `selectedTool` (`"brush"`), `selectedStamp` (null), `syncQueue` (array), `syncStatus` (`"connected"`)
    - Define `PALETTE_COLORS` array with 8 child-friendly colors meeting 3:1 contrast ratio against white
    - Define `BRUSH_SIZES` object: `{ thin: 2, medium: 4, thick: 8 }`
    - Define `STAMP_SHAPES`: `["star", "heart", "circle", "lightning"]`
    - Define `DEFAULT_COLORS`: `{ child1: "<color1>", child2: "<color2>" }` — distinct per sibling
    - Actions: `startSession(prompt, duration)`, `endSession()`, `addStroke(stroke)`, `addRemoteStroke(stroke)`, `undoLastStroke(siblingId)` — removes last stroke by that sibling only (no-op if empty), `setColor(color)`, `setBrushSize(size)`, `setTool(tool)`, `setStamp(stamp)`, `queueStroke(stroke)`, `flushSyncQueue()`, `tick()` — decrements `remainingTime`, auto-ends session at 0, `reset()`
    - _Requirements: 1.3, 1.4, 1.5, 3.2, 6.1, 6.2, 6.4, 6.5, 8.4_

  - [ ]* 5.2 Write property tests for drawingStore (`frontend/src/features/drawing/__tests__/drawing.property.test.js`)
    - **Property 2: Remote stroke preserves attributes** — generate random strokes, add as remote, verify color and brush_size unchanged
    - **Validates: Requirements 2.3**
    - **Property 3: Queue-and-replay preserves stroke order** — generate random stroke sequences, queue them, flush, verify same order
    - **Validates: Requirements 2.4**
    - **Property 6: Session ends when timer expires** — start session, tick to 0, verify `isActive` is false
    - **Validates: Requirements 3.4**
    - **Property 10: Undo removes exactly the last stroke of the active sibling** — generate interleaved strokes, undo for one sibling, verify count reduced by 1 and correct stroke removed
    - **Validates: Requirements 6.1, 6.2**
    - **Property 11: Eraser strokes use canvas background color** — generate strokes with eraser tool, verify color is `#FFFFFF`
    - **Validates: Requirements 6.3**
    - **Property 12: Undo isolation between siblings** — generate interleaved strokes, undo for child1, verify child2 strokes unchanged
    - **Validates: Requirements 6.4**
    - Use fast-check with `numRuns: 100`

  - [ ]* 5.3 Write unit tests for drawingStore (`frontend/src/features/drawing/__tests__/drawingStore.test.js`)
    - Test `startSession` sets `isActive` true with correct prompt and duration
    - Test `endSession` sets `isActive` false
    - Test `addStroke` appends to strokes array
    - Test `addRemoteStroke` appends without adding to local undo stack
    - Test `undoLastStroke` with empty stack is a no-op
    - Test `tick` decrements `remainingTime` by 1
    - Test `tick` at 0 does not go negative
    - Test `reset` clears all state
    - Test palette has exactly 8 colors
    - Test brush sizes include thin, medium, thick
    - Test stamp shapes include star, heart, circle, lightning
    - _Requirements: 1.3, 1.4, 1.5, 3.2, 6.1, 6.5, 8.4_


- [x] 6. Create DrawingCanvas, DrawingToolbar, and DrawingCountdown components
  - [x] 6.1 Create `frontend/src/features/drawing/components/DrawingCanvas.jsx` and `DrawingCanvas.css`
    - Accept props: `prompt`, `duration`, `siblingId`, `profiles`, `onComplete`
    - Render full-width HTML5 `<canvas>` element with minimum 300×300 CSS px
    - Use `PointerEvent` API with `getCoalescedEvents()` for smooth multi-touch input
    - Normalize coordinates to 0.0–1.0 range (fraction of canvas dimensions)
    - On pointer down/move: create stroke with current color, brush size, tool from `drawingStore`
    - Send each completed stroke via `websocketService.send({ type: "DRAWING_STROKE", stroke })` and add to `drawingStore.addStroke()`
    - If WebSocket disconnected: queue stroke via `drawingStore.queueStroke()`
    - Listen for `DRAWING_STROKE` WebSocket messages: call `drawingStore.addRemoteStroke()` and render on canvas
    - Listen for `DRAWING_END` WebSocket messages: end session
    - Re-render canvas from full stroke list on undo (clear + redraw all)
    - Eraser tool: draw strokes with `#FFFFFF` (canvas background color) at selected brush size
    - Stamp mode: render pre-made SVG shapes (star, heart, circle, lightning) at tap position
    - Animated entrance (CSS `@keyframes slideUp`) and exit (CSS `@keyframes fadeOut`) transitions
    - "We're Done!" button calls `onComplete` and sends `DRAWING_EARLY_END` via WebSocket
    - Responsive: on viewport < 768px, toolbar stacks below canvas via CSS media query
    - ARIA live region announces tool changes and session state ("Drawing started", "Drawing complete")
    - Keyboard support: arrow keys + Enter for color/tool selection via `DrawingToolbar`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 2.1, 2.3, 2.4, 3.1, 3.4, 3.5, 3.6, 6.3, 8.1, 8.2, 8.4_

  - [x] 6.2 Create `frontend/src/features/drawing/components/DrawingToolbar.jsx` and `DrawingToolbar.css`
    - Render color palette (8 swatches, each 44×44 CSS px minimum tap target)
    - Render brush size selector (thin, medium, thick) with visual size indicators
    - Render eraser button, undo button, stamp mode toggle
    - Stamp shape selector (star, heart, circle, lightning) visible when stamp mode active
    - Undo button visually disabled when sibling's undo stack is empty
    - All controls keyboard navigable (arrow keys cycle, Enter selects)
    - Read/write `drawingStore` actions: `setColor`, `setBrushSize`, `setTool`, `setStamp`, `undoLastStroke`
    - _Requirements: 1.3, 1.4, 6.1, 6.3, 6.5, 8.1, 8.4_

  - [x] 6.3 Create `frontend/src/features/drawing/components/DrawingCountdown.jsx` and `DrawingCountdown.css`
    - Accept `remainingTime` and `duration` from `drawingStore`
    - Render circular SVG countdown ring (stroke-dashoffset animation)
    - Display remaining seconds as large text in center
    - Color transitions: green → yellow (< 30%) → red (< 10%)
    - CSS-only animation, no requestAnimationFrame
    - _Requirements: 3.3_

- [x] 7. Wire DrawingCanvas into App.jsx and WebSocket event flow
  - [x] 7.1 Integrate drawing components into `frontend/src/App.jsx`
    - Import `DrawingCanvas` from `features/drawing`
    - Import `useDrawingStore` from `stores/drawingStore`
    - Subscribe to `DRAWING_PROMPT` WebSocket event in `connectToAI`: call `drawingStore.startSession(prompt, duration)`
    - Subscribe to `DRAWING_END` WebSocket event: call `drawingStore.endSession()`
    - Render `DrawingCanvas` overlay when `drawingStore.isActive` is true, passing `prompt`, `duration`, `siblingId`, `profiles`, and `onComplete` handler
    - `onComplete` handler: send `DRAWING_COMPLETE` message via WebSocket with all strokes, call `drawingStore.endSession()`
    - Set up `setInterval` for `drawingStore.tick()` while drawing session is active (clear on end)
    - On reconnect: call `drawingStore.flushSyncQueue()` to replay queued strokes
    - Add `drawingStore.reset()` to all existing reset flows (save & exit, emergency exit, etc.)
    - _Requirements: 2.1, 2.4, 3.1, 3.4, 3.5, 3.6, 5.1, 9.1, 9.2_

  - [x] 7.2 Create `frontend/src/features/drawing/index.js` barrel export
    - Export `DrawingCanvas`, `DrawingToolbar`, `DrawingCountdown`
    - _Requirements: N/A (project structure)_


- [x] 8. AI narrative integration — post-drawing story beat
  - [x] 8.1 Update storyteller agent to handle drawing context (`backend/app/agents/storyteller_agent.py`)
    - When `story_context` contains `drawing_context` dict (with `prompt` and `sibling_names`), include it in the Gemini prompt so the AI references the collaborative drawing activity and both siblings by name in the next narration
    - Ensure the post-drawing beat is generated within the existing `generate_story_segment` flow (no separate endpoint needed)
    - _Requirements: 5.1, 5.2, 5.3_

  - [x] 8.2 Wire drawing completion back into orchestrator story flow
    - In `_do_generate_rich_story_moment`: after `DrawingPersistenceService.save_drawing()` completes, inject `drawing_context` into the next `story_context` dict with prompt text and both sibling names
    - Associate saved `DrawingRecord.image_path` with the story beat so the gallery can display it
    - _Requirements: 4.5, 5.1, 5.2, 5.3_

- [x] 9. Session time enforcement during drawing
  - [x] 9.1 Ensure drawing time counts toward session limit
    - In the WebSocket handler: do NOT call `start_generation_pause` / `end_generation_pause` during drawing sessions — drawing time is active play time and must count toward the session limit
    - In the orchestrator's drawing prompt injection: before sending `DRAWING_PROMPT`, call `session_time_enforcer.check_time()` — if expired, skip drawing and continue story
    - If remaining time < requested duration: clamp via `DrawingSyncService.clamp_duration(requested, remaining_seconds)`
    - Set up a background task that checks `session_time_enforcer.check_time()` periodically during drawing — if expired mid-drawing, send `DRAWING_END` with `reason: "session_expired"` via WebSocket
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ]* 9.2 Write property test for session time during drawing (`backend/tests/test_drawing_properties.py`)
    - **Property 14: Session time continues during drawing** — verify that after a drawing session of D seconds, elapsed time increases by at least D seconds
    - **Validates: Requirements 9.1**
    - Use Hypothesis with `max_examples=20`

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (`max_examples=20`) on backend and fast-check (`numRuns: 100`) on frontend
- All animations are CSS-only — no canvas-based UI animations, no requestAnimationFrame for UI
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/` directory, then `pkill -f "python.*pytest"`
- Frontend builds: `npm run build` from `frontend/` directory
- Pillow is already a backend dependency (used by photo pipeline) — no new dependencies needed
- Stroke coordinates are normalized to [0.0, 1.0] for cross-device rendering consistency
