"""Toy photo service for the Toy Companion Visual feature.

Handles validation, resizing, storage, and retrieval of toy companion
photos. Reuses the same JPEG/PNG magic-byte + 10 MB validation logic
as PhotoService.

Requirements: 2.5, 2.6, 2.7, 3.1, 3.2, 3.3, 3.4, 3.5, 3.6
"""

from __future__ import annotations

import io
import json
import logging
import os
from datetime import datetime, timezone

from PIL import Image

from app.models.toy_photo import ToyPhotoMetadata, ToyPhotoResult
from app.services.photo_service import (
    ALLOWED_EXTENSIONS,
    JPEG_MAGIC,
    MAX_FILE_SIZE,
    PNG_MAGIC,
    ValidationError,
)

logger = logging.getLogger(__name__)


class ToyPhotoService:
    """Manages toy companion photo lifecycle: validate, resize, store, retrieve, delete."""

    def __init__(self, storage_root: str = "assets/toy_photos") -> None:
        self._storage_root = storage_root
        os.makedirs(self._storage_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Validation & resize
    # ------------------------------------------------------------------

    def validate_image(self, image_bytes: bytes, filename: str) -> None:
        """Check format (JPEG/PNG) and size (≤10 MB). Raises ValidationError."""
        if len(image_bytes) > MAX_FILE_SIZE:
            raise ValidationError("Photo must be under 10 MB")

        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValidationError("Please upload a JPEG or PNG photo")

        if ext in (".jpg", ".jpeg"):
            if not image_bytes[:3] == JPEG_MAGIC:
                raise ValidationError("Please upload a JPEG or PNG photo")
        elif ext == ".png":
            if not image_bytes[:8] == PNG_MAGIC:
                raise ValidationError("Please upload a JPEG or PNG photo")

    def resize_image(self, image_bytes: bytes, max_dimension: int = 512) -> bytes:
        """Resize preserving aspect ratio so longest side ≤ max_dimension. Returns JPEG bytes."""
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        w, h = img.size

        if max(w, h) > max_dimension:
            if w >= h:
                new_w = max_dimension
                new_h = max(1, round(h * max_dimension / w))
            else:
                new_h = max_dimension
                new_w = max(1, round(w * max_dimension / h))
            img = img.resize((new_w, new_h), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return buf.getvalue()

    # ------------------------------------------------------------------
    # Storage helpers
    # ------------------------------------------------------------------

    def _child_dir(self, sibling_pair_id: str) -> str:
        return os.path.join(self._storage_root, sibling_pair_id)

    def _image_path(self, sibling_pair_id: str, child_number: int) -> str:
        return os.path.join(self._child_dir(sibling_pair_id), f"child{child_number}.jpg")

    def _sidecar_path(self, sibling_pair_id: str, child_number: int) -> str:
        return os.path.join(self._child_dir(sibling_pair_id), f"child{child_number}.json")

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    async def upload_toy_photo(
        self, sibling_pair_id: str, child_number: int, image_bytes: bytes, filename: str
    ) -> ToyPhotoResult:
        """Validate → resize → store image + JSON sidecar. Returns metadata."""
        self.validate_image(image_bytes, filename)
        resized = self.resize_image(image_bytes)

        # Delete previous if exists
        await self.delete_toy_photo(sibling_pair_id, child_number)

        pair_dir = self._child_dir(sibling_pair_id)
        os.makedirs(pair_dir, exist_ok=True)

        img_path = self._image_path(sibling_pair_id, child_number)
        with open(img_path, "wb") as f:
            f.write(resized)

        now = datetime.now(timezone.utc).isoformat()
        image_url = f"/{img_path}"

        sidecar = {
            "child_number": child_number,
            "file_path": img_path,
            "original_filename": filename,
            "uploaded_at": now,
        }
        with open(self._sidecar_path(sibling_pair_id, child_number), "w") as f:
            json.dump(sidecar, f)

        return ToyPhotoResult(
            child_number=child_number,
            image_url=image_url,
            uploaded_at=now,
        )

    async def get_toy_photo(
        self, sibling_pair_id: str, child_number: int
    ) -> ToyPhotoMetadata | None:
        """Read JSON sidecar and return metadata, or None if not found."""
        sidecar_path = self._sidecar_path(sibling_pair_id, child_number)
        if not os.path.exists(sidecar_path):
            return None

        with open(sidecar_path, "r") as f:
            data = json.load(f)

        return ToyPhotoMetadata(
            child_number=data["child_number"],
            image_url=f"/{data['file_path']}",
            original_filename=data["original_filename"],
            uploaded_at=data["uploaded_at"],
            file_path=data["file_path"],
        )

    async def delete_toy_photo(
        self, sibling_pair_id: str, child_number: int
    ) -> bool:
        """Delete image + sidecar. Returns True if deleted."""
        img = self._image_path(sibling_pair_id, child_number)
        sidecar = self._sidecar_path(sibling_pair_id, child_number)
        deleted = False

        for path in (img, sidecar):
            try:
                if os.path.exists(path):
                    os.remove(path)
                    deleted = True
            except OSError as exc:
                logger.warning("Failed to delete %s: %s", path, exc)

        return deleted
