"""
Memory Agent using Vector Embeddings
Maintains session continuity and personalization
"""

import chromadb
from datetime import datetime
from typing import Dict, List, Optional
import json
import os

class MemoryAgent:
    """
    Stores and retrieves memories using vector similarity search
    """
    
    def __init__(self):
        try:
            # Initialize ChromaDB with new configuration
            self.client = chromadb.PersistentClient(
                path="./chroma_data"
            )
            
            # Create collections for different memory types
            self.story_memories = self.client.get_or_create_collection(
                name="story_memories",
                metadata={"description": "Story events and choices"}
            )
            
            self.character_profiles = self.client.get_or_create_collection(
                name="character_profiles",
                metadata={"description": "Child preferences and traits"}
            )
            
            self.enabled = True
            print("✅ Memory agent initialized")
            
        except Exception as e:
            print(f"⚠️  Memory agent disabled: {e}")
            self.enabled = False
    
    async def store_story_moment(
        self,
        session_id: str,
        moment_data: Dict
    ) -> bool:
        """
        Store a story moment in memory
        
        Args:
            session_id: Unique session identifier
            moment_data: {
                "scene": "description",
                "choice_made": "what child chose",
                "outcome": "what happened",
                "emotion": "mood",
                "lesson": "moral/theme"
            }
        """
        if not self.enabled:
            return False
        
        try:
            # Create searchable text
            memory_text = f"""
Scene: {moment_data.get('scene', '')}
Choice: {moment_data.get('choice_made', '')}
Outcome: {moment_data.get('outcome', '')}
Emotion: {moment_data.get('emotion', 'neutral')}
Lesson: {moment_data.get('lesson', '')}
"""
            
            # Store in vector DB
            self.story_memories.add(
                documents=[memory_text],
                metadatas=[{
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    **moment_data
                }],
                ids=[f"{session_id}_{datetime.utcnow().timestamp()}"]
            )
            
            print(f"💾 Stored memory for session {session_id}")
            return True
            
        except Exception as e:
            print(f"❌ Memory storage error: {e}")
            return False
    
    async def recall_relevant_memories(
        self,
        session_id: str,
        current_context: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Retrieve relevant past memories based on current context
        
        Args:
            session_id: Current session
            current_context: What's happening now
            top_k: Number of memories to retrieve
            
        Returns:
            List of relevant memory dictionaries
        """
        if not self.enabled:
            return []
        
        try:
            # Query similar memories
            results = self.story_memories.query(
                query_texts=[current_context],
                n_results=top_k,
                where={"session_id": session_id}
            )
            
            if not results['metadatas']:
                return []
            
            memories = []
            for metadata in results['metadatas'][0]:
                memories.append(metadata)
            
            print(f"🧠 Recalled {len(memories)} relevant memories")
            return memories
            
        except Exception as e:
            print(f"❌ Memory recall error: {e}")
            return []
    
    async def update_character_profile(
        self,
        session_id: str,
        child_name: str,
        profile_update: Dict
    ) -> bool:
        """
        Update child's profile with new preferences/traits
        
        Args:
            profile_update: {
                "favorite_choices": [],
                "preferred_themes": [],
                "emotional_patterns": [],
                "growth_areas": []
            }
        """
        if not self.enabled:
            return False
        
        try:
            profile_text = f"{child_name}'s preferences: {json.dumps(profile_update)}"
            
            self.character_profiles.upsert(
                documents=[profile_text],
                metadatas=[{
                    "session_id": session_id,
                    "child_name": child_name,
                    "last_updated": datetime.utcnow().isoformat(),
                    **profile_update
                }],
                ids=[f"{session_id}_{child_name}"]
            )
            
            print(f"📝 Updated profile for {child_name}")
            return True
            
        except Exception as e:
            print(f"❌ Profile update error: {e}")
            return False
    
    async def get_session_summary(self, session_id: str) -> Dict:
        """
        Get a summary of all memories for a session
        """
        if not self.enabled:
            return {"total_moments": 0, "themes": [], "choices": []}
        
        try:
            # Get all memories for session
            results = self.story_memories.get(
                where={"session_id": session_id}
            )
            
            if not results['metadatas']:
                return {"total_moments": 0, "themes": [], "choices": []}
            
            # Analyze patterns
            choices = [m.get('choice_made', '') for m in results['metadatas']]
            emotions = [m.get('emotion', '') for m in results['metadatas']]
            lessons = [m.get('lesson', '') for m in results['metadatas']]
            
            return {
                "total_moments": len(results['metadatas']),
                "choices": list(set(choices)),
                "emotions": list(set(emotions)),
                "lessons": list(set(lessons)),
                "session_duration": "calculated_later"
            }
            
        except Exception as e:
            print(f"❌ Summary error: {e}")
            return {"total_moments": 0, "error": str(e)}


# Global instance
memory_agent = MemoryAgent()