"""
State Manager Module
Handles session state persistence, profile updates, and story history.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import asdict

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ChildProfile, PersonalityTrait, EmotionalState


class StateManager:
    """
    Manages persistent state for TwinSpark Chronicles:
    - Child profiles and personality evolution
    - Session history
    - Story universe continuity
    - Parent preferences
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        Args:
            data_dir: Directory for storing state files. Defaults to data/
        """
        if data_dir is None:
            self.data_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "data"
            )
        else:
            self.data_dir = data_dir
        
        # Create subdirectories
        self.profiles_dir = os.path.join(self.data_dir, "profiles")
        self.sessions_dir = os.path.join(self.data_dir, "sessions")
        self.universe_dir = os.path.join(self.data_dir, "universe")
        
        for directory in [self.profiles_dir, self.sessions_dir, self.universe_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # In-memory cache
        self._profiles_cache: Dict[str, ChildProfile] = {}
        self._current_session: Optional[Dict] = None
        
        print(f"💾 State Manager initialized (data: {self.data_dir})")
    
    # ==================== PROFILE MANAGEMENT ====================
    
    def save_profile(self, profile: ChildProfile) -> bool:
        """
        Save or update a child profile.
        
        Args:
            profile: ChildProfile to save
            
        Returns:
            True if successful
        """
        try:
            profile_dict = {
                'name': profile.name,
                'age': profile.age,
                'gender': profile.gender,
                'personality_traits': [trait.value for trait in profile.personality_traits],
                'emotional_state': profile.emotional_state.value,
                'preferences': profile.preferences,
                'avatar_url': profile.avatar_url,
                'created_at': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            }
            
            profile_path = self._get_profile_path(profile.name)
            
            # If profile exists, preserve creation date
            if os.path.exists(profile_path):
                existing = self._load_json(profile_path)
                if existing and 'created_at' in existing:
                    profile_dict['created_at'] = existing['created_at']
            
            self._save_json(profile_path, profile_dict)
            self._profiles_cache[profile.name] = profile
            
            print(f"✅ Saved profile: {profile.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving profile: {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[ChildProfile]:
        """
        Load a child profile by name.
        
        Args:
            name: Child's name
            
        Returns:
            ChildProfile or None if not found
        """
        # Check cache first
        if name in self._profiles_cache:
            return self._profiles_cache[name]
        
        try:
            profile_path = self._get_profile_path(name)
            
            if not os.path.exists(profile_path):
                return None
            
            data = self._load_json(profile_path)
            
            if not data:
                return None
            
            # Reconstruct ChildProfile
            profile = ChildProfile(
                name=data['name'],
                age=data['age'],
                gender=data.get('gender', 'other'),
                personality_traits=[
                    PersonalityTrait(trait) for trait in data['personality_traits']
                ],
                emotional_state=EmotionalState(data.get('emotional_state', 'calm')),
                preferences=data.get('preferences', {}),
                avatar_url=data.get('avatar_url')
            )
            
            self._profiles_cache[name] = profile
            print(f"✅ Loaded profile: {name}")
            
            return profile
            
        except Exception as e:
            print(f"❌ Error loading profile {name}: {e}")
            return None
    
    def list_profiles(self) -> List[str]:
        """Get list of all saved profile names"""
        try:
            files = os.listdir(self.profiles_dir)
            return [f.replace('.json', '') for f in files if f.endswith('.json')]
        except Exception as e:
            print(f"❌ Error listing profiles: {e}")
            return []
    
    def update_personality_traits(self, name: str, new_traits: List[PersonalityTrait]) -> bool:
        """
        Update personality traits for a child (tracks evolution over time).
        
        Args:
            name: Child's name
            new_traits: Updated list of personality traits
            
        Returns:
            True if successful
        """
        profile = self.load_profile(name)
        if not profile:
            return False
        
        profile.personality_traits = new_traits
        return self.save_profile(profile)
    
    def update_emotional_state(self, name: str, state: EmotionalState) -> bool:
        """Update current emotional state for a child"""
        profile = self.load_profile(name)
        if not profile:
            return False
        
        profile.emotional_state = state
        return self.save_profile(profile)
    
    # ==================== SESSION MANAGEMENT ====================
    
    def start_session(
        self, 
        child1_name: str, 
        child2_name: str,
        language: str = "en"
    ) -> str:
        """
        Start a new story session.
        
        Args:
            child1_name: First child's name
            child2_name: Second child's name
            language: Language code (en, es, etc.)
            
        Returns:
            Session ID
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._current_session = {
            'session_id': session_id,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'children': [child1_name, child2_name],
            'language': language,
            'story_beats': [],
            'decisions': [],
            'emotions_timeline': [],
            'keepsake_path': None,
            'total_duration_seconds': 0
        }
        
        print(f"🎬 Started session: {session_id}")
        return session_id
    
    def add_story_beat(self, beat: Dict[str, Any]):
        """Add a story beat to the current session"""
        if not self._current_session:
            print("⚠️ No active session")
            return
        
        # Handle both dict and object inputs
        if isinstance(beat, dict):
            beat_dict = {
                'timestamp': datetime.now().isoformat(),
                'narrative': beat.get('narrative', ''),
                'character': beat.get('character', ''),
                'scene_description': beat.get('scene_description', ''),
                'emotional_tone': beat.get('emotional_tone', 'neutral')
            }
        else:
            beat_dict = {
                'timestamp': datetime.now().isoformat(),
                'narrative': beat.narrative,
                'character': beat.character,
                'scene_description': beat.scene_description,
                'emotional_tone': beat.emotional_tone.value if hasattr(beat.emotional_tone, 'value') else str(beat.emotional_tone)
            }
        
        self._current_session['story_beats'].append(beat_dict)
    
    def add_decision(self, child_name: str, decision: str, outcome: str):
        """Record a child's decision and its outcome"""
        if not self._current_session:
            return
        
        self._current_session['decisions'].append({
            'timestamp': datetime.now().isoformat(),
            'child': child_name,
            'decision': decision,
            'outcome': outcome
        })
    
    def add_emotion_snapshot(self, emotions: Dict[str, EmotionalState]):
        """Record emotional states at a point in time"""
        if not self._current_session:
            return
        
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'emotions': {
                name: state.value for name, state in emotions.items()
            }
        }
        
        self._current_session['emotions_timeline'].append(snapshot)
    
    def end_session(self, keepsake_path: Optional[str] = None) -> bool:
        """
        End the current session and save it.
        
        Args:
            keepsake_path: Path to generated keepsake image
            
        Returns:
            True if successful
        """
        if not self._current_session:
            print("⚠️ No active session to end")
            return False
        
        try:
            # Calculate duration
            start_time = datetime.fromisoformat(self._current_session['start_time'])
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self._current_session['end_time'] = end_time.isoformat()
            self._current_session['total_duration_seconds'] = duration
            self._current_session['keepsake_path'] = keepsake_path
            
            # Save session
            session_id = self._current_session['session_id']
            session_path = os.path.join(self.sessions_dir, f"{session_id}.json")
            self._save_json(session_path, self._current_session)
            
            print(f"💾 Saved session: {session_id} ({duration:.0f}s)")
            
            self._current_session = None
            return True
            
        except Exception as e:
            print(f"❌ Error ending session: {e}")
            return False
    
    def get_session_history(self, child_name: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """
        Get recent session history.
        
        Args:
            child_name: Filter by child name (optional)
            limit: Maximum number of sessions to return
            
        Returns:
            List of session summaries
        """
        try:
            sessions = []
            
            # Get all session files
            files = sorted(
                [f for f in os.listdir(self.sessions_dir) if f.endswith('.json')],
                reverse=True  # Most recent first
            )
            
            for filename in files[:limit]:
                session_path = os.path.join(self.sessions_dir, filename)
                session = self._load_json(session_path)
                
                if session:
                    # Filter by child name if specified
                    if child_name and child_name not in session.get('children', []):
                        continue
                    
                    sessions.append(session)
            
            return sessions
            
        except Exception as e:
            print(f"❌ Error loading session history: {e}")
            return []
    
    def get_current_session(self) -> Optional[Dict]:
        """Get the current active session"""
        return self._current_session
    
    # ==================== UNIVERSE MANAGEMENT ====================
    
    def save_story_element(self, element_type: str, element_id: str, data: Dict):
        """
        Save a story universe element (location, character, item, etc.)
        
        Args:
            element_type: Type of element (location, character, item, etc.)
            element_id: Unique identifier
            data: Element data
        """
        try:
            type_dir = os.path.join(self.universe_dir, element_type)
            os.makedirs(type_dir, exist_ok=True)
            
            element_path = os.path.join(type_dir, f"{element_id}.json")
            self._save_json(element_path, data)
            
            print(f"✅ Saved {element_type}: {element_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error saving story element: {e}")
            return False
    
    def load_story_element(self, element_type: str, element_id: str) -> Optional[Dict]:
        """Load a story universe element"""
        try:
            element_path = os.path.join(self.universe_dir, element_type, f"{element_id}.json")
            return self._load_json(element_path)
        except Exception as e:
            print(f"❌ Error loading story element: {e}")
            return None
    
    def list_story_elements(self, element_type: str) -> List[str]:
        """List all elements of a given type"""
        try:
            type_dir = os.path.join(self.universe_dir, element_type)
            if not os.path.exists(type_dir):
                return []
            
            files = os.listdir(type_dir)
            return [f.replace('.json', '') for f in files if f.endswith('.json')]
            
        except Exception as e:
            print(f"❌ Error listing story elements: {e}")
            return []
    
    # ==================== HELPER METHODS ====================
    
    def _get_profile_path(self, name: str) -> str:
        """Get file path for a profile"""
        safe_name = name.lower().replace(' ', '_')
        return os.path.join(self.profiles_dir, f"{safe_name}.json")
    
    def _save_json(self, path: str, data: Dict) -> bool:
        """Save data as JSON"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving JSON to {path}: {e}")
            return False
    
    def _load_json(self, path: str) -> Optional[Dict]:
        """Load data from JSON"""
        try:
            if not os.path.exists(path):
                return None
            
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading JSON from {path}: {e}")
            return None
    
    def get_stats(self) -> Dict:
        """Get statistics about stored data"""
        return {
            'total_profiles': len(self.list_profiles()),
            'total_sessions': len([f for f in os.listdir(self.sessions_dir) if f.endswith('.json')]),
            'story_elements': {
                element_type: len(self.list_story_elements(element_type))
                for element_type in ['locations', 'characters', 'items']
            }
        }


# Test function
if __name__ == "__main__":
    print("💾 State Manager Test\n")
    
    manager = StateManager()
    
    # Create test profiles
    ale = ChildProfile(
        name="Ale",
        age=6,
        gender="girl",
        personality_traits=[
            PersonalityTrait.BOLD,
            PersonalityTrait.LEADER,
            PersonalityTrait.CREATIVE
        ],
        emotional_state=EmotionalState.EXCITED
    )
    
    sofi = ChildProfile(
        name="Sofi",
        age=6,
        gender="girl",
        personality_traits=[
            PersonalityTrait.CAUTIOUS,
            PersonalityTrait.ANALYTICAL,
            PersonalityTrait.KIND
        ],
        emotional_state=EmotionalState.CALM
    )
    
    # Save profiles
    print("📝 Saving profiles...")
    manager.save_profile(ale)
    manager.save_profile(sofi)
    
    # Start session
    print("\n🎬 Starting session...")
    session_id = manager.start_session("Ale", "Sofi", language="en")
    
    # Simulate some activity
    manager.add_emotion_snapshot({
        "Ale": EmotionalState.EXCITED,
        "Sofi": EmotionalState.CURIOUS
    })
    
    manager.add_decision("Ale", "explore the cave", "discovered treasure")
    manager.add_decision("Sofi", "decode the map", "revealed secret path")
    
    # End session
    print("\n💾 Ending session...")
    manager.end_session()
    
    # Show stats
    print("\n📊 Stats:")
    stats = manager.get_stats()
    print(json.dumps(stats, indent=2))
    
    # Show session history
    print("\n📚 Session History:")
    history = manager.get_session_history(limit=5)
    for session in history:
        print(f"  - {session['session_id']}: {session['children']} ({session['total_duration_seconds']:.0f}s)")
    
    print("\n✅ State Manager test complete!")
