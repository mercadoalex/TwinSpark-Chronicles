# Implementation Plan: Story Archival Trigger

## Overview

Wire `StoryArchiveService.archive_story()` into the session-end flow by creating two pure utility functions (title generator, beat transformer), integrating them into the orchestrator's `end_session()`, surfacing `storybook_id` in the API response, and reordering the frontend save flow with archive confirmation feedback.

## Tasks

- [x] 1. Create pure utility functions
  - [x] 1.1 Create `backend/app/utils/title_generator.py` with `generate_story_title()`
    - Create `backend/app/utils/__init__.py` if it doesn't exist
    - Implement `generate_story_title(narration: str | None) -> str`
    - Truncate to ≤60 chars at nearest word boundary, append `…` if truncated
    - Return `"Untitled Adventure"` for empty/None input
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ]* 1.2 Write property test for title generator
    - **Property 2: Title length and word-boundary truncation**
    - **Validates: Requirements 3.2, 3.4**
    - Create `backend/tests/test_title_generator.py`
    - Use Hypothesis with `max_examples=20`
    - Assert: length ≤60, ellipsis iff truncated, no mid-word break, empty→fallback

  - [x] 1.3 Create `backend/app/utils/beat_transformer.py` with `transform_beats()`
    - Implement `transform_beats(story_history: list[dict]) -> list[dict]`
    - Map `choiceMade` → `choice_made`, `choices` → `available_choices`
    - Pass through `narration`, `child1_perspective`, `child2_perspective`, `scene_image_url`
    - Drop `timestamp` and any other frontend-only keys
    - Default missing optional fields to `None` or `[]`
    - _Requirements: 2.3_

  - [ ]* 1.4 Write property test for beat transformer
    - **Property 1: Beat transformation preserves all fields**
    - **Validates: Requirements 2.3**
    - Add to `backend/tests/test_beat_transformer.py`
    - Use Hypothesis with `max_examples=20`
    - Generate random beat dicts, assert field mapping correctness and timestamp dropped

- [x] 2. Integrate archival into orchestrator `end_session()`
  - [x] 2.1 Add archival block to `AgentOrchestrator.end_session()` in `backend/app/agents/orchestrator.py`
    - Import `SessionService`, `StoryArchiveService`, `generate_story_title`, `transform_beats`
    - After world-state extraction block, add archival block:
      - Load snapshot via `SessionService(self._db_conn).load_snapshot(sibling_pair_id)`
      - Guard: skip if snapshot is None or `story_history` is empty (log warning)
      - Extract `language` and `session_duration_seconds` from `session_metadata`
      - Call `transform_beats()` on `story_history`
      - Call `generate_story_title()` on first beat's narration
      - Call `StoryArchiveService(self._db_conn).archive_story(sibling_pair_id, title, language, beats, duration)`
      - Wrap entire block in try/except — log errors, never raise
    - Add `storybook_id` (or `None`) to the returned dict
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.4, 2.5_

  - [ ]* 2.2 Write unit tests for orchestrator archival integration
    - Create `backend/tests/test_orchestrator_archival.py`
    - Test: successful archival → `storybook_id` in response
    - Test: no snapshot → archival skipped, `storybook_id` is None
    - Test: empty story_history → archival skipped, `storybook_id` is None
    - Test: `archive_story()` raises exception → response still returned with `storybook_id: None`
    - Mock `SessionService`, `StoryArchiveService`, and existing orchestrator dependencies
    - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.4, 2.5_

- [x] 3. Update API endpoint response
  - [x] 3.1 Modify `POST /api/sessions/{session_id}/end` in `backend/app/main.py`
    - The orchestrator now returns `storybook_id` in its dict — no endpoint logic change needed beyond verifying the field passes through
    - Update the idempotent cache (`_ended_sessions`) to include `storybook_id`
    - _Requirements: 1.4, 1.5_

- [x] 4. Reorder frontend save flow and add archive feedback
  - [x] 4.1 Reorder `handleSaveAndExit()` in `frontend/src/App.jsx`
    - Move `persistence.saveSnapshot()` call to execute before the `end-session` fetch
    - Wrap `saveSnapshot()` in try/catch so end-session still fires on failure
    - After end-session response, check for non-null `storybook_id`
    - Set a transient local state flag (e.g. `archivedToGallery`) when `storybook_id` is present
    - Show a subtle "Saved to gallery ✨" indicator before reset (CSS-first, no new dependencies)
    - Clear the flag on reset
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.2_

  - [ ]* 4.2 Write unit tests for frontend save order
    - Verify `saveSnapshot()` is called before end-session endpoint
    - Verify archive confirmation shows when `storybook_id` is non-null
    - Verify no error shown when `storybook_id` is null
    - _Requirements: 4.1, 4.2, 5.1, 5.2_

- [x] 5. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- After pytest: `pkill -f "python.*pytest"`
- Frontend builds: `npm run build` from `frontend/`
- Property-based tests use Hypothesis with `max_examples=20`
- All archival errors are swallowed in the orchestrator — end-session must never fail due to archival
