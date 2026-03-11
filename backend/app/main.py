from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict
import json
import os
from dotenv import load_dotenv
import base64
import io
from PIL import Image

from app.agents.storyteller_agent import storyteller
from app.agents.avatar_agent import avatar_agent
from app.agents.orchestrator import orchestrator
from app.agents.memory_agent import memory_agent
from app.models.character import TwinCharacters, StoryContext

# Load environment variables
load_dotenv()

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
# WEBSOCKET for Real-time Storytelling
# ============================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
    
    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
    
    async def send_story(self, session_id: str, story_data: Dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(story_data)

manager = ConnectionManager()


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time story generation"""
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            # Receive user input (voice/gesture/text)
            data = await websocket.receive_json()
            
            # Generate story with Gemini
            story_segment = await storyteller.generate_story_segment(
                context=data.get("context"),
                user_input=data.get("user_input")
            )
            
            # Send back to frontend
            await manager.send_story(session_id, {
                "type": "story_segment",
                "data": story_segment
            })
            
    except WebSocketDisconnect:
        manager.disconnect(session_id)
        print(f"Session {session_id} disconnected")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
