"""
TwinSpark Chronicles - Core Data Models

Pydantic models for type-safe data structures throughout the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum


class PersonalityTrait(str, Enum):
    """Valid personality traits for children"""
    BRAVE = "brave"
    CURIOUS = "curious"
    KIND = "kind"
    CREATIVE = "creative"
    LOGICAL = "logical"
    PLAYFUL = "playful"
    WISE = "wise"
    ADVENTUROUS = "adventurous"
    THOUGHTFUL = "thoughtful"
    ENERGETIC = "energetic"
    CALM = "calm"
    HELPFUL = "helpful"
    FUNNY = "funny"
    SERIOUS = "serious"
    SHY = "shy"
    OUTGOING = "outgoing"
    PATIENT = "patient"
    LEADER = "leader"
    FOLLOWER = "follower"
    IMAGINATIVE = "imaginative"


class SpiritAnimal(str, Enum):
    """Valid spirit animals"""
    DRAGON = "dragon"
    UNICORN = "unicorn"
    OWL = "owl"
    DOLPHIN = "dolphin"
    FOX = "fox"
    BEAR = "bear"
    EAGLE = "eagle"
    CAT = "cat"
    WOLF = "wolf"
    PHOENIX = "phoenix"
    TIGER = "tiger"
    RABBIT = "rabbit"


class FavoriteTool(str, Enum):
    """Signature tools that define problem-solving style."""
    SWORD = "sword"              # Action hero
    BOOK = "book"                # Knowledge seeker
    PAINTBRUSH = "paintbrush"    # Artist creator
    MAGNIFIER = "magnifier"      # Detective mind
    FLUTE = "flute"              # Musician soul
    SHIELD = "shield"            # Protector heart
    WAND = "wand"                # Pure magic
    TOOLKIT = "toolkit"          # Problem solver


class FavoriteOutfit(str, Enum):
    """Adventure style that reflects character identity."""
    ROYAL_CAPE = "royal_cape"         # Leader, confident
    WIZARD_ROBE = "wizard_robe"       # Mysterious, magical
    KNIGHT_ARMOR = "knight_armor"     # Brave, protective
    FLOWER_CROWN = "flower_crown"     # Nature lover
    COLORFUL_SCARF = "colorful_scarf" # Creative, expressive
    EXPLORER_VEST = "explorer_vest"   # Adventurous
    PERFORMER_OUTFIT = "performer_outfit" # Entertaining, bold
    SCIENTIST_COAT = "scientist_coat" # Curious, analytical


class FavoriteToy(str, Enum):
    """Special treasures that provide emotional anchors."""
    TEDDY_BEAR = "teddy_bear"     # Comforting, loyal
    TRAIN_SET = "train_set"       # Builder, organizer
    BOARD_GAME = "board_game"     # Strategic thinker
    SOCCER_BALL = "soccer_ball"   # Active, team player
    ART_SUPPLIES = "art_supplies" # Creative maker
    TELESCOPE = "telescope"       # Dreamer, explorer
    VIDEO_GAME = "video_game"     # Problem solver
    STORYBOOK = "storybook"       # Imagination lover


class FavoritePlace(str, Enum):
    """Dream locations that influence story settings."""
    BEACH = "beach"           # Relaxing, water lover
    MOUNTAINS = "mountains"   # Adventurous, brave
    CASTLE = "castle"         # Royal, historical
    FOREST = "forest"         # Nature connected
    THEME_PARK = "theme_park" # Fun-seeking, excited
    BIG_CITY = "big_city"     # Urban explorer
    CAMPING = "camping"       # Outdoorsy, independent
    ISLAND = "island"         # Peaceful, unique


class EmotionalState(str, Enum):
    """Current emotional state of a child."""
    HAPPY = "happy"
    EXCITED = "excited"
    CALM = "calm"
    CURIOUS = "curious"
    FRUSTRATED = "frustrated"
    SAD = "sad"
    TIRED = "tired"
    ENGAGED = "engaged"


class StoryTheme(str, Enum):
    """Available story themes."""
    FANTASY = "fantasy"
    ADVENTURE = "adventure"
    SCIENCE = "science"
    NATURE = "nature"
    MYSTERY = "mystery"
    FRIENDSHIP = "friendship"
    FAMILY = "family"


class ChildProfile(BaseModel):
    """Profile for a child participant"""
    id: str
    name: str
    gender: str
    age: int
    personality_traits: List[PersonalityTrait] = []
    spirit_animal: SpiritAnimal = SpiritAnimal.DRAGON
    favorite_toy_name: str = "Teddy Bear"
    avatar_url: Optional[str] = None
    
    class Config:
        use_enum_values = True


class RelationshipDynamics(BaseModel):
    """Models the relationship between two siblings."""
    
    child1_id: str
    child2_id: str
    
    # Dynamic patterns
    leadership_balance: float = Field(
        default=0.5, 
        ge=0.0, 
        le=1.0,
        description="0 = child1 always leads, 1 = child2 always leads, 0.5 = balanced"
    )
    
    conflict_resolution_style: Optional[str] = None
    communication_effectiveness: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Shared experiences
    shared_humor_tags: List[str] = Field(default_factory=list)
    successful_collaborations: int = Field(default=0)
    
    # Learning
    complementary_strengths: Dict[str, str] = Field(
        default_factory=dict,
        description="Maps strengths: {child1_strength: child2_strength}"
    )
    
    created_at: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)


class StorySession(BaseModel):
    """A single storytelling session."""
    
    session_id: str
    child1_id: str
    child2_id: str
    
    # Story metadata
    theme: StoryTheme
    title: str
    duration_minutes: int = Field(default=0)
    
    # Session state
    started_at: datetime = Field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    
    # Divergence tracking
    has_divergence: bool = Field(default=False)
    reunion_count: int = Field(default=0)
    
    # Learning outcomes
    skills_practiced: List[str] = Field(default_factory=list)
    emotions_addressed: List[EmotionalState] = Field(default_factory=list)
    
    # Generated content
    generated_images: List[str] = Field(default_factory=list)
    generated_videos: List[str] = Field(default_factory=list)
    keepsake_path: Optional[str] = None


class MultimodalInput(BaseModel):
    """Input data from various sensors."""
    
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Video analysis
    faces_detected: int = Field(default=0)
    child1_emotion: Optional[EmotionalState] = None
    child2_emotion: Optional[EmotionalState] = None
    
    # Audio analysis
    voice_detected: bool = Field(default=False)
    speaker_id: Optional[str] = None
    speech_text: Optional[str] = None
    voice_emotion: Optional[EmotionalState] = None
    
    # Gesture analysis
    gestures_detected: List[str] = Field(default_factory=list)
    
    # Environment
    lighting_level: float = Field(default=0.5, ge=0.0, le=1.0)
    noise_level: float = Field(default=0.5, ge=0.0, le=1.0)


class StoryChoice(BaseModel):
    """A choice point in the story."""
    
    choice_id: str
    prompt: str
    options: List[str]
    child_id: Optional[str] = None  # Which child makes this choice
    selected_option: Optional[str] = None
    timestamp: Optional[datetime] = None


class GeneratedContent(BaseModel):
    """Content generated by AI."""
    
    content_type: Literal["text", "image", "video", "audio"]
    content_path: Optional[str] = None
    content_data: Optional[str] = None
    
    # Metadata
    generation_model: str
    generation_time_seconds: float
    prompt_used: str
    
    # For dual perspective
    perspective: Optional[Literal["child1", "child2", "shared"]] = None
    
    created_at: datetime = Field(default_factory=datetime.now)


class Choice(BaseModel):
    """A choice in the story"""
    id: str
    text: str
    child_id: Optional[str] = None
    requires_cooperation: bool = False


class StoryBeat(BaseModel):
    """A single beat/moment in the story"""
    id: str
    narration: str
    child1_perspective: Optional[str] = None
    child2_perspective: Optional[str] = None
    image_prompt: Optional[str] = None
    audio_cues: List[str] = []
    choices: List[Choice] = []
    requires_cooperation: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)


class SessionState(BaseModel):
    """Current state of a story session"""
    session_id: str
    child1_id: str
    child2_id: str
    current_beat_id: Optional[str] = None
    story_history: List[str] = []
    bond_strength: float = 0.5
    started_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
