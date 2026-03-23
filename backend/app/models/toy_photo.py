"""Pydantic data models for the Toy Companion Visual feature.

Defines structured models for toy photo upload results and metadata
used by the ToyPhotoService for storing and retrieving toy companion
photos: upload → validate → resize → store → retrieve.
"""

from pydantic import BaseModel


class ToyPhotoResult(BaseModel):
    """Response returned after a toy photo is uploaded and processed."""

    child_number: int
    image_url: str
    uploaded_at: str


class ToyPhotoMetadata(BaseModel):
    """Persisted toy photo metadata read from the JSON sidecar file."""

    child_number: int
    image_url: str
    original_filename: str
    uploaded_at: str
    file_path: str
