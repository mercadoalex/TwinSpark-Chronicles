"""Budget guard for e2e Gemini tests.

Tracks cumulative API calls per pytest session and raises
BudgetExceededError when the configurable limit is hit.
"""


class BudgetExceededError(Exception):
    """Raised when the e2e API call budget is exhausted."""


class BudgetGuard:
    """Simple call counter that hard-caps live API calls."""

    def __init__(self, max_calls: int = 20) -> None:
        self._max_calls = max_calls
        self._calls_made = 0

    def record_call(self) -> None:
        """Increment counter; raise BudgetExceededError if over limit."""
        self._calls_made += 1
        if self._calls_made > self._max_calls:
            raise BudgetExceededError(
                f"Budget exceeded: {self._calls_made}/{self._max_calls} calls"
            )

    @property
    def calls_made(self) -> int:
        return self._calls_made

    @property
    def calls_remaining(self) -> int:
        return max(0, self._max_calls - self._calls_made)
