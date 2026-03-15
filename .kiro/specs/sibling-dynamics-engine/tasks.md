# Implementation Plan: Sibling Dynamics Engine

## Overview

Build the 4-layer Sibling Dynamics Engine incrementally: data models first, then persistence, then each service layer (personality → relationship → skills), then orchestrator integration, then storyteller enhancement, then API endpoints, and finally frontend components. Each layer is tested before wiring into the next. Property-based tests use Hypothesis.

## Tasks

- [ ] 1. Define Pydantic data models and shared test strategies
  - [ ] 1.1 Create `backend/app/models/sibling.py` with all Pydantic models
    - Define `TraitScore`, `PersonalityProfile`, `RelationshipModel`, `ConflictEvent`, `ComplementaryPair`, `SkillMap`, and extended `StoryMoment` models
    - Include all helper methods: `is_emerging()`, `trait_dict()`, `high_confidence_count()`, `is_leadership_imbalanced()`, `is_low_cooperation()`, `sibling_dynamics_score()`
    - All field constraints: `ge=0.0, le=1.0` for scores, `ge=0` for counts, default values per design
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.2, 3.4, 3.5, 3.6, 4.5, 9.1_

  - [ ] 1.2 Create Hypothesis strategies in `backend/tests/conftest.py`
    - Add `st_trait_score()`, `st_personality_profile()`, `st_relationship_model()`, `st_complementary_pair()`, `st_skill_map()`, `st_multimodal_event()` strategies
    - Ensure generated models satisfy all Pydantic constraints
    - _Requirements: 10.1, 10.2_

  - [ ]* 1.3 Write property tests for model invariants in `backend/tests/test_sibling_models.py`
    - **Property 1: PersonalityProfile serialization round-trip**
    - **Validates: Requirements 10.1, 10.3, 10.5, 1.4**

  - [ ]* 1.4 Write property test for RelationshipModel round-trip
    - **Property 2: RelationshipModel serialization round-trip**
    - **Validates: Requirements 10.2, 10.4, 10.6**

  - [ ]* 1.5 Write property test for model bounds invariant
    - **Property 3: Model bounds invariant**
    - **Validates: Requirements 2.4, 3.2, 3.4**

  - [ ]* 1.6 Write property test for emerging profile threshold
    - **Property 4: Emerging profile threshold**
    - **Validates: Requirements 2.5**

  - [ ]* 1.7 Write property test for sibling dynamics score formula
    - **Property 22: Sibling dynamics score formula**
    - **Validates: Requirements 9.1**

  - [ ]* 1.8 Write property test for leadership imbalance detection
    - **Property 9: Leadership imbalance detection**
    - **Validates: Requirements 3.3**

  - [ ]* 1.9 Write property test for complementary pair structure completeness
    - **Property 15: Complementary pair structure completeness**
    - **Validates: Requirements 4.5**

- [ ] 2. Implement SQLite persistence layer
  - [ ] 2.1 Create `backend/app/services/sibling_db.py`
    - Implement `SiblingDB` class with `aiosqlite`
    - Methods: `initialize()`, `save_profile()`, `load_profile()`, `save_relationship()`, `load_relationship()`, `save_skill_map()`, `load_skill_map()`, `save_session_summary()`, `load_session_summaries()`
    - Create all tables per design: `personality_profiles`, `relationship_models`, `skill_maps`, `session_summaries`, `initial_profiles`
    - _Requirements: 1.4, 8.1, 8.5, 10.1, 10.2_

  - [ ]* 2.2 Write unit tests for SiblingDB in `backend/tests/test_sibling_db.py`
    - Test save/load round-trips for profiles, relationships, skill maps, and session summaries
    - Test loading non-existent records returns `None`
    - Test `initialize()` creates tables idempotently
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [ ] 3. Checkpoint - Verify models and persistence
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement PersonalityEngine (Layer 1)
  - [ ] 4.1 Create `backend/app/services/personality_engine.py`
    - Implement `PersonalityEngine` class with `SiblingDB` dependency
    - Methods: `update_from_event()`, `record_choice()`, `load_profile()`, `persist_profile()`, `_apply_temporal_decay()`, `_analyze_transcript()`
    - EMA update: `alpha * new_signal + (1 - alpha) * current` with configurable alpha (default 0.3)
    - Transcript analysis: extract personality signals (assertive language → boldness, questions → curiosity, empathetic statements → empathy, etc.)
    - Mark profile as "emerging" when `total_interactions < 5`, use conservative defaults
    - Increment `total_interactions` on each update, update `last_updated` timestamp
    - Discard emotion signals with confidence below 0.1
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 11.2, 11.3_

  - [ ]* 4.2 Write property test for temporal decay weighting
    - **Property 5: Temporal decay weighting**
    - **Validates: Requirements 1.5**

  - [ ]* 4.3 Write property test for profile independence
    - **Property 6: Profile independence**
    - **Validates: Requirements 1.3**

  - [ ]* 4.4 Write property test for personality update from events
    - **Property 7: Personality update from events**
    - **Validates: Requirements 1.1, 1.2, 11.2**

  - [ ]* 4.5 Write property test for transcript analysis
    - **Property 24: Transcript analysis produces signals**
    - **Validates: Requirements 11.3**

  - [ ]* 4.6 Write unit tests for PersonalityEngine in `backend/tests/test_personality_engine.py`
    - Test `update_from_event` with emotion data updates correct traits
    - Test `record_choice` updates preferred themes
    - Test emerging profile defaults when `total_interactions < 5`
    - Test low-confidence emotion signals are discarded
    - Test `_analyze_transcript` with various sentence types
    - _Requirements: 1.1, 1.2, 1.5, 2.2, 2.3, 2.5_

- [ ] 5. Implement RelationshipMapper (Layer 2)
  - [ ] 5.1 Create `backend/app/services/relationship_mapper.py`
    - Implement `RelationshipMapper` class with `SiblingDB` dependency
    - Methods: `update_from_event()`, `record_shared_choice()`, `record_conflict()`, `compute_session_score()`, `generate_summary()`, `load_model()`, `persist_model()`, `_apply_cross_session_decay()`
    - Track `leadership_balance` shifting toward initiator on each shared choice
    - Track `cooperation_score` based on cooperative vs competitive choices
    - Detect conflict: two consecutive disagreements → append `ConflictEvent`
    - Compute `emotional_synchrony` from paired emotion readings
    - Cross-session decay: leadership decays toward 0.5, cooperation and synchrony decay toward 0 with factor 0.9
    - `compute_session_score()`: equal-weighted mean of centered leadership, cooperation, synchrony
    - `generate_summary()`: 2-3 sentence plain-language summary; include suggestion if score drops > 0.2
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 8.3, 9.1, 9.2, 9.3, 9.4_

  - [ ]* 5.2 Write property test for leadership balance shift
    - **Property 8: Leadership balance shift from shared choices**
    - **Validates: Requirements 3.1**

  - [ ]* 5.3 Write property test for conflict detection
    - **Property 10: Conflict detection from consecutive disagreements**
    - **Validates: Requirements 3.5**

  - [ ]* 5.4 Write property test for emotional synchrony
    - **Property 11: Emotional synchrony from emotion pairs**
    - **Validates: Requirements 3.6**

  - [ ]* 5.5 Write property test for cross-session metric decay
    - **Property 20: Cross-session metric decay**
    - **Validates: Requirements 8.3**

  - [ ]* 5.6 Write property test for score drop suggestion trigger
    - **Property 23: Score drop suggestion trigger**
    - **Validates: Requirements 9.4**

  - [ ]* 5.7 Write unit tests for RelationshipMapper in `backend/tests/test_relationship_mapper.py`
    - Test `record_shared_choice` updates leadership and cooperation
    - Test conflict event creation after two consecutive disagreements
    - Test `compute_session_score` formula
    - Test `generate_summary` includes suggestion on score drop
    - Test `_apply_cross_session_decay` with known values
    - _Requirements: 3.1, 3.2, 3.4, 3.5, 3.6, 8.3, 9.1, 9.4_

- [ ] 6. Checkpoint - Verify Layer 1 and Layer 2 services
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement ComplementarySkillsDiscoverer (Layer 3)
  - [ ] 7.1 Create `backend/app/services/skills_discoverer.py`
    - Implement `ComplementarySkillsDiscoverer` class with `SiblingDB` dependency
    - Methods: `evaluate()`, `_find_complementary_pairs()`, `check_growth()`, `load_skill_map()`, `persist_skill_map()`
    - `evaluate()` returns `None` if both profiles don't have `high_confidence_count() >= 3`
    - Only re-evaluate when `interaction_count >= last_evaluation + 10`
    - `_find_complementary_pairs()`: strength > 0.7 paired with growth area < 0.4
    - Each `ComplementaryPair` includes strength holder, growth holder, trait dimension, suggested scenario
    - `check_growth()`: compare current trait scores against initial profiles stored in `initial_profiles` table, return traits improved by >= 0.2
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 8.4_

  - [ ]* 7.2 Write property test for skill map generation threshold
    - **Property 12: Skill map generation threshold**
    - **Validates: Requirements 4.1**

  - [ ]* 7.3 Write property test for complementary pair identification
    - **Property 13: Complementary pair identification**
    - **Validates: Requirements 4.2**

  - [ ]* 7.4 Write property test for skill map re-evaluation interval
    - **Property 14: Skill map re-evaluation interval**
    - **Validates: Requirements 4.4**

  - [ ]* 7.5 Write property test for growth detection
    - **Property 21: Growth detection**
    - **Validates: Requirements 8.4**

  - [ ]* 7.6 Write unit tests for ComplementarySkillsDiscoverer in `backend/tests/test_skills_discoverer.py`
    - Test `evaluate()` returns `None` when profiles lack confidence
    - Test `_find_complementary_pairs()` with known trait values
    - Test re-evaluation skipped when interaction count delta < 10
    - Test `check_growth()` detects improvement >= 0.2
    - _Requirements: 4.1, 4.2, 4.4, 8.4_

- [ ] 8. Implement narrative directives and StorytellerAgent enhancement (Layer 4)
  - [ ] 8.1 Create narrative directive builder in `backend/app/services/narrative_directives.py`
    - Build a `build_narrative_directives()` function that takes `PersonalityProfile` pair, `RelationshipModel`, `SkillMap`, and session state
    - Generate directives: "let less-active child lead" when leadership imbalanced, "cooperative challenge" on conflict/low cooperation, "teaching scenario" when complementary pairs exist, fear avoidance instructions, "soften tone" when child emotion is sad/scared
    - Track protagonist alternation: alternate `protagonist_child_id` across consecutive story moments
    - Track neglected child: if a child not featured in last 3 moments, add directive to feature them
    - Return structured dict with directives list, protagonist ID, and child roles
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 6.2, 7.1, 7.2, 7.3, 7.5_

  - [ ] 8.2 Extend `StorytellerAgent._build_prompt()` in `backend/app/agents/storyteller_agent.py`
    - Add optional kwargs: `personality_context`, `relationship_context`, `skill_map_context`, `narrative_directives`
    - Inject new prompt sections: `PERSONALITY INSIGHTS`, `RELATIONSHIP DYNAMICS`, `COMPLEMENTARY SKILLS`, `NARRATIVE DIRECTIVES`
    - Ensure dual-child prompts address both children by name with distinct roles
    - Add 15-second timeout nudge instruction for silent child
    - Acknowledge both children's responses in prompt when both respond
    - _Requirements: 5.1, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5, 7.1, 7.4_

  - [ ]* 8.3 Write property test for narrative directives
    - **Property 16: Narrative directives reflect active conditions**
    - **Validates: Requirements 5.2, 5.3, 5.4, 7.1, 7.2, 7.3**

  - [ ]* 8.4 Write property test for protagonist alternation
    - **Property 17: Protagonist alternation**
    - **Validates: Requirements 5.5**

  - [ ]* 8.5 Write property test for dual-child prompt addressing
    - **Property 18: Dual-child prompt addressing with distinct roles**
    - **Validates: Requirements 6.1, 6.2**

  - [ ]* 8.6 Write property test for neglected child featuring
    - **Property 19: Neglected child featuring**
    - **Validates: Requirements 7.5**

  - [ ]* 8.7 Write unit tests for narrative directives in `backend/tests/test_narrative_directives.py`
    - Test directive generation for each condition (imbalance, conflict, low cooperation, fears, sad/scared emotion)
    - Test protagonist alternation logic
    - Test neglected child detection after 3 moments
    - _Requirements: 5.2, 5.3, 5.4, 5.5, 7.1, 7.2, 7.5_

- [ ] 9. Checkpoint - Verify all 4 layers independently
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Integrate layers into Orchestrator
  - [ ] 10.1 Extend `AgentOrchestrator` in `backend/app/agents/orchestrator.py`
    - Add `PersonalityEngine`, `RelationshipMapper`, `ComplementarySkillsDiscoverer` as dependencies in `__init__`
    - Add `process_sibling_event()` method: calls Layer 1 → Layer 2 → Layer 3 → Layer 4 in sequence
    - Skip Layers 1-3 when event has no usable data (empty transcript and no emotions) per Requirement 11.4
    - Wrap each layer call in try/except for resilience — log errors and continue
    - Add `end_session()` method: persist profiles, compute `Sibling_Dynamics_Score`, generate summary, save to DB
    - Full pipeline must complete within 8 seconds of receiving a `MultimodalInputEvent`
    - _Requirements: 8.1, 9.1, 9.2, 9.3, 9.4, 11.1, 11.4, 11.5_

  - [ ]* 10.2 Write property test for empty event skipping
    - **Property 25: Empty event skips pipeline**
    - **Validates: Requirements 11.4**

  - [ ]* 10.3 Write unit tests for orchestrator integration in `backend/tests/test_orchestrator_sibling.py`
    - Test `process_sibling_event` calls layers in correct order
    - Test empty event skips personality and relationship updates
    - Test `end_session` persists data and returns score + summary
    - Test resilience: one layer failure doesn't block others
    - _Requirements: 11.1, 11.4, 11.5, 8.1, 9.2_

- [ ] 11. Add API endpoints and WebSocket updates
  - [ ] 11.1 Add REST endpoints in `backend/app/main.py`
    - `GET /api/sessions/{session_id}/sibling-summary` — returns `Sibling_Dynamics_Score` and plain-language summary (404 if not found)
    - `POST /api/sessions/{session_id}/end` — triggers `end_session` flow, idempotent
    - _Requirements: 9.2, 9.3, 9.4_

  - [ ] 11.2 Update WebSocket handler in `backend/app/main.py`
    - Route to `process_sibling_event` instead of `process_multimodal_event` when sibling mode is active
    - Pass `child1_id` and `child2_id` from session context
    - _Requirements: 11.1, 11.5_

- [ ] 12. Checkpoint - Verify full backend integration
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement frontend components
  - [ ] 13.1 Create `frontend/src/stores/siblingStore.js`
    - Zustand store with state: `siblingDynamicsScore`, `sessionSummary`, `parentSuggestion`, `childRoles`, `waitingForChild`
    - Actions: `setSiblingScore()`, `setSessionSummary()`, `setParentSuggestion()`, `setChildRoles()`, `setWaitingForChild()`, `reset()`
    - _Requirements: 9.1, 9.2, 9.3_

  - [ ] 13.2 Create `frontend/src/components/DualPrompt.jsx`
    - Render interactive prompts addressing both children by name with distinct roles from `siblingStore.childRoles`
    - Show gentle nudge after 15 seconds if one child hasn't responded (use `siblingStore.waitingForChild`)
    - Acknowledge both responses when both children reply
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

  - [ ] 13.3 Create `frontend/src/components/SiblingDashboard.jsx`
    - Parent-facing panel showing `Sibling_Dynamics_Score` from `siblingStore`
    - Display session summary text
    - Show parent suggestion when available (score drop > 0.2)
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ] 13.4 Update `frontend/src/components/DualStoryDisplay.jsx`
    - Integrate with `siblingStore` to show current protagonist child
    - Render role-specific prompt text from `childRoles`
    - _Requirements: 5.5, 6.2, 7.4_

- [ ] 14. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation after each major layer
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases using pytest
- The design specifies Python for all backend code and JavaScript/React for frontend
- All 25 correctness properties from the design document are covered as optional sub-tasks
