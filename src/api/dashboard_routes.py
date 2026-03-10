from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import logging

from ..database import get_db
# Import DB models when available, but use dictionaries for now if unlinked or mock data if db empty
# from .. import dtos, crud, database_models

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
logger = logging.getLogger(__name__)

# --- Mock Data Fallbacks if DB query fails or is empty ---
MOCK_SESSIONS = [
    {
        "session_id": "ses_1234",
        "title": "The Forest Guardian",
        "theme": "fantasy",
        "duration_minutes": 25,
        "started_at": (datetime.now() - timedelta(days=2)).isoformat(),
        "ended_at": (datetime.now() - timedelta(days=2, minutes=-25)).isoformat(),
        "has_divergence": True,
        "reunion_count": 1,
        "skills_practiced": ["communication", "patience"],
        "emotions_addressed": ["happy", "curious"]
    },
    {
        "session_id": "ses_5678",
        "title": "Space Explorers",
        "theme": "science",
        "duration_minutes": 40,
        "started_at": (datetime.now() - timedelta(days=1)).isoformat(),
        "ended_at": (datetime.now() - timedelta(days=1, minutes=-40)).isoformat(),
        "has_divergence": False,
        "reunion_count": 0,
        "skills_practiced": ["problem-solving", "bravery"],
        "emotions_addressed": ["excited", "frustrated", "calm"]
    }
]

@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get high-level statistics for the dashboard overview."""
    try:
        # Later, query the DB: db.query(StorySessionDB).count()
        # For phase 4 MVP we return mock data combined with real dynamic DB logic 
        # (This will be expanded when full ORM is mapped or real data exists)
        return {
            "total_sessions": len(MOCK_SESSIONS),
            "total_duration_minutes": sum(s["duration_minutes"] for s in MOCK_SESSIONS),
            "average_bond_score": 0.85
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch dashboard stats")


@router.get("/sessions")
async def get_recent_sessions(limit: int = 10, db: Session = Depends(get_db)):
    """Get a timeline list of recent story sessions."""
    try:
        # Mocking for Phase 4 MVP
        return MOCK_SESSIONS[:limit]
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail="Could not fetch sessions")


@router.get("/duration-chart")
async def get_playtime_chart_data(db: Session = Depends(get_db)):
    """Get formatted data for the playtime duration chart."""
    # Data shape: [{"label": "Day", "value": "Minutes"}]
    data = [
        {"label": "Mon", "value": 0},
        {"label": "Tue", "value": 25},
        {"label": "Wed", "value": 40},
        {"label": "Thu", "value": 0},
        {"label": "Fri", "value": 0},
        {"label": "Sat", "value": 0},
        {"label": "Sun", "value": 0}
    ]
    return {"data": data}


@router.get("/leadership-chart")
async def get_leadership_chart_data(db: Session = Depends(get_db)):
    """Get formatted data for leadership balance dynamically."""
    # Showing 0.5 as balanced, closer to 1 means Child 2 dominant, 0 means Child 1 dominant.
    data = [
        {"label": "Session 1", "value": 0.3}, # Child 1 lead
        {"label": "Session 2", "value": 0.6}, # Child 2 lead slightly
        {"label": "Session 3", "value": 0.5}, # Perfectly balanced
        {"label": "Session 4", "value": 0.5}  # Perfectly balanced
    ]
    return {"data": data}
