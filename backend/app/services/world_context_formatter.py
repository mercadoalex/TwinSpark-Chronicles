"""Formats world state into prompt-injectable context strings.

Produces [WORLD CONTEXT] blocks for Gemini prompts, capping entries
to avoid prompt bloat.

Requirements: 3.2, 3.4, 4.5, 6.1-6.5
"""

import re
import logging

logger = logging.getLogger(__name__)

SESSION_START_CAP = 10  # max entries per category at session start
BEAT_CAP = 5            # max total entries per story beat


class WorldContextFormatter:
    """Formats world state into prompt-injectable context strings."""

    def format_session_start_context(self, world_state: dict) -> str:
        """Format full world context for session start prompt.

        Includes up to 10 locations, 10 NPCs, 10 items.
        Returns empty string if world_state is empty.
        """
        locations = world_state.get("locations", [])[:SESSION_START_CAP]
        npcs = world_state.get("npcs", [])[:SESSION_START_CAP]
        items = world_state.get("items", [])[:SESSION_START_CAP]

        if not locations and not npcs and not items:
            return ""

        lines = ["[WORLD CONTEXT]"]
        if locations:
            lines.append("Previously discovered locations:")
            for loc in locations:
                lines.append(f"- {loc['name']} ({loc.get('state', 'discovered')}): {loc['description']}")
        if npcs:
            lines.append("Known friends:")
            for npc in npcs:
                level = npc.get("relationship_level", 1)
                label = "acquaintance" if level <= 1 else "friend" if level <= 3 else "close friend"
                lines.append(f"- {npc['name']} (relationship: {label}): {npc['description']}")
        if items:
            lines.append("Collected items:")
            for item in items:
                lines.append(f"- {item['name']}: {item['description']}")
        lines.append("[END WORLD CONTEXT]")
        return "\n".join(lines)

    def format_beat_context(self, world_state: dict, current_scene: str) -> str:
        """Format relevant world context for a single story beat.

        Selects up to BEAT_CAP entries most relevant to current_scene
        using keyword matching against entity names and descriptions.
        Returns empty string if nothing is relevant or world is empty.
        """
        if not current_scene:
            return ""

        locations = world_state.get("locations", [])
        npcs = world_state.get("npcs", [])
        items = world_state.get("items", [])

        if not locations and not npcs and not items:
            return ""

        scene_lower = current_scene.lower()
        scored: list[tuple[float, str, dict]] = []

        for loc in locations:
            score = self._relevance_score(loc["name"], loc.get("description", ""), scene_lower)
            if score > 0:
                label = f"- {loc['name']} ({loc.get('state', 'discovered')}): {loc['description']}"
                scored.append((score, "location", {"line": label, "entity": loc}))

        for npc in npcs:
            score = self._relevance_score(npc["name"], npc.get("description", ""), scene_lower)
            if score > 0:
                level = npc.get("relationship_level", 1)
                rel = "acquaintance" if level <= 1 else "friend" if level <= 3 else "close friend"
                label = f"- {npc['name']} (relationship: {rel}): {npc['description']}"
                scored.append((score, "npc", {"line": label, "entity": npc}))

        for item in items:
            score = self._relevance_score(item["name"], item.get("description", ""), scene_lower)
            if score > 0:
                label = f"- {item['name']}: {item['description']}"
                scored.append((score, "item", {"line": label, "entity": item}))

        if not scored:
            return ""

        # Sort by relevance descending, take top BEAT_CAP
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:BEAT_CAP]

        loc_lines = [e["line"] for _, t, e in top if t == "location"]
        npc_lines = [e["line"] for _, t, e in top if t == "npc"]
        item_lines = [e["line"] for _, t, e in top if t == "item"]

        lines = ["[WORLD CONTEXT]"]
        if loc_lines:
            lines.append("Previously discovered locations:")
            lines.extend(loc_lines)
        if npc_lines:
            lines.append("Known friends:")
            lines.extend(npc_lines)
        if item_lines:
            lines.append("Collected items:")
            lines.extend(item_lines)
        lines.append("[END WORLD CONTEXT]")
        return "\n".join(lines)

    @staticmethod
    def _relevance_score(name: str, description: str, scene_lower: str) -> float:
        """Score how relevant an entity is to the current scene text."""
        score = 0.0
        name_lower = name.lower()
        # Exact name match in scene
        if name_lower in scene_lower:
            score += 2.0
        # Individual word matches from name
        for word in re.split(r"\s+", name_lower):
            if len(word) > 2 and word in scene_lower:
                score += 0.5
        # Description keyword overlap
        desc_words = set(re.split(r"\s+", description.lower()))
        scene_words = set(re.split(r"\s+", scene_lower))
        overlap = desc_words & scene_words - {"the", "a", "an", "is", "in", "of", "and", "to"}
        score += len(overlap) * 0.1
        return score
