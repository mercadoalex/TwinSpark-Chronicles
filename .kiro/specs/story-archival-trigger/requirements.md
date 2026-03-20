# Requirements Document

## Introduction

The Story Archival Trigger feature wires up the existing `StoryArchiveService.archive_story()` so that completed stories are automatically archived to the gallery when a session ends. Currently, the archival service is fully implemented and tested, the gallery frontend is built, but nothing invokes `archive_story()` — leaving the gallery permanently empty. This feature bridges that gap by triggering archival from the session-end flow, transforming the frontend story history into the beat format expected by the archive service, and generating a meaningful story title.

## Glossary

- **Orchestrator**: The `AgentOrchestrator` class in `backend/app/agents/orchestrator.py` that coordinates session lifecycle including `end_session()`
- **Archive_Service**: The `StoryArchiveService` class that persists completed stories to the `storybooks` and `story_beats` database tables
- **End_Session_Endpoint**: The `POST /api/sessions/{session_id}/end` FastAPI route that triggers session teardown
- **Story_History**: The array of beat objects accumulated in the frontend `storyStore.history[]` during a storytelling session
- **Beat**: A single story segment containing narration, child perspectives, scene image, and choice data
- **Gallery_API**: The existing `GET /api/gallery/{sibling_pair_id}` endpoint that returns archived storybooks
- **Session_Snapshot**: The payload sent via `POST /api/session/save` containing `story_history`, `character_profiles`, and `session_metadata`
- **Sibling_Pair_ID**: A colon-joined, alphabetically sorted string of the two child names (e.g., `"Ale:Sofi"`)
- **Title_Generator**: A component that produces a human-readable story title from the session's beat content
- **Archival_Result**: The `StorybookRecord` returned by `archive_story()` on success, or `None` on failure

## Requirements

### Requirement 1: Trigger Archival on Session End

**User Story:** As a parent, I want completed stories to be automatically saved to the gallery when a session ends, so that my children can revisit their adventures later.

#### Acceptance Criteria

1. WHEN `end_session()` is called on the Orchestrator with a valid session_id and Sibling_Pair_ID, THE Orchestrator SHALL invoke `Archive_Service.archive_story()` with the story data from that session
2. WHEN the Orchestrator triggers archival, THE Orchestrator SHALL execute archival after sibling dynamics computation but before returning the end-session response
3. IF archival fails with an exception, THEN THE Orchestrator SHALL log the error and continue returning the end-session response without raising an error to the caller
4. WHEN archival succeeds, THE End_Session_Endpoint SHALL include the `storybook_id` from the Archival_Result in the end-session response
5. IF archival fails or is skipped, THEN THE End_Session_Endpoint SHALL return `null` for the `storybook_id` field in the end-session response

### Requirement 2: Collect Story Data for Archival

**User Story:** As a developer, I want the session-end flow to gather all story beats and metadata needed for archival, so that `archive_story()` receives complete and correctly shaped data.

#### Acceptance Criteria

1. WHEN the Orchestrator prepares data for archival, THE Orchestrator SHALL retrieve the Story_History from the Session_Snapshot stored for the given Sibling_Pair_ID
2. WHEN the Orchestrator retrieves the Session_Snapshot, THE Orchestrator SHALL extract the `story_history` array, `session_metadata.language`, and `session_metadata.session_duration_seconds` fields
3. THE Orchestrator SHALL transform each Story_History entry into the Beat format expected by Archive_Service, mapping `narration`, `child1_perspective`, `child2_perspective`, `scene_image_url`, `choiceMade` to `choice_made`, and `choices` to `available_choices`
4. IF the Story_History is empty or contains zero beats, THEN THE Orchestrator SHALL skip archival and log a warning
5. WHEN the Session_Snapshot is not found for the given Sibling_Pair_ID, THE Orchestrator SHALL skip archival and log a warning

### Requirement 3: Generate Story Title

**User Story:** As a child browsing the gallery, I want each story to have a descriptive title, so that I can recognize and pick the adventure I want to re-read.

#### Acceptance Criteria

1. WHEN the Orchestrator prepares archival data, THE Title_Generator SHALL produce a title string from the first beat's narration text
2. THE Title_Generator SHALL truncate the narration to a readable length of 60 characters or fewer, breaking at the nearest word boundary
3. IF the first beat has no narration or the narration is empty, THEN THE Title_Generator SHALL use the fallback title `"Untitled Adventure"`
4. THE Title_Generator SHALL append an ellipsis (`…`) to truncated titles to indicate continuation

### Requirement 4: Frontend Sends Story Data Before Session End

**User Story:** As a developer, I want the frontend to persist the story snapshot before calling the end-session endpoint, so that the backend has the story data available for archival.

#### Acceptance Criteria

1. WHEN the user triggers save-and-exit, THE Frontend SHALL call `saveSnapshot()` to persist the Session_Snapshot to the backend before calling the End_Session_Endpoint
2. WHEN `saveSnapshot()` completes, THE Frontend SHALL call the End_Session_Endpoint with the session ID and character data
3. IF `saveSnapshot()` fails after retry, THEN THE Frontend SHALL still call the End_Session_Endpoint so that sibling dynamics are computed even without archival

### Requirement 5: Archival Response Feedback

**User Story:** As a parent, I want to know that a story was saved to the gallery, so that I have confidence the adventure is preserved.

#### Acceptance Criteria

1. WHEN the End_Session_Endpoint returns a non-null `storybook_id`, THE Frontend SHALL display a confirmation indicator that the story was archived to the gallery
2. WHEN the End_Session_Endpoint returns a null `storybook_id`, THE Frontend SHALL not display any archival error to the user
3. WHEN a story is successfully archived, THE Gallery_API SHALL return the newly archived storybook in subsequent listing requests for the same Sibling_Pair_ID
