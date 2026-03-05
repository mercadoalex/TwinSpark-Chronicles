import sys
import os
import time
import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ChildProfile, PersonalityTrait, EmotionalState
from ai.twin_intelligence import TwinIntelligenceEngine
from story.story_generator import StoryGenerator

from multimodal.camera_processor import CameraProcessor
from multimodal.audio_processor import AudioProcessor
from story.image_generator import ImageGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TwinSpark Chronicles API")

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the assets directory so the React app can load generated images directly via URL
assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "assets")
os.makedirs(assets_dir, exist_ok=True)
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

class AvatarRequest(BaseModel):
    name: str
    gender: str
    personality: str

@app.post("/api/profile/generate_avatar")
async def generate_avatar(request: AvatarRequest):
    """Generates an avatar via Hugging Face and returns the localhost URL."""
    try:
        from fastapi.concurrency import run_in_threadpool
        # ImageGenerator is synchronous, so we run it in a threadpool
        generator = ImageGenerator()
        logger.info(f"Generating avatar for {request.name} ({request.gender}) with personality: {request.personality}")
        
        filepath = await run_in_threadpool(
            generator.generate_character,
            request.name, 
            request.gender, 
            [request.personality]
        )
        
        if not filepath:
            return {"error": "Failed to generate image"}
            
        filename = os.path.basename(filepath)
        # Assuming backend is on 8000
        avatar_url = f"http://localhost:8000/assets/{filename}"
        return {"avatar_url": avatar_url}
        
    except Exception as e:
        logger.error(f"Avatar Generation Error: {e}")
        return {"error": str(e)}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.loop = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        import asyncio
        self.loop = asyncio.get_running_loop()
        logger.info("New WebSocket connection accepted.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("WebSocket connection closed.")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()


class TwinSession:
    """Represents an active, real-time story session between the two siblings."""
    def __init__(self, child1_profile: ChildProfile, child2_profile: ChildProfile):
        self.child1 = child1_profile
        self.child2 = child2_profile
        self.is_active = True
        self.current_story_state = "waiting_to_start"
        self.recent_events = []
        self.story_history = []
        
        # Sibling Dynamics State
        self.current_turn = child1_profile.id # Whose turn it is to speak
        self.simultaneous_mode = False        # If waiting for a "high-five"


class ActiveSessionManager:
    """
    Orchestrates the entire TwinSpark experience using WebSockets.
    """
    def __init__(self):
        logger.info("⚙️ Initializing SessionManager orchestration...")
        
        # Load the Core AI Brain
        self.engine = TwinIntelligenceEngine()
        self.story_gen = StoryGenerator()
        
        # Initialize Camera tracking with zone/gesture callbacks
        self.camera = CameraProcessor(camera_index=0, on_event=self._on_camera_event)
        
        # Initialize Audio listening
        self.audio = AudioProcessor()
        
        try:
            self.image_gen = ImageGenerator()
        except ValueError as e:
            logger.warning(f"⚠️ Image generation disabled: {e}")
            self.image_gen = None
            
        self.active_session = None

    def start_session(self, child1: ChildProfile, child2: ChildProfile):
        """Begin a new connected session for the two children."""
        logger.info(f"\n🚀 Starting new TwinSpark Session for {child1.name} and {child2.name}!")
        
        # Register them with the Brain
        self.engine.register_child(child1)
        self.engine.register_child(child2)
        self.engine.register_relationship(child1.id, child2.id)
        
        self.active_session = TwinSession(child1, child2)
        return self.active_session

    async def generate_initial_story(self, websocket: WebSocket):
        """Generates the first story beat and sends it to the newly connected socket."""
        if not self.active_session:
            return
            
        self.active_session.current_story_state = "in_progress"
        
        # Ask TwinEngine for the best roles and difficulty
        directive = self.engine.generate_story_directive(
            self.active_session.child1.id, 
            self.active_session.child2.id,
            "Magical Forest"
        )
        
        # Generate the story (This is blocking, in the future use run_in_executor)
        story_data = self.story_gen.generate_story_opening(directive)
        
        # Determine the next sibling mechanic!
        # For the first beat, we just assign a turn based on the directive roles
        self.active_session.current_turn = self.active_session.child1.id if directive['child1']['role'] == 'leader' else self.active_session.child2.id
        self.active_session.simultaneous_mode = False
        
        # Send everything directly to this new websocket
        await websocket.send_json(jsonable_encoder({
            "type": "STORY_UPDATE",
            "data": story_data,
            "mechanics": {
                "active_turn": self.active_session.current_turn,
                "simultaneous_mode": self.active_session.simultaneous_mode,
                "prompt": story_data['beats'][0]['interaction_prompt'] if story_data.get('beats') else "What do you do?"
            }
        }))
        
        # Generate image asynchronously so it doesn't block the UI
        if self.image_gen:
             import threading
             threading.Thread(target=self.image_gen.generate_scene, 
                              args=("Magical Forest with glowing trees", [self.active_session.child1.name, self.active_session.child2.name]),
                              daemon=True).start()

    def _on_camera_event(self, event_data: dict):
        """Callback from CameraProcessor when a physical zone gesture happens."""
        if not self.active_session:
            return
            
        logger.info(f"📷 Hardware Camera triggered event: {event_data['action']} by {event_data['user_id']}")
        
        if manager.loop and manager.loop.is_running():
            import asyncio
            try:
                asyncio.run_coroutine_threadsafe(
                    self.process_client_event(event_data),
                    manager.loop
                )
            except Exception as e:
                logger.error(f"Error submitting camera event to main loop: {e}")
        else:
            logger.error("Could not find main event loop for camera callback")

    def _on_audio_command(self, data: dict):
        """Callback from AudioProcessor's background thread when a command is heard."""
        command = data.get("command")
        if not command or not self.active_session:
            return
            
        logger.info(f"🎙️ Hardware Audio triggered command: {command}")
        
        # AudioProcessor doesn't know WHO spoke yet (no diarization in this MVP)
        # So we assume the person whose turn it is spoke it. 
        # If it's simultaneous mode, we assign it to child1 just to advance the beat.
        assumed_user_id = self.active_session.current_turn if self.active_session.current_turn else self.active_session.child1.id
        
        # We must trigger the async event processor from this sync background thread
        # FastAPI's asyncio loop is running in the main thread
        if manager.loop and manager.loop.is_running():
            import asyncio
            try:
                asyncio.run_coroutine_threadsafe(
                    self.process_client_event({"action": command, "user_id": assumed_user_id}),
                    manager.loop
                )
            except Exception as e:
                logger.error(f"Error submitting audio event to main loop: {e}")
        else:
            logger.error("Could not find main event loop for audio callback")

    async def process_client_event(self, event_data: dict):
        """Processes interaction events sent from the React UI."""
        if not self.active_session:
            return
            
        action = event_data.get("action")
        user_id = event_data.get("user_id")
        
        # 1. Enforce Turn-Taking Logic!
        if not self.active_session.simultaneous_mode and user_id != self.active_session.current_turn:
            await manager.broadcast(jsonable_encoder({
                "type": "MECHANIC_WARNING",
                "message": f"Oops! It's not your turn right now. Let your sibling decide!"
            }))
            return

        # 2. Process the valid action
        logger.info(f"Processing action '{action}' from {user_id}")
        
        # Build fresh directive to generate the next beat
        directive = self.engine.generate_story_directive(
            self.active_session.child1.id, 
            self.active_session.child2.id,
            "Magical Forest"
        )
        
        # Inform the story generator of the choice
        beat_data = self.story_gen.generate_next_beat(
            directive, 
            [], # We skip sending full history for this MVP prototype 
            {"beat_0": action} 
        )
        
        # 3. Apply the AI's dictated mechanic!
        self.active_session.simultaneous_mode = directive['relationship'].get('simultaneous_mode', False)
        
        if self.active_session.simultaneous_mode:
            self.active_session.current_turn = None
            prompt_override = "HIGH FIVE! Both of you show a high five to the camera at the same time!"
        else:
            self.active_session.current_turn = self.active_session.child2.id if user_id == self.active_session.child1.id else self.active_session.child1.id
            prompt_override = beat_data['interaction_prompt']
            
        await manager.broadcast(jsonable_encoder({
            "type": "STORY_UPDATE",
            "data": {"beats": [beat_data]},
            "mechanics": {
                "active_turn": self.active_session.current_turn,
                "simultaneous_mode": self.active_session.simultaneous_mode,
                "prompt": prompt_override
            }
        }))


# Global singleton
session_manager = ActiveSessionManager()

@app.websocket("/ws/session")
async def websocket_endpoint(
    websocket: WebSocket, 
    lang: str = "en",
    c1_name: str = "Ale", c1_gender: str = "girl", c1_personality: str = "playful",
    c2_name: str = "Sofi", c2_gender: str = "girl", c2_personality: str = "thoughtful"
):
    await manager.connect(websocket)
    try:
        try:
            # Dynamically register the players for this session
            child1 = ChildProfile(
                id="c1", name=c1_name, gender=c1_gender, age=6, 
                personality_traits=[PersonalityTrait(c1_personality.lower())]
            )
            child2 = ChildProfile(
                id="c2", name=c2_name, gender=c2_gender, age=6, 
                personality_traits=[PersonalityTrait(c2_personality.lower())]
            )
            session_manager.start_session(child1, child2)

            # Set the AI Story Language preference
            if session_manager.active_session:
                session_manager.active_session.language = lang
            # We need a background task to keep the camera frames processing
            import threading
            import time
            def _camera_loop():
                # Graceful polling loop so the thread persists even if the camera connects slowly
                while True:
                    if session_manager.camera and session_manager.camera.cap and session_manager.camera.cap.isOpened():
                        session_manager.camera.process_frame()
                        time.sleep(0.03) # roughly 30fps
                    else:
                        time.sleep(1.0) # Wait gently for camera to spin up
                    
            # Start hardware sensor loops
            session_manager.audio.start_listening(callback=session_manager._on_audio_command)
            if session_manager.camera:
                session_manager.camera.start()
                # Ensure we only start exactly one thread
                if not hasattr(session_manager, "_camera_thread_started"):
                    threading.Thread(target=_camera_loop, daemon=True).start()
                    session_manager._camera_thread_started = True
            
            # Upon connection, optionally send the initial story right away
            await session_manager.generate_initial_story(websocket)
            
            while True:
                # Wait for any messages from the React app (like button clicks or transcribed voice)
                data = await websocket.receive_text()
                event = json.loads(data)
                await session_manager.process_client_event(event)
        except Exception as e:
            logger.error(f"❌ Unhandled WebSocket Error: {e}", exc_info=True)
            raise
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.session_manager:app", host="0.0.0.0", port=8000, reload=True)
