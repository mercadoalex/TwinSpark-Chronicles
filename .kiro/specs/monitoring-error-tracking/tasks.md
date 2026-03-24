# Tasks: Monitoring & Error Tracking

## Task 1: Create monitoring package and StructuredLogFormatter
- [x] 1.1 Create `backend/app/monitoring/__init__.py` and `backend/app/monitoring/log_formatter.py` with `StructuredLogFormatter` class that outputs JSON lines with `timestamp` (ISO 8601 ms), `level`, `logger`, `module`, `func`, `message` fields, merges `extra` dict keys, includes `exception` field when `exc_info` is present, and reads `trace_id` from a `contextvars.ContextVar` [requirement 1.1, 1.2, 1.3, 1.4]
- [x] 1.2 Write unit tests in `backend/tests/test_log_formatter.py` for StructuredLogFormatter: valid JSON output, required keys present, ISO 8601 timestamp, exception field when exc_info set, extra dict merged, trace_id included when set [requirement 1.1, 1.2, 1.3, 1.4]
- [ ] *1.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any log message string and level, formatting then JSON-parsing produces a dict with all required keys and the message value matches the original [requirement 1.1, 1.3] [Property 1]

## Task 2: Create ErrorTracker with fingerprinting and deduplication
- [x] 2.1 Create `backend/app/monitoring/error_tracker.py` with `ErrorTracker` class: `compute_fingerprint(error_type, location)` using SHA256 truncated to 16 hex chars, `capture()` that upserts by fingerprint (increment count + update last_seen for existing, insert for new), `get_recent(limit)`, `get_by_fingerprint(fingerprint)`, and `init_db()` to create the `error_events` table. Use aiosqlite with a separate monitoring.db file. Wrap DB writes in try/except to log and continue on failure [requirement 2.1, 2.2, 2.3, 2.4, 2.5]
- [x] 2.2 Write unit tests in `backend/tests/test_error_tracker.py` for ErrorTracker: fingerprint determinism, capture creates new record, capture deduplicates by fingerprint (count increments, last_seen updates), get_recent returns sorted results, get_by_fingerprint returns full details, DB failure is logged without crash [requirement 2.1, 2.2, 2.3, 2.4, 2.5]
- [ ] *2.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any two (error_type, location) string pairs, `compute_fingerprint` returns the same 16-char hex string for identical inputs and different strings for distinct inputs [requirement 2.2, 3.4] [Property 2]

## Task 3: Create MetricsCollector with counter, gauge, histogram support
- [x] 3.1 Create `backend/app/monitoring/metrics_collector.py` with `MetricsCollector` class: `increment(name, value)` for counters, `set_gauge(name, value)` for gauges, `record(name, value)` for histograms (with `HistogramStats` dataclass tracking count, total, min, max, bounded values list, mean/p95 properties), `get_all()` returning grouped metrics, `flush()` persisting snapshots to `metric_snapshots` table, `start_flush_loop()`/`stop_flush_loop()` for periodic persistence [requirement 4.1, 4.2, 4.3, 4.5]
- [x] 3.2 Write unit tests in `backend/tests/test_metrics_collector.py` for MetricsCollector: counter increment, gauge set, histogram record with min/max/mean/p95, get_all grouping, flush persists to SQLite, stop_flush_loop triggers final flush [requirement 4.1, 4.2, 4.3, 4.5]
- [ ] *3.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any sequence of N increment calls on a counter, the counter value equals N (monotonicity) [requirement 4.1, 5.1] [Property 4]
- [ ] *3.4 Write property-based test (Hypothesis, max_examples=20) verifying that for any non-empty sequence of float values recorded in a histogram, `min_val <= mean <= max_val` and `count == len(sequence)` [requirement 4.1, 5.3] [Property 5]

## Task 4: Create MonitoringService facade and retention cleanup
- [x] 4.1 Create `backend/app/monitoring/service.py` with `MonitoringService` class that owns `MetricsCollector` and `ErrorTracker`, provides `start()`/`stop()` lifecycle methods, `cleanup()` that deletes error records and metric snapshots older than `retention_days`, and a periodic cleanup loop. Expose a module-level `get_monitoring_service()` accessor [requirement 7.1, 7.2, 7.3, 7.4]
- [x] 4.2 Write unit tests in `backend/tests/test_monitoring_service.py` for MonitoringService: cleanup deletes old records, cleanup preserves recent records, cleanup failure is logged without crash, health() returns expected fields [requirement 7.1, 7.2, 7.3, 7.4]

## Task 5: Add @monitor decorator to decorators module
- [x] 5.1 Add `monitor(metrics_collector)` decorator factory to `backend/app/utils/decorators.py` that increments `{qualname}.calls` counter on each invocation, increments `{qualname}.errors` counter on exception (then re-raises), records `{qualname}.duration_ms` histogram value, works with sync and async, and preserves function metadata via `functools.wraps` [requirement 5.1, 5.2, 5.3, 5.4, 5.5]
- [x] 5.2 Write unit tests in `backend/tests/test_monitor_decorator.py` for @monitor: calls counter incremented, errors counter incremented on exception, duration_ms recorded, exception re-raised unchanged, works with sync function, works with async function, preserves __name__ and __doc__ [requirement 5.1, 5.2, 5.3, 5.4, 5.5]
- [ ] *5.3 Write property-based test (Hypothesis, max_examples=20) verifying that for any function (sync or async) decorated with @monitor, `asyncio.iscoroutinefunction(decorated) == asyncio.iscoroutinefunction(original)` and `decorated.__name__ == original.__name__` [requirement 5.4, 5.5] [Property 6]
- [ ] *5.4 Write property-based test (Hypothesis, max_examples=20) verifying that for any exception type raised by a decorated function, @monitor re-raises the same exception type and message, and the errors counter is incremented [requirement 5.2] [Property 7]

## Task 6: Create TraceID and Monitoring middleware
- [x] 6.1 Create `backend/app/monitoring/middleware.py` with `TraceIDMiddleware` (generates UUID4 trace_id, stores in `contextvars.ContextVar` and `request.state`, adds `X-Trace-ID` response header) and `MonitoringMiddleware` (records `request_count`, `request_duration_ms`, `error_count` per route via MetricsCollector, captures unhandled exceptions via ErrorTracker) [requirement 4.4, 8.1, 8.2, 8.3, 8.4]
- [x] 6.2 Write unit tests in `backend/tests/test_monitoring_middleware.py` for middleware: trace_id in response header, trace_id is valid UUID4, request_count incremented, request_duration_ms recorded, error_count incremented on exception, error captured with trace_id [requirement 4.4, 8.1, 8.3, 8.4]

## Task 7: Create monitoring API routes
- [x] 7.1 Create `backend/app/monitoring/routes.py` with FastAPI router: `GET /api/monitoring/health` (uptime, Python version, request count, error count, DB connectivity), `GET /api/monitoring/metrics` (all metrics grouped, optional `since` query param), `GET /api/monitoring/errors` (recent errors, default limit 50), `GET /api/monitoring/errors/{fingerprint}` (full error details), `POST /api/monitoring/errors/frontend` (accepts frontend error reports with message, stack, component_stack, component_name, timestamp) [requirement 3.1, 3.3, 3.4, 6.1, 6.2, 6.3, 6.4, 6.5]
- [x] 7.2 Write unit tests in `backend/tests/test_monitoring_routes.py` for API routes: health endpoint returns expected fields, metrics endpoint returns grouped data, metrics endpoint filters by since param, errors endpoint returns sorted list, errors/{fingerprint} returns details or 404, frontend error POST creates record with source="frontend" [requirement 3.1, 3.3, 6.1, 6.2, 6.3, 6.4, 6.5]

## Task 8: Integrate monitoring into FastAPI app startup/shutdown
- [x] 8.1 Update `backend/app/main.py` to: import and register `TraceIDMiddleware` and `MonitoringMiddleware`, create `MonitoringService` instance, call `monitoring_service.start()` in `startup_event` and `monitoring_service.stop()` in `shutdown_event`, include the monitoring router, configure root logger with `StructuredLogFormatter` [requirement 1.5, 4.4, 8.1]
- [x] 8.2 Write integration test in `backend/tests/test_monitoring_integration.py` verifying: full request lifecycle records metrics, trace_id appears in response headers, triggered exception appears in error list, structured log output is valid JSON [requirement 1.5, 4.4, 8.1, 8.3]

## Task 9: Create frontend error reporter and integrate with ErrorBoundary
- [x] 9.1 Create `frontend/src/shared/utils/errorReporter.js` with `reportError(error, errorInfo, componentName)` function that POSTs to `/api/monitoring/errors/frontend` with `message`, `stack`, `component_stack`, `component_name`, `timestamp`, catches fetch failures and logs to `console.error` without throwing [requirement 3.1, 3.2]
- [x] 9.2 Update `frontend/src/shared/components/ErrorBoundary/ErrorBoundary.jsx` to import and call `reportError` in `componentDidCatch` alongside the existing `console.error` and `onError` callback [requirement 3.1, 3.2]
- [x] 9.3 Write unit tests in `frontend/src/shared/utils/__tests__/errorReporter.test.js` for errorReporter: sends correct payload, handles network failure silently, includes timestamp [requirement 3.1, 3.2]

## Task 10: Verify no external dependencies and run full test suite
- [x] 10.1 Verify `backend/app/monitoring/` modules import only from stdlib (`logging`, `json`, `time`, `uuid`, `hashlib`, `asyncio`, `collections`, `dataclasses`, `datetime`, `contextvars`), `aiosqlite`, and `starlette`/`fastapi` [requirement 9.1, 9.2, 9.3]
- [x] 10.2 Run full backend test suite (`cd backend && python -m pytest tests/ -x -q --tb=short`) and verify all existing tests plus new monitoring tests pass [requirement 9.3]
