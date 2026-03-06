import asyncio
import logging
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class OutputMode(Enum):
    """Different modes of story output"""
    VISUAL_ONLY = "visual"
    AUDIO_ONLY = "audio"
    FULL_MULTIMODAL = "full"
    INTERLEAVED = "interleaved"  # Alternates between modes


@dataclass
class StorySegment:
    """A single segment of the story with timing"""
    text: str
    duration: float  # How long this segment takes (in seconds)
    requires_input: bool = False  # Should we wait for user input?
    input_prompt: Optional[str] = None  # What action are we waiting for?
    child_id: Optional[str] = None  # Which child should respond?


class MultimodalCoordinator:
    """
    Coordinates the delivery of story content across multiple modalities
    with intelligent interleaving and synchronization.
    """
    
    def __init__(self):
        self.current_mode = OutputMode.INTERLEAVED
        self.is_narrating = False
        self.pending_input = None
        self.on_narration_complete: Optional[Callable] = None
        self.on_input_required: Optional[Callable] = None
        
    async def deliver_story_beat(
        self, 
        narration: str,
        child1_perspective: str,
        child2_perspective: str,
        choices: list,
        websocket,
        voice_enabled: bool = True
    ):
        """
        Delivers a story beat with intelligent interleaving:
        1. Narrate main story (with audio if enabled)
        2. Pause for dramatic effect
        3. Show child 1's perspective
        4. Pause
        5. Show child 2's perspective
        6. Pause
        7. Present choices and wait for input
        """
        try:
            self.is_narrating = True
            
            # === SEGMENT 1: Main Narration ===
            await self._send_segment(
                websocket,
                text=narration,
                segment_type="narration",
                audio_enabled=voice_enabled
            )
            await asyncio.sleep(2)  # Dramatic pause
            
            # === SEGMENT 2: Child 1's Perspective ===
            await self._send_segment(
                websocket,
                text=child1_perspective,
                segment_type="child1_perspective",
                audio_enabled=voice_enabled,
                highlight_child="c1"
            )
            await asyncio.sleep(1.5)
            
            # === SEGMENT 3: Child 2's Perspective ===
            await self._send_segment(
                websocket,
                text=child2_perspective,
                segment_type="child2_perspective",
                audio_enabled=voice_enabled,
                highlight_child="c2"
            )
            await asyncio.sleep(2)
            
            # === SEGMENT 4: Present Choices (Interactive) ===
            self.is_narrating = False
            await self._send_choices(websocket, choices)
            
            # Signal that input is required
            if self.on_input_required:
                self.on_input_required(choices)
            
            logger.info("✅ Multimodal story delivery complete, awaiting input")
            
        except Exception as e:
            logger.error(f"❌ Error during multimodal delivery: {e}", exc_info=True)
            self.is_narrating = False
    
    async def _send_segment(
        self,
        websocket,
        text: str,
        segment_type: str,
        audio_enabled: bool = True,
        highlight_child: Optional[str] = None
    ):
        """Send a single story segment to the frontend"""
        await websocket.send_json({
            "type": "STORY_SEGMENT",
            "segment_type": segment_type,
            "text": text,
            "audio_enabled": audio_enabled,
            "highlight_child": highlight_child,
            "timestamp": asyncio.get_event_loop().time()
        })
        
        # Calculate approximate narration time (assuming ~150 words per minute)
        words = len(text.split())
        narration_time = (words / 150) * 60
        
        if audio_enabled:
            await asyncio.sleep(narration_time)
        else:
            await asyncio.sleep(min(narration_time * 0.3, 3))  # Faster if no audio
    
    async def _send_choices(self, websocket, choices: list):
        """Send interactive choices to the frontend"""
        await websocket.send_json({
            "type": "CHOICES_READY",
            "choices": choices,
            "requires_input": True
        })
    
    def handle_user_input(self, choice_id: str, child_id: str):
        """Process user input and continue story flow"""
        logger.info(f"📥 User input received: {choice_id} from {child_id}")
        self.pending_input = None
        
        if self.on_narration_complete:
            self.on_narration_complete(choice_id, child_id)
    
    def set_mode(self, mode: OutputMode):
        """Change the output mode"""
        self.current_mode = mode
        logger.info(f"🎭 Multimodal mode changed to: {mode.value}")