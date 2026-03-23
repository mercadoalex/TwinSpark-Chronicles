"""
Backend mirror of the frontend costume catalog.

Used for:
1. Validating costume IDs on the PUT /api/costume endpoint
2. Looking up prompt_fragment when the frontend only sends the costume ID
"""

COSTUME_CATALOG: dict[str, dict] = {
    "knight_armor": {
        "label": "Knight Armor",
        "emoji": "⚔️",
        "prompt_fragment": "wearing gleaming silver knight armor with a dragon crest shield",
    },
    "space_suit": {
        "label": "Space Suit",
        "emoji": "🚀",
        "prompt_fragment": "wearing a shiny white space suit with a glowing helmet visor",
    },
    "princess_gown": {
        "label": "Princess Gown",
        "emoji": "👑",
        "prompt_fragment": "wearing a sparkling pink princess gown with a golden tiara",
    },
    "pirate_outfit": {
        "label": "Pirate Outfit",
        "emoji": "🏴‍☠️",
        "prompt_fragment": "wearing a rugged pirate coat with a feathered tricorn hat",
    },
    "superhero_cape": {
        "label": "Superhero Cape",
        "emoji": "🦸",
        "prompt_fragment": "wearing a bold superhero suit with a flowing red cape",
    },
    "wizard_robe": {
        "label": "Wizard Robe",
        "emoji": "🧙",
        "prompt_fragment": "wearing a deep purple wizard robe covered in glowing star patterns",
    },
    "explorer_gear": {
        "label": "Explorer Gear",
        "emoji": "🧭",
        "prompt_fragment": "wearing rugged explorer gear with a leather satchel and compass",
    },
    "fairy_wings": {
        "label": "Fairy Wings",
        "emoji": "🧚",
        "prompt_fragment": "wearing a shimmering fairy outfit with translucent rainbow wings",
    },
}

_DEFAULT_PROMPT = "wearing adventure clothes"


def get_costume_prompt(costume_id: str | None) -> str:
    """Return the prompt fragment for a costume ID, or the default."""
    if costume_id and costume_id in COSTUME_CATALOG:
        return COSTUME_CATALOG[costume_id]["prompt_fragment"]
    return _DEFAULT_PROMPT


def is_valid_costume(costume_id: str) -> bool:
    """Return True if the costume ID exists in the catalog."""
    return costume_id in COSTUME_CATALOG
