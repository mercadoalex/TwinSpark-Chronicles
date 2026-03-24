# Requirements: Monitoring & Error Tracking

## Introduction

This document defines requirements for a lightweight, self-hosted monitoring and error-tracking pipeline for Twin Spark Chronicles. The system adds structured logging, metrics collection, error aggregation, and a health dashboard — all running locally with no external services. It builds on the existing decorator infrastructure (`@timed`, `@log_call`, `@safe`, `@with_retry`) and React error boundaries.

## Glossary

- **Monitoring_Service**: The backend Python module (`backend/app/services/monitoring_service.py`) that collects, stores, and queries metrics and error records.
- **Error_Tracker**: The component within Monitoring_Service responsible for capturing, deduplicating, and storing error events from both backend and frontend.
- **Metrics_Collector**: The component within Monitoring_Service responsible for recording numeric metrics (counters, gauges, histograms) in memory and persisting snapshots to SQLite.
- **Health_Dashboard**: The set of API endpoints under `/api/monitoring/` that expose collected metrics, error summaries, and system health status.
- **Structured_Log_Formatter**: A Python `logging.Formatter` subclass that outputs log records as JSON lines with consistent fields (timestamp, level, module, message, context).
- **Error_Report**: A JSON payload sent from the React frontend to the backend containing error details (message, stack, component, timestamp).
- **Monitor_Decorator**: A new `@monitor` decorator in `backend/app/utils/decorators.py` that combines timing, error counting, and call counting for decorated functions.
- **Error_Store**: The SQLite table(s) used by Error_Tracker to persist error events with deduplication by fingerprint.
- **Metrics_Store**: The SQLite table(s) used by Metrics_Collector to persist periodic metric snapshots.
- **Error_Fingerprint**: A hash derived from error type, message, and source location used to group duplicate errors.
- **Retention_Period**: The configurable duration (default 7 days) after which old error records and metric snapshots are pruned.

## Requirements

### Requirement 1: Structured JSON Logging

**User Story:** As a developer, I want all backend log output in structured JSON format, so that I can parse, search, and filter logs programmatically.

#### Acceptance Criteria

1.1. THE Structured_Log_Formatter SHALL output each log record as a single JSON line containing `timestamp`, `level`, `logger`, `message`, `module`, and `func` fields.

1.2. WHEN a log record includes an `exc_info` tuple, THE Structured_Log_Formatter SHALL include an `exception` field containing the formatted traceback string.

1.3. WHEN a log record contains an `extra` dict, THE Structured_Log_Formatter SHALL merge the extra key-value pairs into the top-level JSON object.

1.4. THE Structured_Log_Formatter SHALL format timestamps in ISO 8601 format with millisecond precision.

1.5. WHEN the application starts, THE Monitoring_Service SHALL configure the root logger to use the Structured_Log_Formatter on all handlers.

### Requirement 2: Backend Error Capture and Aggregation

**User Story:** As a developer, I want unhandled backend exceptions automatically captured and stored with deduplication, so that I can see which errors occur most frequently without sifting through raw logs.

#### Acceptance Criteria

2.1. WHEN an unhandled exception occurs in a FastAPI request handler, THE Error_Tracker SHALL capture the exception type, message, traceback, request path, and timestamp.

2.2. THE Error_Tracker SHALL compute an Error_Fingerprint from the exception type and the top stack frame (file, function, line number) to group duplicate errors.

2.3. WHEN an error with an existing Error_Fingerprint is captured, THE Error_Tracker SHALL increment the occurrence count and update the `last_seen` timestamp instead of creating a new record.

2.4. THE Error_Tracker SHALL persist error records to the Error_Store in SQLite.

2.5. IF the SQLite write fails, THEN THE Error_Tracker SHALL log the failure and continue operation without crashing the application.

### Requirement 3: Frontend Error Reporting

**User Story:** As a developer, I want React errors captured by error boundaries forwarded to the backend, so that I have a single place to review all application errors.

#### Acceptance Criteria

3.1. WHEN a React ErrorBoundary catches an error, THE Error_Report SHALL be sent as a POST request to `/api/monitoring/errors/frontend` containing `message`, `stack`, `component_stack`, `component_name`, and `timestamp`.

3.2. WHEN the POST request to the backend fails, THE Error_Report SHALL be logged to `console.error` and silently discarded without affecting the user experience.

3.3. THE Error_Tracker SHALL store frontend Error_Reports in the same Error_Store as backend errors, with a `source` field set to `"frontend"`.

3.4. THE Error_Tracker SHALL compute an Error_Fingerprint for frontend errors using the error message and component name.

### Requirement 4: Metrics Collection

**User Story:** As a developer, I want to collect counters, gauges, and timing histograms for key backend operations, so that I can monitor performance trends.

#### Acceptance Criteria

4.1. THE Metrics_Collector SHALL support three metric types: `counter` (monotonically increasing integer), `gauge` (current value), and `histogram` (distribution of values with min, max, mean, p95).

4.2. WHEN a metric is recorded, THE Metrics_Collector SHALL store the value in an in-memory data structure for fast access.

4.3. THE Metrics_Collector SHALL persist metric snapshots to the Metrics_Store in SQLite at a configurable interval (default 60 seconds).

4.4. THE Metrics_Collector SHALL automatically collect `request_count`, `request_duration_ms`, and `error_count` metrics for all FastAPI routes via middleware.

4.5. WHEN the application shuts down, THE Metrics_Collector SHALL flush all pending metric snapshots to SQLite before exiting.

### Requirement 5: Monitor Decorator

**User Story:** As a developer, I want a single `@monitor` decorator that tracks call count, error count, and execution time for any function, so that I can instrument service methods with minimal boilerplate.

#### Acceptance Criteria

5.1. WHEN applied to a function, THE Monitor_Decorator SHALL increment a `{function_qualname}.calls` counter on each invocation.

5.2. WHEN the decorated function raises an exception, THE Monitor_Decorator SHALL increment a `{function_qualname}.errors` counter and re-raise the exception.

5.3. THE Monitor_Decorator SHALL record the execution time of each call as a `{function_qualname}.duration_ms` histogram value.

5.4. THE Monitor_Decorator SHALL work with both sync and async functions, consistent with the existing decorator conventions in the Decorator_Module.

5.5. THE Monitor_Decorator SHALL preserve the decorated function's `__name__`, `__doc__`, `__module__`, and `__qualname__` using `functools.wraps`.

### Requirement 6: Health Dashboard API

**User Story:** As a developer, I want API endpoints that expose current metrics, recent errors, and system health, so that I can check application status at a glance.

#### Acceptance Criteria

6.1. THE Health_Dashboard SHALL expose `GET /api/monitoring/health` returning system status including uptime, Python version, total request count, total error count, and database connectivity.

6.2. THE Health_Dashboard SHALL expose `GET /api/monitoring/metrics` returning all current metric values grouped by metric type (counters, gauges, histograms).

6.3. THE Health_Dashboard SHALL expose `GET /api/monitoring/errors` returning the most recent error records (default limit 50) sorted by `last_seen` descending, with each record including fingerprint, count, source, message, and timestamps.

6.4. THE Health_Dashboard SHALL expose `GET /api/monitoring/errors/{fingerprint}` returning full details for a single error group including the complete traceback.

6.5. WHEN the `since` query parameter is provided on `/api/monitoring/metrics`, THE Health_Dashboard SHALL return only metric snapshots recorded after the specified ISO 8601 timestamp.

### Requirement 7: Data Retention and Cleanup

**User Story:** As a developer, I want old monitoring data automatically pruned, so that the SQLite database does not grow unbounded on a local machine.

#### Acceptance Criteria

7.1. THE Monitoring_Service SHALL delete error records older than the Retention_Period (default 7 days) from the Error_Store.

7.2. THE Monitoring_Service SHALL delete metric snapshots older than the Retention_Period from the Metrics_Store.

7.3. THE Monitoring_Service SHALL run the cleanup process on a configurable interval (default once per hour).

7.4. IF the cleanup process fails, THEN THE Monitoring_Service SHALL log the failure and retry on the next scheduled interval.

### Requirement 8: Request Tracing

**User Story:** As a developer, I want each HTTP request assigned a unique trace ID that appears in all log messages for that request, so that I can correlate logs across services for a single user action.

#### Acceptance Criteria

8.1. WHEN a request arrives, THE Monitoring_Service SHALL generate a UUID4 trace ID and attach it to the request state.

8.2. THE Monitoring_Service SHALL include the trace ID in all structured log messages emitted during that request's lifecycle.

8.3. THE Monitoring_Service SHALL include the trace ID in the response headers as `X-Trace-ID`.

8.4. WHEN an error is captured during a request, THE Error_Tracker SHALL include the trace ID in the error record.

### Requirement 9: No External Dependencies

**User Story:** As a developer, I want the monitoring system to use only the Python standard library and existing project dependencies (FastAPI, aiosqlite), so that no new packages are added.

#### Acceptance Criteria

9.1. THE Monitoring_Service SHALL use only `logging`, `json`, `time`, `uuid`, `hashlib`, `asyncio`, `collections`, `dataclasses`, and `datetime` from the Python standard library.

9.2. THE Monitoring_Service SHALL use `aiosqlite` for database operations, which is already a project dependency.

9.3. THE Monitoring_Service SHALL not require any additions to `requirements.txt`.
