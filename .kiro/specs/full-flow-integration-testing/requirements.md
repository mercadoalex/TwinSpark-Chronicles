# Requirements Document

## Introduction

This feature adds full-flow integration tests that exercise the complete Twin Spark Chronicles pipeline end-to-end: setup wizard character configuration → WebSocket connection → story generation → scene display. Unlike the existing `e2e-gemini-testing` spec (which covers backend-only real Gemini API tests), this spec validates the entire system working together — frontend stores, WebSocket transport, backend orchestrator, and story rendering — using "Ale" and "Sofi" as the canonical test sibling pair. Because the Gemini API budget is very limited, the backend orchestrator and agents are mocked at the boundary so that full-flow tests run without real API calls, focusing on integration correctness rather than prompt quality.

## Glossary

- **Full_Flow_Test_Suite**: The collection of backend (pytest) and frontend (vitest) integration tests that validate the complete application pipeline from setup through story display
- **Setup_Wizard**: The frontend character configuration flow (`SetupScreen` → `CharacterSetup`) that collects sibling names, genders, spirit animals, costumes, and toys before connecting to the backend
- **WebSocket_Handler**: The FastAPI WebSocket endpoint at `/ws/{session_id}` that accepts connections with query parameters, routes messages, and streams story segments back to the client
- **ConnectionManager**: The server-side class in `main.py` that tracks active WebSocket connections, input managers, and session tasks
- **AgentOrchestrator**: The facade in `orchestrator.py` that coordinates StoryCoordinator, MediaCoordinator, WorldCoordinator, and SessionCoordinator to produce multimodal story moments
- **StoryBeat**: A complete story moment containing narration, child perspectives, scene image URL, choices, and optional voice recordings — rendered by `DualStoryDisplay`
- **Ale_And_Sofi_Fixture**: A reusable test fixture providing character profiles for Ale (girl, Dragon spirit) and Sofi (boy, Owl spirit) as the canonical test sibling pair
- **WebSocketService**: The frontend singleton class that manages WebSocket connection, reconnection, and event routing to Zustand stores
- **SessionStore**: The Zustand store tracking connection state, session ID, and profiles
- **StoryStore**: The Zustand store accumulating story assets (narration, perspectives, image, choices) and assembling them into a StoryBeat on STORY_COMPLETE
- **SetupStore**: The Zustand store managing the setup wizard state (language, child1/child2 profiles, completion status)

## Requirements

### Requirement 1: Canonical Test Fixture for Ale and Sofi

**User Story:** As a developer, I want a shared test fixture with Ale and Sofi's character profiles, so that all full-flow tests use consistent, realistic sibling data.

#### Acceptance Criteria

1. THE Ale_And_Sofi_Fixture SHALL provide a character profiles object containing Ale as child1 (name: "Ale", gender: "girl", spirit_animal: "Dragon", toy_name: "Bruno") and Sofi as child2 (name: "Sofi", gender: "boy", spirit_animal: "Owl", toy_name: "Book")
2. THE Ale_And_Sofi_Fixture SHALL provide WebSocket connection query parameters matching the format expected by the WebSocket_Handler (lang, c1_name, c1_gender, c1_personality, c1_spirit, c1_toy, c2_name, c2_gender, c2_personality, c2_spirit, c2_toy)
3. THE Ale_And_Sofi_Fixture SHALL derive the sibling_pair_id as "Ale:Sofi" (alphabetically sorted, colon-separated)
4. THE Ale_And_Sofi_Fixture SHALL be available as a pytest fixture (backend) and a test helper module (frontend)

### Requirement 2: Backend WebSocket Connection Integration Test

**User Story:** As a developer, I want to verify that the WebSocket endpoint accepts a connection with Ale and Sofi's parameters and returns the initial input_status message, so that I can confirm the connection handshake works end-to-end.

#### Acceptance Criteria

1. WHEN a WebSocket client connects to `/ws/{session_id}` with Ale and Sofi query parameters, THE WebSocket_Handler SHALL accept the connection and send an `input_status` message as the first response
2. WHEN the WebSocket connection is established, THE ConnectionManager SHALL register the session in `active_connections` with the provided session_id
3. WHEN the WebSocket connection is established, THE ConnectionManager SHALL create an InputManager instance for the session
4. WHEN the WebSocket client disconnects, THE ConnectionManager SHALL remove the session from `active_connections` and cancel pending tasks

### Requirement 3: Backend Story Generation Flow Integration Test

**User Story:** As a developer, I want to verify that sending a story context message through the WebSocket triggers the orchestrator and returns a story_segment response, so that I can confirm the full backend pipeline works.

#### Acceptance Criteria

1. WHEN a connected WebSocket client sends a message with `context` containing Ale and Sofi characters, THE WebSocket_Handler SHALL invoke the StorytellerAgent and return a `story_segment` message
2. WHEN the StorytellerAgent is mocked to return a predetermined story, THE WebSocket_Handler SHALL forward the mocked response as a `story_segment` message with `type` and `data` fields
3. WHEN the story_segment response is received, THE Full_Flow_Test_Suite SHALL verify the `data` field contains `text`, `timestamp`, `characters`, and `interactive` keys
4. IF the StorytellerAgent raises an exception, THEN THE WebSocket_Handler SHALL return a fallback story containing both "Ale" and "Sofi" in the text

### Requirement 4: Backend Orchestrator Rich Story Flow Integration Test

**User Story:** As a developer, I want to verify that the AgentOrchestrator produces a complete multimodal story moment with mocked agents, so that I can confirm coordinator delegation and result assembly work correctly.

#### Acceptance Criteria

1. WHEN `generate_rich_story_moment` is called with Ale and Sofi characters and mocked sub-agents, THE AgentOrchestrator SHALL return a result containing `text`, `image`, `audio`, `interactive`, `timestamp`, `memories_used`, `voice_recordings`, and `agents_used` keys
2. WHEN the StorytellerAgent mock returns a story segment, THE AgentOrchestrator SHALL pass the text through the ContentFilter before including it in the result
3. WHEN the VisualStorytellingAgent is disabled, THE AgentOrchestrator SHALL set `agents_used.visual` to False and `image` to None
4. WHEN the MemoryAgent mock returns previous memories, THE AgentOrchestrator SHALL include the memory count in `memories_used`

### Requirement 5: Frontend Setup Store Integration Test

**User Story:** As a developer, I want to verify that the SetupStore correctly processes Ale and Sofi's character profiles through the setup wizard flow, so that I can confirm the frontend state management works.

#### Acceptance Criteria

1. WHEN `handleSetupComplete` is called with Ale and Sofi profiles, THE SetupStore SHALL set child1 with name "Ale" and child2 with name "Sofi"
2. WHEN `handleSetupComplete` completes, THE SetupStore SHALL set `isComplete` to true
3. WHEN `handleSetupComplete` completes, THE SessionStore SHALL receive enriched profiles with personality, spirit, costume, and toy fields populated
4. WHEN the spirit animal is "Dragon", THE SetupStore SHALL map the personality to "brave"; WHEN the spirit animal is "Owl", THE SetupStore SHALL map the personality to "wise"

### Requirement 6: Frontend Story Beat Assembly Integration Test

**User Story:** As a developer, I want to verify that the StoryStore correctly assembles a StoryBeat from streamed WebSocket assets, so that I can confirm the frontend rendering pipeline works.

#### Acceptance Criteria

1. WHEN the StoryStore receives CREATIVE_ASSET messages for narration, child1_perspective, child2_perspective, image, and choices, THE StoryStore SHALL accumulate the assets in `currentAssets`
2. WHEN the StoryStore receives a STORY_COMPLETE message, THE StoryStore SHALL assemble a StoryBeat with `narration`, `child1_perspective`, `child2_perspective`, `scene_image_url`, and `choices` fields
3. WHEN the assembled StoryBeat is set via `setCurrentBeat`, THE StoryStore SHALL make the beat available for rendering by DualStoryDisplay
4. WHEN a STORY_COMPLETE message includes `voice_recordings`, THE StoryStore SHALL include the voice recordings in the assembled StoryBeat

### Requirement 7: Frontend DualStoryDisplay Rendering Test

**User Story:** As a developer, I want to verify that DualStoryDisplay renders a StoryBeat with Ale and Sofi's names and all expected UI elements, so that I can confirm the final display layer works.

#### Acceptance Criteria

1. WHEN DualStoryDisplay receives a StoryBeat with narration text, THE DualStoryDisplay SHALL render the narration in an element with class `story-narration__text`
2. WHEN DualStoryDisplay receives profiles with c1_name "Ale" and c2_name "Sofi", THE DualStoryDisplay SHALL display both names in the scene avatar area
3. WHEN DualStoryDisplay receives a StoryBeat with choices, THE DualStoryDisplay SHALL render one `story-choice-card` button per choice
4. WHEN a choice button is clicked, THE DualStoryDisplay SHALL call the `onChoice` callback with the selected choice text
5. WHEN DualStoryDisplay receives a StoryBeat with a scene_image_url, THE DualStoryDisplay SHALL render the image via SceneImageLoader

### Requirement 8: Cost Control and Mock Boundary

**User Story:** As a developer, I want all full-flow integration tests to run without real Gemini API calls, so that the test suite incurs zero API cost and runs fast.

#### Acceptance Criteria

1. THE Full_Flow_Test_Suite SHALL mock the StorytellerAgent at the module boundary so that `generate_story_segment` returns a predetermined response without calling the Gemini API
2. THE Full_Flow_Test_Suite SHALL mock the VisualStorytellingAgent so that no Imagen 3 or Vertex AI calls are made
3. THE Full_Flow_Test_Suite SHALL mock the VoiceAgent so that no Cloud Text-to-Speech calls are made
4. THE Full_Flow_Test_Suite SHALL mock the MemoryAgent so that no ChromaDB operations are performed
5. WHEN all mocks are in place, THE Full_Flow_Test_Suite SHALL complete a full story generation cycle in under 5 seconds

### Requirement 9: Session Lifecycle Integration Test

**User Story:** As a developer, I want to verify the complete session lifecycle (connect → generate → disconnect → cleanup), so that I can confirm resources are properly managed.

#### Acceptance Criteria

1. WHEN a WebSocket session is established and a story is generated, THE Full_Flow_Test_Suite SHALL verify the session exists in `ConnectionManager.active_connections`
2. WHEN the WebSocket client disconnects, THE Full_Flow_Test_Suite SHALL verify the session is removed from `ConnectionManager.active_connections`
3. WHEN the WebSocket client disconnects, THE Full_Flow_Test_Suite SHALL verify pending async tasks for the session are cancelled
4. WHEN session time tracking is started on connect, THE Full_Flow_Test_Suite SHALL verify `SessionTimeEnforcer` has an active entry for the session_id

### Requirement 10: WebSocket Message Protocol Conformance Test

**User Story:** As a developer, I want to verify that all WebSocket message types conform to the expected protocol, so that frontend and backend stay in sync.

#### Acceptance Criteria

1. WHEN the backend sends an `input_status` message, THE Full_Flow_Test_Suite SHALL verify the message contains `type`, `camera`, and `mic` fields
2. WHEN the backend sends a `story_segment` message, THE Full_Flow_Test_Suite SHALL verify the message contains `type` and `data` fields where `data` includes `text`
3. WHEN the backend sends an `emotion_feedback` message, THE Full_Flow_Test_Suite SHALL verify the message contains `type` and `emotions` fields where each emotion has `face_id`, `emotion`, and `confidence`
4. WHEN the backend sends a `transcript_feedback` message, THE Full_Flow_Test_Suite SHALL verify the message contains `type`, `text`, and `confidence` fields
