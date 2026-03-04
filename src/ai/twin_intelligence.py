"""
TwinSpark Chronicles - Twin Intelligence Engine

The revolutionary AI system that models sibling relationships as dynamic systems.
This is the CORE DIFFERENTIATOR of TwinSpark Chronicles.

Architecture:
- Layer 1: Individual Profile Learning
- Layer 2: Relationship Dynamic Mapping
- Layer 3: Complementary Skills Discovery
- Layer 4: Adaptive Narrative Generation
"""

import logging
import sys
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    ChildProfile, 
    RelationshipDynamics, 
    PersonalityTrait,
    EmotionalState,
    MultimodalInput,
    StorySession
)

logger = logging.getLogger(__name__)


class TwinIntelligenceEngine:
    """
    The heart of TwinSpark Chronicles - models and nurtures sibling bonds.
    
    This engine observes behavioral patterns across multiple sessions and builds
    deep personality models for each child and their relationship dynamics.
    """
    
    def __init__(self):
        self.profiles: Dict[str, ChildProfile] = {}
        self.relationships: Dict[Tuple[str, str], RelationshipDynamics] = {}
        self.session_history: List[StorySession] = []
        
    # ==================== LAYER 1: INDIVIDUAL PROFILE LEARNING ====================
    
    def analyze_voice_patterns(
        self, 
        child_id: str, 
        voice_samples: List[MultimodalInput]
    ) -> Dict[str, float]:
        """
        Analyze voice characteristics to infer personality traits.
        
        Metrics:
        - Volume: Bold vs. Cautious
        - Speed: Excited vs. Thoughtful
        - Tone variation: Playful vs. Serious
        """
        if not voice_samples:
            return {}
        
        # Calculate average characteristics
        avg_volume = sum(1 if sample.voice_detected else 0 for sample in voice_samples) / len(voice_samples)
        
        # Infer traits (simplified - in production, use ML models)
        traits = {}
        
        if avg_volume > 0.7:
            traits[PersonalityTrait.BOLD] = avg_volume
        elif avg_volume < 0.3:
            traits[PersonalityTrait.CAUTIOUS] = 1 - avg_volume
            
        return traits
    
    def analyze_gesture_patterns(
        self, 
        child_id: str, 
        gesture_samples: List[MultimodalInput]
    ) -> Dict[str, float]:
        """
        Analyze physical gestures to understand personality.
        
        Metrics:
        - Large movements: Bold, Playful
        - Precise movements: Analytical, Thoughtful
        - Frequency: Energetic vs. Calm
        """
        if not gesture_samples:
            return {}
        
        traits = {}
        
        # Count gesture frequency
        total_gestures = sum(len(sample.gestures_detected) for sample in gesture_samples)
        avg_gestures = total_gestures / len(gesture_samples)
        
        if avg_gestures > 3:
            traits[PersonalityTrait.PLAYFUL] = min(avg_gestures / 5, 1.0)
        
        return traits
    
    def analyze_decision_patterns(
        self, 
        child_id: str, 
        sessions: List[StorySession]
    ) -> Dict[str, float]:
        """
        Analyze story choices to understand decision-making style.
        
        Patterns:
        - Risky choices: Bold, Independent
        - Safe choices: Cautious, Thoughtful
        - Creative solutions: Creative, Analytical
        """
        if not sessions:
            return {}
        
        # In production, track actual choices made
        # For now, return placeholder
        return {
            PersonalityTrait.CREATIVE: 0.6,
            PersonalityTrait.THOUGHTFUL: 0.5
        }
    
    def update_personality_profile(
        self, 
        child_id: str, 
        new_data: List[MultimodalInput]
    ) -> ChildProfile:
        """
        Update a child's personality profile based on new observational data.
        
        This is called after each session to continuously refine the model.
        """
        if child_id not in self.profiles:
            logger.warning(f"Child {child_id} not found in profiles")
            return None
        
        profile = self.profiles[child_id]
        
        # Analyze different data sources
        voice_traits = self.analyze_voice_patterns(child_id, new_data)
        gesture_traits = self.analyze_gesture_patterns(child_id, new_data)
        
        # Update traits with weighted averaging (new data has 30% weight)
        for trait, confidence in {**voice_traits, **gesture_traits}.items():
            if trait not in profile.personality_traits:
                if confidence > 0.6:  # Threshold for adding new trait
                    profile.personality_traits.append(trait)
        
        profile.last_active = datetime.now()
        logger.info(f"Updated personality profile for {profile.name}: {profile.personality_traits}")
        
        return profile
    
    # ==================== LAYER 2: RELATIONSHIP DYNAMIC MAPPING ====================
    
    def analyze_leadership_patterns(
        self,
        child1_id: str,
        child2_id: str,
        sessions: List[StorySession]
    ) -> float:
        """
        Determine leadership balance between siblings.
        
        Returns: 0-1 scale where 0.5 is perfectly balanced
        """
        if not sessions:
            return 0.5  # Start balanced
        
        # In production: track who initiates, who makes decisions, who drives action
        # For now, simulate based on personality traits
        
        child1 = self.profiles.get(child1_id)
        child2 = self.profiles.get(child2_id)
        
        if not child1 or not child2:
            return 0.5
        
        # Bold and Leader traits indicate leadership tendency
        child1_leadership = (
            (PersonalityTrait.BOLD in child1.personality_traits) * 0.3 +
            (PersonalityTrait.LEADER in child1.personality_traits) * 0.5
        )
        
        child2_leadership = (
            (PersonalityTrait.BOLD in child2.personality_traits) * 0.3 +
            (PersonalityTrait.LEADER in child2.personality_traits) * 0.5
        )
        
        total = child1_leadership + child2_leadership
        if total == 0:
            return 0.5
        
        return child2_leadership / total
    
    def detect_complementary_strengths(
        self,
        child1_id: str,
        child2_id: str
    ) -> Dict[str, str]:
        """
        Identify how siblings' strengths complement each other.
        
        Returns: Dict mapping child1's strength to child2's complementary strength
        """
        child1 = self.profiles.get(child1_id)
        child2 = self.profiles.get(child2_id)
        
        if not child1 or not child2:
            return {}
        
        # Define complementary trait pairs
        complementary_pairs = {
            PersonalityTrait.BOLD: PersonalityTrait.CAUTIOUS,
            PersonalityTrait.CREATIVE: PersonalityTrait.ANALYTICAL,
            PersonalityTrait.LEADER: PersonalityTrait.SUPPORTER,
            PersonalityTrait.PLAYFUL: PersonalityTrait.THOUGHTFUL,
        }
        
        complements = {}
        
        for trait1 in child1.personality_traits:
            complement = complementary_pairs.get(trait1)
            if complement and complement in child2.personality_traits:
                complements[trait1.value] = complement.value
        
        # Also check reverse
        for trait2 in child2.personality_traits:
            complement = complementary_pairs.get(trait2)
            if complement and complement in child1.personality_traits:
                complements[complement.value] = trait2.value
        
        return complements
    
    def update_relationship_dynamics(
        self,
        child1_id: str,
        child2_id: str,
        session: StorySession
    ) -> RelationshipDynamics:
        """
        Update relationship model after a session.
        """
        key = (child1_id, child2_id)
        
        if key not in self.relationships:
            # Create new relationship model
            self.relationships[key] = RelationshipDynamics(
                child1_id=child1_id,
                child2_id=child2_id
            )
        
        dynamics = self.relationships[key]
        
        # Update leadership balance
        relevant_sessions = [s for s in self.session_history if 
                           s.child1_id == child1_id and s.child2_id == child2_id]
        dynamics.leadership_balance = self.analyze_leadership_patterns(
            child1_id, child2_id, relevant_sessions
        )
        
        # Update complementary strengths
        dynamics.complementary_strengths = self.detect_complementary_strengths(
            child1_id, child2_id
        )
        
        # Track successful collaborations
        if session.reunion_count > 0:
            dynamics.successful_collaborations += session.reunion_count
        
        dynamics.last_updated = datetime.now()
        
        logger.info(f"Updated relationship dynamics: leadership_balance={dynamics.leadership_balance:.2f}")
        
        return dynamics
    
    # ==================== LAYER 3: COMPLEMENTARY SKILLS DISCOVERY ====================
    
    def assign_complementary_powers(
        self,
        child1_id: str,
        child2_id: str
    ) -> Tuple[List[str], List[str]]:
        """
        Assign powers/abilities to each child that complement each other.
        
        Returns: (child1_powers, child2_powers)
        
        Key principle: Powers should require teamwork, not competition.
        """
        child1 = self.profiles.get(child1_id)
        child2 = self.profiles.get(child2_id)
        
        if not child1 or not child2:
            return ([], [])
        
        # Power assignment based on personality
        power_mapping = {
            PersonalityTrait.BOLD: ["super_strength", "fire_magic", "shield_breaking"],
            PersonalityTrait.CAUTIOUS: ["invisibility", "shield_creation", "trap_detection"],
            PersonalityTrait.CREATIVE: ["shape_shifting", "illusion_magic", "artistic_creation"],
            PersonalityTrait.ANALYTICAL: ["pattern_reading", "puzzle_solving", "tech_mastery"],
            PersonalityTrait.EMPATHETIC: ["healing", "animal_communication", "emotion_reading"],
            PersonalityTrait.PLAYFUL: ["super_speed", "flight", "laughter_magic"],
        }
        
        child1_powers = []
        child2_powers = []
        
        # Assign based on traits
        for trait in child1.personality_traits[:2]:  # Top 2 traits
            if trait in power_mapping:
                child1_powers.extend(power_mapping[trait][:1])
        
        for trait in child2.personality_traits[:2]:
            if trait in power_mapping:
                child2_powers.extend(power_mapping[trait][:1])
        
        # Ensure complementarity
        if not child1_powers:
            child1_powers = ["light_magic"]
        if not child2_powers:
            child2_powers = ["shadow_magic"]
        
        return (child1_powers, child2_powers)
    
    # ==================== LAYER 4: ADAPTIVE NARRATIVE GENERATION ====================
    
    def should_flip_roles(
        self,
        child1_id: str,
        child2_id: str
    ) -> bool:
        """
        Decide if roles should be flipped to balance relationship dynamics.
        
        Returns: True if child2 should lead this session
        """
        key = (child1_id, child2_id)
        
        if key not in self.relationships:
            return False  # Keep natural order for first sessions
        
        dynamics = self.relationships[key]
        
        # Flip if leadership is too imbalanced (< 0.3 or > 0.7)
        if dynamics.leadership_balance < 0.3:
            logger.info("Flipping roles: child1 leads too often")
            return True
        elif dynamics.leadership_balance > 0.7:
            logger.info("Flipping roles: child2 leads too often")
            return False
        
        # Otherwise, slight randomization with personality bias
        return dynamics.leadership_balance > 0.5
    
    def adapt_story_difficulty(
        self,
        child_id: str,
        current_emotion: EmotionalState
    ) -> float:
        """
        Adjust story challenge level based on emotional state.
        
        Returns: Difficulty multiplier (0.5 = easier, 1.5 = harder)
        """
        if current_emotion == EmotionalState.FRUSTRATED:
            return 0.7  # Make it easier - give them a win
        elif current_emotion == EmotionalState.SAD:
            return 0.6  # Make it easier and uplifting
        elif current_emotion == EmotionalState.EXCITED:
            return 1.2  # Can handle more challenge
        elif current_emotion == EmotionalState.TIRED:
            return 0.8  # Slow it down
        else:
            return 1.0  # Normal difficulty
    
    def generate_story_directive(
        self,
        child1_id: str,
        child2_id: str,
        theme: str
    ) -> Dict:
        """
        Generate high-level story parameters for the narrative engine.
        
        This is where the Twin Intelligence informs story generation.
        """
        child1 = self.profiles.get(child1_id)
        child2 = self.profiles.get(child2_id)
        
        if not child1 or not child2:
            return {}
        
        # Get relationship dynamics
        key = (child1_id, child2_id)
        dynamics = self.relationships.get(key)
        
        # Determine role distribution
        flip_roles = self.should_flip_roles(child1_id, child2_id)
        
        # Get complementary powers
        powers1, powers2 = self.assign_complementary_powers(child1_id, child2_id)
        
        # Adapt to emotional states
        difficulty1 = self.adapt_story_difficulty(child1_id, child1.current_emotion)
        difficulty2 = self.adapt_story_difficulty(child2_id, child2.current_emotion)
        
        directive = {
            "child1": {
                "name": child1.name,
                "role": "leader" if not flip_roles else "supporter",
                "powers": powers1,
                "difficulty_multiplier": difficulty1,
                "personality_hints": [trait.value for trait in child1.personality_traits[:3]],
                "emotional_state": child1.current_emotion.value,
            },
            "child2": {
                "name": child2.name,
                "role": "supporter" if not flip_roles else "leader",
                "powers": powers2,
                "difficulty_multiplier": difficulty2,
                "personality_hints": [trait.value for trait in child2.personality_traits[:3]],
                "emotional_state": child2.current_emotion.value,
            },
            "relationship": {
                "complementary_strengths": dynamics.complementary_strengths if dynamics else {},
                "requires_teamwork": True,
                "divergence_recommended": dynamics and dynamics.communication_effectiveness > 0.7,
            },
            "theme": theme,
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(f"Generated story directive with role flip: {flip_roles}")
        
        return directive
    
    # ==================== PUBLIC API ====================
    
    def register_child(self, child: ChildProfile) -> None:
        """Register a new child in the system."""
        self.profiles[child.id] = child
        logger.info(f"Registered child: {child.name} (age {child.age})")
    
    def register_relationship(self, child1_id: str, child2_id: str) -> None:
        """Register a sibling relationship."""
        key = (child1_id, child2_id)
        if key not in self.relationships:
            self.relationships[key] = RelationshipDynamics(
                child1_id=child1_id,
                child2_id=child2_id
            )
            logger.info(f"Registered relationship: {child1_id} <-> {child2_id}")
    
    def process_session_data(
        self,
        session: StorySession,
        multimodal_data: List[MultimodalInput]
    ) -> None:
        """Process data from a completed session to update all models."""
        self.session_history.append(session)
        
        # Update individual profiles
        child1_data = [d for d in multimodal_data if d.speaker_id == session.child1_id]
        child2_data = [d for d in multimodal_data if d.speaker_id == session.child2_id]
        
        if child1_data:
            self.update_personality_profile(session.child1_id, child1_data)
        if child2_data:
            self.update_personality_profile(session.child2_id, child2_data)
        
        # Update relationship dynamics
        self.update_relationship_dynamics(
            session.child1_id,
            session.child2_id,
            session
        )
        
        logger.info(f"Processed session data for session: {session.session_id}")
