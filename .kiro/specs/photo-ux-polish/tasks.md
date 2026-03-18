# Implementation Plan: Photo UX Polish

## Overview

Upgrade the family photo integration flow from emoji placeholders to a premium, immersive experience for 6-year-old users. All changes are frontend-only — no backend modifications needed. Implementation proceeds bottom-up: shared utilities first, then individual component upgrades, then wiring and integration.

## Tasks

- [x] 1. Create shared effects hook and extend audio service
  - [x] 1.1 Create `usePhotoUxEffects` custom hook
    - Create `frontend/src/shared/hooks/usePhotoUxEffects.js`
    - Implement `haptic(durationMs)` — calls `navigator.vibrate` if supported, no-op otherwise
    - Implement `hapticPattern([100,50,100])` — pattern vibration
    - Implement `playShutter()`, `playChime()`, `playWhoosh()`, `playSnap()` — each calls `audioFeedbackService.playSequence()` with tuned frequency/duration configs
    - Read `audioStore.audioFeedbackEnabled` to gate sound playback; haptic calls are independent of mute
    - Preload/init audio context on first call
    - _Requirements: 6.4, 11.5, 11.6_

  - [x] 1.2 Add new sound methods to `audioFeedbackService`
    - Add `playShutter()` — short click sequence (high freq, very short duration)
    - Add `playChime()` — ascending two-note success sequence
    - Add `playWhoosh()` — descending sweep sequence
    - Add `playSnap()` — single sharp note
    - All methods use existing `playSequence()` infrastructure
    - _Requirements: 11.1, 11.2, 11.3, 11.4_

  - [x] 1.3 Add `approvePhoto` and `deletePhoto` actions to `photoStore.js`
    - `approvePhoto(photoId)`: POST to `/api/photos/{photo_id}/approve`, update local photo status to `safe`
    - `deletePhoto(photoId)`: DELETE to `/api/photos/{photo_id}`, remove photo from local array
    - Both update state optimistically
    - _Requirements: 7.3, 7.4_

- [x] 2. Upgrade PhotoGallery with real thumbnails, bounding boxes, empty state, and transitions
  - [x] 2.1 Replace grid emoji placeholders with real photo thumbnails
    - Replace `🖼️` in grid items with `<img src={API_BASE}/photo_storage/${photo.file_path}>` 
    - Apply `object-fit: cover`, 1:1 aspect ratio, `border-radius: 12px`
    - Add `onError` handler that falls back to 🖼️ emoji
    - Add semi-transparent amber overlay (`rgba(251,191,36,0.25)`) for photos with `status === 'review'`
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 2.2 Replace face card emoji placeholders with real face crop images
    - In detail view, replace `👤` in `faceThumb` with `<img src={API_BASE}/photo_storage/${face.crop_path}>` 
    - Render as circle (border-radius 50%), min 48×48px touch target
    - Add `onError` handler that falls back to 👤 emoji
    - _Requirements: 1.1, 1.4, 1.6_

  - [x] 2.3 Add bounding box overlays on detail view photo
    - Wrap detail image in a `position: relative` container
    - For each face, render an absolutely positioned div using percentage-based coordinates: `left: bbox_x/naturalWidth*100%`, etc.
    - Read `naturalWidth`/`naturalHeight` from `<img>` `onLoad` event
    - Style with distinct bright colors, `border-radius >= 4px`, semi-transparent fill
    - Tapping a bounding box opens the face labeling form for that face
    - Scale proportionally on image resize
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 2.4 Add illustrated empty state for PhotoGallery
    - When `photos.length === 0`, render an inline SVG illustration (camera with sparkles), min 120×120px
    - Add a single-line prompt encouraging the user to add photos
    - Use playful, child-friendly imagery and colors
    - _Requirements: 9.1, 9.3_

  - [x] 2.5 Add grid↔detail transition animation
    - Add CSS scale-up/fade animation (300ms) when transitioning between grid and detail views
    - Use CSS keyframes/transitions only (no JS frame-by-frame) for 60fps
    - _Requirements: 5.2, 5.3_

  - [ ]* 2.6 Write unit tests for PhotoGallery bounding box coordinate scaling
    - Test percentage calculation from pixel coordinates
    - Test fallback behavior when image fails to load
    - _Requirements: 10.1, 10.4, 2.3_

- [x] 3. Upgrade PhotoUploader with progress indicator, celebration, haptics, and sounds
  - [x] 3.1 Replace static upload emoji with animated circular progress indicator
    - Replace `⏳` with a CSS keyframe animated circular spinner during upload
    - Animate to checkmark (✓) on success before transitioning
    - Animate to error state (✕) on failure, then show error bubble
    - Disable confirm and retake buttons while `uploading === true`
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [x] 3.2 Upgrade celebration overlay with confetti and face crops
    - Replace emoji-only celebration with CSS confetti/particle animation (2s duration)
    - Display detected face crop thumbnails (`<img>` from `crop_path`) inside the celebration overlay
    - Store upload result faces in state so celebration can render them
    - Smooth transition back to main capture UI when celebration ends
    - _Requirements: 4.1, 4.2, 4.4_

  - [x] 3.3 Add haptic feedback and sound effects to PhotoUploader
    - Trigger short haptic pulse (≤50ms) on camera capture button tap
    - Trigger haptic pattern (100-50-100ms) during celebration
    - Play shutter sound on camera capture tap
    - Play chime sound during celebration
    - Use `usePhotoUxEffects` hook for all effects
    - _Requirements: 4.3, 6.1, 6.4, 11.1, 11.2_

  - [ ]* 3.4 Write unit tests for upload progress state transitions
    - Test uploading → success → celebration flow
    - Test uploading → error flow
    - Test button disabled state during upload
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Upgrade CharacterMapping with face crop images, drag-drop feedback, haptics, sounds, and empty state
  - [x] 5.1 Replace face chip and role slot emoji with real face crop images
    - In face pool chips, replace `👤` with `<img src={API_BASE}/photo_storage/${face.crop_path}>`, circular, min 40×40px
    - In assigned role slots, replace text name / `👤` with circular face crop `<img>`
    - Add `onError` fallback to 👤 emoji on both
    - _Requirements: 1.2, 1.3, 1.5_

  - [x] 5.2 Enhance drag-and-drop visual feedback
    - While dragging: scale dragged chip to 1.1× with drop shadow elevation
    - While dragging over valid slot: glowing border + scale-up animation on target slot
    - On drop into slot: spring ease-out snap animation (250ms)
    - On drop outside slots: animate chip returning to pool position
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

  - [x] 5.3 Add haptic feedback and sound effects to CharacterMapping
    - Haptic pulse (≤100ms) on drop onto role slot
    - Haptic pulse (≤50ms) on save button tap
    - Whoosh sound on drag start
    - Snap sound on successful drop
    - Use `usePhotoUxEffects` hook for all effects
    - _Requirements: 6.2, 6.3, 6.4, 8.4, 11.3, 11.4_

  - [x] 5.4 Add illustrated empty state for CharacterMapping
    - When `faces.length === 0`, render an inline SVG illustration (faces with arrows), min 120×120px
    - Add a single-line prompt encouraging the user to upload and label photos first
    - Use playful, child-friendly imagery and colors
    - _Requirements: 9.2, 9.4_

  - [ ]* 5.5 Write unit tests for drag-and-drop state transitions
    - Test drag start → drop on valid slot → snap animation
    - Test drag start → drop outside → return to pool
    - Test haptic and sound triggers on drop
    - _Requirements: 8.1, 8.2, 8.3, 8.5_

- [x] 6. Add wizard step transitions to CharacterSetup and review badge
  - [x] 6.1 Add CSS slide/fade transitions between wizard steps
    - Replace instant step swap with CSS slide-out/slide-in animation (350ms)
    - Add directional variants to existing `animation-fade-in` in `CharacterSetup.css`
    - Use CSS transitions/keyframes only for 60fps performance
    - Apply to all wizard steps: name → gender → spirit → photos
    - _Requirements: 5.1, 5.3_

  - [x] 6.2 Add review notification badge on photos step
    - Fetch stats to get count of photos with `status === 'review'`
    - Display notification dot/badge on photos step when review count > 0
    - _Requirements: 7.1_

- [x] 7. Build ParentApprovalScreen component
  - [x] 7.1 Create `ParentApprovalScreen.jsx` with parent gate
    - Create `frontend/src/features/setup/components/ParentApprovalScreen.jsx`
    - Implement 3-second long-press parent gate using `onPointerDown`/`onPointerUp` timer
    - Show visual progress ring that fills during hold
    - Gate prevents children from accessing approval screen
    - _Requirements: 7.6_

  - [x] 7.2 Implement photo review list with approve/reject actions
    - Display each pending photo (`status === 'review'`) as full-width preview image
    - Add approve (✅) and reject (🗑️) buttons, each ≥ 48×48px touch target
    - Approve calls `POST /api/photos/{photo_id}/approve` via `photoStore.approvePhoto()`
    - Reject calls `DELETE /api/photos/{photo_id}` via `photoStore.deletePhoto()`
    - Update UI optimistically without full page reload
    - _Requirements: 7.2, 7.3, 7.4_

  - [x] 7.3 Add completion state and wire into CharacterSetup
    - When no pending photos remain, show completion message with "Done" button
    - "Done" button calls `onComplete` callback
    - Wire `ParentApprovalScreen` into CharacterSetup photos step, visible when review photos exist
    - _Requirements: 7.5_

  - [ ]* 7.4 Write unit tests for ParentApprovalScreen
    - Test parent gate timer (3s hold to unlock)
    - Test approve action updates photo status
    - Test reject action removes photo from list
    - Test completion state when all photos reviewed
    - _Requirements: 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 8. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- All animations use CSS keyframes/transitions only — no JS frame-by-frame — for 60fps mobile performance
- Inline styles are preserved to match existing codebase conventions
- Sound effects route through existing `audioFeedbackService` and respect `audioStore.audioFeedbackEnabled` mute toggle
- Haptic feedback is independent of the mute setting (vibration ≠ audio)
- All `<img>` elements include `onError` fallback to original emoji placeholders
