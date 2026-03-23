# Implementation Plan: Full-Flow Integration Testing

## Overview

Build integration tests that validate the complete Twin Spark Chronicles pipeline: setup wizard → WebSocket connection → story generation → scene display. Backend tests use pytest with FastAPI TestClient; frontend tests use vitest with @testing-library/react. All Gemini/Vertex/TTS agents are mocked at the boundary — zero API calls. Ale and Sofi are the canonical test sibling pair throughout.

## Tasks

- [x] 1. Create shared Ale & Sofi test fixtures
  - [x] 1.1 Create backend fixture in `backend/tests/test_full_flow.py`
    - Define `ale_sofi_profiles` pytest fixture returning child1 (Ale: girl, Dragon, Bruno) and child2 (Sofi: boy, Owl, Book) with costume fields
    - Define `ale_sofi_ws_params` pytest fixture returning WebSocket query parameters (lang, c1_name, c1_gender, c1_personality, c1_spirit, c1_toy, c2_name, c2_gender, c2_personality, c2_spirit, c2_toy)
    - Define `MOCK_STORY_SEGMENT` module-level dict with text mentioning both Ale and Sofi, timestamp, characters placeholder, and interactive dict
    - Derive `sibling_pair_id` as `"Ale:Sofi"` (alphabetically sorted)
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [x] 1.2 Create frontend fixture in `frontend/src/__tests__/testFixtures.js`
    - Export `ALE_SOFI_PROFILES` object with c1_name, c1_gender, c1_personality, c1_spirit, c1_costume, c1_costume_prompt, c1_toy, c1_toy_type, c1_toy_image, and matching c2_ fields
    - Export `MOCK_STORY_BEAT` object with narration, child1_perspective, child2_perspective, scene_image_url, and choices array
    - _Requirements: 1.1, 1.4_

- [x] 2. Implement backend WebSocket connection and session lifecycle tests
  - [x] 2.1 Implement `test_ws_connect_and_input_status` in `backend/tests/test_full_flow.py`
    - Use `starlette.testclient.TestClient` with `client.websocket_connect(f"/ws/{session_id}?{params}")` to connect
    - Mock `app.agents.storyteller_agent.storyteller.generate_story_segment` to return `MOCK_STORY_SEGMENT`
    - Mock `app.agents.storyteller_agent.storyteller.model` to prevent Gemini SDK initialization
    - Receive first message and assert it contains `type: "input_status"`, `camera`, and `mic` fields
    - _Requirements: 2.1, 10.1_

  - [x] 2.2 Implement `test_ws_session_registered` in `backend/tests/test_full_flow.py`
    - Connect via WebSocket, then assert `session_id in manager.active_connections`
    - Assert `session_id in manager.input_managers`
    - _Requirements: 2.2, 2.3, 9.1_

  - [x] 2.3 Implement `test_ws_story_generation` in `backend/tests/test_full_flow.py`
    - Connect, receive input_status, then send a JSON message with `context` containing Ale and Sofi characters
    - Receive the response and assert `type: "story_segment"` with `data` containing `text`, `timestamp`, `characters`, and `interactive` keys
    - _Requirements: 3.1, 3.2, 3.3, 10.2_

  - [x] 2.4 Implement `test_ws_story_fallback_on_error` in `backend/tests/test_full_flow.py`
    - Mock `storyteller.generate_story_segment` to raise `Exception("API failure")`
    - Connect, send context message, receive response
    - Assert fallback story `data.text` contains both "Ale" and "Sofi"
    - _Requirements: 3.4_

  - [x] 2.5 Implement `test_ws_disconnect_cleanup` in `backend/tests/test_full_flow.py`
    - Connect, verify session is in `active_connections`, then close the WebSocket
    - Assert session is removed from `active_connections` after disconnect
    - _Requirements: 2.4, 9.2, 9.3_

  - [x] 2.6 Implement `test_session_time_enforcer_tracking` in `backend/tests/test_full_flow.py`
    - Connect via WebSocket, then assert `session_time_enforcer` has an active entry for the session_id
    - _Requirements: 9.4_

  - [x]* 2.7 Write property test for sibling pair ID derivation
    - **Property 1: Sibling Pair ID Derivation**
    - Use Hypothesis to generate pairs of non-empty alphabetic strings
    - Derive pair ID with `":".join(sorted([name1, name2]))`, verify result has exactly one colon and left ≤ right lexicographically
    - `# Feature: full-flow-integration-testing, Property 1: Sibling Pair ID Derivation`
    - **Validates: Requirements 1.3**

  - [x]* 2.8 Write property test for story segment structure invariant
    - **Property 2: Story Segment Structure Invariant**
    - Use Hypothesis to generate random character name/gender/spirit combos, call `storyteller._fallback_story()`, verify returned dict has `text` (non-empty), `timestamp`, `characters`, and `interactive` (with `type`, `text`, `expects_response`)
    - `# Feature: full-flow-integration-testing, Property 2: Story Segment Structure Invariant`
    - **Validates: Requirements 3.3, 10.2**

- [x] 3. Checkpoint — Ensure all backend WebSocket tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Implement backend orchestrator integration tests
  - [x] 4.1 Implement `test_orchestrator_rich_story` in `backend/tests/test_full_flow.py`
    - Create an `AgentOrchestrator` instance, mock `storyteller.generate_story_segment` to return `MOCK_STORY_SEGMENT`
    - Mock `visual_agent.enabled = False`, `voice_agent.enabled = False`, `memory_agent.enabled = False`
    - Call `generate_rich_story_moment(session_id, ale_sofi_profiles)` and assert result contains all required keys: `text`, `image`, `audio`, `interactive`, `timestamp`, `memories_used`, `voice_recordings`, `agents_used`
    - _Requirements: 4.1, 8.1, 8.2, 8.3, 8.4_

  - [x] 4.2 Implement `test_orchestrator_visual_disabled` in `backend/tests/test_full_flow.py`
    - With visual agent disabled, assert `result["agents_used"]["visual"]` is `False` and `result["image"]` is `None`
    - _Requirements: 4.3_

  - [x] 4.3 Implement `test_orchestrator_memory_count` in `backend/tests/test_full_flow.py`
    - Mock `memory_agent.enabled = True` and `memory_agent.recall_relevant_moments` to return a list of 3 mock memories
    - Call `generate_rich_story_moment`, assert `result["memories_used"] == 3`
    - _Requirements: 4.4_

  - [x]* 4.4 Write property test for orchestrator output completeness
    - **Property 3: Orchestrator Output Completeness**
    - Use Hypothesis to generate random character profiles (names, genders, spirits), call `generate_rich_story_moment` with mocked agents, verify all required keys present
    - `# Feature: full-flow-integration-testing, Property 3: Orchestrator Output Completeness`
    - **Validates: Requirements 4.1**

  - [x]* 4.5 Write property test for memory count consistency
    - **Property 4: Memory Count Consistency**
    - Use Hypothesis to generate random-length lists (0–10) of mock memories, mock `recall_relevant_moments` to return them, call orchestrator, verify `memories_used` equals list length
    - `# Feature: full-flow-integration-testing, Property 4: Memory Count Consistency`
    - **Validates: Requirements 4.4**

- [x] 5. Checkpoint — Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implement frontend setup and story store integration tests
  - [x] 6.1 Implement `test setup store processes Ale and Sofi profiles` in `frontend/src/__tests__/fullFlow.test.js`
    - Import `useSetupStore` and `ALE_SOFI_PROFILES` from testFixtures
    - Call `setChild1` with Ale data and `setChild2` with Sofi data, then `completeSetup()`
    - Assert `child1.name === "Ale"`, `child2.name === "Sofi"`, `isComplete === true`
    - _Requirements: 5.1, 5.2_

  - [x] 6.2 Implement `test spirit animal to personality mapping` in `frontend/src/__tests__/fullFlow.test.js`
    - Verify the `spiritToPersonality` mapping: Dragon→"brave", Owl→"wise", unicorn→"creative", dolphin→"friendly", phoenix→"resilient", tiger→"confident"
    - _Requirements: 5.4_

  - [x] 6.3 Implement `test session store receives enriched profiles` in `frontend/src/__tests__/fullFlow.test.js`
    - Import `useSessionStore`, call `setProfiles(ALE_SOFI_PROFILES)`
    - Assert `profiles.c1_name === "Ale"`, `profiles.c1_personality === "brave"`, `profiles.c2_spirit === "Owl"`
    - _Requirements: 5.3_

  - [x] 6.4 Implement `test story store accumulates assets` in `frontend/src/__tests__/fullFlow.test.js`
    - Import `useStoryStore`, call `addAsset('text', narration)`, `addAsset('text', perspective, {child:'c1'})`, `addAsset('text', perspective, {child:'c2'})`, `addAsset('image', url)`, `addAsset('interactive', choices)`
    - Assert `currentAssets` has all fields populated
    - _Requirements: 6.1_

  - [x] 6.5 Implement `test story store assembles beat` in `frontend/src/__tests__/fullFlow.test.js`
    - After accumulating assets, call `setCurrentBeat(MOCK_STORY_BEAT)`
    - Assert `currentBeat` has `narration`, `child1_perspective`, `child2_perspective`, `scene_image_url`, and `choices`
    - _Requirements: 6.2, 6.3_

  - [x]* 6.6 Write property test for spirit animal to personality mapping
    - **Property 5: Spirit Animal to Personality Mapping**
    - Use fast-check to sample from `['dragon','unicorn','owl','dolphin','phoenix','tiger']`, apply mapping, assert result is a non-empty string and deterministic
    - `// Feature: full-flow-integration-testing, Property 5: Spirit Animal to Personality Mapping`
    - **Validates: Requirements 5.4**

- [x] 7. Implement frontend DualStoryDisplay rendering tests
  - [x] 7.1 Implement `test DualStoryDisplay renders narration` in `frontend/src/__tests__/fullFlow.test.js`
    - Render `<DualStoryDisplay storyBeat={MOCK_STORY_BEAT} profiles={ALE_SOFI_PROFILES} onChoice={vi.fn()} />`
    - Assert `.story-narration__text` contains the narration text
    - _Requirements: 7.1_

  - [x] 7.2 Implement `test DualStoryDisplay renders Ale and Sofi names` in `frontend/src/__tests__/fullFlow.test.js`
    - Assert "Ale" and "Sofi" appear in the rendered output (avatar area)
    - _Requirements: 7.2_

  - [x] 7.3 Implement `test DualStoryDisplay renders choice cards` in `frontend/src/__tests__/fullFlow.test.js`
    - Assert number of `.story-choice-card` buttons equals `MOCK_STORY_BEAT.choices.length`
    - _Requirements: 7.3_

  - [x] 7.4 Implement `test DualStoryDisplay choice callback` in `frontend/src/__tests__/fullFlow.test.js`
    - Click first choice button, assert `onChoice` was called with the first choice text
    - Use `vi.advanceTimersByTime(400)` to handle the setTimeout in `handleChoiceTap`
    - _Requirements: 7.4_

  - [x] 7.5 Implement `test DualStoryDisplay renders scene image` in `frontend/src/__tests__/fullFlow.test.js`
    - Assert `SceneImageLoader` is rendered when `scene_image_url` is present in the beat
    - _Requirements: 7.5_

  - [x]* 7.6 Write property test for choice card count
    - **Property 6: Choice Card Count Matches Choices Array**
    - Use fast-check to generate arrays of 1–6 random choice strings, render DualStoryDisplay, count `.story-choice-card` elements, assert count equals array length
    - `// Feature: full-flow-integration-testing, Property 6: Choice Card Count Matches Choices Array`
    - **Validates: Requirements 7.3**

- [x] 8. Implement backend WebSocket message protocol conformance tests
  - [x] 8.1 Implement `test_ws_message_protocol_input_status` in `backend/tests/test_full_flow.py`
    - Connect, receive first message, assert it has exactly `type`, `camera`, `mic` as top-level keys with correct types
    - _Requirements: 10.1_

  - [x] 8.2 Implement `test_ws_message_protocol_story_segment` in `backend/tests/test_full_flow.py`
    - Connect, send context, receive story_segment, assert message has `type` and `data` fields, and `data` contains `text`
    - _Requirements: 10.2_

- [x] 9. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Backend run: `source venv/bin/activate && python3 -m pytest tests/test_full_flow.py -x -q --tb=short` from `backend/`
- Frontend run: `npm run test` from `frontend/` (vitest --run)
- After pytest: `pkill -f "python.*pytest"` (CacheManager cleanup loop causes hang)
- Backend PBT: Hypothesis with `@settings(max_examples=100)`
- Frontend PBT: fast-check with `{ numRuns: 100 }`
- Each PBT test includes tag comment: `# Feature: full-flow-integration-testing, Property {N}: {title}`
- Node version is 21.5.0 — requires vitest v1
