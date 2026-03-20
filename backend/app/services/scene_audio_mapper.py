"""Scene-to-audio theme mapper service.

Analyzes scene description text via keyword matching and returns
an AudioThemeResult with the matched theme, ambient track path,
and optional sound effect paths.
"""

from app.models.audio_theme import AudioThemeResult


class SceneAudioMapper:
    """Maps scene descriptions to audio themes using keyword matching."""

    THEME_KEYWORDS: dict[str, list[str]] = {
        "forest": ["forest", "tree", "wood", "jungle", "leaf", "branch", "grove"],
        "ocean": ["ocean", "sea", "wave", "beach", "water", "ship", "sail", "island"],
        "castle": ["castle", "throne", "knight", "tower", "dungeon", "king", "queen", "fortress"],
        "space": ["space", "star", "planet", "rocket", "galaxy", "moon", "asteroid", "cosmos"],
        "village": ["village", "town", "market", "house", "farm", "garden", "shop"],
        "cave": ["cave", "underground", "crystal", "tunnel", "mine", "dark", "echo"],
    }

    THEME_TRACKS: dict[str, str] = {
        theme: f"/audio/ambient/{theme}.mp3" for theme in THEME_KEYWORDS
    }

    THEME_SFX: dict[str, list[str]] = {
        "forest": [],
        "ocean": [],
        "castle": [],
        "space": [],
        "village": [],
        "cave": [],
    }

    DEFAULT_THEME: str = "village"

    def map_scene(self, scene_description: str) -> AudioThemeResult:
        """Map a scene description to an audio theme via keyword matching.

        Lowercases the description, counts keyword hits per theme,
        and returns the theme with the highest count. Ties are broken
        by dict insertion order (first theme wins). No match returns
        the default "village" theme.
        """
        description_lower = scene_description.lower()

        best_theme = self.DEFAULT_THEME
        best_count = 0

        for theme, keywords in self.THEME_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in description_lower)
            if count > best_count:
                best_count = count
                best_theme = theme

        return AudioThemeResult(
            theme=best_theme,
            ambient_track=self.THEME_TRACKS[best_theme],
            sound_effects=self.THEME_SFX[best_theme],
        )
