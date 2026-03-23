"""Tests for backend/app/utils/decorators.py"""

import asyncio
import pytest
from unittest.mock import MagicMock

from app.utils.decorators import with_retry


# ─── @with_retry tests ───────────────────────────────────────────────────────


class TestWithRetrySync:
    def test_sync_success_no_retry(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0)
        def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert succeed() == "ok"
        assert call_count == 1

    def test_sync_retry_then_succeed(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0, exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("boom")
            return "recovered"

        assert flaky() == "recovered"
        assert call_count == 3

    def test_sync_exhaustion_reraises(self):
        call_count = 0

        @with_retry(max_attempts=2, backoff=0, exceptions=(ValueError,))
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError("permanent")

        with pytest.raises(ValueError, match="permanent"):
            always_fail()
        assert call_count == 2

    def test_sync_uncaught_exception_propagates_immediately(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0, exceptions=(ValueError,))
        def wrong_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("unexpected")

        with pytest.raises(TypeError, match="unexpected"):
            wrong_error()
        assert call_count == 1

    def test_sync_max_attempts_one(self):
        call_count = 0

        @with_retry(max_attempts=1, backoff=0, exceptions=(ValueError,))
        def fail_once():
            nonlocal call_count
            call_count += 1
            raise ValueError("no retries")

        with pytest.raises(ValueError, match="no retries"):
            fail_once()
        assert call_count == 1


class TestWithRetryAsync:
    @pytest.mark.asyncio
    async def test_async_success_no_retry(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0)
        async def succeed():
            nonlocal call_count
            call_count += 1
            return "ok"

        assert await succeed() == "ok"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_then_succeed(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0, exceptions=(ConnectionError,))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "recovered"

        assert await flaky() == "recovered"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_exhaustion_reraises(self):
        call_count = 0

        @with_retry(max_attempts=2, backoff=0, exceptions=(ConnectionError,))
        async def always_fail():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("down")

        with pytest.raises(ConnectionError, match="down"):
            await always_fail()
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_uncaught_exception_propagates_immediately(self):
        call_count = 0

        @with_retry(max_attempts=3, backoff=0, exceptions=(ConnectionError,))
        async def wrong_error():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("unexpected")

        with pytest.raises(RuntimeError, match="unexpected"):
            await wrong_error()
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_max_attempts_one(self):
        call_count = 0

        @with_retry(max_attempts=1, backoff=0, exceptions=(ValueError,))
        async def fail_once():
            nonlocal call_count
            call_count += 1
            raise ValueError("no retries")

        with pytest.raises(ValueError, match="no retries"):
            await fail_once()
        assert call_count == 1


from app.utils.decorators import log_call
import logging


# ─── @log_call tests ─────────────────────────────────────────────────────────


class TestLogCallSync:
    def test_entry_and_exit_logged(self, caplog):
        test_logger = logging.getLogger("test.log_call")

        @log_call(logger=test_logger, level="info")
        def greet(name):
            return f"hi {name}"

        with caplog.at_level(logging.INFO, logger="test.log_call"):
            result = greet("world")

        assert result == "hi world"
        assert any("Calling" in r.message and "greet" in r.message for r in caplog.records)
        assert any("Finished" in r.message and "greet" in r.message for r in caplog.records)

    def test_exit_log_contains_elapsed(self, caplog):
        test_logger = logging.getLogger("test.log_call.elapsed")

        @log_call(logger=test_logger, level="info")
        def noop():
            return 42

        with caplog.at_level(logging.INFO, logger="test.log_call.elapsed"):
            noop()

        finished = [r for r in caplog.records if "Finished" in r.message]
        assert len(finished) == 1
        assert "s" in finished[0].message  # contains elapsed time like "0.000s"

    def test_exception_logged_and_reraised(self, caplog):
        test_logger = logging.getLogger("test.log_call.exc")

        @log_call(logger=test_logger, level="info")
        def boom():
            raise RuntimeError("kaboom")

        with caplog.at_level(logging.INFO, logger="test.log_call.exc"):
            with pytest.raises(RuntimeError, match="kaboom"):
                boom()

        assert any("Failed" in r.message and "kaboom" in r.message for r in caplog.records)

    def test_default_logger_from_module(self, caplog):
        @log_call(level="info")
        def module_fn():
            return "ok"

        with caplog.at_level(logging.INFO):
            result = module_fn()

        assert result == "ok"
        assert any("Calling" in r.message for r in caplog.records)

    def test_custom_log_level(self, caplog):
        test_logger = logging.getLogger("test.log_call.debug")

        @log_call(logger=test_logger, level="debug")
        def debug_fn():
            return "dbg"

        with caplog.at_level(logging.DEBUG, logger="test.log_call.debug"):
            result = debug_fn()

        assert result == "dbg"
        assert any("Calling" in r.message for r in caplog.records)


class TestLogCallAsync:
    @pytest.mark.asyncio
    async def test_async_entry_and_exit_logged(self, caplog):
        test_logger = logging.getLogger("test.log_call.async")

        @log_call(logger=test_logger, level="info")
        async def greet(name):
            return f"hi {name}"

        with caplog.at_level(logging.INFO, logger="test.log_call.async"):
            result = await greet("world")

        assert result == "hi world"
        assert any("Calling" in r.message and "greet" in r.message for r in caplog.records)
        assert any("Finished" in r.message and "greet" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_async_exception_logged_and_reraised(self, caplog):
        test_logger = logging.getLogger("test.log_call.async.exc")

        @log_call(logger=test_logger, level="info")
        async def boom():
            raise RuntimeError("async kaboom")

        with caplog.at_level(logging.INFO, logger="test.log_call.async.exc"):
            with pytest.raises(RuntimeError, match="async kaboom"):
                await boom()

        assert any("Failed" in r.message for r in caplog.records)


from app.utils.decorators import timed


# ─── @timed tests ────────────────────────────────────────────────────────────


class TestTimedSync:
    def test_metrics_populated_on_success(self):
        m = {}

        @timed(metric_name="test.op", metrics=m)
        def fast():
            return 42

        assert fast() == 42
        assert "test.op" in m
        assert isinstance(m["test.op"], float)
        assert m["test.op"] >= 0

    def test_metrics_populated_on_exception(self):
        m = {}

        @timed(metric_name="test.fail", metrics=m)
        def boom():
            raise ValueError("oops")

        with pytest.raises(ValueError):
            boom()
        assert "test.fail" in m
        assert m["test.fail"] >= 0

    def test_default_metric_name(self):
        m = {}

        @timed(metrics=m)
        def my_func():
            return "ok"

        my_func()
        # Key should contain the qualname
        keys = list(m.keys())
        assert len(keys) == 1
        assert "my_func" in keys[0]

    def test_log_output_contains_timing(self, caplog):
        @timed(metric_name="test.logged")
        def noop():
            return 1

        with caplog.at_level(logging.INFO):
            noop()

        assert any("TIMER" in r.message and "test.logged" in r.message for r in caplog.records)


class TestTimedAsync:
    @pytest.mark.asyncio
    async def test_async_metrics_populated(self):
        m = {}

        @timed(metric_name="test.async_op", metrics=m)
        async def fast():
            return 99

        assert await fast() == 99
        assert "test.async_op" in m
        assert m["test.async_op"] >= 0

    @pytest.mark.asyncio
    async def test_async_metrics_on_exception(self):
        m = {}

        @timed(metric_name="test.async_fail", metrics=m)
        async def boom():
            raise RuntimeError("async oops")

        with pytest.raises(RuntimeError):
            await boom()
        assert "test.async_fail" in m
        assert m["test.async_fail"] >= 0


from app.utils.decorators import safe


# ─── @safe tests ─────────────────────────────────────────────────────────────


class TestSafeSync:
    def test_returns_result_on_success(self):
        @safe(fallback="default")
        def ok():
            return "real"

        assert ok() == "real"

    def test_returns_fallback_on_exception(self):
        @safe(fallback="default")
        def boom():
            raise ValueError("oops")

        assert boom() == "default"

    def test_logs_exception(self, caplog):
        test_logger = logging.getLogger("test.safe")

        @safe(fallback=None, logger=test_logger)
        def boom():
            raise RuntimeError("logged error")

        with caplog.at_level(logging.ERROR, logger="test.safe"):
            result = boom()

        assert result is None
        assert any("Error in" in r.message and "logged error" in r.message for r in caplog.records)

    def test_does_not_catch_keyboard_interrupt(self):
        @safe(fallback="default")
        def interrupt():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            interrupt()

    def test_default_logger(self):
        @safe(fallback="fb")
        def boom():
            raise ValueError("x")

        # Should not raise — just returns fallback
        assert boom() == "fb"


class TestSafeAsync:
    @pytest.mark.asyncio
    async def test_async_returns_result_on_success(self):
        @safe(fallback="default")
        async def ok():
            return "real"

        assert await ok() == "real"

    @pytest.mark.asyncio
    async def test_async_returns_fallback_on_exception(self):
        @safe(fallback=[])
        async def boom():
            raise ValueError("async oops")

        assert await boom() == []

    @pytest.mark.asyncio
    async def test_async_does_not_catch_keyboard_interrupt(self):
        @safe(fallback="default")
        async def interrupt():
            raise KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            await interrupt()


from app.utils.decorators import validate_session, _expired_response


# ─── @validate_session tests ─────────────────────────────────────────────────


class _TimeCheck:
    def __init__(self, expired):
        self.is_expired = expired


class _MockEnforcer:
    def __init__(self, expired):
        self._expired = expired

    def check_time(self, session_id):
        return _TimeCheck(self._expired)


class TestValidateSessionSync:
    def test_returns_expired_response_when_expired(self):
        class Svc:
            session_time_enforcer = _MockEnforcer(expired=True)

            @validate_session()
            def do_work(self, session_id):
                return "should not reach"

        result = Svc().do_work("sess-1")
        assert result["session_time_expired"] is True
        assert result["text"] == ""

    def test_delegates_when_valid(self):
        class Svc:
            session_time_enforcer = _MockEnforcer(expired=False)

            @validate_session()
            def do_work(self, session_id):
                return {"text": "story content"}

        result = Svc().do_work("sess-1")
        assert result == {"text": "story content"}

    def test_skips_check_when_enforcer_is_none(self):
        class Svc:
            session_time_enforcer = None

            @validate_session()
            def do_work(self, session_id):
                return "no enforcer"

        assert Svc().do_work("sess-1") == "no enforcer"

    def test_expired_response_structure(self):
        resp = _expired_response()
        assert resp["text"] == ""
        assert resp["image"] is None
        assert resp["audio"] == {"narration": None, "character_voices": []}
        assert resp["interactive"] == {}
        assert resp["timestamp"] is None
        assert resp["memories_used"] == 0
        assert resp["voice_recordings"] == []
        assert resp["agents_used"] == {
            "storyteller": False,
            "visual": False,
            "voice": False,
            "memory": False,
        }
        assert resp["session_time_expired"] is True


class TestValidateSessionAsync:
    @pytest.mark.asyncio
    async def test_async_returns_expired_response_when_expired(self):
        class Svc:
            session_time_enforcer = _MockEnforcer(expired=True)

            @validate_session()
            async def do_work(self, session_id):
                return "should not reach"

        result = await Svc().do_work("sess-1")
        assert result["session_time_expired"] is True

    @pytest.mark.asyncio
    async def test_async_delegates_when_valid(self):
        class Svc:
            session_time_enforcer = _MockEnforcer(expired=False)

            @validate_session()
            async def do_work(self, session_id):
                return {"text": "async story"}

        result = await Svc().do_work("sess-1")
        assert result == {"text": "async story"}

    @pytest.mark.asyncio
    async def test_async_skips_check_when_enforcer_is_none(self):
        class Svc:
            session_time_enforcer = None

            @validate_session()
            async def do_work(self, session_id):
                return "no enforcer async"

        assert await Svc().do_work("sess-1") == "no enforcer async"


# ─── Signature preservation tests ────────────────────────────────────────────


class TestSignaturePreservation:
    """All five decorators must preserve __name__, __doc__, __module__, __qualname__."""

    DECORATORS = [
        ("with_retry", with_retry(max_attempts=2, backoff=0)),
        ("log_call", log_call(level="info")),
        ("timed", timed()),
        ("safe", safe(fallback=None)),
        ("validate_session", validate_session()),
    ]

    @pytest.mark.parametrize("dec_name,dec", DECORATORS, ids=[d[0] for d in DECORATORS])
    def test_sync_preserves_metadata(self, dec_name, dec):
        def original_sync():
            """Original docstring."""
            pass

        decorated = dec(original_sync)
        assert decorated.__name__ == "original_sync"
        assert decorated.__doc__ == "Original docstring."
        assert decorated.__module__ == original_sync.__module__
        assert decorated.__qualname__ == original_sync.__qualname__

    @pytest.mark.parametrize("dec_name,dec", DECORATORS, ids=[d[0] for d in DECORATORS])
    def test_async_preserves_metadata(self, dec_name, dec):
        async def original_async():
            """Async original docstring."""
            pass

        decorated = dec(original_async)
        assert decorated.__name__ == "original_async"
        assert decorated.__doc__ == "Async original docstring."
        assert decorated.__module__ == original_async.__module__
        assert decorated.__qualname__ == original_async.__qualname__

    @pytest.mark.parametrize("dec_name,dec", DECORATORS, ids=[d[0] for d in DECORATORS])
    def test_sync_async_nature_preserved(self, dec_name, dec):
        def sync_fn():
            pass

        async def async_fn():
            pass

        assert not asyncio.iscoroutinefunction(dec(sync_fn))
        assert asyncio.iscoroutinefunction(dec(async_fn))


# ─── Decorator stacking / composability tests ────────────────────────────────


class TestDecoratorStacking:
    def test_sync_log_timed_retry_stacked(self, caplog):
        m = {}
        test_logger = logging.getLogger("test.stacking")
        call_count = 0

        @log_call(logger=test_logger, level="info")
        @timed(metric_name="stacked.op", metrics=m)
        @with_retry(max_attempts=3, backoff=0, exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("transient")
            return "success"

        with caplog.at_level(logging.INFO, logger="test.stacking"):
            result = flaky()

        assert result == "success"
        assert call_count == 2
        # timed recorded
        assert "stacked.op" in m
        assert m["stacked.op"] >= 0
        # log_call logged entry and exit
        assert any("Calling" in r.message for r in caplog.records)
        assert any("Finished" in r.message for r in caplog.records)

    @pytest.mark.asyncio
    async def test_async_log_timed_retry_stacked(self, caplog):
        m = {}
        test_logger = logging.getLogger("test.stacking.async")
        call_count = 0

        @log_call(logger=test_logger, level="info")
        @timed(metric_name="stacked.async_op", metrics=m)
        @with_retry(max_attempts=3, backoff=0, exceptions=(ConnectionError,))
        async def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("transient")
            return "async success"

        with caplog.at_level(logging.INFO, logger="test.stacking.async"):
            result = await flaky()

        assert result == "async success"
        assert call_count == 2
        assert "stacked.async_op" in m
        assert any("Calling" in r.message for r in caplog.records)
        assert any("Finished" in r.message for r in caplog.records)

    def test_stacked_preserves_return_value(self):
        """Composability: return value passes through all layers unchanged."""
        m = {}

        @log_call(level="debug")
        @timed(metrics=m)
        @safe(fallback="fallback")
        def compute():
            return {"answer": 42}

        result = compute()
        assert result == {"answer": 42}
