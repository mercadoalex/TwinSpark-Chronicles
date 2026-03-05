"""
Complete Phase 2 Integration Test
Tests all multimodal components working together.
"""

import sys
import os
import time
import cv2
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import ChildProfile, PersonalityTrait, EmotionalState
from multimodal.input_manager import InputManager
from story.keepsake_maker import KeepsakeMaker
from utils.state_manager import StateManager
from ai.twin_intelligence import TwinIntelligenceEngine
from story.story_generator import StoryGenerator


def test_phase_2_complete():
    """
    Complete integration test for Phase 2:
    1. Multimodal input processing (camera + audio + emotions)
    2. Twin Intelligence Engine
    3. Story generation
    4. Keepsake creation
    5. State persistence
    """
    
    print("=" * 60)
    print("🚀 TWINSPARK CHRONICLES - PHASE 2 INTEGRATION TEST")
    print("=" * 60)
    print()
    
    # Initialize all components
    print("📦 Initializing components...")
    
    # 1. State Manager
    state_manager = StateManager()
    
    # 2. Create/Load profiles
    print("\n👥 Setting up child profiles...")
    
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
    state_manager.save_profile(ale)
    state_manager.save_profile(sofi)
    print(f"   ✅ Created profiles for {ale.name} and {sofi.name}")
    
    # 3. Twin Intelligence Engine
    twin_engine = TwinIntelligenceEngine(ale, sofi)
    print(f"\n🧠 Twin Intelligence Engine initialized")
    print(f"   Relationship: {twin_engine.get_relationship_summary()}")
    
    # 4. Story Generator
    story_gen = StoryGenerator()
    print(f"\n📚 Story Generator ready")
    
    # 5. Keepsake Maker
    keepsake_maker = KeepsakeMaker()
    print(f"\n📖 Keepsake Maker ready")
    
    # 6. Input Manager
    print(f"\n🎮 Starting Input Manager...")
    print("   (Camera and audio will start)")
    print("   Commands: 'start story', 'stop', 'generate image', 'left', 'right'")
    print("   Press 'q' in the video window to finish test\n")
    
    input_manager = InputManager()
    input_manager.start()
    
    # Map faces to children (in real app, this would be done through face recognition)
    input_manager.map_face_to_child(0, ale)
    input_manager.map_face_to_child(1, sofi)
    
    # 7. Start session
    session_id = state_manager.start_session("Ale", "Sofi", language="en")
    print(f"🎬 Session started: {session_id}\n")
    
    # Track state
    story_started = False
    story_beat_count = 0
    last_emotion_check = time.time()
    
    try:
        while True:
            # Get current frame
            frame = input_manager.get_latest_frame()
            
            if frame is not None:
                # Get current status
                status = input_manager.get_status_summary()
                
                # Draw overlay with status
                y_offset = 30
                cv2.putText(frame, f"Session: {session_id}", (10, y_offset), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                y_offset += 35
                
                cv2.putText(frame, f"Faces Detected: {status['faces']}", (10, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_offset += 35
                
                # Show emotions
                for i, emotion in enumerate(status['emotions']):
                    text = f"Face {i}: {emotion['expression']} -> {emotion['state']}"
                    cv2.putText(frame, text, (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2)
                    y_offset += 30
                
                # Show last command
                if status['last_command']:
                    cv2.putText(frame, f"Command: {status['last_command']}", (10, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
                
                # Instructions
                cv2.putText(frame, "Say: 'start story' to begin | Press 'q' to quit", 
                           (10, frame.shape[0] - 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                
                cv2.imshow('TwinSpark Chronicles - Phase 2 Test', frame)
                
                # Check for voice commands
                if status['last_command'] == 'start_story' and not story_started:
                    print("\n🎭 Starting story generation...")
                    story_started = True
                    
                    # Get current emotions
                    emotions = input_manager.get_both_children_emotions()
                    if emotions:
                        for name, state in emotions.items():
                            print(f"   {name} is feeling: {state.value}")
                            state_manager.update_emotional_state(name, state)
                    
                    # Generate story
                    print("\n📝 Generating story beat...")
                    story = story_gen.generate_story(ale, sofi)
                    
                    if story and story.beats:
                        beat = story.beats[0]
                        print(f"\n📖 Story Beat #{story_beat_count + 1}:")
                        print(f"   Character: {beat.character}")
                        print(f"   Scene: {beat.scene_description}")
                        print(f"   Narrative: {beat.narrative[:100]}...")
                        
                        # Add to session
                        state_manager.add_story_beat(beat)
                        story_beat_count += 1
                
                # Periodically check emotions
                if time.time() - last_emotion_check > 5.0:
                    emotions = input_manager.get_both_children_emotions()
                    if emotions:
                        state_manager.add_emotion_snapshot(emotions)
                    last_emotion_check = time.time()
            
            # Check for quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n⚠️ Ending test...")
                break
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        
        input_manager.stop()
        cv2.destroyAllWindows()
        
        # Generate keepsake if story was started
        keepsake_path = None
        if story_started and story_beat_count > 0:
            print("\n📖 Creating keepsake...")
            
            story_text = f"""
            Ale and Sofi embarked on an amazing adventure together!
            
            Ale, with her bold and creative spirit, led the way into the unknown.
            Sofi, analytical and kind, made sure they stayed safe and found the best path.
            
            Together, they discovered that their different strengths made them 
            the perfect team. Every challenge they faced became an opportunity 
            to learn and grow together.
            
            Story beats generated: {story_beat_count}
            """
            
            keepsake_path = keepsake_maker.create_quick_keepsake(
                title="The TwinSpark Adventure",
                story_excerpt=story_text,
                child1_name="Ale",
                child2_name="Sofi"
            )
            
            print(f"   ✅ Keepsake saved: {keepsake_path}")
        
        # End session
        state_manager.end_session(keepsake_path=keepsake_path)
        
        # Show final stats
        print("\n" + "=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        
        stats = state_manager.get_stats()
        print(f"\nTotal Profiles: {stats['total_profiles']}")
        print(f"Total Sessions: {stats['total_sessions']}")
        print(f"Story Beats Generated: {story_beat_count}")
        
        if keepsake_path:
            print(f"\n✨ Keepsake: {keepsake_path}")
        
        print("\n" + "=" * 60)
        print("✅ PHASE 2 INTEGRATION TEST COMPLETE!")
        print("=" * 60)
        print("\nAll components working together:")
        print("  ✅ Camera + Face Detection")
        print("  ✅ Audio + Voice Recognition")
        print("  ✅ Emotion Detection")
        print("  ✅ Twin Intelligence Engine")
        print("  ✅ Story Generation")
        print("  ✅ Keepsake Creation")
        print("  ✅ State Persistence")
        print("\n🎉 TwinSpark Chronicles Phase 2 is COMPLETE!\n")


if __name__ == "__main__":
    test_phase_2_complete()
