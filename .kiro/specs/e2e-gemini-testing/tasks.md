# Implementation Plan: E2E Gemini Testing

## Overview

Build a real-API end-to-end test suite for the Gemini integration. The suite exercises `StorytellerAgent`, `ContentFilter`, `StoryCoordinator`, and the text-only `AgentOrchestrator` flow against the live `gemini-2.0-flash-exp` model. Cost control is achieved through a file-based `ResponseCache`, a `BudgetGuard` call limiter, and token minimization. All e2e tests are isolated behind a `@pytest.mark.e2e` marker and skip gracefully when `GOOGLE_API_KEY` is absent.

## Tasks

- [x] 1. Create ResponseCache and BudgetGuard modules
  - [x] 1.1 Create `backend/tests/e2e/response_cache.py` with `ResponseCache` class
    - Implement `__init__(cache_dir, ttl_days=7)` that creates the cache directory via `mkdir(parents=True, exist_ok=True)`
    - Implement `get(prompt)` that computes SHA-256 of prompt, reads `{hash}.json`, returns parsed response dict or `None` on miss/corrupt file
    - Implement `put(prompt, response)` that writes `{"prompt_hash", "timestamp", "response"}` as JSON
    - Implement `clear_stale()` that removes entries older than TTL, returns count removed
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.6_

  - [x] 1.2 Create `backend/tests/e2e/budget_guard.py` with `BudgetGuard` class
    - Implement `__init__(max_calls=20)` with internal counter
    - Implement `record_call()` that increments counter and raises `BudgetExceededError` when limit exceeded
    - Implement `calls_made` and `calls_remaining` properties
    - Define `BudgetExceededError` exception class in the same module
    - _Requirements: 8.1, 8.2_

  - [ ]* 1.3 Write property tests for ResponseCache round-trip and TTL invalidation
    - **Property 6: Cache Round Trip** — generate random prompt strings and response dicts, put then get, assert equality
    - **Property 7: Cache TTL Invalidation** — generate cache entries with backdated timestamps, call `clear_stale()`, assert only fresh entries remain
    - **Validates: Requirements 7.1, 7.2, 7.6**

  - [ ]* 1.4 Write property test for BudgetGuard enforcement
    - **Property 8: Budget Guard Enforcement** — generate random `max_calls` (1–100), call `record_call()` exactly `max_calls` times without error, assert `(max_calls + 1)`-th call raises `BudgetExceededError`
    - **Validates: Requirements 8.1, 8.2**

- [x] 2. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 3. Set up e2e test infrastructure and conftest
  - [x] 3.1 Create `backend/tests/e2e/__init__.py` (empty)
    - _Requirements: 1.1_

  - [x] 3.2 Register `e2e` marker and add CLI options
    - Add `e2e` marker registration via `pytest_configure` hook in root `conftest.py` or `pyproject.toml`
    - Add `--e2e-no-cache` boolean flag and `--e2e-max-calls` integer flag via `pytest_addoption` in root `conftest.py`
    - _Requirements: 1.1, 7.5, 8.4_

  - [x] 3.3 Create `backend/tests/e2e/conftest.py` with e2e-specific fixtures
    - Implement `_restore_real_genai` (session-scoped, autouse for e2e) that pops mock entries from `sys.modules` for `google.generativeai`, `google.generativeai.types`, and related keys, then imports the real SDK
    - Implement `e2e_storyteller` (session-scoped) that creates a `StorytellerAgent` with `max_output_tokens` overridden to 256
    - Implement `response_cache` (session-scoped) that creates a `ResponseCache` pointed at `backend/tests/e2e_cache/`, respects `--e2e-no-cache` flag
    - Implement `budget_guard` (session-scoped) that creates a `BudgetGuard` with limit from `--e2e-max-calls` or default 20
    - Implement `e2e_content_filter` (session-scoped) that creates a real `ContentFilter` instance
    - Implement `e2e_story_coordinator` (session-scoped) that wires real storyteller + content filter with mock memory/voice agents
    - Implement `minimal_story_context` (session-scoped) returning `{"characters": {"child1": {"name": "Mia", "gender": "girl", "spirit_animal": "dolphin"}, "child2": {"name": "Leo", "gender": "boy", "spirit_animal": "eagle"}}, "session_id": "e2e-test-session", "language": "en"}`
    - Add module-level `pytestmark = pytest.mark.skipif(not os.environ.get("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")` for credential skip
    - _Requirements: 1.4, 2.1, 2.2, 2.3, 9.1, 9.2, 9.3_

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement e2e test functions
  - [x] 5.1 Create `backend/tests/e2e/test_e2e_gemini.py` with `test_story_segment_structure`
    - Decorate with `@pytest.mark.e2e`
    - Call `e2e_storyteller.generate_story_segment()` with `minimal_story_context` (use `response_cache` for caching, `budget_guard` to track call)
    - Assert response contains non-empty `text`, ISO 8601 `timestamp`, `interactive` dict with `type`/`text`/`expects_response` keys
    - Assert `text` mentions at least one of "Mia" or "Leo" (case-insensitive)
    - Assert `text` contains at least one `?`, length between 50–5000, no blocklist terms
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 4.1, 4.2, 4.3_

  - [x] 5.2 Add `test_content_filter_on_real_output` to the e2e test module
    - Generate a real story segment, pass `text` through `ContentFilter.scan()`, assert rating is `SAFE`
    - Call `ContentFilter.scan()` with `allowed_themes` set to a subset of `AVAILABLE_THEMES`, assert rating is not `BLOCKED`
    - _Requirements: 5.1, 5.2_

  - [x] 5.3 Add `test_safety_settings_configured` to the e2e test module
    - Inspect `e2e_storyteller.model._safety_settings` and verify all four harm categories use `BLOCK_LOW_AND_ABOVE`
    - _Requirements: 6.1_

  - [x] 5.4 Add `test_fallback_story_structure` to the e2e test module
    - Call `e2e_storyteller._fallback_story()` with `minimal_story_context`, assert both "Mia" and "Leo" appear in `text`
    - Assert `text` is non-empty, `interactive` dict has `type`/`text`/`expects_response` keys
    - _Requirements: 6.2, 6.3_

  - [ ]* 5.5 Write property test for fallback story correctness
    - **Property 5: Fallback Story Correctness** — generate random character name pairs, build context, call `_fallback_story()`, assert structure + both names present
    - **Validates: Requirements 6.2, 6.3**

  - [x] 5.6 Add `test_story_coordinator_safe_generation` to the e2e test module
    - Call `e2e_story_coordinator.generate_safe_story_segment()` with `minimal_story_context` and real Gemini
    - Assert returned segment has non-empty `text` that passed content filtering
    - _Requirements: 5.3_

  - [x] 5.7 Add `test_orchestrator_text_only` to the e2e test module
    - Create an `AgentOrchestrator` instance with real `StorytellerAgent` (256 tokens) and real `ContentFilter`
    - Set `visual_agent.enabled = False` on the `MediaCoordinator`'s visual agent, mock memory/voice/session agents
    - Call `generate_rich_story_moment()` with `minimal_story_context`
    - Assert result has non-empty `text`, `agents_used["storyteller"]` is `True`, `agents_used["visual"]` is `False`, `image` is `None`
    - _Requirements: 10.1, 10.2, 10.3_

- [x] 6. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Add `e2e_cache/` to `.gitignore` and finalize skip behavior
  - [x] 7.1 Add `backend/tests/e2e_cache/` to `.gitignore`
    - _Requirements: 7.4_

  - [x] 7.2 Verify default `pytest tests/` skips all e2e tests
    - Ensure e2e tests are skipped when run without `-m e2e` flag (credential skipif handles this)
    - _Requirements: 1.2, 1.3_

- [x] 8. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Run e2e tests: `source venv/bin/activate && GOOGLE_API_KEY=<key> python3 -m pytest tests/ -m e2e -x -q --tb=short` from `backend/`
- Run unit tests only (default): `source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`
- After pytest: `pkill -f "python.*pytest"` (CacheManager cleanup loop causes hang)
- Property tests use Hypothesis with `@settings(max_examples=100)`
- Each property test includes tag comment: `# Feature: e2e-gemini-testing, Property {N}: {title}`
