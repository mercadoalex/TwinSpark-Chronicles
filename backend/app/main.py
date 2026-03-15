from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
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
from app.models.multimodal import TranscriptResult

# Track ended sessions for idempotent POST /api/sessions/{id}/end
_ended_sessions: Dict[str, dict] = {}

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Module-level singleton services for multimodal processing
face_detector = FaceDetector()
emotion_detector = EmotionDetector()
stt_service = STTService()

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
            language=request.language
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


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time story generation with multimodal input."""
    await manager.connect(websocket, session_id)
    
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
    """
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
