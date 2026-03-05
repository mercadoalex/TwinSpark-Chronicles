"""
Database Module
SQLAlchemy-based database layer for TwinSpark Chronicles.
Supports both SQLite (local development) and PostgreSQL (production).
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.pool import StaticPool
from datetime import datetime
from typing import Optional, List, Dict, Any
import os

Base = declarative_base()


# ==================== MODELS ====================

class Child(Base):
    """Child profile table"""
    __tablename__ = "children"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=False)
    gender = Column(String(20))
    avatar_url = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    personality_traits = relationship("PersonalityTrait", back_populates="child", cascade="all, delete-orphan")
    session_participants = relationship("SessionParticipant", back_populates="child")
    decisions = relationship("Decision", back_populates="child")
    emotions = relationship("EmotionSnapshot", back_populates="child")
    owned_items = relationship("UniverseItem", back_populates="owner")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PersonalityTrait(Base):
    """Personality traits with strength tracking over time"""
    __tablename__ = "personality_traits"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    trait = Column(String(50), nullable=False)  # e.g., "bold", "cautious", "creative"
    strength = Column(Float, default=1.0)  # 0.0 to 1.0
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    child = relationship("Child", back_populates="personality_traits")
    
    def to_dict(self) -> Dict:
        return {
            "trait": self.trait,
            "strength": self.strength,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None
        }


class StorySession(Base):
    """Story session table"""
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    language = Column(String(10), default="en")
    
    # Relationships
    participants = relationship("SessionParticipant", back_populates="session", cascade="all, delete-orphan")
    story_beats = relationship("StoryBeat", back_populates="session", cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="session", cascade="all, delete-orphan")
    emotions = relationship("EmotionSnapshot", back_populates="session", cascade="all, delete-orphan")
    keepsakes = relationship("Keepsake", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "language": self.language
        }


class SessionParticipant(Base):
    """Links children to sessions"""
    __tablename__ = "session_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    session = relationship("StorySession", back_populates="participants")
    child = relationship("Child", back_populates="session_participants")


class StoryBeat(Base):
    """Individual story beats/moments"""
    __tablename__ = "story_beats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    character = Column(String(100))  # Which child's perspective
    narrative = Column(Text, nullable=False)
    scene_description = Column(Text)
    emotional_tone = Column(String(50))
    
    # Relationships
    session = relationship("StorySession", back_populates="story_beats")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "character": self.character,
            "narrative": self.narrative,
            "scene_description": self.scene_description,
            "emotional_tone": self.emotional_tone
        }


class Decision(Base):
    """Decisions made by children during sessions"""
    __tablename__ = "decisions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    decision = Column(Text, nullable=False)
    outcome = Column(Text)
    
    # Relationships
    session = relationship("StorySession", back_populates="decisions")
    child = relationship("Child", back_populates="decisions")
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "decision": self.decision,
            "outcome": self.outcome
        }


class EmotionSnapshot(Base):
    """Emotional state at a point in time"""
    __tablename__ = "emotions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(Integer, ForeignKey("children.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    emotional_state = Column(String(50), nullable=False)  # "joyful", "calm", "excited", etc.
    confidence = Column(Float, default=1.0)
    
    # Relationships
    session = relationship("StorySession", back_populates="emotions")
    child = relationship("Child", back_populates="emotions")
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "emotional_state": self.emotional_state,
            "confidence": self.confidence
        }


class Keepsake(Base):
    """Generated keepsake images"""
    __tablename__ = "keepsakes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String(500), nullable=False)
    title = Column(String(200))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("StorySession", back_populates="keepsakes")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UniverseLocation(Base):
    """Persistent story world locations"""
    __tablename__ = "universe_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String(500))
    first_discovered = Column(DateTime, default=datetime.utcnow)
    visit_count = Column(Integer, default=0)
    last_visited = Column(DateTime)
    properties = Column(JSON)  # Custom properties as JSON
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "first_discovered": self.first_discovered.isoformat() if self.first_discovered else None,
            "visit_count": self.visit_count,
            "properties": self.properties
        }


class UniverseCharacter(Base):
    """Persistent story world characters"""
    __tablename__ = "universe_characters"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    personality = Column(Text)
    image_url = Column(String(500))
    relationship_level = Column(Integer, default=0)  # 0-100, friendship level
    first_met = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime)
    properties = Column(JSON)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality": self.personality,
            "image_url": self.image_url,
            "relationship_level": self.relationship_level,
            "first_met": self.first_met.isoformat() if self.first_met else None,
            "properties": self.properties
        }


class UniverseItem(Base):
    """Persistent story world items"""
    __tablename__ = "universe_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    image_url = Column(String(500))
    owner_id = Column(Integer, ForeignKey("children.id", ondelete="SET NULL"))
    acquired_at = Column(DateTime, default=datetime.utcnow)
    properties = Column(JSON)
    
    # Relationships
    owner = relationship("Child", back_populates="owned_items")
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "owner_id": self.owner_id,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
            "properties": self.properties
        }


class FamilyPhoto(Base):
    """Uploaded family photos for story integration"""
    __tablename__ = "family_photos"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    styled_path = Column(String(500))  # Path to styled/processed version
    category = Column(String(50))  # "people", "places", "events"
    description = Column(Text)
    tags = Column(JSON)  # Array of tags
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    enabled = Column(Boolean, default=True)  # Can be disabled by parent
    photo_metadata = Column(JSON)  # Face detection data, etc.
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "file_path": self.file_path,
            "styled_path": self.styled_path,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "uploaded_at": self.uploaded_at.isoformat() if self.uploaded_at else None,
            "enabled": self.enabled,
            "photo_metadata": self.photo_metadata
        }


class VoiceRecording(Base):
    """Family voice recordings for narration"""
    __tablename__ = "voice_recordings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    speaker_name = Column(String(100), nullable=False)
    message_type = Column(String(50))  # "greeting", "encouragement", "story_intro", etc.
    transcription = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    enabled = Column(Boolean, default=True)
    voice_metadata = Column(JSON)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "speaker_name": self.speaker_name,
            "message_type": self.message_type,
            "transcription": self.transcription,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
            "enabled": self.enabled,
            "voice_metadata": self.voice_metadata
        }


# ==================== DATABASE CLASS ====================

class Database:
    """
    Database manager for TwinSpark Chronicles.
    Handles connections, sessions, and provides high-level operations.
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            database_url: SQLAlchemy database URL. 
                         Defaults to sqlite:///data/twinspark.db
        """
        if database_url is None:
            # Default to SQLite in data directory
            data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data"
            )
            os.makedirs(data_dir, exist_ok=True)
            database_url = f"sqlite:///{os.path.join(data_dir, 'twinspark.db')}"
        
        self.database_url = database_url
        
        # Create engine
        if database_url.startswith("sqlite"):
            # SQLite-specific settings
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool
            )
        else:
            # PostgreSQL and others
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        print(f"💾 Database initialized: {database_url}")
    
    def create_all_tables(self):
        """Create all tables in the database"""
        Base.metadata.create_all(bind=self.engine)
        print("✅ All database tables created")
    
    def drop_all_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(bind=self.engine)
        print("⚠️  All database tables dropped")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()
        print("💾 Database connection closed")


# ==================== CONVENIENCE FUNCTIONS ====================

def get_database(database_url: Optional[str] = None) -> Database:
    """Get a database instance"""
    return Database(database_url)


# Test and initialization
if __name__ == "__main__":
    print("🧪 Testing Database Module\n")
    
    # Create database
    db = Database()
    db.create_all_tables()
    
    # Test session
    session = db.get_session()
    
    try:
        # Create test child
        child = Child(
            name="Ale",
            age=6,
            gender="girl",
            avatar_url="assets/ale_avatar.png"
        )
        session.add(child)
        session.commit()
        
        # Add personality traits
        traits = [
            PersonalityTrait(child_id=child.id, trait="bold", strength=0.9),
            PersonalityTrait(child_id=child.id, trait="creative", strength=0.8),
            PersonalityTrait(child_id=child.id, trait="leader", strength=0.85)
        ]
        session.add_all(traits)
        session.commit()
        
        print(f"✅ Created child: {child.name}")
        print(f"   Traits: {[t.trait for t in traits]}")
        
        # Query back
        queried_child = session.query(Child).filter_by(name="Ale").first()
        print(f"\n✅ Queried child: {queried_child.name}")
        print(f"   Personality traits:")
        for trait in queried_child.personality_traits:
            print(f"   - {trait.trait}: {trait.strength}")
        
        print("\n✅ Database test successful!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()
        db.close()
