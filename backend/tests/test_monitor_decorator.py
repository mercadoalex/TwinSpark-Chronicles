"""Unit tests for @monitor decorator."""

import asyncio
import pytest
from app.monitoring.metrics_collector import MetricsCollector
from app.utils.decorators import monitor


@pytest.fixture
def mc():
    return MetricsCollector()


def test_calls_counter_incremented_sync(mc):
    @monitor(metrics_collector=mc)
    def add(a, b):
        return a + b

    add(1, 2)
    add(3, 4)
    name = f"{add.__module__}.{add.__qualname__}"
    assert mc._counters[f"{name}.calls"] == 2


def test_calls_counter_incremented_async(mc):
    @monitor(metrics_collector=mc)
    async def fetch():
        return 42

    asyncio.get_event_loop().run_until_complete(fetch())
    name = f"{fetch.__module__}.{fetch.__qualname__}"
    assert mc._counters[f"{name}.calls"] == 1


def test_errors_counter_on_exception_sync(mc):
    @monitor(metrics_collector=mc)
    def fail():
        raise ValueError("boom")

    with pytest.raises(ValueError):
        fail()
    name = f"{fail.__module__}.{fail.__qualname__}"
    assert mc._counters[f"{name}.errors"] == 1


def test_errors_counter_on_exception_async(mc):
    @monitor(metrics_collector=mc)
    async def fail():
        raise TypeError("async boom")

    with pytest.raises(TypeError):
        asyncio.get_event_loop().run_until_complete(fail())
    name = f"{fail.__module__}.{fail.__qualname__}"
    assert mc._counters[f"{name}.errors"] == 1


def test_duration_ms_recorded_sync(mc):
    @monitor(metrics_collector=mc)
    def slow():
        return "done"

    slow()
    name = f"{slow.__module__}.{slow.__qualname__}"
    h = mc._histograms[f"{name}.duration_ms"]
    assert h.count == 1
    assert h.min_val >= 0


def test_duration_ms_recorded_async(mc):
    @monitor(metrics_collector=mc)
    async def slow():
        return "done"

    asyncio.get_event_loop().run_until_complete(slow())
    name = f"{slow.__module__}.{slow.__qualname__}"
    h = mc._histograms[f"{name}.duration_ms"]
    assert h.count == 1


def test_exception_re_raised_unchanged(mc):
    @monitor(metrics_collector=mc)
    def fail():
        raise RuntimeError("exact message")

    with pytest.raises(RuntimeError, match="exact message"):
        fail()


def test_return_value_preserved_sync(mc):
    @monitor(metrics_collector=mc)
    def compute():
        return 42

    assert compute() == 42


def test_return_value_preserved_async(mc):
    @monitor(metrics_collector=mc)
    async def compute():
        return 99

    result = asyncio.get_event_loop().run_until_complete(compute())
    assert result == 99


def test_preserves_name_and_doc(mc):
    @monitor(metrics_collector=mc)
    def my_function():
        """My docstring."""
        pass

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "My docstring."


def test_preserves_async_nature(mc):
    @monitor(metrics_collector=mc)
    async def async_fn():
        pass

    @monitor(metrics_collector=mc)
    def sync_fn():
        pass

    assert asyncio.iscoroutinefunction(async_fn)
    assert not asyncio.iscoroutinefunction(sync_fn)
