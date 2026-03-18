# Requirements Document

## Introduction

Persistent Story World adds cross-session world state persistence to Twin Spark Chronicles. Currently, ChromaDB-backed `MemoryAgent` stores story moments within a single session, and `SiblingDB` persists personality profiles and relationship data across sessions — but the story world itself (locations, NPCs, items) resets every time. This feature ensures that siblings return to a living world that remembers their discoveries, friendships, and collected artifacts, creating the "one more session" hook that drives re-engagement.

## Glossary

- **World_State**: The persistent data structure representing all discovered locations, befriended NPCs, and collected items for a sibling pair, stored in SQLite via `SiblingDB`.
- **World_DB**: The persistence layer (extension of `SiblingDB`) responsible for CRUD operations on world state data.
- **Location**: A named place within the story world that siblings can discover, revisit, and that can evolve over time (e.g., "Dark Forest" → "Enchanted Grove").
- **NPC**: A non-player character that siblings encounter and befriend during story sessions.
- **Item**: An artifact or object that siblings collect during story sessions.
- **Sibling_Pair**: The two siblings sharing a story world, identified by `sibling_pair_id`.
- **World_Context**: A formatted summary of relevant world state injected into Gemini prompts for story generation.
- **World_State_API**: The set of FastAPI endpoints for loading and saving world state.
- **World_Store**: The Zustand store on the frontend that manages world state for the UI.
- **World_Map_View**: The frontend component displaying discovered locations, befriended NPCs, and collected items visually.
- **Orchestrator**: The `AgentOrchestrator` class that coordinates all agents and now also manages world state loading and saving during sessions.
- **Memory_Agent**: The existing `MemoryAgent` that handles within-session ChromaDB memory; world state extraction feeds from its stored moments.

## Requirements

### Requirement 1: World State Data Model

**User Story:** As a developer, I want a structured data model for world state, so that locations, NPCs, and items can be persisted and queried reliably.

#### Acceptance Criteria

1. THE World_DB SHALL store Location records with fields: id, sibling_pair_id, name, description, state, discovered_at, and updated_at.
2. THE World_DB SHALL store NPC records with fields: id, sibling_pair_id, name, description, relationship_level, met_at, and updated_at.
3. THE World_DB SHALL store Item records with fields: id, sibling_pair_id, name, description, collected_at, and session_id.
4. THE World_DB SHALL enforce that each Location name is unique per Sibling_Pair.
5. THE World_DB SHALL enforce that each NPC name is unique per Sibling_Pair.
6. THE World_DB SHALL enforce that each Item name is unique per Sibling_Pair.

### Requirement 2: World State Persistence

**User Story:** As a sibling pair, I want my discovered locations, befriended NPCs, and collected items to be saved after each session, so that my world is waiting for me next time.

#### Acceptance Criteria

1. WHEN a session ends, THE Orchestrator SHALL extract new locations, NPCs, and items from the session's story moments and persist them to the World_DB.
2. WHEN a Location is discovered during a session, THE World_DB SHALL store the Location with its name, description, and initial state.
3. WHEN an NPC is befriended during a session, THE World_DB SHALL store the NPC with its name, description, and initial relationship_level.
4. WHEN an Item is collected during a session, THE World_DB SHALL store the Item with its name, description, and the session_id in which the Item was collected.
5. IF the World_DB fails to persist world state, THEN THE Orchestrator SHALL log the error and continue the session-end flow without blocking.
6. FOR ALL valid World_State objects, saving then loading SHALL produce an equivalent World_State object (round-trip property).

### Requirement 3: World State Loading at Session Start

**User Story:** As a sibling pair, I want my world to be loaded when I start a new session, so that the story can reference my past discoveries.

#### Acceptance Criteria

1. WHEN a new session starts for a Sibling_Pair, THE Orchestrator SHALL load the full World_State from the World_DB.
2. WHEN the World_State is loaded, THE Orchestrator SHALL format a World_Context summary containing up to 10 most recent locations, 10 most recent NPCs, and 10 most recent items.
3. WHEN generating the first story beat of a session, THE Orchestrator SHALL include the World_Context in the Gemini prompt.
4. IF no World_State exists for a Sibling_Pair, THEN THE Orchestrator SHALL proceed with an empty World_Context and generate a fresh world introduction.
5. THE Orchestrator SHALL load the World_State within 500ms for a world containing up to 100 locations, 100 NPCs, and 100 items.

### Requirement 4: World Evolution

**User Story:** As a sibling pair, I want locations in my world to change based on my story actions, so that the world feels alive and responsive.

#### Acceptance Criteria

1. WHEN a story event changes a Location's narrative state, THE Orchestrator SHALL update the Location's state and description in the World_DB.
2. WHEN a Location's state is updated, THE World_DB SHALL record the updated_at timestamp.
3. WHEN an NPC's relationship deepens through story events, THE Orchestrator SHALL update the NPC's relationship_level in the World_DB.
4. THE World_DB SHALL preserve the full history of a Location's previous states by storing the prior state before overwriting.
5. WHEN the World_Context is generated, THE Orchestrator SHALL include the current state of each Location, not historical states.

### Requirement 5: Sibling-Shared World

**User Story:** As siblings, we want to share the same world, so that both of our actions contribute to building it together.

#### Acceptance Criteria

1. THE World_DB SHALL associate all world state records (locations, NPCs, items) with a single sibling_pair_id.
2. WHEN either sibling discovers a Location, THE World_DB SHALL store the Location under the shared sibling_pair_id.
3. WHEN either sibling befriends an NPC, THE World_DB SHALL store the NPC under the shared sibling_pair_id.
4. WHEN either sibling collects an Item, THE World_DB SHALL store the Item under the shared sibling_pair_id.
5. WHEN loading World_State, THE World_DB SHALL return all records for the sibling_pair_id regardless of which sibling triggered the discovery.

### Requirement 6: Story Continuity via World Context

**User Story:** As a sibling pair, I want the story to naturally reference my past discoveries, so that the world feels continuous and personal.

#### Acceptance Criteria

1. WHEN generating a story beat, THE Orchestrator SHALL include relevant World_Context entries that match the current scene's theme or setting.
2. WHEN the current scene takes place in a previously discovered Location, THE Orchestrator SHALL instruct Gemini to reference the Location by name and acknowledge the siblings' prior visit.
3. WHEN a previously befriended NPC is relevant to the current scene, THE Orchestrator SHALL instruct Gemini to reference the NPC by name and recall the relationship.
4. THE Orchestrator SHALL limit World_Context injection to a maximum of 5 relevant entries per story beat to avoid prompt bloat.
5. IF the World_State is empty, THEN THE Orchestrator SHALL generate story beats without world references and treat the session as a fresh exploration.

### Requirement 7: World State API

**User Story:** As a frontend developer, I want API endpoints for loading and saving world state, so that the UI can display and interact with the persistent world.

#### Acceptance Criteria

1. THE World_State_API SHALL expose a GET endpoint at `/api/world/{sibling_pair_id}` that returns the full World_State as JSON.
2. THE World_State_API SHALL expose a GET endpoint at `/api/world/{sibling_pair_id}/locations` that returns all locations for the Sibling_Pair.
3. THE World_State_API SHALL expose a GET endpoint at `/api/world/{sibling_pair_id}/npcs` that returns all NPCs for the Sibling_Pair.
4. THE World_State_API SHALL expose a GET endpoint at `/api/world/{sibling_pair_id}/items` that returns all items for the Sibling_Pair.
5. IF the sibling_pair_id does not exist, THEN THE World_State_API SHALL return an empty World_State with HTTP status 200.
6. IF an internal error occurs, THEN THE World_State_API SHALL return HTTP status 500 with a JSON error message.
7. FOR ALL World_State responses, serializing to JSON then deserializing SHALL produce an equivalent World_State object (round-trip property).

### Requirement 8: World Map and Inventory UI

**User Story:** As a 6-year-old sibling, I want to see my discovered places, friends, and treasures on a visual map, so that I can feel proud of my adventures.

#### Acceptance Criteria

1. THE World_Map_View SHALL display discovered locations as visual icons on a stylized map layout.
2. THE World_Map_View SHALL display befriended NPCs as character portraits in a "Friends" section.
3. THE World_Map_View SHALL display collected items as visual icons in an "Inventory" section.
4. THE World_Map_View SHALL use minimal text and rely primarily on icons and images, suitable for children aged 6.
5. WHEN a Location has evolved, THE World_Map_View SHALL display the Location's current visual state.
6. WHEN the World_State is empty, THE World_Map_View SHALL display an encouraging empty state message (e.g., "Start an adventure to discover your world").
7. THE World_Map_View SHALL load world state from the World_Store, which fetches data from the World_State_API.
8. THE World_Map_View SHALL be accessible via a navigation element from the main story screen.

### Requirement 9: Integration with Existing Pipeline

**User Story:** As a developer, I want the world state system to integrate cleanly with the existing orchestrator and memory agent pipeline, so that world persistence is seamless.

#### Acceptance Criteria

1. WHEN the Orchestrator calls `end_session`, THE Orchestrator SHALL invoke world state extraction and persistence after the existing session summary logic.
2. WHEN the Orchestrator calls `generate_rich_story_moment`, THE Orchestrator SHALL inject World_Context into the prompt alongside existing Memory_Agent context.
3. THE Orchestrator SHALL load World_State during session initialization without modifying the existing `MemoryAgent` interface.
4. THE World_DB SHALL reuse the existing `SiblingDB` SQLite connection and follow the same async pattern (aiosqlite).
5. IF the World_DB is unavailable, THEN THE Orchestrator SHALL continue story generation without world context and log a warning.
