"""Pydantic data models for the Family Photo Integration feature.

Defines structured models for photo uploads, face portraits, family member
labeling, character mappings, and scene compositing used across the photo
pipeline: upload → safety scan → face extraction → style transfer → compositing.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PhotoStatus(str, Enum):
    """Content safety status assigned to an uploaded photo."""

    SAFE = "safe"
    REVIEW = "review"
    BLOCKED = "blocked"


class FacePortraitRecord(BaseModel):
    """An individual face crop extracted from an uploaded photo."""

    face_id: str
    photo_id: str
    face_index: int
    crop_path: str
    bbox_x: float
    bbox_y: float
    bbox_width: float
    bbox_height: float
    family_member_name: str | None = None


class PhotoRecord(BaseModel):
    """Metadata for an uploaded family photo stored in the Photo_Store."""

    photo_id: str
    sibling_pair_id: str
    filename: str
    file_path: str
    file_size_bytes: int
    width: int
    height: int
    status: PhotoStatus
    uploaded_at: datetime
    faces: list[FacePortraitRecord] = []


class FamilyMember(BaseModel):
    """A labeled person identified in an uploaded photo."""

    face_id: str
    name: str
    crop_path: str
    sibling_pair_id: str


class CharacterMappingInput(BaseModel):
    """Input for assigning a family member to a story character role."""

    character_role: str
    face_id: str | None = None  # None means use default avatar


class CharacterMapping(BaseModel):
    """Persisted association between a family member and a story character role."""

    mapping_id: str
    sibling_pair_id: str
    character_role: str
    face_id: str | None
    family_member_name: str | None
    style_transferred_path: str | None = None
    created_at: datetime


class PhotoUploadResult(BaseModel):
    """Response returned after a photo upload is processed."""

    photo_id: str
    status: PhotoStatus
    faces: list[FacePortraitRecord] = []
    message: str


class DeleteResult(BaseModel):
    """Response returned after a photo is deleted with cascade cleanup."""

    deleted_photo_id: str
    deleted_face_count: int
    invalidated_mapping_count: int
    affected_character_roles: list[str]


class StorageStats(BaseModel):
    """Photo storage usage summary for a sibling pair."""

    photo_count: int
    face_count: int
    total_size_bytes: int


class CharacterPosition(BaseModel):
    """Normalized position and scale for a character portrait within a scene."""

    x: float = Field(ge=0.0, le=1.0, description="Normalized X position in scene")
    y: float = Field(ge=0.0, le=1.0, description="Normalized Y position in scene")
    scale: float = Field(gt=0.0, le=2.0, description="Scale factor relative to scene")
    z_order: int = Field(default=0, description="Layer ordering")
