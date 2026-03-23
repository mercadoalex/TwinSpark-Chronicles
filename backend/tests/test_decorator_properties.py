"""Property-based tests for Cross-Cutting Decorators.

Covers:
- 1.3 (Property 3): with_retry calls function K+1 times when it fails K < N times
- 3.3 (Property 5): timed always populates metrics with non-negative float
- 4.3 (Property 6): safe never raises Exception, returns result or fallback
- 6.3 (Property 1): all decorators preserve sync/async nature
- 6.4 (Property 2): all decorators preserve __name__ and __doc__
"""

import asyncio

import pytest
from hypothesis import given, settings, strategies as st

from app.utils.decorators import with_retry, log_call, timed, safe, validate_session


# ── helpers ───────────────────────────────────────────────────

_safe_text = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz",
    min_size=1,
    max_size=12,
)

# All decorator factories with default args (excluding validate_session which needs self)
_DECORATOR_FACTORIES = [
    lambda: with_retry(max_attempts=2, backoff=0),
    lambda: log_call(),
    lambda: timed(),
    lambda: safe(),
]


# ── 1.3  with_retry: K failures then success → K+1 calls ─────


@settings(max_examples=20)
@given(
    max_attempts=st.integers(min_value=1, max_value=6),
    data=st.data(),
)
def test_retry_calls_k_plus_1_times(max_attempts, data):
    """For K < N failures then success, function is called K+1 times."""
    k = data.draw(st.integers(min_value=0, max_value=max_attempts - 1))
    success_value = data.draw(st.integers(min_value=-1000, max_value=1000))

    call_count = 0

    @with_retry(max_attempts=max_attempts, backoff=0, exceptions=(ValueError,))
    def fn():
        nonlocal call_count
        call_count += 1
        if call_count <= k:
            raise ValueError("transient")
        return success_value

    result = fn()
    assert result == success_value
    assert call_count == k + 1


# ── 3.3  timed: metrics always has key with non-negative float ─


@settings(max_examples=20)
@given(should_fail=st.booleans())
def test_timed_always_populates_metrics(should_fail):
    """After execution (success or failure), metrics dict has the key with a non-negative float."""
    metrics = {}
    metric_name = "test.metric"

    @timed(metric_name=metric_name, metrics=metrics)
    def fn():
        if should_fail:
            raise RuntimeError("boom")
        return 42

    try:
        fn()
    except RuntimeError:
        pass

    assert metric_name in metrics
    assert isinstance(metrics[metric_name], float)
    assert metrics[metric_name] >= 0.0


# ── 4.3  safe: never raises Exception, returns result or fallback


@settings(max_examples=20)
@given(
    fallback=st.integers(min_value=-100, max_value=100),
    should_fail=st.booleans(),
    return_val=st.integers(min_value=-100, max_value=100),
)
def test_safe_never_raises_exception(fallback, should_fail, return_val):
    """@safe decorated function never raises Exception; returns result or fallback."""

    @safe(fallback=fallback)
    def fn():
        if should_fail:
            raise ValueError("error")
        return return_val

    # Must never raise
    result = fn()

    if should_fail:
        assert result == fallback
    else:
        assert result == return_val


# ── 6.3  All decorators preserve sync/async nature ───────────


@settings(max_examples=20)
@given(
    decorator_idx=st.integers(min_value=0, max_value=len(_DECORATOR_FACTORIES) - 1),
    is_async=st.booleans(),
)
def test_decorators_preserve_sync_async(decorator_idx, is_async):
    """For any decorator and function, asyncness is preserved."""
    decorator = _DECORATOR_FACTORIES[decorator_idx]()

    if is_async:
        async def original():
            """Async fn."""
            return 1
    else:
        def original():
            """Sync fn."""
            return 1

    decorated = decorator(original)
    assert asyncio.iscoroutinefunction(decorated) == asyncio.iscoroutinefunction(original)


# ── 6.4  All decorators preserve __name__ and __doc__ ─────────


@settings(max_examples=20)
@given(
    decorator_idx=st.integers(min_value=0, max_value=len(_DECORATOR_FACTORIES) - 1),
    is_async=st.booleans(),
    doc=_safe_text,
)
def test_decorators_preserve_name_and_doc(decorator_idx, is_async, doc):
    """For any decorator and function, __name__ and __doc__ are preserved."""
    decorator = _DECORATOR_FACTORIES[decorator_idx]()

    if is_async:
        async def my_func():
            pass
        my_func.__doc__ = doc
    else:
        def my_func():
            pass
        my_func.__doc__ = doc

    decorated = decorator(my_func)
    assert decorated.__name__ == "my_func"
    assert decorated.__doc__ == doc
