# Requirements Document

## Introduction

The backend already supports a `REVIEW` photo status and an `/api/photos/{photo_id}/approve` endpoint, and the frontend has a `ParentApprovalScreen` component with a 3-second hold-to-unlock parent gate. However, the actual photo review UI inside that screen is minimal — it lacks feedback states, error handling, notification of pending reviews, and integration with the broader parent controls surface. This feature fills that gap by giving parents a polished, accessible approval flow so they can review, approve, or reject photos flagged by the content scanner before those photos enter the story pipeline.

## Glossary

- **Parent_Gate**: The 3-second long-press mechanism that prevents children from accessing parent-only screens.
- **Photo_Review_Queue**: The ordered list of photos with `REVIEW` status awaiting parent action for a given sibling pair.
- **Approval_Flow**: The end-to-end process a parent follows: unlock gate → review photos → approve or reject each → return to app.
- **Photo_Service**: The backend service (`photo_service.py`) that manages photo lifecycle including status transitions.
- **Photo_Store**: The frontend Zustand store (`photoStore.js`) that holds photo state and exposes `approvePhoto` / `deletePhoto` actions.
- **Parent_Controls**: The existing settings panel (`ParentControls.jsx`) where parents configure themes, complexity, and blocked words.
- **Content_Scanner**: The backend service that assigns safety ratings (SAFE, REVIEW, BLOCKED) to uploaded photos.
- **Review_Badge**: A visual indicator on a photo thumbnail showing it is pending parent review.

## Requirements

### Requirement 1: Pending Review Notification

**User Story:** As a parent, I want to be notified when photos are waiting for my review, so that I know to take action before my children's story session is affected.

#### Acceptance Criteria

1. WHEN one or more photos in the Photo_Review_Queue have status `review`, THE Parent_Controls SHALL display a visible badge indicating the count of pending photos.
2. WHEN the pending photo count changes, THE Parent_Controls badge SHALL update within 2 seconds of the Photo_Store state change.
3. WHEN no photos have status `review`, THE Parent_Controls SHALL hide the pending review badge.

### Requirement 2: Parent Gate Access

**User Story:** As a parent, I want the review screen protected behind a child-proof gate, so that my children cannot approve or reject photos themselves.

#### Acceptance Criteria

1. THE Parent_Gate SHALL require a continuous 3-second press to unlock the Approval_Flow.
2. WHEN the parent releases the press before 3 seconds, THE Parent_Gate SHALL reset progress to zero.
3. WHEN the Parent_Gate is unlocked, THE Approval_Flow SHALL display the Photo_Review_Queue.
4. THE Parent_Gate SHALL support both pointer (touch/mouse) and keyboard (Enter/Space) activation.

### Requirement 3: Photo Review Display

**User Story:** As a parent, I want to see each flagged photo clearly with relevant context, so that I can make an informed approve/reject decision.

#### Acceptance Criteria

1. WHEN the Approval_Flow is active, THE Photo_Review_Queue SHALL display each pending photo as a card with the photo image, filename, and upload date.
2. THE Approval_Flow SHALL display the total count of remaining pending photos in a heading.
3. WHEN a photo image fails to load, THE Approval_Flow SHALL display a placeholder instead of a broken image.
4. THE Approval_Flow SHALL present photos in upload-date ascending order (oldest first).

### Requirement 4: Approve Action

**User Story:** As a parent, I want to approve a flagged photo so that it becomes available for face extraction and story use.

#### Acceptance Criteria

1. WHEN a parent taps the approve button on a photo card, THE Photo_Store SHALL send a POST request to `/api/photos/{photo_id}/approve`.
2. WHEN the approve request succeeds, THE Photo_Store SHALL optimistically update the photo status from `review` to `safe` in local state.
3. WHEN the approve request fails, THE Photo_Store SHALL revert the photo status to `review` in local state.
4. WHILE an approve request is in progress, THE Approval_Flow SHALL disable the approve and reject buttons for that photo to prevent duplicate submissions.

### Requirement 5: Reject Action

**User Story:** As a parent, I want to reject a flagged photo so that it is permanently removed and never used in stories.

#### Acceptance Criteria

1. WHEN a parent taps the reject button on a photo card, THE Approval_Flow SHALL display a confirmation prompt before deletion.
2. WHEN the parent confirms rejection, THE Photo_Store SHALL send a DELETE request to `/api/photos/{photo_id}`.
3. WHEN the delete request succeeds, THE Photo_Store SHALL remove the photo from local state.
4. WHEN the delete request fails, THE Photo_Store SHALL restore the photo in local state and THE Approval_Flow SHALL display an inline error message.
5. WHEN the parent cancels the rejection confirmation, THE Approval_Flow SHALL dismiss the prompt and take no action.

### Requirement 6: Review Completion

**User Story:** As a parent, I want a clear indication when all photos have been reviewed, so that I know I can return to the app.

#### Acceptance Criteria

1. WHEN the Photo_Review_Queue becomes empty after the last photo is approved or rejected, THE Approval_Flow SHALL display a completion message.
2. THE Approval_Flow completion view SHALL include a "Done" button that returns the parent to the previous screen.
3. WHEN the "Done" button is activated, THE Approval_Flow SHALL invoke the `onComplete` callback.

### Requirement 7: Accessibility

**User Story:** As a parent using assistive technology, I want the approval flow to be fully navigable with a keyboard and screen reader, so that I can review photos regardless of how I interact with the device.

#### Acceptance Criteria

1. THE Approval_Flow SHALL manage focus by moving focus to the review area heading after the Parent_Gate is unlocked.
2. THE Approval_Flow approve and reject buttons SHALL have descriptive `aria-label` attributes (e.g., "Approve photo", "Reject photo").
3. WHEN a photo is approved or rejected, THE Approval_Flow SHALL announce the result to screen readers using a live region.
4. THE Approval_Flow SHALL be fully operable using keyboard-only navigation (Tab, Enter, Space, Escape).
5. THE Approval_Flow approve and reject buttons SHALL meet a minimum touch target size of 48×48 CSS pixels.

### Requirement 8: Error Handling

**User Story:** As a parent, I want clear feedback when something goes wrong during review, so that I understand what happened and can retry.

#### Acceptance Criteria

1. IF the Photo_Store fails to load photos for the Photo_Review_Queue, THEN THE Approval_Flow SHALL display an error message with a "Retry" button.
2. IF an approve or reject API call returns a server error, THEN THE Approval_Flow SHALL display an inline error message on the affected photo card.
3. IF a network error occurs during an approve or reject action, THEN THE Approval_Flow SHALL display a connectivity error message and retain the photo in the queue.

### Requirement 9: Integration with Parent Controls

**User Story:** As a parent, I want to access the photo review flow from the existing Parent Controls panel, so that I have a single place for all parental settings and actions.

#### Acceptance Criteria

1. THE Parent_Controls panel SHALL include a "Review Photos" entry point that navigates to the Approval_Flow.
2. WHEN no photos are pending review, THE Parent_Controls "Review Photos" entry point SHALL be visible but display "No photos to review" as secondary text.
3. WHEN photos are pending review, THE Parent_Controls "Review Photos" entry point SHALL display the pending count as a badge.
