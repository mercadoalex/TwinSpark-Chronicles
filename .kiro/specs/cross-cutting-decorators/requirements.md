# Requirements: Cross-Cutting Decorators

## Introduction

This document defines requirements for five composable decorators (`@with_retry`, `@log_call`, `@timed`, `@safe`, `@validate_session`) in `backend/app/utils/decorators.py`. These decorators encapsulate retry logic, structured logging, timing instrumentation, error suppression, and session validation — replacing duplicated cross-cutting code across backend services. All decorators work with both sync and async functions and use only the Python standard library.

## Glossary

- **Decorator_Module**: The Python module at `backend/app/utils/decorators.py` containing all five decorator factory functions.
- **Decorated_Function**: Any sync or async Python function to which a decorator is applied.
- **Retry_Decorator**: The `@with_retry` decorator that retries a function on specified exceptions with exponential backoff.
- **Log_Decorator**: The `@log_call` decorator that logs function entry, exit, elapsed time, and exceptions.
- **Timed_Decorator**: The `@timed` decorator that measures and records function execution time.
- **Safe_Decorator**: The `@safe` decorator that catches exceptions and returns a fallback value.
- **Session_Decorator**: The `@validate_session` decorator that checks session expiry before executing the wrapped method.
- **Backoff**: The base delay in seconds used for exponential backoff calculation: `backoff * 2^attempt`.
- **Fallback_Value**: The value returned by `@safe` when the decorated function raises an exception.
- **Expired_Response**: The standard dict returned by `@validate_session` when a session has expired.

## Requirements

### Requirement 1: Sync/Async Transparency

**User Story:** As a developer, I want decorators that automatically handle both sync and async functions, so that I can apply them uniformly without worrying about the function type.

#### Acceptance Criteria

1.1. WHEN a decorator is applied to an async function, THE Decorator_Module SHALL return an async wrapper that is recognized by `asyncio.iscoroutinefunction`.

1.2. WHEN a decorator is applied to a sync function, THE Decorator_Module SHALL return a sync wrapper that is not recognized by `asyncio.iscoroutinefunction`.

1.3. THE Decorator_Module SHALL detect sync vs async at decoration time using `asyncio.iscoroutinefunction` on the original function.

### Requirement 2: Signature Preservation

**User Story:** As a developer, I want decorated functions to retain their original metadata, so that introspection, documentation tools, and debugging work correctly.

#### Acceptance Criteria

2.1. THE Decorator_Module SHALL preserve `__name__`, `__doc__`, and `__module__` of the Decorated_Function using `functools.wraps`.

2.2. WHEN a Decorated_Function is inspected, THE Decorator_Module SHALL ensure the wrapper exposes the same `__qualname__` as the original function.

### Requirement 3: Retry with Exponential Backoff

**User Story:** As a developer, I want to retry transient failures with configurable backoff, so that intermittent errors in external API calls are handled gracefully.

#### Acceptance Criteria

3.1. WHEN a Decorated_Function raises an exception listed in the `exceptions` tuple, THE Retry_Decorator SHALL retry the function up to `max_attempts` total calls.

3.2. WHEN all `max_attempts` attempts fail with a caught exception, THE Retry_Decorator SHALL re-raise the last exception to the caller.

3.3. WHEN a Decorated_Function raises an exception NOT in the `exceptions` tuple, THE Retry_Decorator SHALL propagate the exception immediately without further retries.

3.4. WHEN a retry occurs, THE Retry_Decorator SHALL wait `backoff * 2^attempt` seconds before the next attempt, using `asyncio.sleep` for async functions and `time.sleep` for sync functions.

3.5. WHEN `max_attempts` is set to 1, THE Retry_Decorator SHALL call the function exactly once with no retry.

3.6. WHEN the Decorated_Function succeeds on any attempt, THE Retry_Decorator SHALL return the successful result immediately.

### Requirement 4: Structured Call Logging

**User Story:** As a developer, I want automatic entry/exit logging with timing on service methods, so that I can trace execution flow and diagnose performance issues.

#### Acceptance Criteria

4.1. WHEN a Decorated_Function is called, THE Log_Decorator SHALL emit a log message containing the function's qualified name and its arguments before execution begins.

4.2. WHEN a Decorated_Function completes successfully, THE Log_Decorator SHALL emit a log message containing the function's qualified name and elapsed time in seconds.

4.3. WHEN a Decorated_Function raises an exception, THE Log_Decorator SHALL log the exception at `exception` level with the qualified name, elapsed time, and error details, then re-raise the exception.

4.4. WHEN no logger is provided, THE Log_Decorator SHALL create a logger using `logging.getLogger(fn.__module__)`.

4.5. THE Log_Decorator SHALL emit entry and success messages at the log level specified by the `level` parameter.

### Requirement 5: Execution Timing

**User Story:** As a developer, I want to measure function execution time and optionally collect metrics, so that I can identify performance bottlenecks.

#### Acceptance Criteria

5.1. THE Timed_Decorator SHALL measure elapsed wall-clock time using `time.perf_counter` and log it with the metric name.

5.2. WHEN a `metrics` dict is provided, THE Timed_Decorator SHALL store the elapsed time in `metrics[metric_name]` after execution.

5.3. WHEN `metric_name` is None, THE Timed_Decorator SHALL default to `"{fn.__module__}.{fn.__qualname__}"`.

5.4. WHEN the Decorated_Function raises an exception, THE Timed_Decorator SHALL still record the elapsed time before the exception propagates.

### Requirement 6: Safe Error Suppression

**User Story:** As a developer, I want non-critical operations to return a fallback value instead of crashing, so that failures in optional features do not break the main flow.

#### Acceptance Criteria

6.1. WHEN a Decorated_Function raises any `Exception` subclass, THE Safe_Decorator SHALL catch the exception, log it with full traceback, and return the Fallback_Value.

6.2. WHEN a Decorated_Function raises a `BaseException` subclass that is not an `Exception` (e.g., `KeyboardInterrupt`, `SystemExit`), THE Safe_Decorator SHALL allow the exception to propagate.

6.3. WHEN a Decorated_Function completes successfully, THE Safe_Decorator SHALL return the actual result unchanged.

6.4. WHEN no logger is provided, THE Safe_Decorator SHALL create a logger using `logging.getLogger(fn.__module__)`.

### Requirement 7: Session Validation

**User Story:** As a developer, I want session expiry checks applied declaratively to orchestrator methods, so that expired sessions are handled consistently without duplicating guard logic.

#### Acceptance Criteria

7.1. WHEN the session enforcer attribute exists on `self` and the session is expired, THE Session_Decorator SHALL return the Expired_Response dict without calling the Decorated_Function.

7.2. WHEN the session enforcer attribute exists on `self` and the session is not expired, THE Session_Decorator SHALL call the Decorated_Function normally and return its result.

7.3. WHEN the session enforcer attribute is None or missing on `self`, THE Session_Decorator SHALL skip the session check and call the Decorated_Function normally.

7.4. THE Expired_Response SHALL contain `session_time_expired: True`, empty text, null image, empty audio, empty interactive dict, null timestamp, zero memories_used, empty voice_recordings, and all agents_used set to False.

### Requirement 8: Decorator Composability

**User Story:** As a developer, I want to stack multiple decorators on a single function, so that I can combine retry, logging, timing, and safety concerns declaratively.

#### Acceptance Criteria

8.1. WHEN multiple decorators are stacked on a single function, THE Decorator_Module SHALL ensure each decorator wraps the next without interfering with its behavior.

8.2. WHEN decorators are stacked, THE Decorator_Module SHALL preserve the sync/async nature through the entire decorator chain.

### Requirement 9: No External Dependencies

**User Story:** As a developer, I want the decorator module to use only the Python standard library, so that no new packages are added to the project.

#### Acceptance Criteria

9.1. THE Decorator_Module SHALL import only from `functools`, `asyncio`, `time`, `logging`, and `inspect` modules.

9.2. THE Decorator_Module SHALL not require any changes to `requirements.txt`.
