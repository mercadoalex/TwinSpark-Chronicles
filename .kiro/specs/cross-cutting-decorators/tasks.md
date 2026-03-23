# Tasks: Cross-Cutting Decorators

## Task 1: Create decorator module with @with_retry
- [x] 1.1 Create `backend/app/utils/decorators.py` with the `with_retry(max_attempts, backoff, exceptions)` decorator factory supporting both sync and async functions, using `functools.wraps` for signature preservation and `asyncio.iscoroutinefunction` for sync/async detection [requirement 1.1, 1.2, 1.3, 2.1, 2.2, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6]
- [x] 1.2 Write unit tests in `backend/tests/test_decorators.py` for `@with_retry`: sync success, async success, retry on caught exception, re-raise after exhaustion, immediate propagation of uncaught exception, max_attempts=1 edge case [requirement 3.1, 3.2, 3.3, 3.5, 3.6]
- [ ] *1.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any max_attempts N and function failing K < N times then succeeding, the function is called K+1 times and returns the success value [requirement 3.1, 3.6] [Property 3]

## Task 2: Add @log_call decorator
- [x] 2.1 Add `log_call(logger, level)` decorator factory to `backend/app/utils/decorators.py` supporting sync and async, logging entry with qualname+args, exit with qualname+elapsed, and exceptions at exception level [requirement 4.1, 4.2, 4.3, 4.4, 4.5]
- [x] 2.2 Write unit tests in `backend/tests/test_decorators.py` for `@log_call`: entry log emitted, exit log with elapsed time, exception logged and re-raised, default logger from module, custom log level [requirement 4.1, 4.2, 4.3, 4.4, 4.5]

## Task 3: Add @timed decorator
- [x] 3.1 Add `timed(metric_name, metrics)` decorator factory to `backend/app/utils/decorators.py` supporting sync and async, measuring elapsed time with `time.perf_counter`, logging it, and optionally storing in a metrics dict [requirement 5.1, 5.2, 5.3, 5.4]
- [x] 3.2 Write unit tests in `backend/tests/test_decorators.py` for `@timed`: metrics dict populated on success, metrics dict populated on exception, default metric_name derivation, log output contains timing [requirement 5.1, 5.2, 5.3, 5.4]
- [ ] *3.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any function (success or failure), the metrics dict always contains the metric key with a non-negative float after execution [requirement 5.1, 5.2, 5.4] [Property 5]

## Task 4: Add @safe decorator
- [x] 4.1 Add `safe(fallback, logger)` decorator factory to `backend/app/utils/decorators.py` supporting sync and async, catching `Exception` subclasses and returning fallback, allowing `BaseException` to propagate [requirement 6.1, 6.2, 6.3, 6.4]
- [x] 4.2 Write unit tests in `backend/tests/test_decorators.py` for `@safe`: returns result on success, returns fallback on exception, logs exception, does not catch KeyboardInterrupt, default logger [requirement 6.1, 6.2, 6.3, 6.4]
- [ ] *4.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any Exception subclass and any fallback value, the decorated function never raises and returns either the actual result or the fallback [requirement 6.1, 6.3] [Property 6]

## Task 5: Add @validate_session decorator
- [x] 5.1 Add `validate_session(enforcer_attr)` decorator factory and `_expired_response()` helper to `backend/app/utils/decorators.py` supporting sync and async, checking session expiry via `self.<enforcer_attr>.check_time(session_id)` [requirement 7.1, 7.2, 7.3, 7.4]
- [x] 5.2 Write unit tests in `backend/tests/test_decorators.py` for `@validate_session`: returns expired response when expired, delegates to function when valid, skips check when enforcer is None, expired response structure matches spec [requirement 7.1, 7.2, 7.3, 7.4]

## Task 6: Cross-cutting tests (signature, sync/async, composability)
- [x] 6.1 Write unit tests in `backend/tests/test_decorators.py` verifying all five decorators preserve `__name__`, `__doc__`, `__module__`, `__qualname__` for both sync and async functions [requirement 2.1, 2.2]
- [x] 6.2 Write unit tests in `backend/tests/test_decorators.py` verifying decorator stacking: `@log_call` + `@timed` + `@with_retry` on a single function produces correct result and all decorators execute [requirement 8.1, 8.2]
- [ ] *6.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any decorator and any function (sync or async), `asyncio.iscoroutinefunction(decorated) == asyncio.iscoroutinefunction(original)` [requirement 1.1, 1.2] [Property 1]
- [ ] *6.4 Write property-based test (Hypothesis, max_examples=20) verifying that for any decorator and any function, `decorated.__name__ == original.__name__` and `decorated.__doc__ == original.__doc__` [requirement 2.1, 2.2] [Property 2]

## Task 7: Verify no external dependencies and run full suite
- [x] 7.1 Verify `backend/app/utils/decorators.py` imports only from `functools`, `asyncio`, `time`, `logging`, and optionally `inspect` [requirement 9.1, 9.2]
- [x] 7.2 Run full test suite (`source venv/bin/activate && python3 -m pytest tests/ -x -q --tb=short` from `backend/`) and verify all existing tests plus new decorator tests pass [requirement 9.2]
