"""Content filter service for scanning AI-generated text for age-appropriateness.

Scans story segments against a keyword/phrase blocklist and theme rules,
assigning a ContentRating (SAFE / REVIEW / BLOCKED) before content reaches
the frontend.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

AVAILABLE_THEMES = [
    "friendship",
    "nature",
    "space",
    "animals",
    "problem-solving",
    "creativity",
    "kindness",
    "teamwork",
]

# Minimal fallback blocklist used when the JSON file is missing or malformed.
_FALLBACK_KEYWORDS = [
    "violence",
    "blood",
    "kill",
    "death",
    "weapon",
    "gun",
    "knife",
    "drug",
    "alcohol",
    "hate",
]
_FALLBACK_PHRASES = [
    "run away from home",
    "no one loves you",
    "you are stupid",
]


class ContentRating(str, Enum):
    SAFE = "SAFE"
    REVIEW = "REVIEW"
    BLOCKED = "BLOCKED"


@dataclass
class FilterResult:
    rating: ContentRating
    reason: str
    matched_terms: list[str] = field(default_factory=list)


@dataclass
class ContentFilterLog:
    session_id: str
    timestamp: str
    rating: ContentRating
    reason: str
    text_snippet: str


class ContentFilter:
    """Scans text against a blocklist and theme rules, returning a ContentRating."""

    def __init__(self, blocklist_path: str = "app/config/blocklist.json"):
        self._blocklist_path = Path(blocklist_path)
        self._keywords: list[str] = []
        self._phrases: list[str] = []
        self._load_blocklist()

    # ------------------------------------------------------------------
    # Blocklist loading
    # ------------------------------------------------------------------

    def _load_blocklist(self) -> None:
        """Load blocklist from JSON; fall back to hardcoded minimal list."""
        try:
            raw = self._blocklist_path.read_text(encoding="utf-8")
            data = json.loads(raw)
            keywords = data.get("keywords", [])
            phrases = data.get("phrases", [])
            if not isinstance(keywords, list) or not isinstance(phrases, list):
                raise ValueError("keywords and phrases must be lists")
            self._keywords = [str(k).lower() for k in keywords]
            self._phrases = [str(p).lower() for p in phrases]
            logger.info(
                "Blocklist loaded: %d keywords, %d phrases",
                len(self._keywords),
                len(self._phrases),
            )
        except Exception as exc:
            logger.warning(
                "Failed to load blocklist from %s (%s); using fallback",
                self._blocklist_path,
                exc,
            )
            self._keywords = [k.lower() for k in _FALLBACK_KEYWORDS]
            self._phrases = [p.lower() for p in _FALLBACK_PHRASES]

    def reload_blocklist(self) -> None:
        """Hot-reload the blocklist from disk."""
        self._load_blocklist()

    # ------------------------------------------------------------------
    # Scanning
    # ------------------------------------------------------------------

    def scan(
        self,
        text: str,
        allowed_themes: list[str] | None = None,
        custom_blocked_words: list[str] | None = None,
        session_id: str = "",
    ) -> FilterResult:
        """Scan *text* and return a FilterResult.

        Order:
        1. Blocklist + custom words (case-insensitive) → BLOCKED
        2. Disallowed themes (if *allowed_themes* provided) → REVIEW
        3. Otherwise → SAFE
        """
        text_lower = text.lower()

        # --- Step 1: blocklist + custom words → BLOCKED ---
        matched: list[str] = []

        # Check phrases first (longer matches are more specific)
        for phrase in self._phrases:
            if phrase in text_lower:
                matched.append(phrase)

        # Check keywords using word-boundary matching
        for keyword in self._keywords:
            pattern = r"\b" + re.escape(keyword) + r"\b"
            if re.search(pattern, text_lower):
                matched.append(keyword)

        # Check custom blocked words
        if custom_blocked_words:
            for word in custom_blocked_words:
                word_lower = word.lower()
                pattern = r"\b" + re.escape(word_lower) + r"\b"
                if re.search(pattern, text_lower):
                    matched.append(word_lower)

        if matched:
            # Deduplicate while preserving order
            seen: set[str] = set()
            unique_matched: list[str] = []
            for m in matched:
                if m not in seen:
                    seen.add(m)
                    unique_matched.append(m)
            result = FilterResult(
                rating=ContentRating.BLOCKED,
                reason=f"Blocklist match: {', '.join(unique_matched)}",
                matched_terms=unique_matched,
            )
            self._log_scan(session_id, result, text)
            return result

        # --- Step 2: disallowed themes → REVIEW ---
        if allowed_themes is not None:
            disallowed = [t for t in AVAILABLE_THEMES if t not in allowed_themes]
            found_disallowed: list[str] = []
            for theme in disallowed:
                pattern = r"\b" + re.escape(theme.lower()) + r"\b"
                if re.search(pattern, text_lower):
                    found_disallowed.append(theme)
            if found_disallowed:
                result = FilterResult(
                    rating=ContentRating.REVIEW,
                    reason=f"Disallowed theme: {', '.join(found_disallowed)}",
                    matched_terms=found_disallowed,
                )
                self._log_scan(session_id, result, text)
                return result

        # --- Step 3: all clear → SAFE ---
        result = FilterResult(
            rating=ContentRating.SAFE,
            reason="Content passes all checks",
            matched_terms=[],
        )
        self._log_scan(session_id, result, text)
        return result

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_scan(self, session_id: str, result: FilterResult, text: str) -> None:
        """Log every scan result with session ID, rating, reason, and snippet."""
        snippet = text[:100] if text else ""
        log_entry = ContentFilterLog(
            session_id=session_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            rating=result.rating,
            reason=result.reason,
            text_snippet=snippet,
        )
        logger.info(
            "ContentFilter scan: session=%s rating=%s reason=%s snippet=%r",
            log_entry.session_id,
            log_entry.rating.value,
            log_entry.reason,
            log_entry.text_snippet,
        )
