"""WebSocket endpoint for the new voice-first story loop.

Handles two message types from the frontend:
- voice_input: routes audio to STT, sends transcript feedback, then to freeform handler
- card_selection: routes story_direction text directly to freeform handler

Sends back:
- story_beat: narration, illustration_url, suggestions, perspective, is_milestone
- transcript_result: successful transcription feedback
- transcript_error: failed transcription feedback

Requirements: 2.6, 3.4, 9.5
"""

import base64
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.models.session_state import SessionState
from app.models.story_beat import StoryBeatResponse
from app.services.freeform_input_handler import FreeformInputHandler
from app.services.stt_service import STTService

logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level services (shared across connections)
_stt_service = STTService()
_freeform_handler = FreeformInputHandler()


@router.websocket("/ws/story-loop/{session_id}")
async def story_loop_websocket(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for the voice-first story loop.

    Manages a SessionState per connection and routes incoming messages
    to the appropriate handler (voice_input, card_selection, or start_session).
    """
    await websocket.accept()

    # Initialize session state for this connection
    session_state = SessionState(
        session_id=session_id,
        active_twin="twin1",
        turn_count=0,
        theme="a magical adventure",
        story_context={},
    )

    logger.info("Story loop WebSocket connected: session_id=%s", session_id)

    try:
        while True:
            raw_message = await websocket.receive_text()
            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on session %s", session_id)
                continue

            msg_type = message.get("type")

            if msg_type == "start_session":
                await _handle_start_session(websocket, message, session_state)
            elif msg_type == "voice_input":
                await _handle_voice_input(websocket, message, session_state)
            elif msg_type == "card_selection":
                await _handle_card_selection(websocket, message, session_state)
            else:
                logger.warning(
                    "Unknown message type '%s' on session %s", msg_type, session_id
                )

    except WebSocketDisconnect:
        logger.info("Story loop WebSocket disconnected: session_id=%s", session_id)
    except Exception as e:
        logger.error(
            "Unexpected error in story loop WebSocket (session %s): %s",
            session_id,
            e,
        )


async def _handle_start_session(
    websocket: WebSocket,
    message: dict,
    session_state: SessionState,
) -> None:
    """Handle start_session message: set theme and generate the opening story beat.

    Message format:
        {"type": "start_session", "theme": "enchanted-forest", "twin_names": {"twin1": "Ale", "twin2": "Sofi"}}
    """
    theme = message.get("theme", "a magical adventure")
    twin_names = message.get("twin_names", {})

    # Update session state with theme
    session_state.theme = theme
    session_state.story_context["theme"] = theme
    session_state.story_context["twin_names"] = twin_names

    # Generate the opening story beat
    await _generate_and_send_beat(
        websocket=websocket,
        input_text=f"Start a new {theme.replace('-', ' ')} adventure!",
        active_twin=session_state.active_twin,
        session_state=session_state,
    )


async def _handle_voice_input(
    websocket: WebSocket,
    message: dict,
    session_state: SessionState,
) -> None:
    """Handle voice_input message: STT → transcript feedback → freeform handler → story beat.

    Message format:
        {"type": "voice_input", "audio_data": "<base64 PCM>", "active_twin": "twin1", "session_id": "..."}
    """
    audio_data_b64 = message.get("audio_data", "")
    active_twin = message.get("active_twin", session_state.active_twin)

    # Decode audio from base64
    try:
        audio_bytes = base64.b64decode(audio_data_b64)
    except Exception:
        await websocket.send_json({
            "type": "transcript_error",
            "message": "I didn't catch that — try again or tap a spark!",
        })
        return

    # Transcribe audio via STT service
    transcript_result = await _stt_service.transcribe(audio_bytes)

    # Check if transcript is empty or low-confidence
    if transcript_result.is_empty:
        await websocket.send_json({
            "type": "transcript_error",
            "message": "I didn't catch that — try again or tap a spark!",
        })
        return

    # Send transcript feedback to frontend
    await websocket.send_json({
        "type": "transcript_result",
        "text": transcript_result.text,
        "confidence": transcript_result.confidence,
    })

    # Route transcript to freeform handler
    await _generate_and_send_beat(
        websocket=websocket,
        input_text=transcript_result.text,
        active_twin=active_twin,
        session_state=session_state,
    )


async def _handle_card_selection(
    websocket: WebSocket,
    message: dict,
    session_state: SessionState,
) -> None:
    """Handle card_selection message: route story_direction to freeform handler → story beat.

    Message format:
        {"type": "card_selection", "card_id": "spark_1", "story_direction": "...", "active_twin": "twin1", "session_id": "..."}
    """
    story_direction = message.get("story_direction", "")
    active_twin = message.get("active_twin", session_state.active_twin)

    if not story_direction:
        logger.warning(
            "Empty story_direction in card_selection for session %s",
            session_state.session_id,
        )
        story_direction = "The adventure continues"

    # Route directly to freeform handler
    await _generate_and_send_beat(
        websocket=websocket,
        input_text=story_direction,
        active_twin=active_twin,
        session_state=session_state,
    )


async def _generate_and_send_beat(
    websocket: WebSocket,
    input_text: str,
    active_twin: str,
    session_state: SessionState,
) -> None:
    """Generate a story beat via FreeformInputHandler and send it over WebSocket.

    Sends a story_beat message with: narration, illustration_url, suggestions,
    perspective, is_milestone.
    """
    # Update session state active twin
    session_state.active_twin = active_twin

    # Build story context from session state
    story_context = {
        **session_state.story_context,
        "theme": session_state.theme or "a magical adventure",
    }

    # Generate the next story beat
    beat: StoryBeatResponse = await _freeform_handler.interpret_input(
        input_text=input_text,
        session_id=session_state.session_id,
        active_twin=active_twin,
        story_context=story_context,
    )

    # Update session state after successful beat generation
    session_state.story_context["previous_narration"] = beat.narration
    session_state.last_beat_id = str(uuid.uuid4())
    session_state.switch_turn()

    # Send story_beat response
    await websocket.send_json({
        "type": "story_beat",
        "narration": beat.narration,
        "illustration_url": beat.illustration_url,
        "suggestions": [
            {
                "id": s.id,
                "label": s.label,
                "illustration_url": s.illustration_url,
                "story_direction": s.story_direction,
            }
            for s in beat.suggestions
        ],
        "perspective": beat.perspective,
        "is_milestone": beat.is_milestone,
    })
