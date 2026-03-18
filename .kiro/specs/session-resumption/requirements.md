# Requirements Document

## Introduction

Session Resumption adds the ability for siblings to save their story progress and return to continue where they left off. Currently, closing the browser loses all story state — character setup, story beats, generated scene images, and world context vanish. This feature persists the full session snapshot (character profiles, story history, current beat, generated assets, and world state references) to the backend database, and provides a magical "Continue Story" experience on the landing screen so 6-year-old twins can jump back into their adventure with a single tap.

## Glossary

- **Session_Snapshot**: The complete serializable state of a story session, including character profiles, story history, current beat, generated asset references, and session metadata.
- **Session_Service**: The backend service responsible for saving, loading, listing, and deleting Session_Snapshots in the SQLite database.
- **Session_API**: The set of FastAPI endpoints (`/api/session/save`, `/api/session/load`, `/api/session/list`, `/api/session/delete`) for session persistence operations.
- **Session_Store**: The Zustand store on the frontend that manages session persistence state (save status, available sessions, restore progress).
- **Continue_Screen**: The frontend UI component displayed on the landing screen when a resumable session exists, showing a visual preview of the last story moment and a "Continue Story" call-to-action.
- **Story_History**: The ordered list of completed story beats with their narration, perspectives, scene images, and choices made.
- **Character_Profiles**: The sibling character data including names, genders, spirit animals, personalities, and toy companions.
- **Auto_Save**: The mechanism that automatically persists the Session_Snapshot at key story progression points without user intervention.
- **Sibling_Pair_ID**: The unique identifier for a pair of siblings, derived from their sorted names (e.g., "Ale:Sofi").
- **Landing_Screen**: The initial screen shown after privacy acceptance and language selection, where the Continue_Screen appears if a resumable session exists.

## Requirements

### Requirement 1: Session Snapshot Data Model

**User Story:** As a developer, I want a structured data model for session snapshots, so that all session state can be persisted and restored reliably.

#### Acceptance Criteria

1. THE Session_Service SHALL store Session_Snapshot records with fields: id, sibling_pair_id, character_profiles (JSON), story_history (JSON), current_beat (JSON), session_metadata (JSON), created_at, and updated_at.
2. THE Session_Service SHALL store session_metadata containing: language, story_beat_count, last_choice_made, and session_duration_seconds.
3. THE Session_Service SHALL enforce that each Sibling_Pair_ID has at most one active Session_Snapshot.
4. WHEN a Session_Snapshot is saved for a Sibling_Pair_ID that already has an active snapshot, THE Session_Service SHALL overwrite the existing snapshot with the new data and update the updated_at timestamp.
5. THE Session_Service SHALL store generated asset references (scene image URLs) within the story_history JSON rather than duplicating binary data.

### Requirement 2: Session Save

**User Story:** As a sibling pair, I want my story progress to be saved automatically, so that I never lose my adventure even if the browser closes unexpectedly.

#### Acceptance Criteria

1. WHEN a story beat is completed (choice made by siblings), THE Auto_Save SHALL persist the current Session_Snapshot to the backend via the Session_API.
2. WHEN the user explicitly exits via the Exit Modal, THE App SHALL save the Session_Snapshot before disconnecting the WebSocket.
3. WHEN the browser `beforeunload` event fires during an active story session, THE App SHALL attempt to save the Session_Snapshot using the Beacon API.
4. IF the Session_API save request fails, THEN THE App SHALL retry the save once after a 2-second delay.
5. IF the retry also fails, THEN THE App SHALL store the Session_Snapshot in localStorage as a fallback and log a warning.
6. THE Auto_Save SHALL complete the save operation without blocking story progression or user interaction.
7. WHILE a save operation is in progress, THE Session_Store SHALL track the save status as "saving" and update to "saved" or "error" upon completion.

### Requirement 3: Session Load

**User Story:** As a sibling pair, I want to pick up our story exactly where we left off, so that the adventure feels continuous.

#### Acceptance Criteria

1. WHEN the App starts and a Sibling_Pair_ID is known, THE Session_Store SHALL check the Session_API for an existing Session_Snapshot.
2. WHEN a valid Session_Snapshot is found, THE Continue_Screen SHALL display a visual preview of the last story moment.
3. WHEN the siblings tap "Continue Story" on the Continue_Screen, THE App SHALL restore the Character_Profiles to the Setup_Store, restore the Story_History to the Story_Store, restore the current beat to the Story_Store, and reconnect the WebSocket with the restored Character_Profiles.
4. WHEN the session is restored, THE App SHALL skip the character setup wizard and proceed directly to the story experience.
5. IF the Session_Snapshot is corrupted or cannot be parsed, THEN THE App SHALL discard the snapshot, log an error, and present the normal setup flow.
6. IF a localStorage fallback snapshot exists and no server snapshot is found, THEN THE App SHALL attempt to restore from the localStorage snapshot and re-sync to the server.
7. THE Session_Store SHALL load the Session_Snapshot within 1 second for snapshots containing up to 50 story beats.

### Requirement 4: Continue Screen UI

**User Story:** As a 6-year-old sibling, I want to see my last adventure waiting for me when I come back, so that I feel excited to continue.

#### Acceptance Criteria

1. WHEN a resumable Session_Snapshot exists, THE Continue_Screen SHALL display the last scene image from the Story_History as a visual preview.
2. THE Continue_Screen SHALL display the sibling names and spirit animal icons from the Character_Profiles.
3. THE Continue_Screen SHALL display a large, animated "Continue Story" button with a sparkle or glow effect.
4. THE Continue_Screen SHALL display a "New Adventure" option as a secondary action, allowing siblings to start fresh.
5. WHEN "New Adventure" is selected, THE App SHALL prompt for confirmation before deleting the existing Session_Snapshot.
6. THE Continue_Screen SHALL use minimal text and rely primarily on visual elements (images, icons, animations), suitable for children aged 6.
7. THE Continue_Screen SHALL play a welcoming sound effect or short musical cue when it appears.
8. THE Continue_Screen SHALL display the character names in a friendly greeting (e.g., "Welcome back, Ale & Sofi").

### Requirement 5: Session API Endpoints

**User Story:** As a frontend developer, I want API endpoints for saving and loading session snapshots, so that the frontend can persist and restore session state.

#### Acceptance Criteria

1. THE Session_API SHALL expose a POST endpoint at `/api/session/save` that accepts a Session_Snapshot JSON body and persists the snapshot to the database.
2. THE Session_API SHALL expose a GET endpoint at `/api/session/load/{sibling_pair_id}` that returns the active Session_Snapshot for the given Sibling_Pair_ID.
3. THE Session_API SHALL expose a DELETE endpoint at `/api/session/{sibling_pair_id}` that deletes the active Session_Snapshot for the given Sibling_Pair_ID.
4. WHEN the save endpoint receives a valid Session_Snapshot, THE Session_API SHALL return HTTP 200 with a JSON body containing the snapshot id and updated_at timestamp.
5. WHEN the load endpoint finds no snapshot for the given Sibling_Pair_ID, THE Session_API SHALL return HTTP 404 with a JSON body containing an error message.
6. IF the save endpoint receives an invalid or incomplete Session_Snapshot, THEN THE Session_API SHALL return HTTP 422 with a JSON body describing the validation errors.
7. IF an internal database error occurs, THEN THE Session_API SHALL return HTTP 500 with a JSON error message.
8. FOR ALL valid Session_Snapshot objects, saving then loading SHALL produce an equivalent Session_Snapshot object (round-trip property).

### Requirement 6: Session Database Schema

**User Story:** As a developer, I want a database migration for the session snapshots table, so that session data is stored reliably using the existing migration infrastructure.

#### Acceptance Criteria

1. THE Session_Service SHALL create a `session_snapshots` table via the existing migration runner infrastructure.
2. THE migration SHALL create the table with columns: id (TEXT PRIMARY KEY), sibling_pair_id (TEXT NOT NULL), character_profiles (TEXT NOT NULL), story_history (TEXT NOT NULL), current_beat (TEXT), session_metadata (TEXT NOT NULL), created_at (TEXT NOT NULL), and updated_at (TEXT NOT NULL).
3. THE migration SHALL create a unique index on sibling_pair_id to enforce the one-active-snapshot-per-pair constraint.
4. THE migration SHALL be idempotent and safe to run multiple times without data loss.

### Requirement 7: Interrupted Session Handling

**User Story:** As a sibling pair, I want my story to be safe even if the internet drops or the tablet runs out of battery, so that I never lose my progress.

#### Acceptance Criteria

1. WHEN the WebSocket connection drops unexpectedly during a story session, THE App SHALL save the current Session_Snapshot to localStorage immediately.
2. WHEN the WebSocket reconnects after an unexpected disconnection, THE App SHALL sync the localStorage snapshot to the server via the Session_API.
3. WHEN the browser `visibilitychange` event fires with `document.hidden === true` during an active session, THE App SHALL trigger an Auto_Save to the server.
4. IF both the server save and localStorage save fail, THEN THE App SHALL display a child-friendly warning icon (not text-heavy error) indicating that progress may not be saved.
5. WHEN the App restores a session after an interruption, THE App SHALL resume from the last successfully saved story beat rather than attempting to replay in-flight generation.

### Requirement 8: Session Cleanup

**User Story:** As a developer, I want stale sessions to be cleaned up, so that the database does not grow unbounded.

#### Acceptance Criteria

1. WHEN a "New Adventure" is started for a Sibling_Pair_ID that has an existing Session_Snapshot, THE Session_Service SHALL delete the old snapshot before creating the new session.
2. THE Session_Service SHALL delete Session_Snapshots that have not been updated for more than 30 days.
3. WHEN a session is explicitly completed (story reaches a natural ending), THE Session_Service SHALL delete the Session_Snapshot for that Sibling_Pair_ID.
4. THE Session_Service SHALL perform stale session cleanup as a background task during application startup.

### Requirement 9: Integration with Existing Stores

**User Story:** As a developer, I want session resumption to integrate cleanly with the existing Zustand stores and WebSocket pipeline, so that restoration is seamless.

#### Acceptance Criteria

1. WHEN restoring a session, THE App SHALL hydrate the Setup_Store with the saved Character_Profiles, setting `isComplete` to true and `currentStep` to "complete".
2. WHEN restoring a session, THE App SHALL hydrate the Story_Store with the saved Story_History and current_beat.
3. WHEN restoring a session, THE App SHALL hydrate the Session_Store with the saved profiles and session_id.
4. WHEN restoring a session, THE App SHALL re-establish the WebSocket connection using the restored Character_Profiles and resume story generation from the current beat's choices.
5. THE App SHALL serialize the Session_Snapshot by reading state from the Setup_Store, Story_Store, and Session_Store without modifying their existing interfaces.
6. FOR ALL restorable sessions, saving the full store state then restoring SHALL produce equivalent store state in Setup_Store, Story_Store, and Session_Store (round-trip property).
