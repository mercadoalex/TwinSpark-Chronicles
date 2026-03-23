from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
import fastapi
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import asyncio
import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
import base64
import io
from PIL import Image

from app.agents.storyteller_agent import storyteller
from app.agents.avatar_agent import avatar_agent
from app.agents.orchestrator import orchestrator
from app.agents.memory_agent import memory_agent
from app.models.character import TwinCharacters, StoryContext
from app.services.face_detector import FaceDetector
from app.services.emotion_detector import EmotionDetector
from app.services.stt_service import STTService
from app.services.input_manager import InputManager
from app.services.photo_service import PhotoService, ValidationError, PhotoNotFoundError
from app.services.voice_recording_service import (
    VoiceRecordingService,
    VoiceRecordingValidationError,
    VoiceRecordingCapacityError,
)
from app.services.audio_normalizer import AudioNormalizer, AudioNormalizationError
from app.models.voice_recording import RecordingMetadata, MessageType, RecordingStats
from app.services.content_scanner import ContentScanner
from app.services.face_extractor import FaceExtractor
from app.services.session_service import SessionService
from app.models.multimodal import TranscriptResult
from app.models.photo import CharacterMappingInput
from app.models.session import SessionSnapshotPayload, SessionSnapshotResponse, SessionSaveResult
from app.services.cache_manager import CacheManager
from app.services.style_transfer_cache import StyleTransferCache
from app.services.face_crop_cache import FaceCropCache
from app.models.audio_theme import SceneThemeRequest, AudioThemeResult
from app.services.scene_audio_mapper import SceneAudioMapper
from app.services.story_archive_service import StoryArchiveService
from app.models.storybook import StorybookSummary, StorybookDetail, DeleteStorybookResult
from app.services.session_time_enforcer import SessionTimeEnforcer
from app.services.drawing_sync_service import DrawingSyncService
from app.services.drawing_persistence_service import DrawingPersistenceService
from app.data.costume_catalog import is_valid_costume, get_costume_prompt, COSTUME_CATALOG

# Track ended sessions for idempotent POST /api/sessions/{id}/end
_ended_sessions: Dict[str, dict] = {}

# Module-level CacheManager — initialized at startup (task 12.1)
cache_manager: CacheManager | None = None

# Module-level SessionTimeEnforcer — tracks per-session elapsed time server-side
session_time_enforcer = SessionTimeEnforcer()

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Module-level singleton services for multimodal processing
face_detector = FaceDetector()
emotion_detector = EmotionDetector()
stt_service = STTService()

# Drawing sync service — validates and serializes stroke messages
drawing_sync_service = DrawingSyncService()

# Initialize FastAPI app
app = FastAPI(
    title="TwinSpark Chronicles API",
    description="Google Gemini 2.0 powered storytelling for twins",
    version="1.0.0"
)

# CORS configuration - UPDATE THIS SECTION
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3006",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",  # Vite sometimes uses this
        "*"  # TEMPORARY: Allow all origins for testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    global cache_manager

    # Initialize caches
    style_transfer_cache = StyleTransferCache(
        storage_root=os.path.join("photo_storage", "style_cache"),
    )
    face_crop_cache = FaceCropCache()

    # Create CacheManager and start cleanup loop
    cache_manager = CacheManager(
        style_transfer_cache=style_transfer_cache,
        face_crop_cache=face_crop_cache,
    )
    await cache_manager.start_cleanup_loop()

    logger.info("CacheManager initialized and cleanup loop started")


@app.on_event("shutdown")
async def shutdown_event():
    global cache_manager
    if cache_manager is not None:
        await cache_manager.stop_cleanup_loop()
        logger.info("CacheManager cleanup loop stopped")


# ============================================
# MODELS
# ============================================

class AvatarMetadata(BaseModel):
    name: str
    gender: str
    spirit_animal: str
    toy_name: Optional[str] = None
    style: str = "child-friendly"


class AvatarRequest(BaseModel):
    photo_base64: str
    metadata: AvatarMetadata


class AvatarResponse(BaseModel):
    avatar_url: Optional[str] = None
    avatar_base64: str
    metadata: dict


class StoryRequest(BaseModel):
    characters: Dict
    session_id: str
    language: str = "en"
    user_input: Optional[str] = None
    allowed_themes: Optional[list[str]] = None
    complexity_level: Optional[str] = None
    custom_blocked_words: Optional[list[str]] = None


class CostumeUpdateRequest(BaseModel):
    costume: str


# ============================================
# ROUTES
# ============================================

@app.get("/")
async def root():
    return {
        "service": "TwinSpark Chronicles API",
        "status": "running",
        "ai_engine": "Google Gemini 2.0 Flash",
        "version": "1.0.0"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "gemini_configured": bool(os.getenv("GOOGLE_API_KEY")),
        "timestamp": str(datetime.utcnow())
    }


@app.post("/api/avatar/generate", response_model=AvatarResponse)
async def generate_avatar(request: AvatarRequest):
    """
    Generate child-friendly avatar from photo
    Currently returns original photo (AI generation coming soon)
    """
    try:
        # Decode and validate image
        image_data = request.photo_base64.split(',')[1] if ',' in request.photo_base64 else request.photo_base64
        image_bytes = base64.b64decode(image_data)
        
        # Validate it's an image
        img = Image.open(io.BytesIO(image_bytes))
        
        # TODO: Add AI generation with Imagen 3 here
        # For now, return original photo
        
        return AvatarResponse(
            avatar_url=None,
            avatar_base64=request.photo_base64,
            metadata={
                "name": request.metadata.name,
                "gender": request.metadata.gender,
                "spirit_animal": request.metadata.spirit_animal,
                "toy_name": request.metadata.toy_name,
                "style": request.metadata.style,
                "generated": False,
                "message": "Using original photo. AI avatar generation coming soon!"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Avatar processing failed: {str(e)}")


@app.post("/api/story/generate")
async def generate_story(request: StoryRequest):
    """Generate story segment with Gemini 2.0"""
    try:
        context = {
            "characters": request.characters,
            "session_id": request.session_id,
            "language": request.language
        }
        
        story_segment = await storyteller.generate_story_segment(
            context,
            request.user_input
        )
        
        return story_segment
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/story/generate-rich")
async def generate_rich_story(request: StoryRequest):
    """
    Generate multimodal story with images, voice, and memory
    """
    try:
        rich_moment = await orchestrator.generate_rich_story_moment(
            session_id=request.session_id,
            characters=request.characters,
            user_input=request.user_input,
            language=request.language,
            allowed_themes=request.allowed_themes,
            complexity_level=request.complexity_level,
            custom_blocked_words=request.custom_blocked_words,
        )
        
        return rich_moment
        
    except Exception as e:
        print(f"❌ Rich story generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/{session_id}/summary")
async def get_session_summary(session_id: str):
    """
    Get session summary with all memories
    """
    try:
        summary = await memory_agent.get_session_summary(session_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# SIBLING DYNAMICS ENDPOINTS (Req 9.2, 9.3, 9.4)
# ============================================

@app.get("/api/sessions/{session_id}/sibling-summary")
async def get_sibling_summary(session_id: str):
    """Return Sibling_Dynamics_Score and plain-language summary for a session.

    Returns 404 if no sibling summary exists for the given session.
    Requirements: 9.2, 9.3, 9.4
    """
    try:
        await orchestrator._ensure_db_initialized()
        row = await orchestrator._sibling_db.load_session_summary(session_id)
    except Exception as e:
        logger.error("Failed to load sibling summary for session=%s: %s", session_id, e)
        raise HTTPException(status_code=500, detail=str(e))

    if row is None:
        raise HTTPException(status_code=404, detail="Sibling summary not found")

    return {
        "session_id": row["session_id"],
        "sibling_dynamics_score": row["score"],
        "summary": row["summary"],
        "suggestion": row.get("suggestion"),
    }


@app.post("/api/sessions/{session_id}/end")
async def end_session(session_id: str, body: dict | None = None):
    """Trigger end_session flow for a sibling session. Idempotent.

    Expects a JSON body with ``characters`` dict containing child1/child2
    info so the sibling_pair_id can be derived. If the session was already
    ended, the cached result is returned.

    Requirements: 9.2, 9.3, 9.4
    """
    # Idempotent: return cached result if already ended
    if session_id in _ended_sessions:
        return _ended_sessions[session_id]

    body = body or {}
    characters = body.get("characters", {})

    # Derive child IDs from characters dict
    child1_id = characters.get("child1", {}).get("name", "child1")
    child2_id = characters.get("child2", {}).get("name", "child2")
    sibling_pair_id = ":".join(sorted([child1_id, child2_id]))

    try:
        result = await orchestrator.end_session(session_id, sibling_pair_id)
    except Exception as e:
        logger.error("end_session failed for session=%s: %s", session_id, e)
        raise HTTPException(status_code=500, detail=str(e))

    _ended_sessions[session_id] = result
    return result


# ============================================
# PARENT DASHBOARD ENDPOINTS
# ============================================

@app.get("/api/dashboard/stats")
async def dashboard_stats():
    """Aggregate stats for the parent dashboard overview."""
    try:
        await orchestrator._ensure_db_initialized()
        db_conn = orchestrator._db_conn

        row = await db_conn.fetch_one("SELECT COUNT(*) as cnt FROM session_summaries")
        total_sessions = row["cnt"] if row else 0

        row = await db_conn.fetch_one("SELECT AVG(score) as avg_score FROM session_summaries")
        avg_bond = round(row["avg_score"], 2) if row and row["avg_score"] is not None else 0

        return {
            "total_sessions": total_sessions,
            "total_duration_minutes": total_sessions * 8,
            "average_bond_score": avg_bond,
        }
    except Exception as e:
        logger.error("dashboard_stats failed: %s", e)
        return {"total_sessions": 0, "total_duration_minutes": 0, "average_bond_score": 0}


@app.get("/api/dashboard/sessions")
async def dashboard_sessions():
    """Return recent session history for the parent dashboard."""
    try:
        await orchestrator._ensure_db_initialized()
        db_conn = orchestrator._db_conn

        rows = await db_conn.fetch_all(
            "SELECT session_id, sibling_pair_id, score, summary, suggestion, created_at "
            "FROM session_summaries ORDER BY created_at DESC LIMIT 20"
        )

        sessions = []
        for r in rows:
            sessions.append({
                "session_id": r["session_id"],
                "title": (r.get("summary") or "Adventure")[:60],
                "started_at": r["created_at"],
                "duration_minutes": 8,
                "theme": "Fantasy",
                "skills_practiced": [],
                "emotions_addressed": [],
                "has_divergence": False,
                "reunion_count": 0,
            })
        return sessions
    except Exception as e:
        logger.error("dashboard_sessions failed: %s", e)
        return []


@app.get("/api/dashboard/duration-chart")
async def dashboard_duration_chart():
    """Return playtime chart data for the parent dashboard."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return {"data": [{"label": d, "value": 0} for d in days]}


@app.get("/api/dashboard/leadership-chart")
async def dashboard_leadership_chart():
    """Return leadership balance chart data for the parent dashboard."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return {"data": [{"label": d, "value": 0} for d in days]}


# ============================================
# COSTUME UPDATE ENDPOINT
# ============================================

@app.put("/api/costume/{sibling_pair_id}/{child_num}")
async def update_costume(sibling_pair_id: str, child_num: int, body: CostumeUpdateRequest):
    """Update a sibling's costume in the session snapshot.

    Validates the costume ID against the catalog, updates character_profiles
    JSON, evicts the style transfer cache, and returns the new costume info.

    Requirements: 9.3, 9.4
    """
    # Validate costume ID
    if not is_valid_costume(body.costume):
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_costume",
                "valid_options": list(COSTUME_CATALOG.keys()),
            },
        )

    # Validate child_num
    if child_num not in (1, 2):
        raise HTTPException(status_code=422, detail="child_num must be 1 or 2")

    # Load the session snapshot
    svc = await _get_session_service()
    snapshot = await svc.load_snapshot(sibling_pair_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update the costume field in character_profiles
    profiles = snapshot["character_profiles"]
    costume_key = f"c{child_num}_costume"
    profiles[costume_key] = body.costume

    # Save the updated snapshot
    snapshot["character_profiles"] = profiles
    try:
        await svc.save_snapshot(snapshot)
    except Exception as e:
        logger.error("Failed to save costume update for pair=%s: %s", sibling_pair_id, e)
        raise HTTPException(status_code=500, detail="Failed to save costume update")

    # Evict style transfer cache for the affected sibling
    try:
        style_transfer = orchestrator.media._style_transfer
        cache = getattr(style_transfer, "_style_transfer_cache", None)
        if cache is not None:
            cache.evict(sibling_pair_id)
    except Exception:
        logger.warning("Style transfer cache eviction failed for pair=%s", sibling_pair_id)

    costume_prompt = get_costume_prompt(body.costume)
    return {"ok": True, "costume": body.costume, "costume_prompt": costume_prompt}


# ============================================
# EMERGENCY STOP ENDPOINT
# ============================================

@app.post("/api/emergency-stop/{session_id}")
async def emergency_stop(session_id: str):
    """Cancel all in-flight tasks for a session and return status.

    Returns 404 for unknown sessions (no active tasks tracked).
    Requirements: 6.2, 6.3, 6.5
    """
    # Check if session has any tracked tasks or is known
    if session_id not in orchestrator._session_tasks and session_id not in manager.active_connections:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result = await orchestrator.cancel_session(session_id)
        return {
            "status": result["status"],
            "session_id": result["session_id"],
            "session_saved": result["session_saved"],
        }
    except Exception as e:
        logger.error("Emergency stop failed for session=%s: %s", session_id, e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# WORLD STATE ENDPOINTS
# ============================================

class LocationResponse(BaseModel):
    id: str
    sibling_pair_id: str
    name: str
    description: str
    state: str
    discovered_at: str
    updated_at: str


class NpcResponse(BaseModel):
    id: str
    sibling_pair_id: str
    name: str
    description: str
    relationship_level: int
    met_at: str
    updated_at: str


class ItemResponse(BaseModel):
    id: str
    sibling_pair_id: str
    name: str
    description: str
    collected_at: str
    session_id: str


class WorldStateResponse(BaseModel):
    locations: list[LocationResponse] = []
    npcs: list[NpcResponse] = []
    items: list[ItemResponse] = []


@app.get("/api/world/{sibling_pair_id}", response_model=WorldStateResponse)
async def get_world_state(sibling_pair_id: str):
    """Return full world state for a sibling pair. Empty 200 if none exists."""
    try:
        await orchestrator._ensure_db_initialized()
        state = await orchestrator._world_db.load_world_state(sibling_pair_id)
        return WorldStateResponse(
            locations=[LocationResponse(**loc) for loc in state.get("locations", [])],
            npcs=[NpcResponse(**npc) for npc in state.get("npcs", [])],
            items=[ItemResponse(**item) for item in state.get("items", [])],
        )
    except Exception as e:
        logger.error("GET /api/world/%s failed: %s", sibling_pair_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/world/{sibling_pair_id}/locations", response_model=list[LocationResponse])
async def get_world_locations(sibling_pair_id: str):
    """Return locations for a sibling pair."""
    try:
        await orchestrator._ensure_db_initialized()
        locs = await orchestrator._world_db.load_locations(sibling_pair_id)
        return [LocationResponse(**loc) for loc in locs]
    except Exception as e:
        logger.error("GET /api/world/%s/locations failed: %s", sibling_pair_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/world/{sibling_pair_id}/npcs", response_model=list[NpcResponse])
async def get_world_npcs(sibling_pair_id: str):
    """Return NPCs for a sibling pair."""
    try:
        await orchestrator._ensure_db_initialized()
        npcs = await orchestrator._world_db.load_npcs(sibling_pair_id)
        return [NpcResponse(**npc) for npc in npcs]
    except Exception as e:
        logger.error("GET /api/world/%s/npcs failed: %s", sibling_pair_id, e)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/world/{sibling_pair_id}/items", response_model=list[ItemResponse])
async def get_world_items(sibling_pair_id: str):
    """Return items for a sibling pair."""
    try:
        await orchestrator._ensure_db_initialized()
        items = await orchestrator._world_db.load_items(sibling_pair_id)
        return [ItemResponse(**item) for item in items]
    except Exception as e:
        logger.error("GET /api/world/%s/items failed: %s", sibling_pair_id, e)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# PHOTO API ENDPOINTS
# ============================================

# Lazy-initialized PhotoService singleton
_photo_service: PhotoService | None = None


async def _get_photo_service() -> PhotoService:
    """Return (and lazily create) the shared PhotoService instance."""
    global _photo_service
    if _photo_service is None:
        await orchestrator._ensure_db_initialized()
        from app.services.content_filter import ContentFilter
        from app.db.photo_repository import PhotoRepository

        content_filter = ContentFilter()
        scanner = ContentScanner(content_filter)
        extractor = FaceExtractor(face_detector)
        photo_repo = PhotoRepository(orchestrator._db_conn)
        _photo_service = PhotoService(
            db=orchestrator._db_conn,
            content_scanner=scanner,
            face_extractor=extractor,
            photo_repo=photo_repo,
        )
    return _photo_service


@app.post("/api/photos/upload")
async def upload_photo(
    sibling_pair_id: str = fastapi.Form(...),
    file: fastapi.UploadFile = fastapi.File(...),
):
    """Upload a family photo. Validates, scans for safety, extracts faces."""
    svc = await _get_photo_service()
    image_bytes = await file.read()
    try:
        result = await svc.upload_photo(
            sibling_pair_id=sibling_pair_id,
            image_bytes=image_bytes,
            filename=file.filename or "photo.jpg",
        )
        return result.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Photo upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Upload failed")


@app.get("/api/photos/{sibling_pair_id}")
async def list_photos(sibling_pair_id: str):
    """List all photos for a sibling pair."""
    svc = await _get_photo_service()
    photos = await svc.get_photos(sibling_pair_id)
    return [p.model_dump() for p in photos]


@app.delete("/api/photos/{photo_id}")
async def delete_photo(photo_id: str):
    """Delete a photo and cascade-remove faces, portraits, and mappings."""
    svc = await _get_photo_service()
    try:
        result = await svc.delete_photo(photo_id)
        return result.model_dump()
    except PhotoNotFoundError:
        raise HTTPException(status_code=404, detail="Photo not found")
    except Exception as e:
        logger.error("Photo delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Delete failed")


@app.post("/api/photos/{photo_id}/approve")
async def approve_photo(photo_id: str):
    """Parent approves a photo flagged as REVIEW."""
    svc = await _get_photo_service()
    try:
        photo = await svc.approve_photo(photo_id)
        return photo.model_dump()
    except PhotoNotFoundError:
        raise HTTPException(status_code=404, detail="Photo not found")
    except Exception as e:
        logger.error("Photo approve failed: %s", e)
        raise HTTPException(status_code=500, detail="Approve failed")


@app.put("/api/photos/faces/{face_id}/label")
async def label_face(face_id: str, body: dict):
    """Set a family member name on a face portrait."""
    name = body.get("name", "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required")
    svc = await _get_photo_service()
    try:
        member = await svc.save_family_member(face_id, name)
        return member.model_dump()
    except Exception as e:
        logger.error("Face label failed: %s", e)
        raise HTTPException(status_code=500, detail="Label failed")


@app.get("/api/photos/mappings/{sibling_pair_id}")
async def get_character_mappings(sibling_pair_id: str):
    """Get character-to-family-member mappings for a sibling pair."""
    svc = await _get_photo_service()
    mappings = await svc.get_character_mappings(sibling_pair_id)
    return [m.model_dump() for m in mappings]


@app.post("/api/photos/mappings/{sibling_pair_id}")
async def save_character_mappings(sibling_pair_id: str, body: list[dict]):
    """Save character-to-family-member mappings."""
    svc = await _get_photo_service()
    try:
        inputs = [CharacterMappingInput(**item) for item in body]
        mappings = await svc.save_character_mapping(sibling_pair_id, inputs)
        return [m.model_dump() for m in mappings]
    except Exception as e:
        logger.error("Save mappings failed: %s", e)
        raise HTTPException(status_code=500, detail="Save mappings failed")


@app.get("/api/photos/stats/{sibling_pair_id}")
async def get_storage_stats(sibling_pair_id: str):
    """Return photo count and storage usage for a sibling pair."""
    svc = await _get_photo_service()
    stats = await svc.get_storage_stats(sibling_pair_id)
    return stats.model_dump()


# ============================================
# TOY PHOTO API ENDPOINTS
# ============================================

# Lazy-initialized ToyPhotoService singleton (follows _photo_service pattern)
_toy_photo_service: "ToyPhotoService | None" = None


async def _get_toy_photo_service():
    """Return (and lazily create) the shared ToyPhotoService instance."""
    global _toy_photo_service
    if _toy_photo_service is None:
        from app.services.toy_photo_service import ToyPhotoService

        _toy_photo_service = ToyPhotoService()
    return _toy_photo_service


@app.post("/api/toy-photo/{sibling_pair_id}/{child_number}")
async def upload_toy_photo(
    sibling_pair_id: str,
    child_number: int,
    file: fastapi.UploadFile = fastapi.File(...),
):
    """Upload a toy companion photo for a child. Validates, resizes, stores."""
    if child_number not in (1, 2):
        raise HTTPException(status_code=422, detail="Child number must be 1 or 2")
    svc = await _get_toy_photo_service()
    image_bytes = await file.read()
    try:
        result = await svc.upload_toy_photo(
            sibling_pair_id=sibling_pair_id,
            child_number=child_number,
            image_bytes=image_bytes,
            filename=file.filename or "toy.jpg",
        )
        return result.model_dump()
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Toy photo upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save photo")


@app.get("/api/toy-photo/{sibling_pair_id}/{child_number}")
async def get_toy_photo(sibling_pair_id: str, child_number: int):
    """Get toy photo metadata and URL for a child."""
    if child_number not in (1, 2):
        raise HTTPException(status_code=422, detail="Child number must be 1 or 2")
    svc = await _get_toy_photo_service()
    metadata = await svc.get_toy_photo(sibling_pair_id, child_number)
    if metadata is None:
        raise HTTPException(status_code=404, detail="No toy photo found")
    return metadata.model_dump()


# ============================================
# VOICE RECORDING API ENDPOINTS
# ============================================

# Lazy-initialized VoiceRecordingService singleton (follows _photo_service pattern)
_voice_recording_service: VoiceRecordingService | None = None


async def _get_voice_recording_service() -> VoiceRecordingService:
    """Return (and lazily create) the shared VoiceRecordingService instance."""
    global _voice_recording_service
    if _voice_recording_service is None:
        await orchestrator._ensure_db_initialized()
        from app.db.voice_recording_repository import VoiceRecordingRepository

        normalizer = AudioNormalizer()
        voice_repo = VoiceRecordingRepository(orchestrator._db_conn)
        _voice_recording_service = VoiceRecordingService(
            db=orchestrator._db_conn,
            audio_normalizer=normalizer,
            voice_repo=voice_repo,
        )
    return _voice_recording_service


def _verify_parent_pin(pin: str | None) -> None:
    """Verify the parent PIN from the X-Parent-Pin header.

    Raises HTTPException 401 if the PIN is missing or invalid.
    The expected PIN is read from the PARENT_PIN env var (default: '1234').
    """
    expected = os.getenv("PARENT_PIN", "1234")
    if not pin or pin != expected:
        raise HTTPException(status_code=401, detail="Parent PIN required")


@app.post("/api/voice-recordings/upload", status_code=201)
async def upload_voice_recording(
    sibling_pair_id: str = fastapi.Form(...),
    recorder_name: str = fastapi.Form(...),
    relationship: str = fastapi.Form(...),
    message_type: str = fastapi.Form(...),
    language: str = fastapi.Form("en"),
    command_phrase: str | None = fastapi.Form(None),
    command_action: str | None = fastapi.Form(None),
    file: fastapi.UploadFile = fastapi.File(...),
):
    """Upload a voice recording with audio file and metadata."""
    svc = await _get_voice_recording_service()
    audio_bytes = await file.read()
    try:
        metadata = RecordingMetadata(
            recorder_name=recorder_name,
            relationship=relationship,
            message_type=MessageType(message_type),
            language=language,
            sibling_pair_id=sibling_pair_id,
            command_phrase=command_phrase,
            command_action=command_action,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    try:
        result = await svc.upload_recording(sibling_pair_id, audio_bytes, metadata)
        return result.model_dump()
    except VoiceRecordingValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except VoiceRecordingCapacityError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except AudioNormalizationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error("Voice recording upload failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save recording")


@app.get("/api/voice-recordings/detail/{recording_id}")
async def get_voice_recording_detail(recording_id: str):
    """Get a single voice recording with audio URL."""
    svc = await _get_voice_recording_service()
    record = await svc.get_recording(recording_id)
    if not record:
        raise HTTPException(status_code=404, detail="Recording not found")
    return record.model_dump()


@app.get("/api/voice-recordings/stats/{sibling_pair_id}", response_model=RecordingStats)
async def get_voice_recording_stats(sibling_pair_id: str):
    """Return recording count and capacity for a sibling pair."""
    svc = await _get_voice_recording_service()
    count = await svc.get_recording_count(sibling_pair_id)
    return RecordingStats(
        recording_count=count,
        max_recordings=50,
        remaining=50 - count,
    )


@app.get("/api/voice-recordings/commands/{sibling_pair_id}")
async def get_voice_commands(sibling_pair_id: str):
    """List voice commands for a sibling pair."""
    svc = await _get_voice_recording_service()
    commands = await svc.get_voice_commands(sibling_pair_id)
    return [c.model_dump() for c in commands]


@app.get("/api/voice-recordings/{sibling_pair_id}")
async def list_voice_recordings(
    sibling_pair_id: str,
    message_type: str | None = None,
    recorder_name: str | None = None,
):
    """List voice recordings for a sibling pair with optional filters."""
    svc = await _get_voice_recording_service()
    recordings = await svc.get_recordings(sibling_pair_id, message_type, recorder_name)
    return [r.model_dump() for r in recordings]


@app.delete("/api/voice-recordings/all/{sibling_pair_id}")
async def delete_all_voice_recordings(
    sibling_pair_id: str,
    x_parent_pin: str | None = fastapi.Header(None),
):
    """Delete all voice recordings for a sibling pair. Requires parent PIN."""
    _verify_parent_pin(x_parent_pin)
    svc = await _get_voice_recording_service()
    try:
        count = await svc.delete_all_recordings(sibling_pair_id)
        return {"deleted_count": count}
    except Exception as e:
        logger.error("Bulk voice recording delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Bulk delete failed")


@app.delete("/api/voice-recordings/{recording_id}")
async def delete_voice_recording(
    recording_id: str,
    x_parent_pin: str | None = fastapi.Header(None),
):
    """Delete a single voice recording. Requires parent PIN."""
    _verify_parent_pin(x_parent_pin)
    svc = await _get_voice_recording_service()
    try:
        result = await svc.delete_recording(recording_id)
        return result.model_dump()
    except VoiceRecordingValidationError:
        raise HTTPException(status_code=404, detail="Recording not found")
    except Exception as e:
        logger.error("Voice recording delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Delete failed")


# ============================================
# SCENE AUDIO ENDPOINTS
# ============================================


@app.post("/api/audio/scene-theme", response_model=AudioThemeResult)
async def scene_theme(request: SceneThemeRequest):
    """Map a scene description to an audio theme via keyword matching."""
    mapper = SceneAudioMapper()
    return mapper.map_scene(request.scene_description)


# ============================================
# GALLERY ENDPOINTS
# ============================================

# Lazy-initialized StoryArchiveService singleton (follows _voice_recording_service pattern)
_story_archive_service: StoryArchiveService | None = None


async def _get_story_archive_service() -> StoryArchiveService:
    """Return (and lazily create) the shared StoryArchiveService instance."""
    global _story_archive_service
    if _story_archive_service is None:
        await orchestrator._ensure_db_initialized()
        _story_archive_service = StoryArchiveService(db=orchestrator._db_conn)
    return _story_archive_service


@app.get("/api/gallery/detail/{storybook_id}")
async def get_storybook_detail(storybook_id: str):
    """Get full storybook with all beats for the reader."""
    svc = await _get_story_archive_service()
    detail = await svc.get_storybook(storybook_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Storybook not found")
    return detail.model_dump()


@app.get("/api/gallery/{sibling_pair_id}")
async def list_gallery_storybooks(sibling_pair_id: str):
    """List storybook summaries for a sibling pair."""
    svc = await _get_story_archive_service()
    storybooks = await svc.list_storybooks(sibling_pair_id)
    return [s.model_dump() for s in storybooks]


@app.delete("/api/gallery/all/{sibling_pair_id}")
async def delete_all_gallery_storybooks(
    sibling_pair_id: str,
    x_parent_pin: str | None = fastapi.Header(None),
):
    """Bulk delete all storybooks for a sibling pair. Requires parent PIN."""
    _verify_parent_pin(x_parent_pin)
    svc = await _get_story_archive_service()
    try:
        count = await svc.delete_all_storybooks(sibling_pair_id)
        return {"deleted_count": count}
    except Exception as e:
        logger.error("Bulk gallery delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Bulk delete failed")


@app.delete("/api/gallery/{storybook_id}")
async def delete_gallery_storybook(
    storybook_id: str,
    x_parent_pin: str | None = fastapi.Header(None),
):
    """Delete a single storybook. Requires parent PIN."""
    _verify_parent_pin(x_parent_pin)
    svc = await _get_story_archive_service()
    try:
        deleted = await svc.delete_storybook(storybook_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Storybook not found")
        return {"deleted_count": 1}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Gallery storybook delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Delete failed")


# ============================================
# SESSION PERSISTENCE ENDPOINTS
# ============================================

# Lazy-initialized SessionService singleton
_session_service: SessionService | None = None


async def _get_session_service() -> SessionService:
    global _session_service
    if _session_service is None:
        await orchestrator._ensure_db_initialized()
        from app.db.session_repository import SessionRepository

        session_repo = SessionRepository(orchestrator._db_conn)
        _session_service = SessionService(orchestrator._db_conn, session_repo=session_repo)
    return _session_service


@app.post("/api/session/save", response_model=SessionSaveResult)
async def save_session(payload: SessionSnapshotPayload):
    """Save or update a session snapshot for a sibling pair."""
    svc = await _get_session_service()
    try:
        result = await svc.save_snapshot(payload.model_dump())
        return SessionSaveResult(**result)
    except Exception as e:
        logger.error("Session save failed: %s", e)
        raise HTTPException(status_code=500, detail="Session save failed")


@app.get("/api/session/load/{sibling_pair_id}", response_model=SessionSnapshotResponse)
async def load_session(sibling_pair_id: str):
    """Load the active session snapshot for a sibling pair."""
    svc = await _get_session_service()
    try:
        snapshot = await svc.load_snapshot(sibling_pair_id)
        if snapshot is None:
            raise HTTPException(status_code=404, detail="No session found")
        return SessionSnapshotResponse(**snapshot)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Session load failed: %s", e)
        raise HTTPException(status_code=500, detail="Session load failed")


@app.delete("/api/session/{sibling_pair_id}")
async def delete_session(sibling_pair_id: str):
    """Delete the active session snapshot for a sibling pair."""
    svc = await _get_session_service()
    try:
        deleted = await svc.delete_snapshot(sibling_pair_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="No session found")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Session delete failed: %s", e)
        raise HTTPException(status_code=500, detail="Session delete failed")


@app.on_event("startup")
async def _cleanup_stale_sessions():
    """Run stale session cleanup on app startup."""
    try:
        svc = await _get_session_service()
        count = await svc.cleanup_stale(max_age_days=30)
        if count > 0:
            logger.info("Cleaned up %d stale session(s) on startup", count)
    except Exception as e:
        logger.warning("Stale session cleanup failed on startup: %s", e)


# ============================================
# CACHE STATS ENDPOINT
# ============================================


@app.get("/api/cache/stats")
async def get_cache_stats():
    """Return aggregate cache statistics for style transfer and face crop caches."""
    import dataclasses

    if cache_manager is None:
        raise HTTPException(status_code=503, detail="Cache manager not initialized")
    stats = cache_manager.get_stats()
    return dataclasses.asdict(stats)


# ============================================
# WEBSOCKET for Real-time Storytelling
# ============================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.input_managers: Dict[str, InputManager] = {}
        self._session_tasks: Dict[str, set[asyncio.Task]] = {}
        self._session_contexts: Dict[str, Dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.input_managers[session_id] = InputManager(session_id)
        self._session_tasks[session_id] = set()
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.input_managers:
            self.input_managers[session_id].reset()
            del self.input_managers[session_id]
        self._session_contexts.pop(session_id, None)
        # Cancel all pending processing tasks for this session
        tasks = self._session_tasks.pop(session_id, set())
        for task in tasks:
            if not task.done():
                task.cancel()
    
    def track_task(self, session_id: str, task: asyncio.Task) -> None:
        """Register a background processing task for a session."""
        if session_id in self._session_tasks:
            self._session_tasks[session_id].add(task)
            task.add_done_callback(lambda t: self._session_tasks.get(session_id, set()).discard(t))
    
    async def send_story(self, session_id: str, story_data: Dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(story_data)
    
    def get_input_manager(self, session_id: str) -> Optional[InputManager]:
        return self.input_managers.get(session_id)

    def set_session_context(self, session_id: str, context: Dict) -> None:
        """Store session context (characters, language) for sibling mode detection."""
        self._session_contexts[session_id] = context

    def get_session_context(self, session_id: str) -> Optional[Dict]:
        return self._session_contexts.get(session_id)

manager = ConnectionManager()

# Wire session_time_enforcer and ws_manager into the orchestrator (Req 1.2, 7.1, 7.2)
orchestrator.session_time_enforcer = session_time_enforcer
orchestrator.ws_manager = manager


def _is_sibling_mode(session_id: str) -> bool:
    """Detect sibling mode from session context.

    Sibling mode is active when the session's characters dict contains
    both child1 and child2 with non-empty names.
    """
    ctx = manager.get_session_context(session_id)
    if ctx is None:
        return False
    characters = ctx.get("characters", {})
    c1 = characters.get("child1", {})
    c2 = characters.get("child2", {})
    return bool(c1.get("name")) and bool(c2.get("name"))


def _get_sibling_ids(session_id: str) -> tuple[str, str]:
    """Extract child1_id and child2_id from session context."""
    ctx = manager.get_session_context(session_id) or {}
    characters = ctx.get("characters", {})
    child1_id = characters.get("child1", {}).get("name", "child1")
    child2_id = characters.get("child2", {}).get("name", "child2")
    return child1_id, child2_id


async def send_drawing_prompt(session_id: str, prompt: str, duration: int) -> None:
    """Send a DRAWING_PROMPT message to the client for the given session."""
    await manager.send_story(session_id, {
        "type": "DRAWING_PROMPT",
        "prompt": prompt,
        "duration": duration,
        "session_id": session_id,
    })


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time story generation with multimodal input."""
    await manager.connect(websocket, session_id)

    # Start session time tracking (default 30 minutes)
    time_limit_minutes = 30
    try:
        raw = websocket.query_params.get("time_limit_minutes")
        if raw is not None:
            parsed = int(raw)
            if 1 <= parsed <= 120:
                time_limit_minutes = parsed
    except (ValueError, TypeError):
        pass
    session_time_enforcer.start_session(session_id, time_limit_minutes)
    
    # Send initial input status
    await manager.send_story(session_id, {
        "type": "input_status",
        "camera": face_detector.enabled,
        "mic": stt_service.enabled,
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # Store session context when provided (for sibling mode detection)
            if data.get("context") and data["context"].get("characters"):
                manager.set_session_context(session_id, data["context"])

            if msg_type == "camera_frame":
                task = asyncio.create_task(
                    _process_camera_frame(session_id, data)
                )
                manager.track_task(session_id, task)

            elif msg_type == "audio_segment":
                task = asyncio.create_task(
                    _process_audio_segment(session_id, data)
                )
                manager.track_task(session_id, task)

            elif msg_type == "TIME_EXTENSION":
                additional_minutes = data.get("additional_minutes", 0)
                if isinstance(additional_minutes, (int, float)) and additional_minutes > 0:
                    new_limit = session_time_enforcer.extend_time(session_id, int(additional_minutes))
                    await manager.send_story(session_id, {
                        "type": "TIME_EXTENSION_CONFIRMED",
                        "session_id": session_id,
                        "new_limit_minutes": new_limit,
                        "added_minutes": int(additional_minutes),
                    })

            elif msg_type == "WRAP_UP":
                # Forward wrap-up signal to orchestrator for story conclusion
                logger.info(
                    "WRAP_UP received for session %s, reason=%s",
                    session_id,
                    data.get("reason", "unknown"),
                )

            elif msg_type == "DRAWING_STROKE":
                stroke_data = data.get("stroke", data)
                validated = drawing_sync_service.validate_stroke(stroke_data)
                if validated is not None:
                    await manager.send_story(session_id, {
                        "type": "DRAWING_STROKE",
                        "stroke": {
                            "session_id": validated.session_id,
                            "sibling_id": validated.sibling_id,
                            "points": validated.points,
                            "color": validated.color,
                            "brush_size": validated.brush_size,
                            "timestamp": validated.timestamp,
                            "tool": validated.tool,
                            "stamp_shape": validated.stamp_shape,
                        },
                    })
                else:
                    logger.warning(
                        "Invalid DRAWING_STROKE message discarded for session %s",
                        session_id,
                    )

            elif msg_type == "DRAWING_COMPLETE":
                strokes = data.get("strokes", [])
                complete_session_id = data.get("session_id", session_id)
                drawing_prompt = data.get("prompt", "")
                drawing_duration = data.get("duration", 0)
                drawing_beat_index = data.get("beat_index", 0)

                child1_id, child2_id = _get_sibling_ids(session_id)
                sibling_pair_id = ":".join(sorted([child1_id, child2_id]))

                async def _persist_and_continue(
                    sid: str,
                    pair_id: str,
                    strokes_list: list,
                    prompt: str,
                    duration: int,
                    beat_index: int,
                    c1_name: str,
                    c2_name: str,
                ) -> None:
                    """Persist drawing, then generate next story beat with drawing context."""
                    try:
                        await orchestrator._ensure_db_initialized()
                        persistence_svc = DrawingPersistenceService(
                            orchestrator._db_conn
                        )
                        record = await persistence_svc.save_drawing(
                            session_id=sid,
                            sibling_pair_id=pair_id,
                            strokes=strokes_list,
                            prompt=prompt,
                            duration_seconds=duration,
                            beat_index=beat_index,
                        )

                        # Build drawing_context for the next story beat (Req 5.1, 5.2, 5.3)
                        drawing_context = {
                            "prompt": prompt,
                            "sibling_names": [c1_name, c2_name],
                            "image_path": record.image_path,
                        }

                        # Retrieve session context for characters
                        ctx = manager.get_session_context(sid) or {}
                        characters = ctx.get("characters", {})
                        language = ctx.get("language", "en")

                        # Generate next story beat referencing the drawing
                        result = await orchestrator.generate_rich_story_moment(
                            session_id=sid,
                            characters=characters,
                            user_input="continue after drawing",
                            language=language,
                            drawing_context=drawing_context,
                        )

                        # Send the post-drawing story beat to the client
                        await manager.send_story(sid, {
                            "type": "story_segment",
                            "data": result,
                        })
                    except Exception as exc:
                        logger.error(
                            "Failed to persist/continue drawing for session %s: %s",
                            sid,
                            exc,
                        )

                task = asyncio.create_task(
                    _persist_and_continue(
                        complete_session_id,
                        sibling_pair_id,
                        strokes,
                        drawing_prompt,
                        drawing_duration,
                        drawing_beat_index,
                        child1_id,
                        child2_id,
                    )
                )
                manager.track_task(session_id, task)

                await manager.send_story(session_id, {
                    "type": "DRAWING_END",
                    "reason": "manual",
                })

            elif msg_type == "DRAWING_EARLY_END":
                await manager.send_story(session_id, {
                    "type": "DRAWING_END",
                    "reason": "manual",
                })

            else:
                # Existing story generation flow for "user_input" / "context" messages
                story_segment = await storyteller.generate_story_segment(
                    context=data.get("context"),
                    user_input=data.get("user_input"),
                )
                await manager.send_story(session_id, {
                    "type": "story_segment",
                    "data": story_segment,
                })
            
    except WebSocketDisconnect:
        await _cleanup_session(session_id)
        print(f"Session {session_id} disconnected")


async def _cleanup_session(session_id: str, timeout: float = 5.0) -> None:
    """Discard buffered frames/audio and cancel pending tasks within timeout.

    Cancels all in-flight processing tasks for the session and waits up to
    ``timeout`` seconds for them to finish before forcibly moving on.
    Also ends and removes session time tracking.
    """
    # End session time tracking and clean up
    session_time_enforcer.end_session(session_id)
    session_time_enforcer.remove_session(session_id)

    tasks = manager._session_tasks.get(session_id, set()).copy()
    manager.disconnect(session_id)  # cancels tasks + removes input manager

    if tasks:
        # Wait for cancelled tasks to wrap up, bounded by timeout
        done, pending = await asyncio.wait(tasks, timeout=timeout)
        for t in pending:
            t.cancel()
        logger.info(
            "Session %s cleanup: %d tasks finished, %d force-cancelled",
            session_id, len(done), len(pending),
        )


async def _process_camera_frame(session_id: str, data: dict) -> None:
    """Process a camera frame through face detection → emotion → fusion → orchestrator."""
    try:
        frame_bytes = base64.b64decode(data["data"])
        timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")

        # Face detection
        faces = face_detector.detect(frame_bytes)

        # Emotion classification for each detected face
        emotions = emotion_detector.classify_all(frame_bytes, faces)

        # Send emotion feedback to frontend (Task 7.2)
        if emotions:
            await manager.send_story(session_id, {
                "type": "emotion_feedback",
                "emotions": [
                    {"face_id": e.face_id, "emotion": e.emotion.value, "confidence": e.confidence}
                    for e in emotions
                ],
            })

        # Fuse into a MultimodalInputEvent (camera-only: empty transcript)
        input_mgr = manager.get_input_manager(session_id)
        if input_mgr is None:
            return

        event = input_mgr.fuse(
            transcript=TranscriptResult(),  # empty — no audio in this path
            emotions=emotions,
            faces_detected=len(faces) > 0,
            timestamp=timestamp,
        )

        if event is not None:
            # Route to sibling pipeline when sibling mode is active (Req 11.1, 11.5)
            if _is_sibling_mode(session_id):
                child1_id, child2_id = _get_sibling_ids(session_id)
                ctx = manager.get_session_context(session_id) or {}
                result = await orchestrator.process_sibling_event(
                    event=event,
                    child1_id=child1_id,
                    child2_id=child2_id,
                    characters=ctx.get("characters", {}),
                    language=ctx.get("language", "en"),
                )
            else:
                ctx = event.to_orchestrator_context()
                result = await orchestrator.generate_rich_story_moment(
                    session_id=session_id,
                    characters={},
                    user_input=ctx.get("user_input"),
                    language="en",
                )
            await manager.send_story(session_id, {
                "type": "story_segment",
                "data": result,
            })

    except Exception as e:
        logger.error("Camera frame processing failed for session=%s: %s", session_id, e)


async def _process_audio_segment(session_id: str, data: dict) -> None:
    """Process an audio segment through STT → fusion → orchestrator."""
    try:
        audio_bytes = base64.b64decode(data["data"])
        timestamp = data.get("timestamp", datetime.utcnow().isoformat() + "Z")
        language = data.get("language", "en-US")
        speech_id = data.get("speech_id")

        # Speech-to-text
        transcript = await stt_service.transcribe(audio_bytes, language=language)

        # Send transcript feedback to frontend (Task 7.2)
        if not transcript.is_empty:
            await manager.send_story(session_id, {
                "type": "transcript_feedback",
                "text": transcript.text,
                "confidence": transcript.confidence,
            })

            # Voice command matching (Task 6.3)
            try:
                await orchestrator._ensure_db_initialized()
                if orchestrator._playback_integrator is not None:
                    ctx = manager.get_session_context(session_id) or {}
                    characters = ctx.get("characters", {})
                    child1_name = characters.get("child1", {}).get("name", "child1")
                    child2_name = characters.get("child2", {}).get("name", "child2")
                    sibling_pair_id = ":".join(sorted([child1_name, child2_name]))

                    match = await orchestrator._playback_integrator.match_voice_command(
                        sibling_pair_id, transcript.text
                    )
                    if match and match.matched:
                        await manager.send_story(session_id, {
                            "type": "voice_command_match",
                            "command_action": match.command_action,
                            "similarity_score": match.similarity_score,
                            "confirmation_audio_url": match.confirmation_audio_url,
                        })
            except Exception as e:
                logger.warning("Voice command matching failed for session=%s: %s", session_id, e)

        # Fuse into a MultimodalInputEvent (audio-only: no emotions)
        input_mgr = manager.get_input_manager(session_id)
        if input_mgr is None:
            return

        event = input_mgr.fuse(
            transcript=transcript,
            emotions=[],
            faces_detected=False,
            timestamp=timestamp,
            speech_id=speech_id,
        )

        if event is not None:
            # Route to sibling pipeline when sibling mode is active (Req 11.1, 11.5)
            if _is_sibling_mode(session_id):
                child1_id, child2_id = _get_sibling_ids(session_id)
                ctx = manager.get_session_context(session_id) or {}
                result = await orchestrator.process_sibling_event(
                    event=event,
                    child1_id=child1_id,
                    child2_id=child2_id,
                    characters=ctx.get("characters", {}),
                    language=ctx.get("language", language.split("-")[0]),
                )
            else:
                ctx = event.to_orchestrator_context()
                result = await orchestrator.generate_rich_story_moment(
                    session_id=session_id,
                    characters={},
                    user_input=ctx.get("user_input"),
                    language=language.split("-")[0],  # "en-US" → "en"
                )
            await manager.send_story(session_id, {
                "type": "story_segment",
                "data": result,
            })

    except Exception as e:
        logger.error("Audio segment processing failed for session=%s: %s", session_id, e)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
