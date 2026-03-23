# Requirements Document

## Introduction

This feature introduces end-to-end tests that make real Gemini API calls against the StorytellerAgent and the content filtering pipeline. The existing 809+ backend tests all run against mocks (conftest.py pre-populates sys.modules with MagicMock for google.generativeai, vertexai, chromadb). Real API tests will catch prompt quality regressions, safety setting misconfigurations, and structural issues in Gemini responses that mocks cannot detect. Because the budget is very limited, the test suite must minimize API calls through response caching, short prompts, and explicit opt-in execution.

## Glossary

- **E2E_Test_Suite**: The pytest test module(s) marked with `@pytest.mark.e2e` that execute real Gemini API calls
- **StorytellerAgent**: The agent in `storyteller_agent.py` that uses the `google.generativeai` SDK with `gemini-2.0-flash-exp` to generate story segments
- **ContentFilter**: The service in `content_filter.py` that scans AI-generated text against a blocklist and theme rules, returning a ContentRating (SAFE, REVIEW, BLOCKED)
- **StoryCoordinator**: The coordinator in `story_coordinator.py` that orchestrates story generation with content filtering and retry logic
- **ResponseCache**: A file-based cache that records Gemini API responses keyed by prompt hash, enabling replay without additional API calls
- **BudgetGuard**: A mechanism that tracks cumulative API cost per test run and aborts the suite when a configurable spending threshold is exceeded
- **Orchestrator**: The top-level coordinator in `orchestrator.py` that drives the full multimodal story generation flow (text, image, audio, memory)
- **GOOGLE_API_KEY**: Environment variable required to authenticate with the google.generativeai SDK

## Requirements

### Requirement 1: E2E Test Marker and Isolation

**User Story:** As a developer, I want e2e tests separated from unit tests via a pytest marker, so that real API calls only run when explicitly requested and never in default CI.

#### Acceptance Criteria

1. THE E2E_Test_Suite SHALL register a custom pytest marker named `e2e` in `pyproject.toml` or `conftest.py`
2. WHEN `pytest tests/ -m e2e` is executed, THE E2E_Test_Suite SHALL run only tests decorated with `@pytest.mark.e2e`
3. WHEN `pytest tests/` is executed without the `-m e2e` flag, THE E2E_Test_Suite SHALL skip all e2e-marked tests
4. THE E2E_Test_Suite SHALL bypass the sys.modules mock patching from `conftest.py` so that real `google.generativeai` imports are used

### Requirement 2: Graceful Skip on Missing Credentials

**User Story:** As a CI operator, I want e2e tests to skip gracefully when API credentials are absent, so that CI pipelines do not fail due to missing secrets.

#### Acceptance Criteria

1. WHEN the GOOGLE_API_KEY environment variable is not set, THE E2E_Test_Suite SHALL skip all e2e tests with a descriptive skip reason
2. WHEN the GOOGLE_API_KEY environment variable is set to an empty string, THE E2E_Test_Suite SHALL treat the key as absent and skip all e2e tests
3. THE E2E_Test_Suite SHALL use `pytest.importorskip` or `pytest.mark.skipif` to implement the credential check at the module or fixture level

### Requirement 3: StorytellerAgent Real Generation Test

**User Story:** As a developer, I want to verify that StorytellerAgent produces a valid story segment with a real Gemini call, so that I can catch prompt quality regressions.

#### Acceptance Criteria

1. WHEN a minimal story context with two named characters is provided, THE E2E_Test_Suite SHALL call `StorytellerAgent.generate_story_segment()` with the real Gemini API
2. WHEN the StorytellerAgent returns a response, THE E2E_Test_Suite SHALL verify the response contains a non-empty `text` field
3. WHEN the StorytellerAgent returns a response, THE E2E_Test_Suite SHALL verify the response contains a `timestamp` field in ISO 8601 format
4. WHEN the StorytellerAgent returns a response, THE E2E_Test_Suite SHALL verify the response contains an `interactive` dictionary with `type`, `text`, and `expects_response` keys
5. WHEN the StorytellerAgent returns a response, THE E2E_Test_Suite SHALL verify the `text` field mentions at least one of the two character names provided in the context

### Requirement 4: Prompt Quality Validation

**User Story:** As a developer, I want to validate that Gemini output meets child-friendly storytelling standards, so that prompt regressions are caught before they reach users.

#### Acceptance Criteria

1. WHEN the StorytellerAgent generates a story segment, THE E2E_Test_Suite SHALL verify the `text` field contains at least one question mark (indicating an interactive element)
2. WHEN the StorytellerAgent generates a story segment, THE E2E_Test_Suite SHALL verify the `text` field length is between 50 and 5000 characters
3. WHEN the StorytellerAgent generates a story segment, THE E2E_Test_Suite SHALL verify the `text` field does not contain any terms from the ContentFilter blocklist

### Requirement 5: Content Filter Integration with Real Output

**User Story:** As a developer, I want to run the ContentFilter against real Gemini output, so that I can verify the filtering pipeline works end-to-end.

#### Acceptance Criteria

1. WHEN a real Gemini story segment is generated, THE E2E_Test_Suite SHALL pass the `text` field through `ContentFilter.scan()` and verify the result rating is SAFE
2. WHEN `ContentFilter.scan()` is called with allowed_themes set to a subset of AVAILABLE_THEMES, THE E2E_Test_Suite SHALL verify the result rating is either SAFE or REVIEW (not BLOCKED)
3. WHEN the StoryCoordinator `generate_safe_story_segment()` is called with real Gemini, THE E2E_Test_Suite SHALL verify the returned segment passed content filtering

### Requirement 6: Safety Settings Handling

**User Story:** As a developer, I want to verify that Gemini safety settings are correctly configured and that blocked responses are handled gracefully, so that the app never shows unsafe content.

#### Acceptance Criteria

1. THE E2E_Test_Suite SHALL verify that the StorytellerAgent model is configured with `BLOCK_LOW_AND_ABOVE` threshold for all four harm categories
2. WHEN the Gemini API raises a `StopCandidateException` or `BlockedPromptException`, THE StorytellerAgent SHALL return the fallback story containing both character names
3. IF the Gemini API blocks a response, THEN THE E2E_Test_Suite SHALL verify the fallback story contains a non-empty `text` field and a valid `interactive` dictionary

### Requirement 7: Response Caching for Cost Control

**User Story:** As a developer, I want API responses cached to disk so that repeated test runs during development do not incur additional API costs.

#### Acceptance Criteria

1. THE ResponseCache SHALL store Gemini API responses as JSON files keyed by a SHA-256 hash of the prompt text
2. WHEN a cached response exists for a given prompt hash, THE ResponseCache SHALL return the cached response without making an API call
3. WHEN no cached response exists, THE ResponseCache SHALL call the real API, store the response, and return the result
4. THE ResponseCache SHALL store cached responses in a configurable directory (default: `backend/tests/e2e_cache/`)
5. WHEN the `--e2e-no-cache` pytest flag is passed, THE ResponseCache SHALL bypass the cache and make fresh API calls
6. THE ResponseCache SHALL include a cache invalidation mechanism that clears entries older than a configurable TTL (default: 7 days)

### Requirement 8: Budget Guard

**User Story:** As a developer, I want a fail-safe that prevents runaway API costs during e2e test runs, so that a misconfigured test loop cannot drain the budget.

#### Acceptance Criteria

1. THE BudgetGuard SHALL track the cumulative number of API calls made during a single pytest session
2. WHEN the cumulative API call count exceeds a configurable maximum (default: 20 calls per session), THE BudgetGuard SHALL abort the remaining e2e tests with a clear error message
3. THE BudgetGuard SHALL be implemented as a pytest plugin or session-scoped fixture
4. WHEN the `--e2e-max-calls` pytest flag is provided, THE BudgetGuard SHALL use the specified value as the maximum call limit

### Requirement 9: Token Usage Minimization

**User Story:** As a developer, I want e2e tests to use minimal token budgets, so that each test run costs as little as possible.

#### Acceptance Criteria

1. THE E2E_Test_Suite SHALL use a reduced `max_output_tokens` value (256 tokens) for all e2e test Gemini calls instead of the production value (2048 tokens)
2. THE E2E_Test_Suite SHALL use short, minimal test prompts with two-character contexts containing only required fields (name, gender, spirit_animal)
3. THE E2E_Test_Suite SHALL reuse a single StorytellerAgent instance across all e2e tests within a session via a session-scoped fixture

### Requirement 10: Text-Only Orchestrator Flow

**User Story:** As a developer, I want to test the full orchestrator flow with real Gemini but without image generation, so that I can validate the end-to-end pipeline without incurring Imagen 3 costs.

#### Acceptance Criteria

1. WHEN the E2E_Test_Suite runs the orchestrator flow, THE E2E_Test_Suite SHALL disable the VisualStorytellingAgent by setting `visual_agent.enabled = False`
2. WHEN the orchestrator flow completes, THE E2E_Test_Suite SHALL verify the result contains a non-empty `text` field and `agents_used.storyteller` is True
3. WHEN the orchestrator flow completes with image generation disabled, THE E2E_Test_Suite SHALL verify `agents_used.visual` is False and `image` is None
