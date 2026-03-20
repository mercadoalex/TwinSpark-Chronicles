# Requirements Document

## Introduction

The Storybook Gallery is a magical bookshelf feature for Twin Spark Chronicles where Ale & Sofi can revisit completed adventures. When a story session ends, the full adventure (all beats, scene images, narration, choices made, and perspective cards) is archived as a beautiful "storybook" on a virtual shelf. Children can browse their collection, tap a book to open it, and re-read the story page by page. Parents can manage (delete) stored stories. The gallery integrates into the existing app navigation and follows the "Living Storybook" design system with premium, immersive animations.

## Glossary

- **Gallery_View**: The main bookshelf screen displaying completed stories as tappable book covers arranged on animated wooden shelves.
- **Storybook**: A single archived adventure containing all beats, metadata, and the cover image derived from the first scene.
- **Story_Beat**: One scene within a story, containing narration text, child perspective cards, a scene image, and the choice that was made.
- **Story_Reader**: The full-screen view for re-reading a completed storybook beat by beat, with page-turn navigation.
- **Cover_Image**: The scene image from the first beat of a completed story, used as the book cover thumbnail on the shelf.
- **Story_Archive_Service**: The backend service responsible for persisting completed stories and their beats to the database.
- **Gallery_API**: The set of FastAPI endpoints that list, retrieve, and delete archived storybooks.
- **Gallery_Store**: The Zustand store on the frontend managing gallery state (story list, selected story, loading status).
- **Sibling_Pair_ID**: The colon-joined, alphabetically sorted pair of child names used to scope data per sibling pair (existing convention).
- **Parent_PIN**: The four-digit PIN used to authorize destructive parent actions such as story deletion (existing convention).

## Requirements

### Requirement 1: Archive Completed Stories

**User Story:** As the app, I want to automatically archive a completed story with all its beats, so that children can revisit past adventures.

#### Acceptance Criteria

1. WHEN a story session ends with status "complete", THE Story_Archive_Service SHALL persist a new Storybook record containing the Sibling_Pair_ID, a generated title, the story language, and the completion timestamp.
2. WHEN a Storybook record is created, THE Story_Archive_Service SHALL persist each Story_Beat in order, including beat index, narration text, child1 perspective, child2 perspective, scene image URL, the choice made, and the list of available choices.
3. THE Story_Archive_Service SHALL derive the Cover_Image from the scene image URL of the first Story_Beat in the archived story.
4. THE Story_Archive_Service SHALL store the total beat count and the story duration in seconds as metadata on the Storybook record.
5. IF the story session has zero completed beats, THEN THE Story_Archive_Service SHALL skip archival and log a warning.
6. IF a database write fails during archival, THEN THE Story_Archive_Service SHALL log the error and raise an exception without leaving partial data (all-or-nothing write within a transaction).

### Requirement 2: Gallery Listing API

**User Story:** As the frontend, I want to fetch a list of completed storybooks for a sibling pair, so that I can display the bookshelf.

#### Acceptance Criteria

1. WHEN a GET request is made to the Gallery_API list endpoint with a Sibling_Pair_ID, THE Gallery_API SHALL return a JSON array of Storybook summaries sorted by completion date descending.
2. THE Gallery_API SHALL include in each summary: storybook ID, title, Cover_Image URL, completion date, beat count, and duration in seconds.
3. WHEN no archived storybooks exist for the given Sibling_Pair_ID, THE Gallery_API SHALL return an empty JSON array with HTTP status 200.

### Requirement 3: Story Detail API

**User Story:** As the frontend, I want to fetch the full detail of a single storybook including all beats, so that I can render the Story_Reader.

#### Acceptance Criteria

1. WHEN a GET request is made to the Gallery_API detail endpoint with a storybook ID, THE Gallery_API SHALL return the full Storybook record including all Story_Beat records in beat-index order.
2. Each Story_Beat in the response SHALL include: beat index, narration, child1 perspective, child2 perspective, scene image URL, choice made, and available choices.
3. IF the requested storybook ID does not exist, THEN THE Gallery_API SHALL return HTTP status 404 with a descriptive error message.

### Requirement 4: Story Deletion API

**User Story:** As a parent, I want to delete a storybook from the gallery, so that I can manage storage and content.

#### Acceptance Criteria

1. WHEN a DELETE request is made to the Gallery_API with a storybook ID and a valid Parent_PIN header, THE Gallery_API SHALL delete the Storybook and all associated Story_Beat records.
2. IF the Parent_PIN header is missing or invalid, THEN THE Gallery_API SHALL return HTTP status 401.
3. IF the requested storybook ID does not exist, THEN THE Gallery_API SHALL return HTTP status 404.
4. WHEN a bulk-delete request is made with a Sibling_Pair_ID and a valid Parent_PIN header, THE Gallery_API SHALL delete all Storybooks and associated beats for that sibling pair and return the count of deleted storybooks.

### Requirement 5: Gallery Bookshelf View

**User Story:** As Ale or Sofi, I want to see a magical bookshelf of past adventures, so that I can pick one to re-read.

#### Acceptance Criteria

1. WHEN the Gallery_View is opened, THE Gallery_View SHALL display each Storybook as a book cover card showing the Cover_Image, title, and a sparkle decoration.
2. THE Gallery_View SHALL arrange book covers on horizontal wooden shelf rows with a warm, glowing ambient animation consistent with the Living Storybook design system.
3. WHEN a book cover is tapped, THE Gallery_View SHALL navigate to the Story_Reader for that storybook with a book-opening transition animation.
4. THE Gallery_View SHALL use touch targets of at least 120px by 160px for each book cover card to meet child-friendly tap requirements.
5. WHILE the gallery data is loading, THE Gallery_View SHALL display a shimmer skeleton placeholder shaped like book covers on shelves.
6. WHEN no storybooks exist for the sibling pair, THE Gallery_View SHALL display an empty-state illustration with the message "No adventures yet — start your first story!" and a call-to-action button.

### Requirement 6: Story Reader View

**User Story:** As Ale or Sofi, I want to re-read a past adventure page by page, so that I can relive the story.

#### Acceptance Criteria

1. WHEN the Story_Reader opens a storybook, THE Story_Reader SHALL display the first Story_Beat with its scene image, narration text, and the choice that was made, highlighted with a subtle glow.
2. THE Story_Reader SHALL provide forward and backward navigation controls (arrow buttons and swipe gestures) to move between beats.
3. WHEN the child navigates to a new beat, THE Story_Reader SHALL animate the transition using a page-turn or slide effect consistent with the TransitionEngine style.
4. THE Story_Reader SHALL display a page indicator showing the current beat number out of the total beat count (e.g., "3 / 8").
5. WHEN the child taps the narration area, THE Story_Reader SHALL expand to show the child1 and child2 perspective cards, matching the DualStoryDisplay tap-to-expand pattern.
6. THE Story_Reader SHALL display the choice that was made for each beat with a "You chose:" label and the selected choice icon.
7. WHEN the child reaches the last beat, THE Story_Reader SHALL display a "The End" card with a celebration sparkle animation and a button to return to the Gallery_View.
8. THE Story_Reader SHALL provide a close button to return to the Gallery_View at any time.

### Requirement 7: Gallery Navigation Integration

**User Story:** As a user, I want to access the storybook gallery from the main app, so that I can easily find past adventures.

#### Acceptance Criteria

1. WHEN the app setup is complete and a story session is active, THE App SHALL display a bookshelf icon button in the top navigation bar that opens the Gallery_View as a full-screen overlay.
2. WHEN the Gallery_View close button is tapped, THE App SHALL return to the previous screen (story session or dashboard) without losing state.
3. THE Gallery_View SHALL be accessible from the Parent Dashboard as a "Story Gallery" link.

### Requirement 8: Parent Story Management

**User Story:** As a parent, I want to manage stored storybooks, so that I can delete stories and control content.

#### Acceptance Criteria

1. WHEN a parent enters the Gallery_View from the Parent Dashboard, THE Gallery_View SHALL display a delete button on each book cover card.
2. WHEN the delete button is tapped, THE Gallery_View SHALL show a confirmation dialog asking "Delete this adventure?" with confirm and cancel options.
3. WHEN the parent confirms deletion, THE Gallery_View SHALL call the Gallery_API delete endpoint with the Parent_PIN and remove the book from the shelf with a fade-out animation.
4. IF the deletion API call fails, THEN THE Gallery_View SHALL display a child-friendly error message and keep the book on the shelf.

### Requirement 9: Gallery Data Store

**User Story:** As the frontend, I want a dedicated store for gallery state, so that gallery data is managed independently from the active story session.

#### Acceptance Criteria

1. THE Gallery_Store SHALL maintain the list of Storybook summaries, the currently selected Storybook detail, loading state, and error state.
2. WHEN the Gallery_View mounts, THE Gallery_Store SHALL fetch the storybook list from the Gallery_API for the current Sibling_Pair_ID.
3. WHEN a storybook is deleted, THE Gallery_Store SHALL remove the storybook from the local list without re-fetching the full list.
4. THE Gallery_Store SHALL expose a reset action that clears all gallery state.

### Requirement 10: Accessibility and Reduced Motion

**User Story:** As a child using assistive technology, I want the gallery to be accessible, so that I can browse and read stories.

#### Acceptance Criteria

1. THE Gallery_View SHALL use semantic HTML with appropriate ARIA labels on the bookshelf region, each book cover button, and navigation controls.
2. THE Story_Reader SHALL announce page changes to screen readers using an aria-live polite region.
3. WHILE the user has prefers-reduced-motion enabled, THE Gallery_View SHALL disable shelf glow animations and book-opening transitions, using instant state changes instead.
4. THE Gallery_View SHALL support keyboard navigation with visible focus indicators on all interactive elements.

### Requirement 11: Storybook Serialization Round-Trip

**User Story:** As the system, I want to ensure that story data survives a full save-and-load cycle without loss, so that children always see their complete adventures.

#### Acceptance Criteria

1. FOR ALL valid Storybook records, archiving a story then retrieving the story via the Gallery_API detail endpoint SHALL produce a response containing identical narration, perspectives, choices, and beat ordering as the original session data.
2. FOR ALL valid Story_Beat records, the scene image URL, choice made, and available choices list SHALL be identical after a round-trip through the database.
