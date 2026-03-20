"""Unit tests for SceneAudioMapper service.

Tests keyword matching, default theme fallback, case insensitivity,
multi-keyword tie-breaking, and ambient_track consistency.
"""

import pytest

from app.services.scene_audio_mapper import SceneAudioMapper


@pytest.fixture
def mapper():
    return SceneAudioMapper()


# --- Test each of the 6 themes with representative descriptions ---

class TestThemeMatching:
    def test_forest_theme(self, mapper):
        result = mapper.map_scene("The twins walked through a dense forest with tall trees")
        assert result.theme == "forest"

    def test_ocean_theme(self, mapper):
        result = mapper.map_scene("Waves crashed on the beach as the ship sailed the sea")
        assert result.theme == "ocean"

    def test_castle_theme(self, mapper):
        result = mapper.map_scene("The knight entered the castle and approached the throne")
        assert result.theme == "castle"

    def test_space_theme(self, mapper):
        result = mapper.map_scene("A rocket launched toward a distant planet among the stars")
        assert result.theme == "space"

    def test_village_theme(self, mapper):
        result = mapper.map_scene("They visited the village market and a small shop")
        assert result.theme == "village"

    def test_cave_theme(self, mapper):
        result = mapper.map_scene("Deep underground in a crystal cave the echo was loud")
        assert result.theme == "cave"


# --- Default fallback ---

class TestDefaultFallback:
    def test_no_match_returns_village(self, mapper):
        result = mapper.map_scene("Something completely unrelated to any theme")
        assert result.theme == "village"

    def test_gibberish_returns_village(self, mapper):
        result = mapper.map_scene("xyzzy plugh abracadabra")
        assert result.theme == "village"


# --- Tie-breaking (dict order wins) ---

class TestTieBreaking:
    def test_tie_broken_by_dict_order(self, mapper):
        """When two themes have equal keyword counts, the first in dict order wins."""
        # "forest" has 1 hit, "ocean" has 1 hit → forest comes first in dict
        result = mapper.map_scene("forest ocean")
        assert result.theme == "forest"


# --- Case insensitivity ---

class TestCaseInsensitivity:
    def test_uppercase_keywords_match(self, mapper):
        result = mapper.map_scene("FOREST TREE WOOD")
        assert result.theme == "forest"

    def test_mixed_case_keywords_match(self, mapper):
        result = mapper.map_scene("The Castle had a Knight and a Queen")
        assert result.theme == "castle"


# --- Multi-keyword: highest count wins ---

class TestMultiKeywordHighestCount:
    def test_highest_keyword_count_wins(self, mapper):
        """Description with keywords from multiple themes returns the one with most hits."""
        # ocean: sea, wave, beach = 3 hits; forest: tree = 1 hit
        result = mapper.map_scene("The tree stood near the sea with a wave on the beach")
        assert result.theme == "ocean"


# --- ambient_track matches THEME_TRACKS ---

class TestAmbientTrackConsistency:
    def test_ambient_track_matches_theme_tracks(self, mapper):
        for theme in SceneAudioMapper.THEME_KEYWORDS:
            # Use a single keyword to force that theme
            keyword = SceneAudioMapper.THEME_KEYWORDS[theme][0]
            result = mapper.map_scene(keyword)
            assert result.ambient_track == SceneAudioMapper.THEME_TRACKS[result.theme]

    def test_default_theme_ambient_track(self, mapper):
        result = mapper.map_scene("xyzzy")
        assert result.ambient_track == "/audio/ambient/village.mp3"
