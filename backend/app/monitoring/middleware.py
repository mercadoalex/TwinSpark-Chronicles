"""TraceID and Monitoring middleware for FastAPI."""

import logging
import time
import traceback
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.log_formatter import trace_id_var

logger = logging.getLogger(__name__)


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Generate UUID4 trace_id per request, store in contextvars and response header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        tid = str(uuid.uuid4())
        token = trace_id_var.set(tid)
        request.state.trace_id = tid
        try:
            response = await call_next(request)
            response.headers["X-Trace-ID"] = tid
            return response
        finally:
            trace_id_var.reset(token)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """Record request_count, request_duration_ms, error_count per route."""

    def __init__(self, app, monitoring_service):
        super().__init__(app)
        self._service = monitoring_service

    async def dispatch(self, request: Request, call_next) -> Response:
        metrics = self._service.metrics
        errors = self._service.errors
        start = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Capture unhandled exception
            try:
                metrics.increment("error_count")
                tb = traceback.format_exc()
                tid = getattr(request.state, "trace_id", None)
                await errors.capture(
                    error_type=type(exc).__name__,
                    message=str(exc),
                    traceback=tb,
                    source="backend",
                    location=f"{type(exc).__module__}:{type(exc).__qualname__}",
                    request_path=str(request.url.path),
                    trace_id=tid,
                )
            except Exception:
                logger.error("MonitoringMiddleware failed to capture error", exc_info=True)
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            try:
                metrics.increment("request_count")
                metrics.record("request_duration_ms", elapsed_ms)
            except Exception:
                logger.error("MonitoringMiddleware failed to record metrics", exc_info=True)
