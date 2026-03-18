# Implementation Plan: Parent Approval Flow

## Overview

Enhance the existing `ParentApprovalScreen`, `photoStore`, and `ParentControls` to deliver a polished, accessible photo review experience. The store gains error-reporting return values on approve/delete actions. The approval screen gains per-photo loading states, inline errors, rejection confirmation, image placeholders, and accessibility hooks. ParentControls gains a "Review Photos" entry point with pending count badge. No backend changes needed.

## Tasks

- [x] 1. Enhance photoStore with error-reporting return values
  - [x] 1.1 Update `approvePhoto` to return `{ success, error }` result
    - Modify `approvePhoto` in `frontend/src/stores/photoStore.js`
    - Return `{ success: true }` on successful API response
    - Return `{ success: false, error: 'server' }` on non-ok response (after reverting)
    - Return `{ success: false, error: 'network' }` on fetch exception (after reverting)
    - Preserve existing optimistic update and revert behavior
    - _Requirements: 4.1, 4.2, 4.3, 8.2, 8.3_

  - [x] 1.2 Update `deletePhoto` to return `{ success, error }` result
    - Modify `deletePhoto` in `frontend/src/stores/photoStore.js`
    - Return `{ success: true }` on successful API response
    - Return `{ success: false, error: 'server' }` on non-ok response (after reverting)
    - Return `{ success: false, error: 'network' }` on fetch exception (after reverting)
    - Preserve existing optimistic update and revert behavior
    - _Requirements: 5.2, 5.3, 5.4, 8.2, 8.3_

  - [ ]* 1.3 Write property tests for photoStore approve/delete actions
    - **Property 5: Approve success transitions status** — for any photo with status `review`, when `approvePhoto` succeeds, status becomes `safe`
    - **Validates: Requirements 4.2**
    - **Property 6: Approve failure reverts status** — for any photo with status `review`, when `approvePhoto` fails, status remains `review`
    - **Validates: Requirements 4.3**
    - **Property 7: Delete success removes photo** — for any photo, when `deletePhoto` succeeds, photo is removed from store
    - **Validates: Requirements 5.3**
    - **Property 8: Delete failure restores photo** — for any photo, when `deletePhoto` fails, photo remains in store with original data
    - **Validates: Requirements 5.4**

- [x] 2. Enhance ParentApprovalScreen with review UX
  - [x] 2.1 Add per-photo metadata display and upload-date sorting
    - Show filename and formatted upload date below each photo image
    - Sort pending photos by `uploaded_at` ascending (oldest first)
    - Update heading to show count: "Review Photos (N)"
    - _Requirements: 3.1, 3.2, 3.4_

  - [x] 2.2 Add image load error placeholder
    - Track image load failures in `imageLoadErrors` state (Set of photo IDs)
    - On `<img>` `onError`, add photo ID to set and render a placeholder icon instead of broken image
    - _Requirements: 3.3_

  - [x] 2.3 Add per-photo loading states and button disabling
    - Track `actionInProgress` state as `Record<string, 'approving' | 'rejecting'>`
    - Disable approve and reject buttons while action is in progress for that photo
    - Add `aria-busy="true"` on the photo card during API calls
    - _Requirements: 4.4_

  - [x] 2.4 Add inline error messages per photo
    - Track `photoErrors` state as `Record<string, string>`
    - On approve/reject failure, set error message from store result (`'server'` → "Something went wrong", `'network'` → "Connection issue")
    - Display inline error below the photo card actions
    - Clear error when user retries the action
    - _Requirements: 8.2, 8.3_

  - [x] 2.5 Add rejection confirmation dialog
    - Track `rejectConfirmId` state (photo ID or null)
    - On reject button tap, set `rejectConfirmId` instead of immediately deleting
    - Render inline confirmation with `role="alertdialog"` and `aria-label="Confirm photo rejection"`
    - "Remove" button confirms and calls `deletePhoto`; "Cancel" button dismisses
    - _Requirements: 5.1, 5.5_

  - [x] 2.6 Add load error state with retry button
    - Track `loadError` boolean state
    - If `photoStore.error` is set after `loadPhotos`, show error message with "Retry" button
    - Retry button calls `loadPhotos` again
    - _Requirements: 8.1_

  - [ ]* 2.7 Write property tests for review display
    - **Property 1: Pending review count accuracy** — for any photo array, computed pending count equals number of photos with status `review`
    - **Validates: Requirements 1.1, 9.3**
    - **Property 2: Photo card displays required metadata** — for any photo with filename and upload date, card contains both
    - **Validates: Requirements 3.1**
    - **Property 3: Heading reflects queue size** — for any non-empty pending list, heading contains the count
    - **Validates: Requirements 3.2**
    - **Property 4: Photos ordered by upload date ascending** — for any photo list, displayed order is sorted by upload date ascending
    - **Validates: Requirements 3.4**

  - [ ]* 2.8 Write property test for empty queue completion
    - **Property 9: Empty queue shows completion** — when zero photos have status `review`, approval flow renders completion view
    - **Validates: Requirements 6.1**

  - [ ]* 2.9 Write property test for API failure behavior
    - **Property 12: API failure displays error and retains photo** — when approve/reject fails, inline error is shown and photo remains in queue
    - **Validates: Requirements 8.2, 8.3**

- [x] 3. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Add accessibility enhancements to ParentApprovalScreen
  - [x] 4.1 Integrate `useFocusTrap` on review area
    - Add ref to review container and activate `useFocusTrap` after gate unlock
    - Move focus to review area heading after gate unlocks
    - Support Escape key to dismiss (via focus trap's `onClose`)
    - _Requirements: 7.1, 7.4_

  - [x] 4.2 Add screen reader announcements with `useAnnounce`
    - Announce approve/reject outcomes: "Photo approved", "Photo removed", "Failed to approve photo"
    - Announce when all photos reviewed: "All photos reviewed"
    - _Requirements: 7.3_

  - [x] 4.3 Add descriptive `aria-label` attributes to all interactive elements
    - Approve button: `"Approve photo {filename}"`
    - Reject button: `"Reject photo {filename}"`
    - Done button: appropriate label
    - Confirmation dialog buttons: `"Confirm removal"`, `"Cancel removal"`
    - _Requirements: 7.2_

  - [x] 4.4 Ensure minimum 48×48px touch targets on all buttons
    - Verify `minWidth: 48px` and `minHeight: 48px` on approve, reject, done, confirm, and cancel buttons
    - _Requirements: 7.5_

  - [ ]* 4.5 Write property tests for accessibility
    - **Property 10: Interactive elements have aria-labels** — for any rendered photo card, approve and reject buttons have non-empty `aria-label`
    - **Validates: Requirements 7.2**
    - **Property 11: Touch targets meet minimum size** — for any approve/reject button, element has minWidth and minHeight ≥ 48px
    - **Validates: Requirements 7.5**

- [x] 5. Integrate "Review Photos" entry point into ParentControls
  - [x] 5.1 Add "Review Photos" section to ParentControls
    - Add new `<section>` to `frontend/src/components/ParentControls.jsx`
    - Read pending review count from `usePhotoStore` (filter photos with `status === 'review'`)
    - Display "Review Photos" button with pending count badge when count > 0
    - Display "No photos to review" secondary text when count is 0
    - Accept new `onReviewPhotos` callback prop
    - _Requirements: 9.1, 9.2, 9.3_

  - [x] 5.2 Add CSS styles for review entry point and badge
    - Add `.pc-review-btn`, `.pc-review-badge`, `.pc-review-secondary` styles to `frontend/src/components/ParentControls.css`
    - Badge uses gradient background matching existing theme
    - Button meets 48×48px minimum touch target
    - _Requirements: 1.1, 9.3_

  - [x] 5.3 Wire `onReviewPhotos` callback in parent component
    - Update the component that renders `ParentControls` to pass `onReviewPhotos` prop
    - Navigate to `ParentApprovalScreen` when "Review Photos" is tapped
    - _Requirements: 9.1_

  - [ ]* 5.4 Write unit tests for ParentControls review entry point
    - Test badge shows correct pending count
    - Test "No photos to review" text when count is 0
    - Test `onReviewPhotos` callback fires on click
    - _Requirements: 9.1, 9.2, 9.3_

- [x] 6. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Property tests use `fast-check` with Vitest (minimum 100 iterations per property)
- No backend changes needed — existing approve and delete endpoints are sufficient
- Inline styles preserved to match existing codebase conventions
- All `<img>` elements include `onError` fallback to placeholder
