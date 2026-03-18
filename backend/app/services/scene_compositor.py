"""Scene Compositor — composites style-transferred portraits into scene images.

Uses Pillow to overlay illustrated character portraits onto AI-generated base
scene images at specified positions. Applies scaling, color grading, and shadow
blending so composited characters appear naturally integrated.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import logging
from io import BytesIO

from PIL import Image, ImageFilter

from app.models.photo import CharacterPosition

logger = logging.getLogger(__name__)


class SceneCompositor:
    """Composites style-transferred portraits into generated scene images."""

    def composite(
        self,
        base_scene_bytes: bytes,
        portraits: dict[str, bytes],
        character_positions: dict[str, CharacterPosition],
    ) -> bytes:
        """Overlay portraits onto the base scene at specified positions.

        Applies scaling, color grading, and shadow blending.
        Returns final composited PNG bytes.

        If compositing fails entirely, returns the base scene unchanged.
        Missing portraits for a position are skipped with a warning.
        """
        try:
            scene = Image.open(BytesIO(base_scene_bytes)).convert("RGBA")
        except Exception:
            logger.exception("Failed to open base scene image")
            return base_scene_bytes

        scene_width, scene_height = scene.size

        # Compute average scene colour for colour grading
        scene_avg = self._average_color(scene)

        # Sort positions by z_order so lower layers are composited first
        sorted_roles = sorted(
            character_positions.items(),
            key=lambda item: item[1].z_order,
        )

        for role, position in sorted_roles:
            if role not in portraits:
                logger.warning(
                    "No portrait for character role '%s'; skipping", role
                )
                continue

            try:
                portrait = Image.open(BytesIO(portraits[role])).convert("RGBA")
            except Exception:
                logger.warning(
                    "Failed to open portrait for role '%s'; skipping", role
                )
                continue

            try:
                # Scale portrait relative to scene height
                target_height = int(scene_height * position.scale * 0.3)
                if target_height < 1:
                    target_height = 1
                aspect = portrait.width / max(portrait.height, 1)
                target_width = max(1, int(target_height * aspect))
                portrait = portrait.resize(
                    (target_width, target_height), Image.LANCZOS
                )

                # Apply colour grading to match scene tone
                portrait = self._apply_color_grading(portrait, scene_avg)

                # Compute paste position (normalized coords → pixel coords)
                paste_x = int(position.x * scene_width - target_width / 2)
                paste_y = int(position.y * scene_height - target_height / 2)

                # Create and composite drop shadow
                shadow = self._create_shadow(portrait)
                shadow_offset = max(2, target_height // 30)
                scene.paste(
                    shadow,
                    (paste_x + shadow_offset, paste_y + shadow_offset),
                    shadow,
                )

                # Composite portrait onto scene
                scene.paste(portrait, (paste_x, paste_y), portrait)

            except Exception:
                logger.exception(
                    "Failed to composite portrait for role '%s'; skipping", role
                )
                continue

        # Convert to RGB and return PNG bytes
        try:
            output = scene.convert("RGB")
            buf = BytesIO()
            output.save(buf, format="PNG")
            return buf.getvalue()
        except Exception:
            logger.exception("Failed to encode final composited image")
            return base_scene_bytes

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _average_color(image: Image.Image) -> tuple[int, int, int]:
        """Compute the average RGB colour of an image."""
        small = image.resize((1, 1), Image.LANCZOS).convert("RGB")
        return small.getpixel((0, 0))

    @staticmethod
    def _apply_color_grading(
        portrait: Image.Image,
        scene_avg: tuple[int, int, int],
        strength: float = 0.15,
    ) -> Image.Image:
        """Shift portrait colours toward the scene's average tone.

        Blends each pixel's RGB channels toward *scene_avg* by *strength*
        (0 = no change, 1 = fully scene colour). Alpha is preserved.
        """
        r_avg, g_avg, b_avg = scene_avg
        pixels = portrait.load()
        width, height = portrait.size

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                r = int(r + (r_avg - r) * strength)
                g = int(g + (g_avg - g) * strength)
                b = int(b + (b_avg - b) * strength)
                pixels[x, y] = (
                    max(0, min(255, r)),
                    max(0, min(255, g)),
                    max(0, min(255, b)),
                    a,
                )
        return portrait

    @staticmethod
    def _create_shadow(
        portrait: Image.Image,
        opacity: int = 80,
        blur_radius: int = 6,
    ) -> Image.Image:
        """Create a soft drop-shadow image from the portrait's alpha channel."""
        shadow = Image.new("RGBA", portrait.size, (0, 0, 0, 0))
        alpha = portrait.split()[3]  # extract alpha channel
        shadow.putalpha(alpha)

        # Darken to shadow colour
        shadow_pixels = shadow.load()
        w, h = shadow.size
        for y in range(h):
            for x in range(w):
                _, _, _, a = shadow_pixels[x, y]
                shadow_pixels[x, y] = (0, 0, 0, min(a, opacity))

        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return shadow
