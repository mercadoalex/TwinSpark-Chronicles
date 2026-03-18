"""Scene Compositor — composites style-transferred portraits into scene images.

Uses Pillow to overlay illustrated character portraits onto AI-generated base
scene images at specified positions. Applies scaling, color grading, and shadow
blending so composited characters appear naturally integrated.

Requirements: 6.1, 6.2, 6.3, 6.4, 6.5
"""

from __future__ import annotations

import logging
from io import BytesIO

try:
    import numpy as np

    _HAS_NUMPY = True
except ImportError:  # pragma: no cover
    _HAS_NUMPY = False

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

        # Pre-scale all portraits in one batch before the compositing loop
        scaled_portraits = self._batch_scale_portraits(
            portraits, character_positions, scene_height
        )

        # Sort positions by z_order so lower layers are composited first
        sorted_roles = sorted(
            character_positions.items(),
            key=lambda item: item[1].z_order,
        )

        for role, position in sorted_roles:
            if role not in scaled_portraits:
                if role not in portraits:
                    logger.warning(
                        "No portrait for character role '%s'; skipping", role
                    )
                continue

            try:
                portrait = scaled_portraits[role]
                target_width, target_height = portrait.size

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

        Uses NumPy vectorized operations when available, falling back to
        per-pixel iteration otherwise.
        """
        if _HAS_NUMPY:
            arr = np.array(portrait, dtype=np.float32)
            mask = arr[:, :, 3] > 0
            for c in range(3):
                channel = arr[:, :, c]
                channel[mask] = channel[mask] + (scene_avg[c] - channel[mask]) * strength
            arr = np.clip(arr, 0, 255).astype(np.uint8)
            return Image.fromarray(arr, "RGBA")

        # Fallback: per-pixel loop when NumPy is not available
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
        """Create a soft drop-shadow image from the portrait's alpha channel.

        Uses NumPy vectorized operations when available, falling back to
        per-pixel iteration otherwise.
        """
        if _HAS_NUMPY:
            alpha_arr = np.array(portrait.split()[3], dtype=np.uint8)
            shadow_alpha = np.minimum(alpha_arr, opacity)
            h, w = shadow_alpha.shape
            shadow_arr = np.zeros((h, w, 4), dtype=np.uint8)
            shadow_arr[:, :, 3] = shadow_alpha
            shadow = Image.fromarray(shadow_arr, "RGBA")
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            return shadow

        # Fallback: per-pixel loop when NumPy is not available
        shadow = Image.new("RGBA", portrait.size, (0, 0, 0, 0))
        alpha = portrait.split()[3]
        shadow.putalpha(alpha)

        shadow_pixels = shadow.load()
        w, h = shadow.size
        for y in range(h):
            for x in range(w):
                _, _, _, a = shadow_pixels[x, y]
                shadow_pixels[x, y] = (0, 0, 0, min(a, opacity))

        shadow = shadow.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return shadow

    @staticmethod
    def _batch_scale_portraits(
        portraits: dict[str, bytes],
        character_positions: dict[str, CharacterPosition],
        scene_height: int,
    ) -> dict[str, Image.Image]:
        """Pre-scale all portraits in one pass before the compositing loop.

        Returns dict of {role: scaled_portrait_image}.
        Roles present in *character_positions* but missing from *portraits*
        are silently skipped.  Portraits that fail to open are logged and
        skipped.
        """
        scaled: dict[str, Image.Image] = {}
        for role, position in character_positions.items():
            if role not in portraits:
                continue
            try:
                portrait = Image.open(BytesIO(portraits[role])).convert("RGBA")
            except Exception:
                logger.warning(
                    "Failed to open portrait for role '%s'; skipping", role
                )
                continue

            target_height = int(scene_height * position.scale * 0.3)
            if target_height < 1:
                target_height = 1
            aspect = portrait.width / max(portrait.height, 1)
            target_width = max(1, int(target_height * aspect))
            scaled[role] = portrait.resize(
                (target_width, target_height), Image.LANCZOS
            )
        return scaled
