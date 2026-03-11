import sys
import os
import time
import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Ensure src is in path BEFORE any local imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import local modules
from config import settings
from models import ChildProfile, PersonalityTrait, SpiritAnimal, StoryBeat, Choice
from story.story_generator import StoryGenerator
from story.multimodal_coordinator import MultimodalCoordinator, OutputMode
from ai.creative_director import CreativeDirectorAgent as CreativeDirector, CreativeAsset, MediaType

# Import ImageGenerator - REMOVE THE MOCK BELOW
from story.image_generator import ImageGenerator

try:
    from ai.twin_intelligence import TwinIntelligenceEngine as TwinSparkBrain
except (ImportError, ModuleNotFoundError):
    logger = logging.getLogger(__name__)
    logger.warning("TwinIntelligenceEngine not available - using mock")
    class TwinSparkBrain:
        def __init__(self):
            self.child_states = {}
        def register_child(self, profile):
            pass
        def register_relationship(self, id1, id2):
            pass

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

from typing import Optional

class AvatarRequest(BaseModel):
    name: str
    gender: str
    personality: str
    outfit: Optional[str] = None
    base64_photo: Optional[str] = None
    
    class Config:
        extra = "ignore"

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
            [request.personality],
            request.base64_photo
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
        self.active_connections: dict[str, WebSocket] = {}
        self.loop = None

    async def connect(self, websocket: WebSocket, client_id: str = "default"):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        if self.loop is None:
            self.loop = asyncio.get_event_loop()

    def disconnect(self, client_id: str = "default"):
        if client_id in self.active_connections:
            del self.active_connections[client_id]

    async def send_personal_message(self, message: dict, client_id: str = "default"):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)
            
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections.values():
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
    """Manages active storytelling sessions"""
    
    def __init__(self):
        self.engine = TwinSparkBrain()
        self.story_gen = StoryGenerator()
        self.creative_director = CreativeDirector(self.story_gen)
        self.image_gen = ImageGenerator()
        
        self.child1 = None
        self.child2 = None
        self.active_session = None
        self.current_websocket = None
        
        self.profiles = []
        
        logger.info("✅ SessionManager ready!")

    def start_session(self, child1: ChildProfile, child2: ChildProfile):
        """Begin a new connected session for the two children."""
        logger.info(f"\n🚀 Starting new TwinSpark Session for {child1.name} and {child2.name}!")
        
        self.child1 = child1
        self.child2 = child2
        
        # Register them with the Brain
        self.engine.register_child(child1)
        self.engine.register_child(child2)
        self.engine.register_relationship(child1.id, child2.id)
        
        self.active_session = TwinSession(child1, child2)
        return self.active_session

    async def generate_initial_story(self, websocket: WebSocket):
        """Generate story using FULL sibling dynamics modeling."""
        
        logger.info("🎬🎬🎬 ENTERING generate_initial_story()")
        
        try:
            self.current_websocket = websocket
            
            logger.info("   → Sending STATUS message...")
            await websocket.send_json({
                "type": "STATUS",
                "message": "Creative Director is preparing your adventure..."
            })
            logger.info("   ✅ STATUS message sent")
            
            logger.info(f"   → Checking child profiles: c1={self.child1.name}, c2={self.child2.name}")
            
            # Get current emotional states
            child1_state = self.engine.child_states.get("c1")
            child2_state = self.engine.child_states.get("c2")
            
            logger.info(f"   → Child states: c1_state={child1_state}, c2_state={child2_state}")
            
            if not child1_state or not child2_state:
                logger.warning("   ⚠️ Child states not initialized, using defaults")
                child1_emotion = "wonder"
                child2_emotion = "wonder"
            else:
                child1_emotion = child1_state.primary_emotion
                child2_emotion = child2_state.primary_emotion
            
            logger.info(f"   ✅ Emotions set: {child1_emotion}, {child2_emotion}")
            
            # Extract values safely - handle both enum objects and strings
            if self.child1.personality_traits:
                trait = self.child1.personality_traits[0]
                child1_personality = trait.value if hasattr(trait, 'value') else str(trait)
            else:
                child1_personality = "brave"
            
            if self.child2.personality_traits:
                trait = self.child2.personality_traits[0]
                child2_personality = trait.value if hasattr(trait, 'value') else str(trait)
            else:
                child2_personality = "wise"
            
            # Handle spirit animal - could be enum or string
            spirit1 = self.child1.spirit_animal
            child1_spirit = spirit1.value if hasattr(spirit1, 'value') else str(spirit1)
            
            spirit2 = self.child2.spirit_animal
            child2_spirit = spirit2.value if hasattr(spirit2, 'value') else str(spirit2)
            
            child1_toy = self.child1.favorite_toy_name
            child2_toy = self.child2.favorite_toy_name
            
            logger.info(f"   → Profile data extracted:")
            logger.info(f"      Child 1: {self.child1.name}, {child1_personality}, {child1_spirit}, {child1_toy}")
            logger.info(f"      Child 2: {self.child2.name}, {child2_personality}, {child2_spirit}, {child2_toy}")
            
            logger.info("   → Starting story beat generation...")
            
            # Collect all assets first
            assets = []
            asset_count = 0
            
            logger.info("   → Calling creative_director.generate_story_beat_with_dynamics()...")
            
            async for asset in self.creative_director.generate_story_beat_with_dynamics(
                child1_name=self.child1.name,
                child1_personality=child1_personality,
                child1_spirit=child1_spirit,
                child1_toy=child1_toy,
                child1_emotion=child1_emotion,
                child2_name=self.child2.name,
                child2_personality=child2_personality,
                child2_spirit=child2_spirit,
                child2_toy=child2_toy,
                child2_emotion=child2_emotion,
                story_context="beginning of the adventure"
            ):
                asset_count += 1
                logger.info(f"   📦 Asset #{asset_count} generated: {asset.media_type.value} - {asset.metadata}")
                assets.append(asset)
            
            logger.info(f"   ✅ Total assets collected: {len(assets)}")
            
            if len(assets) == 0:
                logger.error("   ❌❌❌ NO ASSETS WERE GENERATED!")
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Story generation produced no content"
                })
                return
            
            logger.info(f"   → Now sending {len(assets)} assets to frontend...")
            
            # Send them one by one
            for i, asset in enumerate(assets):
                logger.info(f"   → Delivering asset {i+1}/{len(assets)}: {asset.media_type.value}")
                await self._deliver_creative_asset(websocket, asset)
                logger.info(f"   ✅ Asset {i+1}/{len(assets)} delivered")
                await asyncio.sleep(0.3)
            
            logger.info("   → Sending STORY_COMPLETE...")
            await websocket.send_json({
                "type": "STORY_COMPLETE",
                "message": "Your adventure awaits! Make your choice..."
            })
            logger.info("   ✅ STORY_COMPLETE sent")
            
            logger.info("🎬🎬🎬 EXITING generate_initial_story() - SUCCESS!")
            
        except Exception as e:
            logger.error(f"❌❌❌ EXCEPTION in generate_initial_story(): {e}", exc_info=True)
            await websocket.send_json({
                "type": "ERROR",
                "message": f"Story generation error: {str(e)}"
            })

    async def _deliver_creative_asset(self, websocket: WebSocket, asset: CreativeAsset):
        """Deliver a single creative asset to the frontend"""
        
        try:
            payload = {
                "type": "CREATIVE_ASSET",
                "media_type": asset.media_type.value,
                "content": asset.content,
                "timestamp": asset.timestamp,
                "metadata": asset.metadata or {}
            }
            
            # Add child identifier to metadata for perspective texts
            if asset.media_type == MediaType.TEXT and asset.metadata:
                if 'child' not in asset.metadata:
                    # Try to infer from content
                    if self.child1 and self.child1.name in asset.content:
                        payload["metadata"]["child"] = "c1"
                    elif self.child2 and self.child2.name in asset.content:
                        payload["metadata"]["child"] = "c2"
            
            logger.info(f"      → Sending: {payload['media_type']}, metadata={payload['metadata']}")
            
            # Special handling for images
            if asset.media_type == MediaType.IMAGE and self.image_gen:
                logger.info(f"      → Image detected, generating...")
                try:
                    await websocket.send_json({
                        "type": "STATUS",
                        "message": "Generating scene artwork..."
                    })
                    
                    image_url = await asyncio.to_thread(
                        self.image_gen.generate_scene,
                        asset.content
                    )
                    
                    if image_url:
                        payload["content"] = image_url
                        payload["metadata"]["generated"] = True
                        logger.info(f"      ✅ Image generated: {image_url}")
                    else:
                        logger.warning("      ⚠️ Image generation returned None")
                        payload["metadata"]["generated"] = False
                except Exception as e:
                    logger.error(f"      ❌ Image generation failed: {e}")
                    payload["metadata"]["generated"] = False
            
            logger.info(f"      → Sending payload to WebSocket...")
            await websocket.send_json(payload)
            logger.info(f"      ✅ Payload sent successfully!")
            
        except Exception as e:
            logger.error(f"      ❌❌❌ EXCEPTION in _deliver_creative_asset(): {e}", exc_info=True)

    async def create_profile(self, profile_data: dict):
        """Create a child profile from frontend data"""
        try:
            logger.info(f"Creating profile with data: {profile_data}")
            
            # Extract personality - accept any string and map to valid enum
            personality_raw = profile_data.get('personality_traits', ['brave'])
            if isinstance(personality_raw, str):
                personality_raw = [personality_raw]
            
            # Mapping de strings comunes a PersonalityTrait válidos
            personality_map = {
                # Spirit animals to personality
                'dragon': PersonalityTrait.BRAVE,
                'unicorn': PersonalityTrait.CREATIVE,
                'owl': PersonalityTrait.WISE,
                'dolphin': PersonalityTrait.PLAYFUL,      # ← CORREGIDO
                'phoenix': PersonalityTrait.ENERGETIC,    # ← CORREGIDO
                'tiger': PersonalityTrait.ADVENTUROUS,    # ← CORREGIDO
                
                # Direct personality traits
                'brave': PersonalityTrait.BRAVE,
                'curious': PersonalityTrait.CURIOUS,
                'kind': PersonalityTrait.KIND,
                'creative': PersonalityTrait.CREATIVE,
                'logical': PersonalityTrait.LOGICAL,
                'playful': PersonalityTrait.PLAYFUL,
                'wise': PersonalityTrait.WISE,
                'adventurous': PersonalityTrait.ADVENTUROUS,
                'thoughtful': PersonalityTrait.THOUGHTFUL,
                'energetic': PersonalityTrait.ENERGETIC,
                'calm': PersonalityTrait.CALM,
                'helpful': PersonalityTrait.HELPFUL,
                'funny': PersonalityTrait.FUNNY,
                'serious': PersonalityTrait.SERIOUS
            }
            
            valid_traits = []
            for trait in personality_raw:
                trait_lower = trait.lower()
                if trait_lower in personality_map:
                    valid_traits.append(personality_map[trait_lower])
                else:
                    logger.warning(f"⚠️ Unknown personality '{trait}', using BRAVE")
                    valid_traits.append(PersonalityTrait.BRAVE)
            
            if not valid_traits:
                valid_traits = [PersonalityTrait.BRAVE]
            
            # Extract and validate spirit animal
            spirit_animal = profile_data.get('spirit_animal', 'dragon')
            try:
                spirit_animal_enum = SpiritAnimal(spirit_animal.lower())
            except ValueError:
                logger.warning(f"⚠️ Invalid spirit animal '{spirit_animal}', using DRAGON as default")
                spirit_animal_enum = SpiritAnimal.DRAGON
            
            # Create profile
            profile = ChildProfile(
                id=f"c{len(self.profiles) + 1}",
                name=profile_data['name'],
                gender=profile_data['gender'],
                age=6,
                personality_traits=valid_traits,
                spirit_animal=spirit_animal_enum,
                favorite_toy_name=profile_data.get('favorite_toy_name', 'Teddy Bear'),
                avatar_url=profile_data.get('avatar_url')
            )
            
            logger.info(f"✅ Profile created: {profile.name}, traits={profile.personality_traits}, spirit={profile.spirit_animal}")
            return profile
            
        except Exception as e:
            logger.error(f"❌ Error creating profile: {e}", exc_info=True)
            raise

    async def handle_choice(self, websocket: WebSocket, choice: str):
        """Handle a choice made by the children and generate next story beat"""
        try:
            logger.info(f"🎯🎯🎯 ENTERING handle_choice()")
            logger.info(f"   Choice: {choice}")
            
            await websocket.send_json({
                "type": "STATUS",
                "message": "✨ The magic swirls as your choice takes effect..."
            })
            
            # Build context for continuation
            scene_prompt = f"""Continue the story based on this choice: "{choice}"
            
    The children {self.child1.name} and {self.child2.name} have decided to {choice}.
    Show what happens next from both of their perspectives.
    Keep it magical, age-appropriate (4-8 years), and exciting!
    
    Remember:
    - {self.child1.name}'s spirit animal is {self.child1.spirit_animal}
    - {self.child2.name}'s spirit animal is {self.child2.spirit_animal}
    - Their toys {self.child1.favorite_toy_name} and {self.child2.favorite_toy_name} might help them
    """
            
            logger.info(f"   → Generating new story beat...")
            
            # Generate new story beat
            assets = self.creative_director.generate_story_beat(
                scene_description=scene_prompt,
                child1_state={"emotion": "excited", "energy": 0.8},
                child2_state={"emotion": "curious", "energy": 0.8}
            )
            
            if not assets:
                logger.error("   ❌ No assets generated for continuation")
                await websocket.send_json({
                    "type": "ERROR",
                    "message": "Failed to generate story continuation"
                })
                return
            
            logger.info(f"   → Generated {len(assets)} assets, delivering...")
            
            # Deliver assets one by one
            for i, asset in enumerate(assets):
                logger.info(f"   → Delivering asset {i+1}/{len(assets)}: {asset.media_type.value}")
                await self._deliver_creative_asset(websocket, asset)
                await asyncio.sleep(0.3)
            
            logger.info("   → Sending STORY_COMPLETE...")
            await websocket.send_json({
                "type": "STORY_COMPLETE",
                "message": "The adventure continues!"
            })
            
            logger.info("🎯🎯🎯 EXITING handle_choice() - SUCCESS!")
            
        except Exception as e:
            logger.error(f"❌ Error handling choice: {e}", exc_info=True)
            await websocket.send_json({
                "type": "ERROR",
                "message": "Something magical went wrong. Try another choice!"
            })


# Create global session manager instance
session_manager = ActiveSessionManager()


# WebSocket endpoint with query parameters for direct session start
@app.websocket("/ws/session")
async def websocket_session_endpoint(
    websocket: WebSocket,
    lang: str = Query("en"),
    c1_name: str = Query(...),
    c1_gender: str = Query(...),
    c1_personality: str = Query("brave"),
    c1_spirit: str = Query("dragon"),
    c1_toy: str = Query("Teddy"),
    c2_name: str = Query(...),
    c2_gender: str = Query(...),
    c2_personality: str = Query("wise"),
    c2_spirit: str = Query("owl"),
    c2_toy: str = Query("Book")
):
    """WebSocket endpoint with query parameters for direct session start"""
    await websocket.accept()
    logger.info("🔌 WebSocket /ws/session connection accepted")
    logger.info(f"   Language: {lang}")
    logger.info(f"   Child 1: {c1_name} ({c1_gender}, {c1_personality}, {c1_spirit})")
    logger.info(f"   Child 2: {c2_name} ({c2_gender}, {c2_personality}, {c2_spirit})")
    
    try:
        # Create profiles from query parameters
        profile1_data = {
            'name': c1_name,
            'gender': c1_gender,
            'age': 6,
            'personality_traits': [c1_personality],
            'spirit_animal': c1_spirit,
            'favorite_toy_name': c1_toy
        }
        
        profile2_data = {
            'name': c2_name,
            'gender': c2_gender,
            'age': 6,
            'personality_traits': [c2_personality],
            'spirit_animal': c2_spirit,
            'favorite_toy_name': c2_toy
        }
        
        # Create profiles
        profile1 = await session_manager.create_profile(profile1_data)
        profile2 = await session_manager.create_profile(profile2_data)
        
        # Start session
        session_manager.child1 = profile1
        session_manager.child2 = profile2
        
        logger.info(f"✅ Session started for {profile1.name} and {profile2.name}")
        
        # Generate initial story
        await session_manager.generate_initial_story(websocket)
        
        # Keep connection alive and handle messages
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.info(f"📨 Received message: {message_type}")
            logger.info(f"   Full data: {data}")
            
            if message_type == "MAKE_CHOICE":
                choice_text = data.get("choice")
                logger.info(f"🎯 Processing choice: {choice_text}")
                
                # Generate continuation based on choice
                await session_manager.handle_choice(websocket, choice_text)
                
            else:
                logger.warning(f"⚠️ Unknown message type: {message_type}")
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket /ws/session disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket /ws/session error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "ERROR",
                "message": str(e)
            })
        except:
            pass


# Existing /ws endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Main WebSocket endpoint for real-time story interaction"""
    await websocket.accept()
    logger.info("🔌 WebSocket connection accepted")
    
    try:
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type")
            
            logger.info(f"📨 Received message type: {message_type}")
            
            if message_type == "CREATE_PROFILE":
                profile = await session_manager.create_profile(data["profile"])
                session_manager.profiles.append(profile)
                
                await websocket.send_json({
                    "type": "PROFILE_CREATED",
                    "profile": {
                        "id": profile.id,
                        "name": profile.name,
                        "avatar_url": profile.avatar_url
                    }
                })
                
            elif message_type == "START_STORY":
                if len(session_manager.profiles) == 2:
                    session_manager.child1 = session_manager.profiles[0]
                    session_manager.child2 = session_manager.profiles[1]
                    
                    await session_manager.generate_initial_story(websocket)
                else:
                    await websocket.send_json({
                        "type": "ERROR",
                        "message": "Need 2 profiles to start story"
                    })
                    
            elif message_type == "MAKE_CHOICE":
                choice_text = data.get("choice")
                await session_manager.handle_choice(websocket, choice_text)
                
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
        try:
            await websocket.send_json({
                "type": "ERROR",
                "message": str(e)
            })
        except:
            pass

# Dashboard Mock Endpoints
@app.get("/api/dashboard/stats")
async def get_dashboard_stats():
    return {
        "total_sessions": 12,
        "total_duration_minutes": 145,
        "average_bond_score": "0.8"
    }

@app.get("/api/dashboard/duration-chart")
async def get_dashboard_duration():
    return {"data": []}

@app.get("/api/dashboard/leadership-chart")
async def get_dashboard_leadership():
    return {"data": []}

@app.get("/api/dashboard/sessions")
async def get_dashboard_sessions():
    return {"sessions": []}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting TwinSpark API Server on port 8000...")
    uvicorn.run("api.session_manager:app", host="0.0.0.0", port=8000, reload=True)
