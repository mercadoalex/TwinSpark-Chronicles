# Requirements: Orchestrator Decomposition

## Requirement 1: StoryCoordinator Extraction

### Acceptance Criteria
- 1.1 Given the monolithic orchestrator, when StoryCoordinator is created, then it contains `generate_safe_story_segment`, `filter_text`, `filter_choices`, `check_voice_playback`, `recall_memories`, `store_memory`, `generate_narration`, `generate_character_voices`, `extract_dialogues`, and `extract_lesson` methods
- 1.2 Given a StoryCoordinator with mocked storyteller and content_filter, when `generate_safe_story_segment` is called and the content filter returns SAFE, then the segment is returned without retry
- 1.3 Given a StoryCoordinator, when `generate_safe_story_segment` exhausts MAX_CONTENT_RETRIES with REVIEW/BLOCKED ratings, then the fallback story is returned
- 1.4 Given a StoryCoordinator with a playback_integrator, when `check_voice_playback` is called with story text containing "brave", then an encouragement recording is included in the result
- 1.5 Given a StoryCoordinator, when `filter_choices` is called with choices containing unsafe text, then those choices are removed and safe choices are preserved

## Requirement 2: SessionCoordinator Extraction

### Acceptance Criteria
- 2.1 Given the monolithic orchestrator, when SessionCoordinator is created, then it contains `cancel_session`, `check_time`, `is_expired`, `start_generation_pause`, `end_generation_pause`, `notify_generation_started`, `notify_generation_completed`, and `track_task` methods
- 2.2 Given a SessionCoordinator with tracked tasks, when `cancel_session` is called, then all non-done tasks are cancelled, the session key is removed from `_session_tasks`, and the result contains `status: "stopped"`
- 2.3 Given a SessionCoordinator with a session_time_enforcer, when `check_time` is called for an expired session, then `is_expired` returns True
- 2.4 Given a SessionCoordinator with a ws_manager, when `notify_generation_started` is called, then a `GENERATION_STARTED` message is sent via ws_manager
- 2.5 Given a SessionCoordinator without a session_time_enforcer (None), when `is_expired` is called, then it returns False (graceful degradation)

## Requirement 3: WorldCoordinator Extraction

### Acceptance Criteria
- 3.1 Given the monolithic orchestrator, when WorldCoordinator is created, then it contains `get_world_context`, `extract_and_persist_world_state`, `invalidate_cache`, and `world_db` property
- 3.2 Given a WorldCoordinator with an empty cache, when `get_world_context` is called, then world state is loaded from WorldDB, cached, and formatted context string is returned
- 3.3 Given a WorldCoordinator with a cached world state, when `get_world_context` is called again for the same sibling_pair_id, then WorldDB is NOT called again (cache hit)
- 3.4 Given a WorldCoordinator, when `extract_and_persist_world_state` completes, then the in-memory cache for that sibling_pair_id is invalidated
- 3.5 Given a WorldCoordinator, when `extract_and_persist_world_state` encounters an error in WorldDB, then the error is logged and no exception propagates

## Requirement 4: MediaCoordinator Extraction

### Acceptance Criteria
- 4.1 Given the monolithic orchestrator, when MediaCoordinator is created, then it contains `generate_scene`, `inject_drawing_prompt`, `drawing_time_watchdog`, `extract_setting`, and `extract_key_objects` methods
- 4.2 Given a MediaCoordinator with a disabled visual_agent, when `generate_scene` is called, then None is returned
- 4.3 Given a MediaCoordinator with photo portraits and a working compositor, when `generate_scene` is called, then the scene image is composited with portraits
- 4.4 Given a MediaCoordinator where the compositor raises an exception, when `generate_scene` is called, then the base (non-composited) scene image is returned
- 4.5 Given a MediaCoordinator with a session_coordinator, when `inject_drawing_prompt` is called with a story_segment containing a drawing_prompt, then a DRAWING_PROMPT message is sent via ws_manager with duration clamped to remaining session time

## Requirement 5: Facade Preservation

### Acceptance Criteria
- 5.1 Given the decomposed AgentOrchestrator, when `generate_rich_story_moment` is called, then it delegates to StoryCoordinator, SessionCoordinator, WorldCoordinator, and MediaCoordinator in the correct sequence
- 5.2 Given the decomposed AgentOrchestrator, when any of `session_time_enforcer`, `ws_manager`, `_session_tasks`, `_world_db`, `content_filter`, `_playback_integrator` are accessed, then they resolve to the same objects as the corresponding coordinator attributes
- 5.3 Given the decomposed AgentOrchestrator, when `process_sibling_event` is called, then the sibling dynamics pipeline (Layers 1-4) executes identically to the monolithic version
- 5.4 Given the decomposed AgentOrchestrator, when `_ensure_db_initialized` is called, then the database is connected, migrations are run, and PlaybackIntegrator is initialized — identical to the monolithic version
- 5.5 Given the decomposed AgentOrchestrator, when `generate_rich_story_moment` raises during `_do_generate`, then `end_generation_pause` is still called (try/finally invariant)

## Requirement 6: Test Compatibility

### Acceptance Criteria
- 6.1 Given the decomposed orchestrator, when the full test suite is run (`python3 -m pytest tests/ -x -q --tb=short`), then all 610+ existing tests pass without modification
- 6.2 Given test code that constructs `AgentOrchestrator()` and sets `orch.storyteller = MagicMock()`, then the mock is accessible and used by the story generation pipeline
- 6.3 Given test code that sets `orch.content_filter = MagicMock()`, then the mock is forwarded to StoryCoordinator and used during content filtering
- 6.4 Given test code that sets `orch._playback_integrator = MagicMock()`, then the mock is forwarded to StoryCoordinator and used during voice playback checks
- 6.5 Given test code that patches `AgentOrchestrator.__init__` with `lambda self: None`, then the orchestrator can still be used after manually setting attributes (existing test pattern in test_orchestrator_sibling.py)
