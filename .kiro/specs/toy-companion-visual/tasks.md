# Implementation Plan: Toy Companion Visual

## Overview

Add a toy companion setup step to the character creation wizard and render toy companion avatars during story playback. The implementation covers three layers: setup wizard UI (new "toy" step), backend service (ToyPhotoService + endpoints), and story display (companion avatars in DualStoryDisplay). Tasks are ordered so each builds on the previous, starting with backend models/service, then frontend setup, then story display integration.

## Tasks

- [x] 1. Create ToyPhotoService backend models and service
  - [x] 1.1 Create ToyPhotoResult and ToyPhotoMetadata Pydantic models
    - Add `ToyPhotoResult` and `ToyPhotoMetadata` models (see design Data Models section)
    - Add to a new file `backend/app/models/toy_photo.py`
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 1.2 Implement ToyPhotoService class
    - Create `backend/app/services/toy_photo_service.py`
    - Implement `validate_image` reusing same JPEG/PNG magic-byte + 10 MB checks as PhotoService
    - Implement `resize_image` with max_dimension=512, aspect-ratio preserving, JPEG output
    - Implement `upload_toy_photo`: validate → resize → store image + JSON sidecar under `assets/toy_photos/{sibling_pair_id}/child{N}.jpg`
    - Implement `get_toy_photo`: read JSON sidecar, return ToyPhotoMetadata or None
    - Implement `delete_toy_photo`: remove image + sidecar, return bool
    - On re-upload, delete previous file before writing new one
    - _Requirements: 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_

  - [x] 1.3 Write unit tests for ToyPhotoService
    - Create `backend/tests/test_toy_photo_service.py`
    - Test validate_image accepts JPEG/PNG, rejects GIF, rejects >10 MB
    - Test resize_image produces ≤512px longest side, preserves aspect ratio
    - Test upload_toy_photo stores file + sidecar, get_toy_photo returns correct metadata
    - Test re-upload replaces previous file
    - Test delete_toy_photo removes files
    - _Requirements: 2.6, 3.3, 3.4, 3.5, 3.6_

  - [ ]* 1.4 Write property test for toy name length validation
    - **Property 1: Toy name length validation**
    - **Validates: Requirements 1.3**
    - Use Hypothesis with `max_examples=20`

  - [ ]* 1.5 Write property test for toy photo resize aspect ratio
    - **Property 4: Toy photo resize preserves aspect ratio and enforces max dimension**
    - **Validates: Requirements 2.6**
    - Use Hypothesis with `max_examples=20`, generate random PIL images

  - [ ]* 1.6 Write property test for validation consistency with PhotoService
    - **Property 6: Toy photo validation consistency with PhotoService**
    - **Validates: Requirements 3.3, 3.6**
    - Use Hypothesis with `max_examples=20`, generate random byte sequences + filenames

- [x] 2. Add toy photo API endpoints to main.py
  - [x] 2.1 Register POST and GET toy-photo endpoints
    - Add `POST /api/toy-photo/{sibling_pair_id}/{child_number}` endpoint (multipart upload)
    - Add `GET /api/toy-photo/{sibling_pair_id}/{child_number}` endpoint (return metadata + URL)
    - Validate child_number is 1 or 2, return 422 otherwise
    - Lazy-init `ToyPhotoService` singleton following existing `_photo_service` pattern
    - Handle ValidationError → 400, PhotoNotFoundError → 404
    - _Requirements: 3.1, 3.2, 3.6_

  - [x] 2.2 Write unit tests for toy photo API endpoints
    - Create `backend/tests/test_toy_photo_api.py`
    - Test upload returns correct response shape
    - Test GET returns 404 when no photo exists
    - Test invalid child_number returns 422
    - _Requirements: 3.1, 3.2, 3.6_

  - [ ]* 2.3 Write property test for upload round-trip
    - **Property 5: Toy photo upload round-trip**
    - **Validates: Requirements 2.5, 2.7, 3.4**
    - Use Hypothesis with `max_examples=20`

  - [ ]* 2.4 Write property test for re-upload replaces previous
    - **Property 7: Re-upload replaces previous toy photo**
    - **Validates: Requirements 3.5**
    - Use Hypothesis with `max_examples=20`

- [x] 3. Extend frontend setup store and enriched profiles
  - [x] 3.1 Add toyType and toyImage fields to useSetupStore
    - Extend child1 and child2 objects in `frontend/src/stores/setupStore.js` with `toyType: ''` and `toyImage: ''`
    - Add to `partialize` so they persist in localStorage
    - Update `getProfiles` to include `c1_toy_type`, `c1_toy_image`, `c2_toy_type`, `c2_toy_image`
    - _Requirements: 4.1, 4.3, 4.4_

  - [x] 3.2 Update enrichedProfiles in App.jsx
    - Add `c1_toy_type`, `c1_toy_image`, `c2_toy_type`, `c2_toy_image` to the enrichedProfiles object in `handleSetupComplete`
    - Wire `c1_toy_name` and `c2_toy_name` from `formData.c1_toy_name` / `formData.c2_toy_name`
    - Pass toy fields through to `session.setProfiles`
    - _Requirements: 4.2, 8.1_

- [x] 4. Implement Toy Step in CharacterSetup wizard
  - [x] 4.1 Add toy step to wizard flow in CharacterSetup.jsx
    - Insert `'toy'` into `stepOrder` array between `'spirit'` and `'photos'`
    - Add `toy: 'Toy Companion'` to `stepLabels`
    - Update `handleSpiritPick` to navigate to `'toy'` step instead of photos/child2
    - Add `handleToyNext` that navigates to child 2 (reset to name) or photos step
    - _Requirements: 1.1, 1.8_

  - [x] 4.2 Implement toy step UI rendering block
    - Add `wizardStep === 'toy'` conditional block with:
      - Toy name input (pre-populated with existing defaults "Bruno"/"Book")
      - Preset toy grid (6 cards: teddy 🧸, robot 🤖, bunny 🐰, dino 🦕, kitty 🐱, puppy 🐶)
      - Photo capture button (`<input type="file" accept="image/*" capture="environment">` hidden, triggered by styled button)
      - Circular thumbnail preview when photo captured
      - File size validation (>10 MB shows error inline)
      - Next button enabled when name non-empty AND (preset selected OR photo captured)
      - Inline validation "Please name your toy!" when name empty on Next tap
    - All tap targets ≥ 48px, emoji-first design, aria-labels on interactive elements
    - _Requirements: 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.1, 2.2, 2.3, 2.4, 7.1, 7.2, 7.3_

  - [x] 4.3 Add toy step CSS styles to CharacterSetup.css
    - Add styles for toy name input, preset grid (3×2), photo capture button, circular thumbnail preview
    - Add bounce animation on preset card selection (reuse existing `.wizard-card--bounce`)
    - Add focus ring styles for gamepad navigation
    - _Requirements: 1.5, 7.5_

  - [x] 4.4 Wire toy photo upload to backend on step completion
    - When toy type is `'photo'`, upload the captured file to `POST /api/toy-photo/{sibling_pair_id}/{child_number}`
    - On success, store returned `image_url` in formData as `toy_image`
    - On failure, show inline error "Oops! Try again 🔄", keep preview, allow retry
    - _Requirements: 2.5, 2.7_

  - [x] 4.5 Add gamepad navigation support to toy step
    - Wrap toy step interactive elements with existing `FocusNavigator` component
    - Ensure preset cards, photo button, name input, and Next button are navigable via `useGamepad` hook
    - _Requirements: 7.4, 7.5_

- [x] 5. Render Companion Avatars in DualStoryDisplay
  - [x] 5.1 Add companion avatar elements to story scene
    - In `DualStoryDisplay.jsx`, inside the `.story-scene__avatar` divs for each child, render a companion element:
      - If `toy_type === 'photo'` and `toy_image` is non-empty: render `<img>` (40px circle, object-fit cover)
      - If `toy_type === 'preset'`: render `<span>` with the preset emoji looked up from the preset registry
      - If no scene image loaded: don't render companion avatars
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [x] 5.2 Add companion avatar elements to perspective cards
    - In the `.story-card` header for each child, render a smaller companion element:
      - Photo toy: 28px circular `<img>`
      - Preset toy: emoji `<span>` at 1.2rem
    - _Requirements: 6.1, 6.2, 6.3_

  - [x] 5.3 Add companion avatar CSS to DualStoryDisplay.css
    - `.companion-avatar` base styles: 40px circle, border-radius 50%, overflow hidden
    - `.companion-avatar--c1` glow border in child 1 color (pink), `.companion-avatar--c2` in child 2 color (blue)
    - Bobbing animation with 0.5s offset from parent avatar animation
    - Perspective card variant: 28px size, 1.2rem emoji
    - _Requirements: 5.2, 5.4, 5.5, 6.2, 6.3_

  - [ ]* 5.4 Write property test for companion avatar render logic
    - **Property 8: Companion avatar render logic**
    - **Validates: Requirements 5.3, 5.6**
    - Use fast-check with `numRuns: 20`

- [x] 6. Extend CharacterData backend model for toy fields
  - [x] 6.1 Add toy_type and toy_image_url to CharacterData model
    - In `backend/app/models/character.py`, add `toy_type: Optional[str] = None` and `toy_image_url: Optional[str] = None` to `CharacterData`
    - Ensure backward compatibility — old sessions without these fields still work
    - _Requirements: 8.2, 8.3_

- [x] 7. Final wiring and integration
  - [x] 7.1 Wire toy companion data end-to-end
    - Verify formData flows from CharacterSetup → App.jsx enrichedProfiles → session.setProfiles → WebSocket story context
    - Ensure `c1_toy`, `c1_toy_type`, `c1_toy_image` (and c2 equivalents) reach the orchestrator
    - Verify DualStoryDisplay reads toy fields from profiles prop and renders companion avatars
    - _Requirements: 4.2, 8.1, 8.3_

  - [x] 7.2 Add graceful degradation fallbacks
    - If toy photo URL is missing/broken at story time, fall back to preset emoji (or generic 🧸)
    - If `toyType`/`toyImage` are missing from profiles (old sessions), companion avatars simply don't render
    - _Requirements: 5.6_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests validate universal correctness properties from the design document
- Backend tests use Hypothesis with `max_examples=20`; frontend property tests use fast-check with `numRuns: 20`
- CSS-first approach — no new npm dependencies needed
- Run backend tests with: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` (from backend/ directory)
- After pytest: `pkill -f "python.*pytest"` (CacheManager cleanup loop causes hang)
- Frontend builds with `npm run build` from frontend/ directory
