"""File-based response cache for e2e Gemini tests.

Stores API responses as JSON files keyed by SHA-256 of the prompt,
enabling replay without additional API calls.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_TTL_DAYS = 7


class ResponseCache:
    """Cache Gemini API responses to disk keyed by SHA-256(prompt)."""

    def __init__(self, cache_dir: Path, ttl_days: int = _DEFAULT_TTL_DAYS) -> None:
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_days * 86400
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _hash(prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()

    def get(self, prompt: str) -> Optional[dict]:
        """Return cached response dict or None on miss / corrupt file."""
        path = self.cache_dir / f"{self._hash(prompt)}.json"
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data.get("response")
        except Exception as exc:
            logger.warning("Cache read failed for %s: %s", path.name, exc)
            return None

    def put(self, prompt: str, response: dict) -> None:
        """Store response JSON keyed by SHA-256(prompt)."""
        path = self.cache_dir / f"{self._hash(prompt)}.json"
        payload = {
            "prompt_hash": self._hash(prompt),
            "timestamp": time.time(),
            "response": response,
        }
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def clear_stale(self) -> int:
        """Remove entries older than TTL. Returns count removed."""
        now = time.time()
        removed = 0
        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                age = now - data.get("timestamp", 0)
                if age > self.ttl_seconds:
                    path.unlink()
                    removed += 1
            except Exception:
                path.unlink(missing_ok=True)
                removed += 1
        return removed
