"""
Cross-cutting decorators for retry, logging, timing, error suppression,
and session validation. All decorators support both sync and async functions
and preserve function signatures via functools.wraps.
"""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, Optional, Tuple, Type


def with_retry(
    max_attempts: int = 3,
    backoff: float = 1.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
) -> Callable:
    """Retry with exponential backoff. Works with sync and async functions."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await fn(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(backoff * (2 ** attempt))

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts - 1:
                        raise
                    time.sleep(backoff * (2 ** attempt))

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator


def log_call(
    logger: Optional[logging.Logger] = None,
    level: str = "info",
) -> Callable:
    """Log function entry/exit with args, result summary, and elapsed time."""

    def decorator(fn: Callable) -> Callable:
        _logger = logger or logging.getLogger(fn.__module__)
        log_fn = getattr(_logger, level)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            log_fn("Calling %s(args=%s, kwargs=%s)", fn.__qualname__, args, kwargs)
            start = time.perf_counter()
            try:
                result = await fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_fn("Finished %s -> %.3fs", fn.__qualname__, elapsed)
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                _logger.exception("Failed %s -> %.3fs: %s", fn.__qualname__, elapsed, e)
                raise

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            log_fn("Calling %s(args=%s, kwargs=%s)", fn.__qualname__, args, kwargs)
            start = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_fn("Finished %s -> %.3fs", fn.__qualname__, elapsed)
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                _logger.exception("Failed %s -> %.3fs: %s", fn.__qualname__, elapsed, e)
                raise

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator


def timed(
    metric_name: Optional[str] = None,
    metrics: Optional[dict] = None,
) -> Callable:
    """Measure execution time. Log it and optionally store in a metrics dict."""

    def decorator(fn: Callable) -> Callable:
        name = metric_name or f"{fn.__module__}.{fn.__qualname__}"
        _logger = logging.getLogger(fn.__module__)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                _logger.info("TIMER %s: %.4fs", name, elapsed)
                if metrics is not None:
                    metrics[name] = elapsed

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                _logger.info("TIMER %s: %.4fs", name, elapsed)
                if metrics is not None:
                    metrics[name] = elapsed

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator


def safe(
    fallback: Any = None,
    logger: Optional[logging.Logger] = None,
) -> Callable:
    """Catch all Exception subclasses, log them, return fallback value.
    BaseException subclasses (KeyboardInterrupt, SystemExit) propagate."""

    def decorator(fn: Callable) -> Callable:
        _logger = logger or logging.getLogger(fn.__module__)

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                _logger.exception("Error in %s: %s — returning fallback", fn.__qualname__, e)
                return fallback

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                _logger.exception("Error in %s: %s — returning fallback", fn.__qualname__, e)
                return fallback

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator


def _expired_response() -> dict:
    """Standard response dict returned when a session has expired."""
    return {
        "text": "",
        "image": None,
        "audio": {"narration": None, "character_voices": []},
        "interactive": {},
        "timestamp": None,
        "memories_used": 0,
        "voice_recordings": [],
        "agents_used": {
            "storyteller": False,
            "visual": False,
            "voice": False,
            "memory": False,
        },
        "session_time_expired": True,
    }


def validate_session(
    enforcer_attr: str = "session_time_enforcer",
) -> Callable:
    """Check session time before executing. Return early dict if expired."""

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def async_wrapper(self, session_id: str, *args, **kwargs):
            enforcer = getattr(self, enforcer_attr, None)
            if enforcer is not None:
                time_check = enforcer.check_time(session_id)
                if time_check.is_expired:
                    return _expired_response()
            return await fn(self, session_id, *args, **kwargs)

        @functools.wraps(fn)
        def sync_wrapper(self, session_id: str, *args, **kwargs):
            enforcer = getattr(self, enforcer_attr, None)
            if enforcer is not None:
                time_check = enforcer.check_time(session_id)
                if time_check.is_expired:
                    return _expired_response()
            return fn(self, session_id, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(fn) else sync_wrapper

    return decorator
