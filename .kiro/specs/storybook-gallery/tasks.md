# Implementation Plan: Storybook Gallery

## Overview

Implement a persistent storybook gallery spanning backend (SQLite schema, StoryArchiveService, Gallery API endpoints) and frontend (galleryStore Zustand store, GalleryView bookshelf component, StoryReader page-by-page reader, App.jsx navigation integration). Backend uses Python 3.11/FastAPI with DatabaseConnection, frontend uses React/Zustand with CSS-first styling.

## Tasks

- [x] 1. Backend data models and SQLite schema
  - [x] 1.1 Create `backend/app/models/storybook.py` with Pydantic models: `StorybookSummary`, `StoryBeatRecord`, `StorybookDetail`, `StorybookRecord`, and `DeleteStorybookResult` as defined in the design document
    - `StorybookSummary`: storybook_id, title, cover_image_url (optional), beat_count, duration_seconds, completed_at
    - `StoryBeatRecord`: beat_id, beat_index, narration, child1_perspective (optional), child2_perspective (optional), scene_image_url (optional), choice_made (optional), available_choices (list[str])
    - `StorybookDetail`: extends summary with sibling_pair_id, language, beats list
    - _Requirements: 2.2, 3.1, 3.2_

  - [x] 1.2 Create the `storybooks` and `story_beats` tables via `StoryArchiveService.__init__` table creation (following the existing pattern of services creating their own tables)
    - `storybooks` table with: storybook_id TEXT PK, sibling_pair_id TEXT NOT NULL, title TEXT NOT NULL, language TEXT DEFAULT 'en', cover_image_url TEXT, beat_count INTEGER, duration_seconds INTEGER, completed_at TEXT, created_at TEXT
    - `story_beats` table with: beat_id TEXT PK, storybook_id TEXT NOT NULL REFERENCES storybooks ON DELETE CASCADE, beat_index INTEGER, narration TEXT, child1_perspective TEXT, child2_perspective TEXT, scene_image_url TEXT, choice_made TEXT, available_choices TEXT (JSON), created_at TEXT
    - Create indexes: `idx_storybooks_pair` on (sibling_pair_id, completed_at DESC), `idx_beats_storybook` on (storybook_id, beat_index ASC)
    - _Requirements: 1.1, 1.2, 1.4_

- [x] 2. Backend StoryArchiveService
  - [x] 2.1 Create `backend/app/services/story_archive_service.py` with `StoryArchiveService` class accepting `DatabaseConnection` in constructor, calling table creation on init
    - Implement `archive_story(sibling_pair_id, title, language, beats, duration_seconds)` → `StorybookRecord | None`
    - Use `db.transaction()` context manager for all-or-nothing writes
    - Generate `storybook_id` and `beat_id` with `uuid.uuid4().hex[:12]`
    - Derive `cover_image_url` from first beat's `scene_image_url`
    - Set `beat_count` to `len(beats)`, store `duration_seconds`
    - Return `None` and log warning if beats list is empty
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 2.2 Implement `list_storybooks(sibling_pair_id)` → `list[StorybookSummary]`
    - Query `storybooks` table filtered by sibling_pair_id, ordered by completed_at DESC
    - Return empty list if no results
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 2.3 Implement `get_storybook(storybook_id)` → `StorybookDetail | None`
    - Join storybooks + story_beats, return full detail with beats in beat_index order
    - Parse `available_choices` from JSON string to list
    - Return `None` if storybook_id not found
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 2.4 Implement `delete_storybook(storybook_id)` → `bool` and `delete_all_storybooks(sibling_pair_id)` → `int`
    - Single delete: delete from storybooks (CASCADE removes beats), return True if found
    - Bulk delete: count storybooks for pair, delete all, return count
    - _Requirements: 4.1, 4.4_

  - [x] 2.5 Write unit tests in `backend/tests/test_story_archive_service.py`
    - Test archive with 3 beats verifies all fields persisted correctly
    - Test archive with empty beats returns None and logs warning
    - Test list_storybooks for pair with no stories returns empty list
    - Test get_storybook for nonexistent ID returns None
    - Test delete nonexistent storybook returns False
    - Test bulk delete returns correct count and removes all records
    - Test cover_image_url equals first beat's scene_image_url
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 2.1, 3.1, 4.1, 4.4_


  - [x]* 2.6 Write property test for storybook round-trip preservation in `backend/tests/test_story_archive_properties.py`
    - **Property 1: Storybook round-trip preservation**
    - Generate random beat lists (1–10 beats) with random narration, perspectives, image URLs, choices; archive then retrieve via get_storybook; assert all fields match input
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 1.1, 1.2, 3.1, 3.2, 11.1, 11.2**

  - [x]* 2.7 Write property test for archive metadata invariants in `backend/tests/test_story_archive_properties.py`
    - **Property 2: Archive metadata invariants**
    - Generate random beat lists and duration values; archive; assert beat_count == len(beats), duration_seconds matches input, cover_image_url == first beat's scene_image_url
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 1.3, 1.4**

  - [x]* 2.8 Write property test for gallery listing order in `backend/tests/test_story_archive_properties.py`
    - **Property 3: Gallery listing order**
    - Archive multiple storybooks with random timestamps for the same sibling pair; list them; assert descending order by completed_at and all storybooks present
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 2.1, 2.2**

  - [x]* 2.9 Write property test for deletion completeness in `backend/tests/test_story_archive_properties.py`
    - **Property 4: Deletion completeness**
    - Archive random storybooks, delete one, verify get_storybook returns None and no beats remain; for bulk delete, verify count matches and list returns empty
    - Use Hypothesis with `@settings(max_examples=20)`
    - **Validates: Requirements 4.1, 4.4**

- [x] 3. Backend Gallery API endpoints
  - [x] 3.1 Add Gallery API endpoints to `backend/app/main.py`
    - `GET /api/gallery/{sibling_pair_id}` → list storybook summaries (200 with JSON array)
    - `GET /api/gallery/detail/{storybook_id}` → full storybook detail (200 or 404)
    - `DELETE /api/gallery/{storybook_id}` with `X-Parent-Pin` header → delete single (200, 401, or 404)
    - `DELETE /api/gallery/all/{sibling_pair_id}` with `X-Parent-Pin` header → bulk delete (200 or 401)
    - Lazy-initialize `StoryArchiveService` singleton following the `_voice_recording_service` pattern
    - Reuse existing `_verify_parent_pin()` helper for PIN validation
    - _Requirements: 2.1, 2.2, 2.3, 3.1, 3.2, 3.3, 4.1, 4.2, 4.3, 4.4_

  - [x] 3.2 Write API tests in `backend/tests/test_gallery_api.py` using FastAPI TestClient
    - Test GET list returns 200 with correct JSON structure
    - Test GET detail returns 404 for missing storybook
    - Test DELETE returns 401 without PIN header
    - Test DELETE returns 404 for missing storybook
    - Test bulk DELETE returns correct count
    - _Requirements: 2.1, 2.3, 3.3, 4.1, 4.2, 4.3_

- [x] 4. Checkpoint — Backend complete
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Frontend galleryStore (Zustand)
  - [x] 5.1 Create `frontend/src/stores/galleryStore.js` with Zustand store using devtools middleware
    - State: `storybooks` (array), `selectedStorybook` (null), `isLoading` (false), `error` (null)
    - Actions: `fetchStorybooks(siblingPairId)`, `fetchStorybookDetail(storybookId)`, `deleteStorybook(storybookId, pin)`, `removeStorybookLocally(storybookId)`, `clearSelectedStorybook()`, `reset()`
    - `fetchStorybooks` calls `GET /api/gallery/{siblingPairId}`, sets loading/error states
    - `fetchStorybookDetail` calls `GET /api/gallery/detail/{storybookId}`
    - `deleteStorybook` calls `DELETE /api/gallery/{storybookId}` with `X-Parent-Pin` header
    - `removeStorybookLocally` filters the storybook out of the local list without re-fetching
    - _Requirements: 9.1, 9.2, 9.3, 9.4_


  - [x]* 5.2 Write property test for local store deletion consistency
    - **Property 6: Local store deletion consistency**
    - Generate random storybook summary lists (1–10 items), pick a random ID to remove via `removeStorybookLocally`; assert list shrinks by exactly 1 and the removed ID is no longer present
    - Use fast-check with `numRuns: 20`
    - **Validates: Requirements 9.3**

- [x] 6. Frontend GalleryView bookshelf component
  - [x] 6.1 Create `frontend/src/features/gallery/components/GalleryView.jsx` as a full-screen overlay component
    - Accept props: `siblingPairId`, `onClose`, `isParentMode` (optional)
    - On mount, call `galleryStore.fetchStorybooks(siblingPairId)`
    - Render book cover cards on horizontal wooden shelf rows with Cover_Image, title, and sparkle decoration
    - Each book cover card uses touch targets of at least 120px × 160px
    - Tapping a book opens StoryReader with a book-opening transition
    - Show shimmer skeleton placeholders during loading
    - Show empty state with "No adventures yet — start your first story!" message when no storybooks exist
    - In parent mode (`isParentMode={true}`), show delete button on each card
    - Delete button triggers confirmation dialog → API call → local removal with fade-out
    - Show child-friendly error messages on failure
    - Close button to dismiss the overlay
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 8.1, 8.2, 8.3, 8.4_

  - [x] 6.2 Create `frontend/src/features/gallery/components/GalleryView.css` with premium bookshelf styling
    - Warm wooden shelf rows with ambient glow animation (Living Storybook design system)
    - Book cover cards with glass-panel effect, sparkle decorations, hover/tap scale
    - Shimmer skeleton animation for loading state
    - Empty state illustration styling
    - Fade-out animation for deleted books
    - `prefers-reduced-motion` media query: disable glow animations and book-opening transitions
    - Visible focus indicators on all interactive elements
    - _Requirements: 5.2, 5.5, 10.1, 10.2, 10.3, 10.4_

  - [x] 6.3 Create `frontend/src/features/gallery/index.js` barrel export for GalleryView and StoryReader
    - _Requirements: 7.1_

- [x] 7. Frontend StoryReader component
  - [x] 7.1 Create `frontend/src/features/gallery/components/StoryReader.jsx` as a full-screen reader
    - Accept props: `storybookId`, `onClose`
    - On mount, call `galleryStore.fetchStorybookDetail(storybookId)`
    - Display one beat at a time: scene image (with fallback placeholder on error), narration text, "You chose:" label with the selected choice
    - Tap narration area to expand/collapse child1 and child2 perspective cards (matching DualStoryDisplay pattern)
    - Forward/backward navigation via arrow buttons and swipe gestures (touch events)
    - Page indicator showing "current / total" (e.g., "3 / 8")
    - Page-turn transition animation between beats (reuse TransitionEngine CSS patterns)
    - "The End" card on last beat with celebration sparkle (CelebrationOverlay) and "Back to Gallery" button
    - Close button always visible
    - Announce page changes via `aria-live="polite"` region
    - `prefers-reduced-motion`: instant page changes, no transition animation
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7, 6.8_

  - [x] 7.2 Create `frontend/src/features/gallery/components/StoryReader.css` with immersive reader styling
    - Scene image display with fade overlay
    - Narration text styling matching DualStoryDisplay
    - "You chose:" badge with subtle glow
    - Page-turn/slide transition animations
    - "The End" card with celebration styling
    - Navigation arrow buttons with 56px min touch targets
    - Page indicator styling
    - `prefers-reduced-motion` media query: disable transitions
    - _Requirements: 6.1, 6.3, 6.4, 6.7_

  - [x]* 7.3 Write property test for page indicator correctness
    - **Property 5: Page indicator correctness**
    - Generate random beat counts (1–20) and current indices (0 to N-1); assert indicator text matches `"${i+1} / ${N}"`
    - Use fast-check with `numRuns: 20`
    - **Validates: Requirements 6.4**

- [x] 8. Navigation integration and wiring
  - [x] 8.1 Update `frontend/src/App.jsx` to add gallery navigation
    - Add `showGallery` local state (boolean, default false)
    - Add bookshelf icon button (📚) in the top navigation bar alongside World Map and Settings buttons, visible when `setup.isComplete`
    - Render `GalleryView` as full-screen overlay when `showGallery` is true, passing `siblingPairId` and `onClose`
    - Import GalleryView from the gallery feature barrel export
    - _Requirements: 7.1, 7.2_

  - [x] 8.2 Update Parent Dashboard to include gallery access
    - Add "Story Gallery" link/button in `ParentDashboard` or `ParentControls` that opens `GalleryView` with `isParentMode={true}`
    - _Requirements: 7.3, 8.1_

  - [x] 8.3 Add `galleryStore.reset()` call to all exit/cleanup paths in `App.jsx` (handleSaveAndExit, handleExitWithoutSaving, handleEmergencyExit)
    - _Requirements: 9.4_

- [x] 9. Accessibility polish
  - [x] 9.1 Add semantic HTML and ARIA attributes to GalleryView and StoryReader
    - Bookshelf region: `role="region"` with `aria-label="Story gallery bookshelf"`
    - Each book cover: `role="button"` with `aria-label` including the story title
    - Navigation controls: `aria-label` on forward/backward buttons
    - Page indicator: `aria-live="polite"` for screen reader announcements
    - Keyboard navigation: all interactive elements focusable with visible focus indicators
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 10. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Backend tests run with: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- Frontend builds with: `npm run build` from `frontend/`
- The gallery follows the same overlay pattern as WorldMapView in App.jsx
- Parent PIN reuse: deletion uses the existing `_verify_parent_pin()` helper and `X-Parent-Pin` header convention
