"""Tests for storyteller agent drawing context integration (Req 5.1, 5.2, 5.3)."""

import pytest
from unittest.mock import patch, MagicMock
from app.agents.storyteller_agent import StorytellerAgent


CHARACTERS = {
    "child1": {"name": "Ale", "gender": "male", "spirit_animal": "dragon", "toy_name": "Sparky"},
    "child2": {"name": "Sofi", "gender": "female", "spirit_animal": "unicorn", "toy_name": "Rainbow"},
}


@pytest.fixture
def agent():
    """Create a StorytellerAgent with mocked Gemini API."""
    with patch("app.agents.storyteller_agent.genai"):
        return StorytellerAgent()


class TestBuildPromptDrawingContext:
    """_build_prompt includes drawing context when present in story context."""

    def test_drawing_context_included_in_prompt(self, agent):
        """When drawing_context is in context, the prompt references the drawing."""
        context = {
            "characters": CHARACTERS,
            "drawing_context": {
                "prompt": "Draw the magic door!",
                "sibling_names": ["Ale", "Sofi"],
            },
        }
        prompt = agent._build_prompt(context, user_input="continue")

        assert "COLLABORATIVE DRAWING CONTEXT" in prompt
        assert "Draw the magic door!" in prompt
        assert "Ale and Sofi" in prompt

    def test_drawing_context_references_both_siblings_by_name(self, agent):
        """Post-drawing prompt mentions both sibling names (Req 5.3)."""
        context = {
            "characters": CHARACTERS,
            "drawing_context": {
                "prompt": "Draw your favorite animal!",
                "sibling_names": ["Ale", "Sofi"],
            },
        }
        prompt = agent._build_prompt(context, user_input=None)

        assert "Ale" in prompt
        assert "Sofi" in prompt
        # The drawing section specifically should mention both names together
        drawing_section_start = prompt.index("COLLABORATIVE DRAWING CONTEXT")
        drawing_section = prompt[drawing_section_start:]
        assert "Ale" in drawing_section
        assert "Sofi" in drawing_section

    def test_no_drawing_context_omits_section(self, agent):
        """When drawing_context is absent, no drawing section appears."""
        context = {"characters": CHARACTERS}
        prompt = agent._build_prompt(context, user_input="continue")

        assert "COLLABORATIVE DRAWING CONTEXT" not in prompt
        assert "collaborative drawing" not in prompt.lower()

    def test_drawing_context_with_empty_sibling_names_falls_back(self, agent):
        """When sibling_names is empty, falls back to character names."""
        context = {
            "characters": CHARACTERS,
            "drawing_context": {
                "prompt": "Draw a rainbow bridge!",
                "sibling_names": [],
            },
        }
        prompt = agent._build_prompt(context, user_input=None)

        assert "COLLABORATIVE DRAWING CONTEXT" in prompt
        assert "Draw a rainbow bridge!" in prompt
        # Falls back to character names from context
        assert "Ale and Sofi" in prompt

    def test_drawing_context_preserves_other_prompt_sections(self, agent):
        """Drawing context doesn't break other prompt sections."""
        context = {
            "characters": CHARACTERS,
            "drawing_context": {
                "prompt": "Draw the enchanted forest!",
                "sibling_names": ["Ale", "Sofi"],
            },
        }
        prompt = agent._build_prompt(context, user_input="we drew trees")

        # Character info still present
        assert "CHARACTER INFO" in prompt
        # User input still present
        assert "we drew trees" in prompt
        # Drawing context present
        assert "COLLABORATIVE DRAWING CONTEXT" in prompt
