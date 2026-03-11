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
import asyncio
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from google.generativeai.types import GenerationConfig
    GENAI_AVAILABLE = True
except ImportError:
    logger.warning("Google Generative AI not available")
    GENAI_AVAILABLE = False
    genai = None

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


class RelationshipState(Enum):
    """States of the sibling relationship"""
    DISCONNECTED = "disconnected"  # Working separately
    COOPERATING = "cooperating"    # Working together
    SYNCHRONIZED = "synchronized"  # In perfect harmony
    CONFLICTED = "conflicted"      # Disagreeing
    SUPPORTIVE = "supportive"      # One helping the other


class EmotionalResonance(Enum):
    """How emotions transfer between siblings"""
    HIGH = "high"      # They feel each other's emotions strongly
    MEDIUM = "medium"  # Some emotional awareness
    LOW = "low"        # Emotionally independent


@dataclass
class SiblingBond:
    """Tracks the emotional and collaborative bond between siblings"""
    child1_id: str
    child2_id: str
    bond_strength: float = 0.5  # 0.0 to 1.0
    current_state: RelationshipState = RelationshipState.DISCONNECTED
    emotional_resonance: EmotionalResonance = EmotionalResonance.MEDIUM
    cooperation_history: List[Dict] = field(default_factory=list)
    empathy_moments: int = 0
    conflict_moments: int = 0
    synchronized_actions: int = 0
    
    def strengthen_bond(self, amount: float = 0.1):
        """Strengthen the bond when siblings cooperate"""
        self.bond_strength = min(1.0, self.bond_strength + amount)
        logger.info(f"💞 Bond strengthened to {self.bond_strength:.2f}")
    
    def weaken_bond(self, amount: float = 0.05):
        """Weaken the bond during conflict"""
        self.bond_strength = max(0.0, self.bond_strength - amount)
        logger.info(f"💔 Bond weakened to {self.bond_strength:.2f}")
    
    def record_cooperation(self, action: str, success: bool):
        """Record a cooperative action"""
        self.cooperation_history.append({
            "action": action,
            "success": success,
            "timestamp": datetime.now(),
            "bond_at_time": self.bond_strength
        })
        if success:
            self.synchronized_actions += 1


@dataclass
class ChildEmotionalState:
    """Real-time emotional state of a child"""
    child_id: str
    primary_emotion: str = "neutral"  # joy, fear, excitement, sadness, anger, wonder
    intensity: float = 0.5  # 0.0 to 1.0
    needs_support: bool = False
    is_supporting_sibling: bool = False
    last_action: Optional[str] = None
    confidence_level: float = 0.5


class TwinIntelligenceEngine:
    """
    Core AI system that models sibling relationships as a dynamic system.
    Uses Gemini to understand:
    1. When siblings need to cooperate vs. act independently
    2. How emotions transfer between them (emotional resonance)
    3. Creating teachable moments for empathy
    4. Balancing challenge to require teamwork
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model = None
        self.sibling_bonds: Dict[Tuple[str, str], SiblingBond] = {}
        self.child_states: Dict[str, ChildEmotionalState] = {}
        
        if GENAI_AVAILABLE and api_key:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash-exp',
                    generation_config=GenerationConfig(
                        temperature=0.8,
                        top_p=0.9,
                        max_output_tokens=4096,
                    ),
                    system_instruction="""You are the Twin Intelligence Engine, an AI that deeply understands sibling dynamics.

Your role is to:
1. **Model Empathy**: Create moments where siblings FEEL each other's emotions
2. **Teach Cooperation**: Design challenges they can only solve together
3. **Balance Independence**: Sometimes they work separately, sometimes together
4. **Emotional Resonance**: When one sibling is scared, the other can sense it
5. **Family Universe**: Their actions affect each other and their shared world

You think in terms of:
- Bond Strength (0-1): How connected are they?
- Emotional States: What is each child feeling RIGHT NOW?
- Cooperation Opportunities: When should they work together?
- Teachable Moments: Chances to learn empathy and teamwork

Always respond with structured analysis of the sibling relationship system."""
                )
                
                self.chat = self.model.start_chat(history=[])
                logger.info("✅ Twin Intelligence Engine initialized with Gemini 2.0")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twin Intelligence: {e}")
                self.model = None
        else:
            logger.warning("⚠️ Twin Intelligence running in MOCK mode")
    
    def register_child(self, child_profile):
        """Register a child in the system"""
        self.child_states[child_profile.id] = ChildEmotionalState(
            child_id=child_profile.id,
            primary_emotion="wonder",
            confidence_level=0.5
        )
        logger.info(f"👶 Registered {child_profile.name} in Twin Intelligence Engine")
    
    def register_relationship(self, child1_id: str, child2_id: str):
        """Register the sibling relationship"""
        bond_key = tuple(sorted([child1_id, child2_id]))
        self.sibling_bonds[bond_key] = SiblingBond(
            child1_id=child1_id,
            child2_id=child2_id,
            bond_strength=0.5,
            current_state=RelationshipState.COOPERATING
        )
        logger.info(f"👫 Registered sibling bond between {child1_id} and {child2_id}")
    
    async def analyze_sibling_dynamics(
        self,
        child1_name: str,
        child1_action: Optional[str],
        child1_emotion: str,
        child2_name: str,
        child2_action: Optional[str],
        child2_emotion: str,
        story_context: str
    ) -> Dict:
        """
        Use Gemini to deeply analyze the current sibling dynamics
        and determine how they should interact next.
        """
        
        bond = self.get_bond("c1", "c2")
        
        prompt = f"""Analyze this sibling interaction in TwinSpark Chronicles:

**CURRENT SITUATION:**
Story Context: {story_context}

**SIBLING STATES:**
{child1_name}:
- Last Action: {child1_action or "waiting"}
- Emotion: {child1_emotion} 
- Confidence: {self.child_states.get("c1", ChildEmotionalState("c1")).confidence_level:.2f}

{child2_name}:
- Last Action: {child2_action or "waiting"}  
- Emotion: {child2_emotion}
- Confidence: {self.child_states.get("c2", ChildEmotionalState("c2")).confidence_level:.2f}

**RELATIONSHIP STATUS:**
Bond Strength: {bond.bond_strength:.2f} / 1.0
Current State: {bond.current_state.value}
Empathy Moments So Far: {bond.empathy_moments}
Synchronized Actions: {bond.synchronized_actions}

**YOUR TASK:**
Analyze their relationship and provide:

1. EMOTIONAL_RESONANCE: Is one child's emotion affecting the other? (YES/NO + explanation)
2. COOPERATION_REQUIRED: Do they NEED each other for the next challenge? (REQUIRED/OPTIONAL/INDEPENDENT)
3. TEACHABLE_MOMENT: Is this a chance to teach empathy? (YES/NO + what lesson)
4. NEXT_CHALLENGE_TYPE: What kind of interaction should happen next?
   - SYNCHRONIZED: They must act at the exact same time
   - COMPLEMENTARY: Each has a different role that supports the other
   - EMOTIONAL_SUPPORT: One helps the other through fear/sadness
   - INDEPENDENT_THEN_SHARE: They explore separately, then compare discoveries
5. BOND_CHANGE: Should bond strengthen (+0.1), weaken (-0.1), or stay (0)?

Format your response as:
EMOTIONAL_RESONANCE: [YES/NO]
EXPLANATION: [how their emotions connect]
COOPERATION_REQUIRED: [REQUIRED/OPTIONAL/INDEPENDENT]
TEACHABLE_MOMENT: [YES/NO]
LESSON: [what they can learn]
NEXT_CHALLENGE_TYPE: [type]
CHALLENGE_DESCRIPTION: [brief description]
BOND_CHANGE: [+0.1/-0.1/0]
"""

        if not self.model:
            # Mock response
            return {
                "emotional_resonance": True,
                "cooperation_required": "REQUIRED",
                "teachable_moment": True,
                "lesson": "They need to work together to overcome the obstacle",
                "next_challenge_type": "SYNCHRONIZED",
                "challenge_description": "They must both place their hands on the magic door at the same time",
                "bond_change": 0.1
            }
        
        try:
            response = await asyncio.to_thread(
                self.chat.send_message,
                prompt
            )
            
            # Parse Gemini's analysis
            analysis = self._parse_dynamics_response(response.text)
            
            # Apply bond changes
            if analysis["bond_change"] != 0:
                if analysis["bond_change"] > 0:
                    bond.strengthen_bond(abs(analysis["bond_change"]))
                else:
                    bond.weaken_bond(abs(analysis["bond_change"]))
            
            # Update relationship state
            if analysis["cooperation_required"] == "REQUIRED":
                bond.current_state = RelationshipState.SYNCHRONIZED
            elif analysis["cooperation_required"] == "OPTIONAL":
                bond.current_state = RelationshipState.COOPERATING
            else:
                bond.current_state = RelationshipState.DISCONNECTED
            
            # Track empathy moments
            if analysis["teachable_moment"]:
                bond.empathy_moments += 1
            
            logger.info(f"""
╔════════════════════════════════════════════╗
║   TWIN INTELLIGENCE ANALYSIS               ║
╠════════════════════════════════════════════╣
║ Emotional Resonance: {analysis['emotional_resonance']}
║ Cooperation: {analysis['cooperation_required']}
║ Teachable Moment: {analysis['teachable_moment']}
║ Bond Strength: {bond.bond_strength:.2f}
║ Next Challenge: {analysis['next_challenge_type']}
╚════════════════════════════════════════════╝
            """)
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Dynamics analysis failed: {e}", exc_info=True)
            return {
                "emotional_resonance": True,
                "cooperation_required": "REQUIRED",
                "teachable_moment": True,
                "lesson": "Work together",
                "next_challenge_type": "SYNCHRONIZED",
                "challenge_description": "Cooperate to proceed",
                "bond_change": 0.1
            }
    
    def _parse_dynamics_response(self, text: str) -> Dict:
        """Parse Gemini's structured response about sibling dynamics"""
        lines = text.strip().split('\n')
        analysis = {
            "emotional_resonance": False,
            "explanation": "",
            "cooperation_required": "OPTIONAL",
            "teachable_moment": False,
            "lesson": "",
            "next_challenge_type": "COMPLEMENTARY",
            "challenge_description": "",
            "bond_change": 0.0
        }
        
        for line in lines:
            if "EMOTIONAL_RESONANCE:" in line:
                analysis["emotional_resonance"] = "YES" in line.upper()
            elif "EXPLANATION:" in line:
                analysis["explanation"] = line.split(":", 1)[1].strip()
            elif "COOPERATION_REQUIRED:" in line:
                if "REQUIRED" in line.upper():
                    analysis["cooperation_required"] = "REQUIRED"
                elif "INDEPENDENT" in line.upper():
                    analysis["cooperation_required"] = "INDEPENDENT"
            elif "TEACHABLE_MOMENT:" in line:
                analysis["teachable_moment"] = "YES" in line.upper()
            elif "LESSON:" in line:
                analysis["lesson"] = line.split(":", 1)[1].strip()
            elif "NEXT_CHALLENGE_TYPE:" in line:
                analysis["next_challenge_type"] = line.split(":", 1)[1].strip()
            elif "CHALLENGE_DESCRIPTION:" in line:
                analysis["challenge_description"] = line.split(":", 1)[1].strip()
            elif "BOND_CHANGE:" in line:
                change_str = line.split(":", 1)[1].strip()
                try:
                    analysis["bond_change"] = float(change_str)
                except:
                    analysis["bond_change"] = 0.0
        
        return analysis
    
    def get_bond(self, child1_id: str, child2_id: str) -> SiblingBond:
        """Get the bond between two siblings"""
        bond_key = tuple(sorted([child1_id, child2_id]))
        return self.sibling_bonds.get(bond_key, SiblingBond(child1_id, child2_id))
    
    def update_emotional_state(
        self,
        child_id: str,
        emotion: str,
        intensity: float,
        action: Optional[str] = None
    ):
        """Update a child's emotional state"""
        if child_id in self.child_states:
            state = self.child_states[child_id]
            state.primary_emotion = emotion
            state.intensity = intensity
            if action:
                state.last_action = action
            
            logger.info(f"😊 {child_id} now feeling {emotion} (intensity: {intensity:.2f})")
            
            # Check for emotional resonance with sibling
            self._check_emotional_resonance(child_id)
    
    def _check_emotional_resonance(self, child_id: str):
        """Check if this child's emotion affects their sibling"""
        state = self.child_states.get(child_id)
        if not state:
            return
        
        # Find sibling
        sibling_id = "c2" if child_id == "c1" else "c1"
        sibling_state = self.child_states.get(sibling_id)
        
        if not sibling_state:
            return
        
        bond = self.get_bond(child_id, sibling_id)
        
        # High bond strength = emotions transfer
        if bond.bond_strength > 0.7 and state.intensity > 0.7:
            logger.info(f"💫 EMOTIONAL RESONANCE: {sibling_id} is feeling {child_id}'s {state.primary_emotion}")
            
            # Sibling feels a portion of the emotion
            resonance_strength = bond.bond_strength * 0.5
            sibling_state.intensity = min(1.0, sibling_state.intensity + (state.intensity * resonance_strength))
    
    def record_cooperation(self, child1_id: str, child2_id: str, action: str, success: bool):
        """Record a cooperative action"""
        bond = self.get_bond(child1_id, child2_id)
        bond.record_cooperation(action, success)
        
        if success:
            bond.strengthen_bond(0.1)
            logger.info(f"🤝 Successful cooperation: {action}")
        else:
            logger.info(f"😔 Cooperation failed: {action}")
