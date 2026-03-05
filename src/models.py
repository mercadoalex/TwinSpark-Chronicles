"""
TwinSpark Chronicles - Core Data Models

Pydantic models for type-safe data structures throughout the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum


class PersonalityTrait(str, Enum):
    """Personality traits detected by the Twin Intelligence Engine."""
    BOLD = "bold"
    CAUTIOUS = "cautious"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"
    EMPATHETIC = "empathetic"
    INDEPENDENT = "independent"
    LEADER = "leader"
    SUPPORTER = "supporter"
    PLAYFUL = "playful"
    THOUGHTFUL = "thoughtful"


class SpiritAnimal(str, Enum):
    """Spirit animals that represent personality archetypes."""
    DRAGON = "dragon"      # Bold, brave, protective
    UNICORN = "unicorn"    # Creative, magical, dreamer
    OWL = "owl"            # Wise, analytical, curious
    DOLPHIN = "dolphin"    # Playful, social, friendly
    FOX = "fox"            # Clever, quick, adventurous
    BEAR = "bear"          # Strong, loyal, caring
    EAGLE = "eagle"        # Free, confident, visionary
    CAT = "cat"            # Independent, mysterious, agile


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
    """Profile for a single child in the twin system."""
    
    id: str = Field(description="Unique identifier for the child")
    name: str = Field(description="Child's name")
    gender: str = Field(description="Child's gender", default="unspecified")
    age: int = Field(description="Child's age in years")
    
    # Rich character identity (NEW!)
    spirit_animal: Optional[SpiritAnimal] = Field(default=None, description="Character's spirit guide")
    favorite_tool: Optional[FavoriteTool] = Field(default=None, description="Signature item")
    favorite_outfit: Optional[FavoriteOutfit] = Field(default=None, description="Adventure style")
    favorite_toy: Optional[FavoriteToy] = Field(default=None, description="Special treasure")
    toy_name: Optional[str] = Field(default=None, description="Custom name for favorite toy")
    favorite_place: Optional[FavoritePlace] = Field(default=None, description="Dream location")
    
    # Personality modeling
    personality_traits: List[PersonalityTrait] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    interests: List[str] = Field(default_factory=list)
    
    # Current state
    current_emotion: EmotionalState = Field(default=EmotionalState.CALM)
    energy_level: float = Field(default=0.5, ge=0.0, le=1.0)
    
    # Character evolution
    character_name: Optional[str] = None
    character_level: int = Field(default=1)
    unlocked_powers: List[str] = Field(default_factory=list)
    
    # Avatar
    avatar_url: Optional[str] = Field(default=None, description="URL to character avatar")
    avatar_type: str = Field(default="ai_generated", description="photo_filtered or ai_generated")
    
    # Analytics
    total_sessions: int = Field(default=0)
    total_stories: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    last_active: datetime = Field(default_factory=datetime.now)


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
