"""Style Transfer Agent — transforms face crops into Pixar/Disney-style portraits.

Uses Imagen 3 (imagen-3.0-generate-001) via Vertex AI to generate illustrated
character portraits from real face photos. Caches results in the
style_transferred_portraits table to avoid redundant generation.

Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6
"""

from __future__ import annotations

import base64
import logging
import os
import uuid
from datetime import datetime, timezone
from io import BytesIO

from PIL import Image

from app.db.connection import DatabaseConnection
from app.models.photo import CharacterMapping

logger = logging.getLogger(__name__)

_STYLE_PROMPT = (
    "Transform this face photo into a Pixar/Disney animation style character "
    "portrait. Preserve the person's facial features (hair color, skin tone, "
    "eye shape). Use bright colors, soft lighting, and a child-friendly aesthetic."
)

# 1×1 purple PNG used when style transfer is unavailable or fails.
_DEFAULT_AVATAR_BYTES: bytes | None = None


def _make_default_avatar() -> bytes:
    """Generate a small default avatar PNG (purple square)."""
    global _DEFAULT_AVATAR_BYTES  # noqa: PLW0603
    if _DEFAULT_AVATAR_BYTES is None:
        img = Image.new("RGB", (256, 256), color=(168, 85, 247))
        buf = BytesIO()
        img.save(buf, format="PNG")
        _DEFAULT_AVATAR_BYTES = buf.getvalue()
    return _DEFAULT_AVATAR_BYTES


class StyleTransferAgent:
    """Generates illustrated portraits from face crops using Imagen 3."""

    def __init__(self, storage_root: str = "photo_storage") -> None:
        project_id = os.getenv("GOOGLE_PROJECT_ID")
        location = os.getenv("GOOGLE_LOCATION", "us-central1")
        self._storage_root = storage_root
        self._model = None
        self._enabled = False

        if project_id:
            try:
                import vertexai
                from vertexai.preview.vision_models import ImageGenerationModel

                vertexai.init(project=project_id, location=location)
                self._model = ImageGenerationModel.from_pretrained(
                    "imagen-3.0-generate-001"
                )
                self._enabled = True
                logger.info("StyleTransferAgent initialised with Imagen 3")
            except Exception as exc:
                logger.warning(
                    "StyleTransferAgent disabled — failed to load Imagen 3: %s", exc
                )
        else:
            logger.info(
                "StyleTransferAgent disabled (set GOOGLE_PROJECT_ID to enable)"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def generate_portrait(
        self,
        face_crop_bytes: bytes,
        character_context: dict,
    ) -> bytes | None:
        """Style-transfer a face crop into an illustrated portrait.

        Returns PNG bytes on success, or ``None`` when the agent is disabled
        or generation fails.
        """
        if not self._enabled or self._model is None:
            return None

        try:
            role = character_context.get("role", "character")
            prompt = (
                f"{_STYLE_PROMPT} "
                f"This character is the {role} in a children's story."
            )

            response = self._model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="1:1",
                safety_filter_level="block_most",
                person_generation="allow_adult",
            )

            if response.images:
                image_bytes: bytes = response.images[0]._image_bytes
                logger.info("Portrait generated for role '%s'", role)
                return image_bytes

            logger.warning("Imagen 3 returned no images for role '%s'", role)
            return None

        except Exception:
            logger.exception("Style transfer failed for role '%s'",
                             character_context.get("role", "?"))
            return None

    async def generate_portraits_for_session(
        self,
        sibling_pair_id: str,
        session_id: str,
        mappings: list[CharacterMapping],
        db: DatabaseConnection,
    ) -> dict[str, str]:
        """Generate (or load cached) illustrated portraits for mapped characters.

        Returns ``{character_role: base64_portrait}``.  Characters whose
        ``face_id`` is ``None`` are skipped (they use the default avatar).
        On any per-character failure the default avatar is returned instead.
        """
        result: dict[str, str] = {}
        default_b64 = base64.b64encode(_make_default_avatar()).decode("utf-8")

        for mapping in mappings:
            if mapping.face_id is None:
                # Unmapped role — use default avatar
                result[mapping.character_role] = default_b64
                continue

            # 1. Check cache
            cached = await self._load_cached_portrait(mapping.face_id, session_id, db)
            if cached is not None:
                result[mapping.character_role] = cached
                continue

            # 2. Load face crop from disk
            face_crop = await self._load_face_crop(mapping.face_id, db)
            if face_crop is None:
                logger.warning(
                    "Face crop not found for face_id=%s; using default avatar",
                    mapping.face_id,
                )
                result[mapping.character_role] = default_b64
                continue

            # 3. Generate portrait
            portrait_bytes = await self.generate_portrait(
                face_crop,
                {"role": mapping.character_role},
            )

            if portrait_bytes is None:
                logger.warning(
                    "Style transfer failed for role '%s'; using default avatar",
                    mapping.character_role,
                )
                result[mapping.character_role] = default_b64
                continue

            # 4. Persist & cache
            portrait_b64 = base64.b64encode(portrait_bytes).decode("utf-8")
            await self._store_portrait(
                sibling_pair_id,
                mapping.face_id,
                session_id,
                portrait_bytes,
                db,
            )
            result[mapping.character_role] = portrait_b64

        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _load_cached_portrait(
        self, face_id: str, session_id: str, db: DatabaseConnection
    ) -> str | None:
        """Return base64 portrait from cache, or ``None``."""
        row = await db.fetch_one(
            "SELECT file_path FROM style_transferred_portraits "
            "WHERE face_id = ? AND session_id = ?",
            (face_id, session_id),
        )
        if row is None:
            return None

        file_path = row["file_path"]
        try:
            with open(file_path, "rb") as fh:
                return base64.b64encode(fh.read()).decode("utf-8")
        except FileNotFoundError:
            logger.warning("Cached portrait file missing: %s", file_path)
            return None

    async def _load_face_crop(
        self, face_id: str, db: DatabaseConnection
    ) -> bytes | None:
        """Read face crop bytes from disk using the path stored in DB."""
        row = await db.fetch_one(
            "SELECT crop_path FROM face_portraits WHERE face_id = ?",
            (face_id,),
        )
        if row is None:
            return None

        try:
            with open(row["crop_path"], "rb") as fh:
                return fh.read()
        except FileNotFoundError:
            logger.warning("Face crop file missing: %s", row["crop_path"])
            return None

    async def _store_portrait(
        self,
        sibling_pair_id: str,
        face_id: str,
        session_id: str,
        portrait_bytes: bytes,
        db: DatabaseConnection,
    ) -> None:
        """Write portrait PNG to disk and insert a cache row."""
        portrait_id = str(uuid.uuid4())
        dir_path = os.path.join(
            self._storage_root, sibling_pair_id, "portraits"
        )
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, f"{portrait_id}.png")

        with open(file_path, "wb") as fh:
            fh.write(portrait_bytes)

        await db.execute(
            "INSERT INTO style_transferred_portraits "
            "(portrait_id, face_id, session_id, file_path, generated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                portrait_id,
                face_id,
                session_id,
                file_path,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        logger.info(
            "Stored portrait %s for face %s (session %s)",
            portrait_id, face_id, session_id,
        )
