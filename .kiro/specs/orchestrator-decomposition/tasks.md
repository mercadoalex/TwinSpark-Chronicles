# Tasks: Orchestrator Decomposition

## Task 1: Create coordinator package and SessionCoordinator
- [x] 1.1 Create `backend/app/agents/coordinators/__init__.py` with exports for all four coordinators
- [x] 1.2 Create `backend/app/agents/coordinators/session_coordinator.py` with `SessionCoordinator` class implementing `cancel_session`, `check_time`, `is_expired`, `start_generation_pause`, `end_generation_pause`, `notify_generation_started`, `notify_generation_completed`, `notify_session_expired`, and `track_task`
- [x] 1.3 Write unit tests for SessionCoordinator in `backend/tests/test_session_coordinator.py` covering cancel_session task cancellation, time check delegation, generation pause signaling, and graceful degradation when enforcer is None
  - Requirements: 2.1, 2.2, 2.3, 2.4, 2.5
- [x] * 1.4 Write Hypothesis property test verifying that for any set of asyncio tasks tracked for a session, after cancel_session all non-done tasks are cancelled and the session key is removed
  - Requirements: 2.2

## Task 2: Create StoryCoordinator
- [x] 2.1 Create `backend/app/agents/coordinators/story_coordinator.py` with `StoryCoordinator` class implementing `generate_safe_story_segment`, `filter_text`, `filter_choices`, `check_voice_playback`, `recall_memories`, `store_memory`, `generate_narration`, `generate_character_voices`, `extract_dialogues`, and `extract_lesson`
- [x] 2.2 Write unit tests for StoryCoordinator in `backend/tests/test_story_coordinator.py` covering safe generation with SAFE/REVIEW/BLOCKED ratings, fallback on retry exhaustion, choice filtering, voice playback triggers, and text extraction helpers
  - Requirements: 1.1, 1.2, 1.3, 1.4, 1.5
- [x] * 2.3 Write Hypothesis property test verifying that generate_safe_story_segment never returns a segment rated REVIEW or BLOCKED — it always returns SAFE or fallback
  - Requirements: 1.3

## Task 3: Create WorldCoordinator
- [x] 3.1 Create `backend/app/agents/coordinators/world_coordinator.py` with `WorldCoordinator` class implementing `get_world_context`, `extract_and_persist_world_state`, `invalidate_cache`, and `world_db` property
- [x] 3.2 Write unit tests for WorldCoordinator in `backend/tests/test_world_coordinator.py` covering cache miss loading, cache hit skipping DB, cache invalidation after extract, error resilience, and world_db property access
  - Requirements: 3.1, 3.2, 3.3, 3.4, 3.5
- [x] * 3.3 Write Hypothesis property test verifying that after extract_and_persist_world_state, the cache for that sibling_pair_id is always empty
  - Requirements: 3.4

## Task 4: Create MediaCoordinator
- [x] 4.1 Create `backend/app/agents/coordinators/media_coordinator.py` with `MediaCoordinator` class implementing `generate_scene`, `inject_drawing_prompt`, `drawing_time_watchdog`, `extract_setting`, and `extract_key_objects`
- [x] 4.2 Write unit tests for MediaCoordinator in `backend/tests/test_media_coordinator.py` covering disabled visual_agent, scene compositing, compositor failure fallback, drawing prompt injection with duration clamping, and text extraction helpers
  - Requirements: 4.1, 4.2, 4.3, 4.4, 4.5

## Task 5: Refactor AgentOrchestrator into thin facade
- [x] 5.1 Refactor `backend/app/agents/orchestrator.py` to initialize the four coordinators in `__init__` and delegate `generate_rich_story_moment`, `cancel_session`, and helper methods to the appropriate coordinators
- [x] 5.2 Add backward-compatible property accessors on AgentOrchestrator for `session_time_enforcer`, `ws_manager`, `_session_tasks`, `_world_db`, `content_filter`, `_playback_integrator` that delegate to the corresponding coordinator attributes
- [x] 5.3 Keep `process_multimodal_event`, `process_sibling_event`, `end_session`, `_ensure_db_initialized`, `_resolve_perspective_emotion`, and sibling dynamics pipeline (Layers 1-4) on the facade, updating them to use coordinators where applicable
- [x] 5.4 Ensure the global `orchestrator = AgentOrchestrator()` singleton is preserved at module level
  - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

## Task 6: Verify backward compatibility
- [x] 6.1 Run the full test suite (`source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from backend/) and verify all 610+ existing tests pass without modification
  - Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
- [x] 6.2 Write a facade delegation test in `backend/tests/test_orchestrator_facade.py` verifying that property accessors (`session_time_enforcer`, `ws_manager`, `_session_tasks`, `_world_db`, `content_filter`, `_playback_integrator`) resolve to the correct coordinator attributes
  - Requirements: 5.2
- [x] * 6.3 Write Hypothesis property test verifying that for any attribute path used in main.py/tests, accessing it on the facade returns the same object as the coordinator's attribute
  - Requirements: 5.2
