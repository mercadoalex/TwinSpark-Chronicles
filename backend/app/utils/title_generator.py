def generate_story_title(narration: str | None) -> str:
    """Produce a ≤60-char title from the first beat's narration."""
    if not narration or not narration.strip():
        return "Untitled Adventure"

    text = narration.strip()

    if len(text) <= 60:
        return text

    # Truncate at nearest word boundary before position 60
    truncated = text[:60]
    # Find last space to avoid breaking mid-word
    last_space = truncated.rfind(" ")
    if last_space > 0:
        truncated = truncated[:last_space]

    return truncated + "\u2026"
