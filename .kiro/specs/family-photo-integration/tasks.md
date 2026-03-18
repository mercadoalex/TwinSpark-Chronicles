# Implementation Plan: Family Photo Integration

## Overview

Incrementally build the photo-to-story pipeline: database schema → data models → backend services (upload, safety scan, face extraction, style transfer, compositing) → API endpoints → frontend components (uploader, gallery, character mapping) → orchestrator wiring. Each task builds on the previous, with property tests and unit tests alongside implementation.

## Tasks

- [x] 1. Database schema and data models
  - [x] 1.1 Create database migration `backend/app/db/migrations/002_family_photos.sql`
    - Create `photos`, `face_portraits`, `character_mappings`, and `style_transferred_portraits` tables with indexes and foreign keys as specified in the design
    - Ensure `ON DELETE CASCADE` and `ON DELETE SET NULL` constraints are correct
    - _Requirements: 8.1, 8.3_

  - [x] 1.2 Create Pydantic models in `backend/app/models/photo.py`
    - Define `PhotoStatus`, `PhotoRecord`, `FacePortraitRecord`, `FamilyMember`, `CharacterMappingInput`, `CharacterMapping`, `PhotoUploadResult`, `DeleteResult`, `StorageStats`, `CharacterPosition` as specified in the design
    - _Requirements: 1.6, 3.4, 4.2, 4.6, 8.1_

- [x] 2. Content scanning and face extraction services
  - [x] 2.1 Implement `ContentScanner` in `backend/app/services/content_scanner.py`
    - Extend existing `ContentFilter` with `scan_image` method returning `ImageSafetyRating` (SAFE/REVIEW/BLOCKED)
    - Define `ImageSafetyRating` enum and `ImageScanResult` dataclass
    - Fall back to REVIEW rating if Google Vision is unavailable
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 2.2 Implement `FaceExtractor` in `backend/app/services/face_extractor.py`
    - Wrap existing `FaceDetector` with cropping logic using 20% margin padding
    - Define `ExtractedFace` and `FaceBBox` dataclasses
    - Clamp crop to image boundaries, support 1–10 faces, raise `NoFacesFoundError` when none detected
    - _Requirements: 3.1, 3.2, 3.3, 3.5_

  - [ ]* 2.3 Write property test for face crop margin calculation
    - **Property 4: Face crop includes consistent margin padding**
    - Generate random bounding boxes and image dimensions with Hypothesis; verify crop dimensions match the 20%-margin formula clamped to image bounds
    - **Validates: Requirement 3.2**

  - [ ]* 2.4 Write property test for content scan routing
    - **Property 3: Content scan rating determines photo processing path**
    - Mock scanner ratings (SAFE/REVIEW/BLOCKED); verify stored photo status matches rating and that BLOCKED photos are not persisted
    - **Validates: Requirements 2.2, 2.3, 2.4**

- [x] 3. PhotoService — upload, validation, resize, and CRUD
  - [x] 3.1 Implement `PhotoService` in `backend/app/services/photo_service.py`
    - Implement `validate_image` (JPEG/PNG, ≤10 MB), `resize_image` (max 1024px longest side, preserve aspect ratio)
    - Implement `upload_photo` pipeline: validate → resize → content scan → face extract → store
    - Implement `get_photos`, `get_photo`, `delete_photo` (cascade delete of faces, portraits, and mapping invalidation), `approve_photo`
    - Implement `save_family_member`, `save_character_mapping`, `get_character_mappings`, `get_storage_stats`
    - Create `photo_storage/` directory structure at init
    - _Requirements: 1.3, 1.4, 1.5, 1.6, 2.2, 2.3, 2.4, 3.3, 3.4, 4.2, 4.6, 7.3, 7.4, 7.5, 8.1, 8.2, 8.3_

  - [ ]* 3.2 Write property test for image validation
    - **Property 1: Image validation accepts if and only if format and size are valid**
    - Generate random bytes with random extensions and sizes using Hypothesis; verify acceptance iff JPEG/PNG and ≤10 MB
    - **Validates: Requirements 1.3, 1.4**

  - [ ]* 3.3 Write property test for resize aspect ratio
    - **Property 2: Resize preserves aspect ratio and enforces max dimension**
    - Generate random image dimensions with Hypothesis; verify longest side ≤1024 and aspect ratio preserved within tolerance
    - **Validates: Requirement 1.5**

  - [ ]* 3.4 Write property test for cascade delete
    - **Property 10: Cascade delete removes all derived data and invalidates mappings**
    - Generate random photo trees, delete, verify photo/faces/portraits gone and mappings have face_id=NULL
    - **Validates: Requirements 7.3, 7.4**

  - [ ]* 3.5 Write property test for round-trip persistence
    - **Property 11: Photo record storage round-trip**
    - Generate random PhotoRecords with Hypothesis, store then load, verify equivalence
    - **Validates: Requirements 1.6, 3.4, 4.2, 4.6, 8.1, 8.2, 8.4**

  - [ ]* 3.6 Write property test for sibling pair isolation
    - **Property 12: Sibling pair photo isolation**
    - Generate two random sibling_pair_ids, store photos under each, cross-query and verify empty intersection
    - **Validates: Requirement 8.3**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. StyleTransferAgent and SceneCompositor
  - [x] 5.1 Implement `StyleTransferAgent` in `backend/app/agents/style_transfer_agent.py`
    - Use Imagen 3 (`imagen-3.0-generate-001`) to transform face crops into Pixar/Disney-style portraits
    - Implement `generate_portrait` and `generate_portraits_for_session` with caching in Photo_Store
    - Fall back to default AI avatar on failure; set `_enabled = False` if `GOOGLE_PROJECT_ID` not set
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 5.2 Implement `SceneCompositor` in `backend/app/services/scene_compositor.py`
    - Use Pillow to composite style-transferred portraits onto base scene images at character positions
    - Apply scaling, color grading, and shadow blending for natural integration
    - Use default AI avatar for unmapped characters
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 5.3 Write property test for style transfer portrait count
    - **Property 7: Style transfer produces one portrait per mapped family member**
    - Generate random mapping sets with N non-null face_ids; verify exactly N portraits returned and stored
    - **Validates: Requirements 5.1, 5.5**

  - [ ]* 5.4 Write property test for style transfer fallback
    - **Property 8: Style transfer failure falls back to default avatar**
    - Mock style transfer failures; verify default avatar returned and error logged
    - **Validates: Requirement 5.6**

  - [ ]* 5.5 Write property test for scene compositor output
    - **Property 9: Scene compositor includes all mapped portraits**
    - Generate random base scenes and portrait sets; verify output is valid PNG with correct dimensions and all portraits processed
    - **Validates: Requirement 6.1**

  - [ ]* 5.6 Write property test for unmapped character default avatar
    - **Property 6: Unmapped characters use default avatar**
    - Generate mappings with some face_id=None; verify compositor uses default avatar and style transfer is not called for those roles
    - **Validates: Requirements 4.5, 6.4**

- [x] 6. FastAPI endpoints
  - [x] 6.1 Add photo API routes to `backend/app/main.py`
    - `POST /photos/upload` — multipart upload, returns `PhotoUploadResult`
    - `GET /photos/{sibling_pair_id}` — list photos
    - `DELETE /photos/{photo_id}` — cascade delete
    - `POST /photos/{photo_id}/approve` — parent approves REVIEW photo
    - `PUT /photos/faces/{face_id}/label` — set family member name
    - `GET /photos/mappings/{sibling_pair_id}` — get character mappings
    - `POST /photos/mappings/{sibling_pair_id}` — save character mappings
    - `GET /photos/stats/{sibling_pair_id}` — storage stats
    - Wire endpoints to `PhotoService` with proper error handling (422 for validation, 404 for not found, 500 for server errors)
    - _Requirements: 1.3, 1.4, 1.6, 2.2, 3.3, 4.2, 4.6, 7.3, 7.4, 7.5_

  - [ ]* 6.2 Write unit tests for photo API endpoints
    - Test upload success, upload rejection (size/format), content blocked response, delete cascade, approve flow, labeling, mapping CRUD
    - _Requirements: 1.3, 1.4, 2.2, 7.3, 7.4_

- [x] 7. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 8. Frontend — PhotoUploader component
  - [x] 8.1 Create `frontend/src/features/setup/components/PhotoUploader.jsx`
    - Camera capture via `<input type="file" accept="image/*" capture="environment">`
    - Gallery picker via `<input type="file" accept="image/jpeg,image/png">`
    - Drag-and-drop zone for desktop browsers
    - Preview with confirm/retake controls
    - Large touch targets (min 48×48 CSS px), colorful icons, no text labels
    - Max 3 action choices visible at any time
    - Celebratory animation + sound on successful face detection
    - _Requirements: 1.1, 1.2, 1.7, 9.1, 9.4, 9.5_

  - [x] 8.2 Add voice prompt integration to PhotoUploader
    - Play short voice prompts via Google Cloud TTS at each upload/labeling step
    - _Requirements: 9.2_

  - [ ]* 8.3 Write unit tests for PhotoUploader
    - Verify touch target sizes ≥48×48, max 3 actions rendered, drag-and-drop zone present on desktop, preview/confirm flow
    - _Requirements: 9.1, 9.5_

- [x] 9. Frontend — PhotoGallery component
  - [x] 9.1 Create `frontend/src/features/setup/components/PhotoGallery.jsx`
    - Grid of uploaded photos sorted by upload date
    - Tap photo to see full image with face bounding boxes highlighted
    - Face cards with editable name labels
    - Swipe gesture support for touch browsing
    - Delete button with confirmation dialog
    - Storage count + usage indicator
    - _Requirements: 4.1, 4.2, 7.1, 7.2, 7.3, 7.5, 9.3_

  - [ ]* 9.2 Write unit tests for PhotoGallery
    - Verify photo grid rendering, face card labels, delete confirmation, storage indicator
    - _Requirements: 7.1, 7.2, 7.5_

- [x] 10. Frontend — CharacterMapping component
  - [x] 10.1 Create `frontend/src/features/setup/components/CharacterMapping.jsx`
    - List of story character roles with drag-to-assign family member faces
    - Enforce minimum 2 sibling protagonists mapped before starting with photo integration
    - Unmapped roles show default AI avatar with "use default" label
    - Persist mapping via `POST /photos/mappings/{sibling_pair_id}`
    - _Requirements: 4.3, 4.4, 4.5, 4.6_

  - [ ]* 10.2 Write property test for minimum mapping validation
    - **Property 5: Photo integration requires minimum two sibling protagonist mappings**
    - Generate random mapping sets; verify validation rejects sets with fewer than 2 sibling protagonist face_ids
    - **Validates: Requirement 4.4**

  - [ ]* 10.3 Write unit tests for CharacterMapping
    - Test drag-to-assign flow, minimum mapping enforcement, default avatar display for unmapped roles
    - _Requirements: 4.3, 4.4, 4.5_

- [x] 11. Orchestrator integration and wiring
  - [x] 11.1 Integrate photo pipeline into `backend/app/agents/orchestrator.py`
    - Before scene generation, load character mappings for the sibling pair
    - Call `StyleTransferAgent.generate_portraits_for_session` for mapped characters (use cached portraits when available)
    - Pass illustrated portraits to `VisualAgent` → `SceneCompositor` for compositing into scene images
    - Handle photo integration being disabled (no mappings) gracefully — use existing avatar flow
    - _Requirements: 5.1, 6.1, 6.4, 8.2_

  - [x] 11.2 Wire frontend photo components into the setup flow
    - Add PhotoUploader, PhotoGallery, and CharacterMapping to `frontend/src/features/setup/components/CharacterSetup.jsx` (or appropriate setup step)
    - Add Zustand store slice for photo state management
    - Connect API calls to backend photo endpoints
    - _Requirements: 1.1, 4.1, 4.3_

  - [ ]* 11.3 Write integration tests for the full photo pipeline
    - Test end-to-end: upload → scan → extract → store → retrieve → style transfer → composite
    - Test cross-session persistence: upload in session 1, verify available in session 2
    - _Requirements: 8.1, 8.2_

- [x] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use Hypothesis (Python) with minimum 100 examples per property
- Checkpoints ensure incremental validation
- Backend tests: `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- Frontend builds: `npm run build` from `frontend/`
