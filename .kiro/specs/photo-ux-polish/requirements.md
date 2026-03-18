# Requirements Document

## Introduction

The Photo UX Polish feature upgrades the family photo integration flow in Twin Spark Chronicles from functional-but-placeholder quality to a premium, immersive experience worthy of the "WOOOAW factor." The current implementation uses emoji placeholders (👤, 🖼️) instead of real image thumbnails, lacks animations and haptic feedback, has no parent approval UI despite backend support, and provides minimal visual feedback during drag-and-drop and upload operations. This spec covers replacing all placeholders with real imagery, adding motion/sound/haptic polish, building the missing parent approval screen, and improving empty states — all designed for 6-year-old users with large touch targets, minimal text, and voice/camera/touch/drag-drop interactions.

## Glossary

- **Photo_Gallery**: The React component (`PhotoGallery.jsx`) that displays a grid of uploaded family photos and a detail view for individual photos.
- **Photo_Uploader**: The React component (`PhotoUploader.jsx`) that handles camera capture, gallery pick, and drag-and-drop upload of family photos.
- **Character_Mapper**: The React component (`CharacterMapping.jsx`) that lets users drag-and-drop labeled face chips onto story character role slots.
- **Face_Crop**: A JPEG image file stored on the backend at `crop_path`, extracted from a family photo during face detection, representing a single detected face.
- **Bounding_Box**: The rectangle coordinates (bbox_x, bbox_y, bbox_width, bbox_height) stored per face portrait, describing where a face appears in the original photo.
- **Photo_Status**: The lifecycle state of an uploaded photo: `safe`, `review`, or `blocked`.
- **Parent_Approval_Screen**: A dedicated UI screen where a parent can review photos flagged with `review` status and approve or reject them.
- **Touch_Target**: An interactive UI element with a minimum size of 48×48 CSS pixels, per accessibility and child-usability guidelines.
- **Haptic_Pulse**: A short vibration triggered via `navigator.vibrate()` on supported mobile devices.
- **Face_Chip**: A draggable UI element in the Character_Mapper representing a labeled face, used for drag-and-drop assignment to character role slots.

## Requirements

### Requirement 1: Real Face Crop Thumbnails

**User Story:** As a child user, I want to see actual face photos instead of 👤 emoji placeholders, so that I can recognize family members at a glance.

#### Acceptance Criteria

1. WHEN the Photo_Gallery detail view renders a face card, THE Photo_Gallery SHALL display the Face_Crop image loaded from the backend `crop_path` instead of the 👤 emoji placeholder.
2. WHEN the Character_Mapper renders a Face_Chip in the face pool, THE Character_Mapper SHALL display the Face_Crop image as a circular thumbnail (minimum 40×40 CSS pixels) instead of the 👤 emoji.
3. WHEN the Character_Mapper renders an assigned face in a role slot, THE Character_Mapper SHALL display the Face_Crop image as a circular thumbnail instead of the text name or 👤 emoji.
4. IF a Face_Crop image fails to load, THEN THE Photo_Gallery SHALL fall back to displaying the 👤 emoji placeholder.
5. IF a Face_Crop image fails to load, THEN THE Character_Mapper SHALL fall back to displaying the 👤 emoji placeholder.
6. THE Photo_Gallery SHALL render each Face_Crop thumbnail as a circle with a minimum Touch_Target size of 48×48 CSS pixels.

### Requirement 2: Real Photo Thumbnails in Gallery Grid

**User Story:** As a child user, I want to see actual photo thumbnails in the gallery grid instead of 🖼️ emoji, so that I can find and select the photo I want.

#### Acceptance Criteria

1. WHEN the Photo_Gallery renders the grid view, THE Photo_Gallery SHALL display each photo as an `<img>` element loaded from the backend `file_path` instead of the 🖼️ emoji placeholder.
2. THE Photo_Gallery SHALL render each grid thumbnail with `object-fit: cover` and a 1:1 aspect ratio within a rounded container (border-radius ≥ 12px).
3. IF a photo thumbnail image fails to load, THEN THE Photo_Gallery SHALL fall back to displaying the 🖼️ emoji placeholder.
4. WHILE a photo has Photo_Status `review`, THE Photo_Gallery SHALL overlay a semi-transparent amber tint on the thumbnail to visually distinguish it from safe photos.

### Requirement 3: Upload Progress Indicator

**User Story:** As a child user, I want to see how far along my photo upload is, so that I know the app is working and I can wait patiently.

#### Acceptance Criteria

1. WHILE the Photo_Uploader is uploading a file, THE Photo_Uploader SHALL display an animated circular progress indicator instead of the static ⏳ emoji.
2. WHEN the upload completes successfully, THE Photo_Uploader SHALL animate the progress indicator to a completion state (checkmark) before transitioning to the celebration or result view.
3. WHILE the Photo_Uploader is uploading, THE Photo_Uploader SHALL disable the confirm and retake buttons to prevent duplicate submissions.
4. IF the upload fails, THEN THE Photo_Uploader SHALL animate the progress indicator to an error state and display the error bubble.

### Requirement 4: Face Detection Celebration Animation

**User Story:** As a child user, I want a fun celebration when the app finds faces in my photo, so that the experience feels magical and rewarding.

#### Acceptance Criteria

1. WHEN the backend returns one or more detected faces after upload, THE Photo_Uploader SHALL play a celebration animation lasting between 1.5 and 3 seconds that includes particle or confetti effects.
2. WHEN the celebration animation plays, THE Photo_Uploader SHALL display the detected Face_Crop thumbnails within the celebration overlay so the child can see the faces that were found.
3. WHEN the celebration animation plays on a device that supports `navigator.vibrate`, THE Photo_Uploader SHALL trigger a Haptic_Pulse pattern (e.g., 100ms-50ms-100ms).
4. WHEN the celebration animation ends, THE Photo_Uploader SHALL transition smoothly back to the main capture UI.

### Requirement 5: Page Transition Animations

**User Story:** As a child user, I want smooth animated transitions between screens, so that the app feels fluid and alive rather than jumpy.

#### Acceptance Criteria

1. WHEN the user navigates between wizard steps in CharacterSetup (name → gender → spirit → photos), THE CharacterSetup SHALL animate the outgoing view out and the incoming view in using a slide or fade transition lasting between 200ms and 500ms.
2. WHEN the Photo_Gallery transitions between grid view and detail view, THE Photo_Gallery SHALL animate the transition using a scale-up or slide-in effect lasting between 200ms and 500ms.
3. THE CharacterSetup SHALL use CSS transitions or keyframe animations (no JavaScript-driven frame-by-frame animation) to maintain 60fps performance on mobile devices.

### Requirement 6: Haptic Feedback on Key Interactions

**User Story:** As a child user on a mobile device, I want to feel a little buzz when I tap important buttons, so that the app feels responsive and tactile.

#### Acceptance Criteria

1. WHEN the user taps the camera capture button in the Photo_Uploader, THE Photo_Uploader SHALL trigger a short Haptic_Pulse (≤ 50ms) on devices that support `navigator.vibrate`.
2. WHEN the user drops a Face_Chip onto a role slot in the Character_Mapper, THE Character_Mapper SHALL trigger a Haptic_Pulse (≤ 100ms) on devices that support `navigator.vibrate`.
3. WHEN the user taps the save button in the Character_Mapper, THE Character_Mapper SHALL trigger a Haptic_Pulse (≤ 50ms) on devices that support `navigator.vibrate`.
4. IF the device does not support `navigator.vibrate`, THEN THE Photo_Uploader and Character_Mapper SHALL skip the vibration call without errors.

### Requirement 7: Parent Approval Flow UI

**User Story:** As a parent, I want a dedicated screen to review and approve photos flagged for review, so that I can ensure only appropriate photos are used in my children's stories.

#### Acceptance Criteria

1. WHEN one or more photos have Photo_Status `review`, THE Parent_Approval_Screen SHALL display a notification badge on the photos step of the CharacterSetup wizard indicating the count of photos pending review.
2. THE Parent_Approval_Screen SHALL display each pending photo as a full-width preview image with two action buttons: approve (✅) and reject (🗑️), each meeting the minimum Touch_Target size.
3. WHEN the parent taps the approve button, THE Parent_Approval_Screen SHALL call the `POST /api/photos/{photo_id}/approve` endpoint and update the photo's status to `safe` in the UI without a full page reload.
4. WHEN the parent taps the reject button, THE Parent_Approval_Screen SHALL call the `DELETE /api/photos/{photo_id}` endpoint and remove the photo from the UI without a full page reload.
5. WHEN all pending photos have been reviewed, THE Parent_Approval_Screen SHALL display a completion message and allow the parent to return to the photos step.
6. THE Parent_Approval_Screen SHALL require a simple parent gate (e.g., a "hold for 3 seconds" long-press) before granting access, to prevent children from approving their own photos.

### Requirement 8: Drag-and-Drop Visual Feedback in Character Mapping

**User Story:** As a child user, I want to see clear visual cues when I drag a face onto a character slot, so that I know where to drop it and that the app understood my action.

#### Acceptance Criteria

1. WHILE the user is dragging a Face_Chip, THE Character_Mapper SHALL visually elevate the dragged chip (scale increase and drop shadow) to indicate it is being moved.
2. WHILE a Face_Chip is being dragged over a valid role slot, THE Character_Mapper SHALL highlight the target slot with a glowing border and a scale-up animation to indicate it is a valid drop target.
3. WHEN a Face_Chip is dropped onto a role slot, THE Character_Mapper SHALL animate the chip snapping into the slot with a spring or ease-out transition lasting between 150ms and 400ms.
4. WHEN a Face_Chip is dropped onto a role slot on a device that supports `navigator.vibrate`, THE Character_Mapper SHALL trigger a Haptic_Pulse (≤ 100ms).
5. WHEN a Face_Chip is dropped outside any valid role slot, THE Character_Mapper SHALL animate the chip returning to its original position in the face pool.

### Requirement 9: Empty State Illustrations

**User Story:** As a child user, I want to see a fun illustration when no photos have been uploaded yet, so that the empty screen feels inviting rather than broken.

#### Acceptance Criteria

1. WHEN the Photo_Gallery has zero photos, THE Photo_Gallery SHALL display an illustrated empty state with a colorful graphic (SVG or image) and a single-line prompt encouraging the user to add photos.
2. WHEN the Character_Mapper has zero labeled faces, THE Character_Mapper SHALL display an illustrated empty state with a colorful graphic and a single-line prompt encouraging the user to upload and label photos first.
3. THE Photo_Gallery empty state illustration SHALL have a minimum display size of 120×120 CSS pixels and use playful, child-friendly imagery.
4. THE Character_Mapper empty state illustration SHALL have a minimum display size of 120×120 CSS pixels and use playful, child-friendly imagery.

### Requirement 10: Photo Detail View with Face Bounding Boxes

**User Story:** As a child user, I want to see colored boxes around the faces the app found in my photo, so that I can understand which faces were detected and label them.

#### Acceptance Criteria

1. WHEN the Photo_Gallery detail view displays a photo, THE Photo_Gallery SHALL overlay a colored rectangle on the image for each detected face, positioned using the Bounding_Box coordinates (bbox_x, bbox_y, bbox_width, bbox_height) relative to the displayed image dimensions.
2. THE Photo_Gallery SHALL render each Bounding_Box overlay with a distinct bright color, rounded corners (border-radius ≥ 4px), and a semi-transparent fill so the face beneath remains visible.
3. WHEN the user taps a Bounding_Box overlay, THE Photo_Gallery SHALL open the face labeling form for the corresponding face, pre-filled with the existing name if one has been set.
4. THE Photo_Gallery SHALL scale the Bounding_Box overlays proportionally when the detail image is resized, so that the boxes remain aligned with the faces.

### Requirement 11: Sound Effects

**User Story:** As a child user, I want to hear fun sounds when I take a photo, complete an action, or drag things around, so that the app feels alive and playful.

#### Acceptance Criteria

1. WHEN the user taps the camera capture button in the Photo_Uploader, THE Photo_Uploader SHALL play a camera shutter sound effect.
2. WHEN the Photo_Uploader celebration animation plays after face detection, THE Photo_Uploader SHALL play a success chime sound effect.
3. WHEN the user begins dragging a Face_Chip in the Character_Mapper, THE Character_Mapper SHALL play a short whoosh or pick-up sound effect.
4. WHEN a Face_Chip is successfully dropped onto a role slot, THE Character_Mapper SHALL play a snap or success sound effect.
5. THE Photo_Uploader and Character_Mapper SHALL respect a global mute setting; WHILE the mute setting is active, THE Photo_Uploader and Character_Mapper SHALL suppress all sound effects.
6. THE Photo_Uploader and Character_Mapper SHALL preload sound effect audio files during component mount to avoid playback latency.
