"""
Agent Orchestrator
Coordinates all AI agents to create rich multimodal story experiences
"""

from typing import Dict, Optional, List
from datetime import datetime

class AgentOrchestrator:
    """
    Master coordinator for all AI agents
    """
    
    def __init__(self):
        # Import agents here to avoid circular imports
        from .storyteller_agent import storyteller
        from .visual_agent import visual_agent
        from .voice_agent import voice_agent
        from .memory_agent import memory_agent
        
        self.storyteller = storyteller
        self.visual = visual_agent
        self.voice = voice_agent
        self.memory = memory_agent
        
        print("🎭 Agent orchestrator initialized")
    
    async def generate_rich_story_moment(
        self,
        session_id: str,
        characters: Dict,
        user_input: Optional[str] = None,
        language: str = "en"
    ) -> Dict:
        """
        Orchestrate all agents to create a complete story moment
        
        Args:
            session_id: Unique session identifier
            characters: Dict with child1 and child2 data
            user_input: User's choice or input (optional)
            language: Story language (en/es/hi)
            
        Returns:
            Complete multimodal story moment with text, image, audio
        """
        
        print(f"\n🎬 Generating rich story moment for session {session_id}")
        
        # STEP 1: Recall relevant memories
        memories = []
        if user_input and self.memory.enabled:
            try:
                memories = await self.memory.recall_relevant_memories(
                    session_id=session_id,
                    current_context=user_input,
                    top_k=3
                )
                print(f"🧠 Using {len(memories)} memories for context")
            except Exception as e:
                print(f"⚠️  Memory recall skipped: {e}")
        
        # STEP 2: Generate story text with context
        story_context = {
            "characters": characters,
            "session_id": session_id,
            "language": language,
            "memories": memories
        }
        
        story_segment = await self.storyteller.generate_story_segment(
            context=story_context,
            user_input=user_input
        )
        
        print(f"📖 Story text generated: {len(story_segment['text'])} chars")
        
        # STEP 3: Generate scene illustration (if enabled)
        scene_image = None
        if self.visual.enabled:
            try:
                scene_image = await self.visual.generate_scene_image(
                    story_context={
                        "setting": self._extract_setting(story_segment['text']),
                        "mood": "joyful",
                        "key_objects": self._extract_key_objects(story_segment['text'])
                    },
                    child_profiles=characters,
                    scene_description=story_segment['text'][:200]
                )
                print(f"🎨 Scene image: {'✅ Generated' if scene_image else '❌ Failed'}")
            except Exception as e:
                print(f"⚠️  Visual generation skipped: {e}")
        
        # STEP 4: Generate narration audio (if enabled)
        narration_audio = None
        if self.voice.enabled:
            try:
                narration_audio = await self.voice.generate_narration(
                    text=story_segment['text'],
                    language=language
                )
                print(f"🎤 Narration: {'✅ Generated' if narration_audio else '❌ Failed'}")
            except Exception as e:
                print(f"⚠️  Voice generation skipped: {e}")
        
        # STEP 5: Generate character dialogue voices (optional)
        character_voices = []
        dialogues = self._extract_dialogues(story_segment['text'])
        
        if dialogues and self.voice.enabled:
            for dialogue in dialogues[:2]:  # Limit to 2 dialogues
                try:
                    spirit_animal = characters.get('child1', {}).get('spirit_animal', 'dragon')
                    voice_type = self.voice.get_character_voice_for_spirit_animal(spirit_animal)
                    
                    audio = await self.voice.generate_dialogue(
                        text=dialogue['text'],
                        character_type=voice_type,
                        emotion=dialogue.get('emotion', 'neutral'),
                        language=language
                    )
                    
                    if audio:
                        character_voices.append({
                            "character": dialogue['character'],
                            "audio": audio,
                            "text": dialogue['text']
                        })
                except Exception as e:
                    print(f"⚠️  Character voice skipped: {e}")
        
        # STEP 6: Store this moment in memory (if enabled)
        if self.memory.enabled:
            try:
                await self.memory.store_story_moment(
                    session_id=session_id,
                    moment_data={
                        "scene": story_segment['text'][:100],
                        "choice_made": user_input or "story_start",
                        "outcome": story_segment.get('interactive', {}).get('text', ''),
                        "emotion": "joyful",
                        "lesson": self._extract_lesson(story_segment['text'])
                    }
                )
            except Exception as e:
                print(f"⚠️  Memory storage skipped: {e}")
        
        # STEP 7: Return complete multimodal experience
        return {
            "text": story_segment['text'],
            "image": scene_image,
            "audio": {
                "narration": narration_audio,
                "character_voices": character_voices
            },
            "interactive": story_segment.get('interactive', {}),
            "timestamp": story_segment.get('timestamp'),
            "memories_used": len(memories),
            "agents_used": {
                "storyteller": True,
                "visual": scene_image is not None,
                "voice": narration_audio is not None,
                "memory": len(memories) > 0
            }
        }
    
    def _extract_setting(self, text: str) -> str:
        """Extract setting from story text"""
        text_lower = text.lower()
        if "forest" in text_lower:
            return "magical forest"
        elif "castle" in text_lower:
            return "enchanted castle"
        elif "mountain" in text_lower:
            return "mystical mountains"
        elif "ocean" in text_lower or "sea" in text_lower:
            return "crystal ocean"
        elif "sky" in text_lower or "cloud" in text_lower:
            return "floating sky islands"
        else:
            return "magical realm"
    
    def _extract_key_objects(self, text: str) -> str:
        """Extract key objects from story"""
        objects = []
        keywords = [
            "portal", "treasure", "sword", "wand", "crystal", 
            "dragon", "owl", "phoenix", "unicorn", "lion",
            "tree", "star", "moon", "sun", "flower"
        ]
        
        text_lower = text.lower()
        for keyword in keywords:
            if keyword in text_lower:
                objects.append(keyword)
        
        return ", ".join(objects[:3]) if objects else "magical sparkles"
    
    def _extract_dialogues(self, text: str) -> List[Dict]:
        """Extract character dialogues from story text"""
        dialogues = []
        
        # Simple quoted text extraction
        if '"' in text:
            parts = text.split('"')
            for i in range(1, len(parts), 2):
                if parts[i].strip():
                    dialogues.append({
                        "character": "character",
                        "text": parts[i].strip(),
                        "emotion": "neutral"
                    })
        
        return dialogues
    
    def _extract_lesson(self, text: str) -> str:
        """Extract moral/lesson from story"""
        themes = {
            "brave": "courage",
            "courage": "courage",
            "kind": "kindness",
            "kindness": "kindness",
            "share": "sharing",
            "sharing": "sharing",
            "help": "helping others",
            "friend": "friendship",
            "friendship": "friendship",
            "honest": "honesty",
            "truth": "honesty",
            "teamwork": "teamwork",
            "together": "teamwork"
        }
        
        text_lower = text.lower()
        for keyword, theme in themes.items():
            if keyword in text_lower:
                return theme
        
        return "adventure"


# Global instance
orchestrator = AgentOrchestrator()