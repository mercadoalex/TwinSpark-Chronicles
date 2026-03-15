# TwinSpark Chronicles

AI-powered interactive storytelling for siblings. Models children as a relationship system to create dual-perspective narratives that strengthen sibling bonds.

Built for Ale & Sofi.

## Architecture

```
backend/           FastAPI + Gemini 2.0 agents (storyteller, voice, memory, visual, avatar)
frontend/          React app (Vite) — dual-screen story display, character setup, i18n
```

## Quick Start

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Or: `./dev.sh` to start both.

Frontend: http://localhost:5173 | Backend: http://localhost:8000 | API Docs: http://localhost:8000/docs

## Environment

Copy `.env.example` and set your keys:

```
GOOGLE_API_KEY=your_gemini_key
HUGGINGFACE_API_KEY=your_hf_key       # optional
GOOGLE_PROJECT_ID=your_gcp_project    # for Imagen 3
```

## What's Built

**Backend agents** (backend/app/agents/):
- Storyteller — Gemini 2.0 Flash story generation with child-safe prompts
- Orchestrator — coordinates all agents for rich multimodal moments
- Voice — Google Cloud TTS with character-specific voice profiles
- Memory — ChromaDB vector embeddings for session continuity
- Visual — Imagen 3 scene generation (requires GCP project)
- Avatar — photo-to-avatar pipeline (awaiting Imagen 3 integration)

**Frontend** (frontend/src/):
- Character setup flow
- Dual-screen story display
- Voice-only mode
- i18n (English/Spanish)
- Zustand state management

## What's Not Built Yet

- Camera / face detection / emotion detection
- Audio input / voice commands / speech-to-text
- Real-time multimodal input pipeline
- Image generation for avatars (currently returns original photo)
- Keepsake / storybook page generation
- Database persistence (SQLAlchemy)
- Family photo integration
- Parent dashboard

## Docs

- `docs/PHASE3_PLAN.md` — Phase 3 roadmap
- `docs/PHASE4_PLAN.md` — Phase 4 roadmap
- `docs/GCP_DEPLOYMENT.md` — Deployment guide
- `CHANGELOG.md` — Change history
