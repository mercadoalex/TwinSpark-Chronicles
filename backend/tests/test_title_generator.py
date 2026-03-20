from app.utils.title_generator import generate_story_title


class TestGenerateStoryTitle:
    """Unit tests for generate_story_title()."""

    def test_none_returns_fallback(self):
        assert generate_story_title(None) == "Untitled Adventure"

    def test_empty_string_returns_fallback(self):
        assert generate_story_title("") == "Untitled Adventure"

    def test_whitespace_only_returns_fallback(self):
        assert generate_story_title("   ") == "Untitled Adventure"

    def test_short_narration_unchanged(self):
        text = "The dragon flew over the hill"
        assert generate_story_title(text) == text

    def test_exactly_60_chars_unchanged(self):
        text = "A" * 60
        assert generate_story_title(text) == text
        assert len(generate_story_title(text)) == 60

    def test_long_narration_truncated_with_ellipsis(self):
        text = "The brave siblings ventured deep into the enchanted forest where magical creatures awaited them"
        result = generate_story_title(text)
        assert len(result) <= 60
        assert result.endswith("\u2026")

    def test_truncation_at_word_boundary(self):
        text = "The brave siblings ventured deep into the enchanted forest where magical creatures awaited them"
        result = generate_story_title(text)
        # Should not break mid-word: the part before … should end with a complete word
        before_ellipsis = result[:-1]
        assert not before_ellipsis.endswith(" "), "Should not have trailing space before ellipsis"
        # Verify the truncated text is a prefix of the original at a word boundary
        assert text.startswith(before_ellipsis)
