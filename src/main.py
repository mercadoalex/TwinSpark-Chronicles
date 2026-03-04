"""
TwinSpark Chronicles - Main Application

Entry point for the TwinSpark Chronicles interactive storytelling system.
"""

import logging
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from models import (
    ChildProfile,
    PersonalityTrait,
    EmotionalState,
    StorySession,
    StoryTheme,
    MultimodalInput
)
from ai.twin_intelligence import TwinIntelligenceEngine
from story.story_generator import StoryGenerator

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TwinSparkApp:
    """Main application orchestrator for TwinSpark Chronicles."""
    
    def __init__(self):
        """Initialize the application components."""
        logger.info("🌟 Initializing TwinSpark Chronicles...")
        
        # Core engines
        self.twin_intelligence = TwinIntelligenceEngine()
        self.story_generator = StoryGenerator()
        
        # Application state
        self.current_session: StorySession = None
        
        logger.info("✅ TwinSpark Chronicles initialized successfully!")
    
    def create_demo_profiles(self) -> tuple[str, str]:
        """
        Create demo profiles for testing.
        Replace with real profiles from your daughters!
        """
        logger.info("Creating demo profiles...")
        
        # Child 1 - Ale (Bold, Creative)
        ale = ChildProfile(
            id="ale_001",
            name="Ale",
            age=6,
            personality_traits=[
                PersonalityTrait.BOLD,
                PersonalityTrait.CREATIVE,
                PersonalityTrait.PLAYFUL
            ],
            strengths=["adventurous", "artistic", "energetic"],
            interests=["animals", "drawing", "running"],
            current_emotion=EmotionalState.EXCITED,
            energy_level=0.8
        )
        
        # Child 2 - Sofi (Thoughtful, Analytical)
        sofi = ChildProfile(
            id="sofi_001",
            name="Sofi",
            age=6,
            personality_traits=[
                PersonalityTrait.THOUGHTFUL,
                PersonalityTrait.ANALYTICAL,
                PersonalityTrait.EMPATHETIC
            ],
            strengths=["problem-solving", "kind", "observant"],
            interests=["puzzles", "reading", "helping"],
            current_emotion=EmotionalState.CALM,
            energy_level=0.6
        )
        
        # Register in Twin Intelligence Engine
        self.twin_intelligence.register_child(ale)
        self.twin_intelligence.register_child(sofi)
        self.twin_intelligence.register_relationship(ale.id, sofi.id)
        
        logger.info(f"✅ Created profiles for {ale.name} and {sofi.name}")
        
        return (ale.id, sofi.id)
    
    def start_story_session(
        self,
        child1_id: str,
        child2_id: str,
        theme: StoryTheme = StoryTheme.FANTASY
    ) -> StorySession:
        """Start a new interactive story session."""
        logger.info(f"🎬 Starting story session with theme: {theme.value}")
        
        # Create session
        session = StorySession(
            session_id=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            child1_id=child1_id,
            child2_id=child2_id,
            theme=theme,
            title="To be determined...",
            started_at=datetime.now()
        )
        
        self.current_session = session
        
        # Generate story directive from Twin Intelligence
        logger.info("🧠 Consulting Twin Intelligence Engine...")
        directive = self.twin_intelligence.generate_story_directive(
            child1_id,
            child2_id,
            theme.value
        )
        
        # Generate story opening
        logger.info("📖 Generating story opening...")
        story_opening = self.story_generator.generate_story_opening(directive)
        
        session.title = story_opening.get("title", "An Amazing Adventure")
        
        return session, story_opening, directive
    
    def demo_interactive_session(self):
        """Run a demo interactive story session."""
        print("\n" + "="*70)
        print("🌟 WELCOME TO TWINPARK CHRONICLES 🌟")
        print("="*70 + "\n")
        
        # Create demo profiles
        child1_id, child2_id = self.create_demo_profiles()
        
        child1 = self.twin_intelligence.profiles[child1_id]
        child2 = self.twin_intelligence.profiles[child2_id]
        
        print(f"Today's adventure features:")
        print(f"  🌟 {child1.name} - {', '.join([t.value for t in child1.personality_traits])}")
        print(f"  🌟 {child2.name} - {', '.join([t.value for t in child2.personality_traits])}")
        print()
        
        # Start session
        session, story_opening, directive = self.start_story_session(
            child1_id,
            child2_id,
            StoryTheme.FANTASY
        )
        
        print(f"\n📚 Story Title: {session.title}")
        print("="*70)
        print()
        
        print("📖 Story Opening:")
        print(story_opening.get("opening", ""))
        print()
        
        # Display story beats
        for i, beat in enumerate(story_opening.get("beats", []), 1):
            print(f"\n--- Story Beat {i} ---")
            print(f"\n{beat.get('narration', '')}")
            print()
            
            print(f"👧 {child1.name}'s Perspective:")
            print(f"   {beat.get('child1_perspective', '')}")
            print()
            
            print(f"👧 {child2.name}'s Perspective:")
            print(f"   {beat.get('child2_perspective', '')}")
            print()
            
            print(f"❓ {beat.get('interaction_prompt', '')}")
            print()
            
            if i < len(story_opening.get("beats", [])):
                input("   Press Enter to continue... ")
        
        print("\n" + "="*70)
        print("🎭 TWIN INTELLIGENCE INSIGHTS")
        print("="*70)
        
        print(f"\n🧬 Personality Analysis:")
        print(f"  • {child1.name} is showing: {', '.join([t.value for t in child1.personality_traits])}")
        print(f"  • {child2.name} is showing: {', '.join([t.value for t in child2.personality_traits])}")
        
        print(f"\n⚡ Assigned Powers:")
        print(f"  • {child1.name}: {', '.join(directive['child1']['powers'])}")
        print(f"  • {child2.name}: {', '.join(directive['child2']['powers'])}")
        
        print(f"\n🤝 Relationship Dynamics:")
        print(f"  • Role Distribution: {directive['child1']['role']} & {directive['child2']['role']}")
        print(f"  • Complementary Strengths: {directive['relationship']['complementary_strengths']}")
        print(f"  • Teamwork Required: {'Yes!' if directive['relationship']['requires_teamwork'] else 'No'}")
        
        print(f"\n😊 Emotional Adaptation:")
        print(f"  • {child1.name} is feeling: {directive['child1']['emotional_state']}")
        print(f"  • {child2.name} is feeling: {directive['child2']['emotional_state']}")
        print(f"  • Story difficulty adjusted accordingly")
        
        print("\n" + "="*70)
        print("✨ Demo Complete! This is just the beginning...")
        print("="*70)
        
        print("\n💡 Next Steps:")
        print("  1. Add your Google API key to .env file")
        print("  2. Customize child profiles with your daughters' real data")
        print("  3. Integrate video/image generation")
        print("  4. Add multimodal input processing (camera, microphone)")
        print("  5. Build the web interface")
        print()


def main():
    """Main entry point."""
    try:
        app = TwinSparkApp()
        app.demo_interactive_session()
        
    except KeyboardInterrupt:
        logger.info("\n\n👋 Goodbye! Thanks for using TwinSpark Chronicles!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
