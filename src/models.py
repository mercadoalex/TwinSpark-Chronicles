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
