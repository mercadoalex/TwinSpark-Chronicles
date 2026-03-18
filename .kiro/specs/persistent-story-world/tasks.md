# Implementation Plan: Persistent Story World

## Overview

Add cross-session world state persistence so that discovered locations, befriended NPCs, and collected items survive across sessions. This involves a new `WorldDB` persistence layer sharing `SiblingDB`'s SQLite connection, a Gemini-driven world state extractor, context injection into story prompts, REST API endpoints, and a child-friendly World Map UI.

## Tasks

- [x] 1. Implement WorldDB persistence layer
  - [x] 1.1 Create `backend/app/services/world_db.py` with `WorldDB` class
    - Accept `SiblingDB` instance and reuse its `_get_db()` connection
    - Implement `initialize()` to create `world_locations`, `world_location_history`, `world_npcs`, and `world_items` tables with UNIQUE constraints on `(sibling_pair_id, name)`
    - Implement `save_location`, `load_locations`, `update_location_state` (archive prior state to `world_location_history` before overwriting)
    - Implement `save_npc`, `load_npcs`, `update_npc_relationship`
    - Implement `save_item`, `load_items`
    - Implement `load_world_state` returning `{"locations": [...], "npcs": [...], "items": [...]}`
    - Use `uuid4` for IDs and `datetime.now(timezone.utc).isoformat()` for timestamps
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 4.2, 4.4, 5.1, 5.2, 5.3, 5.4, 5.5, 9.4_

  - [ ]* 1.2 Write property test: World state DB round-trip (Property 1)
    - **Property 1: World state DB round-trip**
    - **Validates: Requirements 1.1, 1.2, 1.3, 2.2, 2.3, 2.4, 2.6, 5.1, 5.2, 5.3, 5.4, 5.5**
    - Create `backend/tests/test_world_db_properties.py` with Hypothesis strategies for locations, NPCs, items
    - For any valid world state, saving then loading should produce equivalent data

  - [ ]* 1.3 Write property test: Entity name uniqueness per sibling pair (Property 2)
    - **Property 2: Entity name uniqueness per sibling pair**
    - **Validates: Requirements 1.4, 1.5, 1.6**
    - Saving two entities with the same `(sibling_pair_id, name)` should result in exactly one record (upsert)

  - [ ]* 1.4 Write property test: Location state update reflected on load (Property 4)
    - **Property 4: Location state update reflected on load**
    - **Validates: Requirements 4.1, 4.2**
    - After `update_location_state`, loading should return the new state/description with `updated_at >= original`

  - [ ]* 1.5 Write property test: Location history preserved on update (Property 5)
    - **Property 5: Location history preserved on update**
    - **Validates: Requirements 4.4**
    - After N state updates, `world_location_history` should contain exactly N records for that location

  - [ ]* 1.6 Write property test: NPC relationship update reflected on load (Property 7)
    - **Property 7: NPC relationship update reflected on load**
    - **Validates: Requirements 4.3**
    - After `update_npc_relationship`, loading should return the updated level with `updated_at >= original`

  - [ ]* 1.7 Write unit tests for WorldDB
    - Create `backend/tests/test_world_db.py`
    - Test save/load specific location, NPC, item
    - Test empty world state returns empty collections (Req 3.4)
    - Test DB failure during save is catchable
    - _Requirements: 1.1, 1.2, 1.3, 3.4_

- [x] 2. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Implement WorldStateExtractor and WorldContextFormatter
  - [x] 3.1 Create `backend/app/services/world_state_extractor.py` with `WorldStateExtractor` class
    - Implement `build_extraction_prompt(moments)` that constructs a Gemini prompt requesting structured JSON output for new locations, NPCs, items, and updates
    - Implement `parse_extraction_response(response_text)` that parses Gemini's JSON response, returning empty result on malformed JSON
    - Implement `extract(session_moments)` that calls Gemini 2.0 Flash and returns structured world changes dict
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.2 Create `backend/app/services/world_context_formatter.py` with `WorldContextFormatter` class
    - Implement `format_session_start_context(world_state)` capping at 10 locations, 10 NPCs, 10 items; return empty string if world is empty
    - Implement `format_beat_context(world_state, current_scene)` selecting up to 5 relevant entries by keyword matching names/descriptions against scene text
    - Format output as `[WORLD CONTEXT]...[END WORLD CONTEXT]` block
    - _Requirements: 3.2, 3.4, 4.5, 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ]* 3.3 Write property test: Session start context capped at 10 per category (Property 3)
    - **Property 3: Session start context capped at 10 per category**
    - **Validates: Requirements 3.2**
    - Create `backend/tests/test_world_context_properties.py`
    - For any world state with N>10 entries per category, output should contain at most 10 per category

  - [ ]* 3.4 Write property test: Context contains only current location state (Property 6)
    - **Property 6: Context contains only current location state**
    - **Validates: Requirements 4.5**
    - For any location updated at least once, context formatters should include only the current state, never historical states

  - [ ]* 3.5 Write property test: Beat context relevance matching (Property 8)
    - **Property 8: Beat context relevance matching**
    - **Validates: Requirements 6.1, 6.2, 6.3**
    - When scene text contains a known entity name, `format_beat_context` should return non-empty context including that entity

  - [ ]* 3.6 Write property test: Beat context capped at 5 entries (Property 9)
    - **Property 9: Beat context capped at 5 entries**
    - **Validates: Requirements 6.4**
    - For any world state and scene text, total entries returned should be at most 5

  - [ ]* 3.7 Write unit tests for WorldStateExtractor and WorldContextFormatter
    - Create `backend/tests/test_world_state_extractor.py` — malformed JSON returns empty result, valid response parses correctly
    - Create `backend/tests/test_world_context_formatter.py` — empty world state produces empty string (Req 6.5), known name in scene appears in output
    - _Requirements: 2.1, 6.5_

  - [ ]* 3.8 Write property test: Extraction response parsing round-trip (Property 11)
    - **Property 11: Extraction response parsing round-trip**
    - **Validates: Requirements 2.1**
    - Create `backend/tests/test_world_serialization_properties.py`
    - For any valid extraction result dict, serializing to JSON then parsing via `parse_extraction_response` should produce equivalent dict

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Integrate world state into AgentOrchestrator
  - [x] 5.1 Modify `backend/app/agents/orchestrator.py` to initialize world components
    - In `__init__`, instantiate `WorldDB(self._sibling_db)`, `WorldStateExtractor()`, `WorldContextFormatter()`
    - Add `_world_state_cache: dict[str, dict]` for per-session world state
    - Call `self._world_db.initialize()` inside `_ensure_db_initialized()`
    - _Requirements: 9.3, 9.4_

  - [x] 5.2 Modify `generate_rich_story_moment` to inject world context
    - After STEP 1 (memory recall), load world state from cache or `WorldDB.load_world_state()`
    - Call `WorldContextFormatter.format_beat_context(world_state, user_input or scene)` and merge into `story_context`
    - Wrap in try/except: on failure, log warning and continue without world context
    - _Requirements: 3.1, 3.2, 3.3, 6.1, 6.2, 6.3, 6.4, 9.2, 9.5_

  - [x] 5.3 Modify `end_session` to extract and persist world state
    - After existing session summary logic, call `WorldStateExtractor.extract()` on session moments
    - Persist new locations, NPCs, items via `WorldDB.save_*` methods
    - Apply location updates via `WorldDB.update_location_state()` and NPC updates via `WorldDB.update_npc_relationship()`
    - Wrap in try/except: on failure, log error and continue session-end flow
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 4.1, 4.3, 9.1_

  - [ ]* 5.4 Write unit tests for orchestrator world integration
    - Create `backend/tests/test_orchestrator_world.py`
    - Test `end_session` persists world state after summary
    - Test `generate_rich_story_moment` includes world context
    - Test WorldDB failure doesn't block story generation
    - _Requirements: 9.1, 9.2, 9.5_

- [x] 6. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Implement World State API endpoints
  - [x] 7.1 Add Pydantic response models and API endpoints to `backend/app/main.py`
    - Define `LocationResponse`, `NpcResponse`, `ItemResponse`, `WorldStateResponse` Pydantic models
    - Add `GET /api/world/{sibling_pair_id}` returning full `WorldStateResponse`
    - Add `GET /api/world/{sibling_pair_id}/locations` returning `list[LocationResponse]`
    - Add `GET /api/world/{sibling_pair_id}/npcs` returning `list[NpcResponse]`
    - Add `GET /api/world/{sibling_pair_id}/items` returning `list[ItemResponse]`
    - Return empty collections with HTTP 200 for nonexistent `sibling_pair_id`
    - Return HTTP 500 with `{"detail": "..."}` on internal errors
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

  - [ ]* 7.2 Write property test: World state JSON serialization round-trip (Property 10)
    - **Property 10: World state JSON serialization round-trip**
    - **Validates: Requirements 7.7**
    - Add to `backend/tests/test_world_serialization_properties.py`
    - For any valid `WorldStateResponse`, `model_dump_json()` then `model_validate_json()` should produce equal object

  - [ ]* 7.3 Write unit tests for World State API
    - Create `backend/tests/test_world_api.py`
    - Test GET endpoints return 200 with valid JSON
    - Test nonexistent pair_id returns 200 with empty state
    - Test internal error returns 500
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

- [x] 8. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 9. Implement frontend WorldStore and WorldMapView
  - [x] 9.1 Create `frontend/src/stores/worldStore.js` Zustand store
    - Follow existing store pattern with `devtools` middleware
    - State: `locations`, `npcs`, `items`, `isLoading`, `error`
    - Actions: `fetchWorldState(siblingPairId)` calling `GET /api/world/{id}`, `reset()`
    - Selectors: `getLocationCount`, `getNpcCount`, `getItemCount`, `isEmpty`
    - _Requirements: 8.7_

  - [x] 9.2 Create `frontend/src/features/world/components/WorldMapView.jsx`
    - Display discovered locations as colorful icons in a stylized map layout
    - Display befriended NPCs as character portraits in a "Friends" section
    - Display collected items as visual icons in an "Inventory" section
    - Use minimal text, large icons, bright colors suitable for age 6
    - Show encouraging empty state message when world is empty: "Start an adventure to discover your world! 🌟"
    - Show current visual state for evolved locations
    - Load data from `useWorldStore`
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

  - [x] 9.3 Add navigation to WorldMapView from main story screen
    - Add a "My World 🗺️" navigation button in `frontend/src/App.jsx`
    - Wire routing/toggle to show `WorldMapView`
    - _Requirements: 8.8_

  - [ ]* 9.4 Write frontend tests for WorldMapView and WorldStore
    - Create `frontend/src/features/world/__tests__/WorldMapView.test.jsx`
    - Test empty state message renders when no data
    - Test navigation button is accessible
    - Test `fetchWorldState` populates store correctly
    - _Requirements: 8.6, 8.8_

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- All world state operations use graceful degradation — failures are logged but never block story generation
