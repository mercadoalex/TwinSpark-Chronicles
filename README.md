# TwinSpark Chronicles

AI-powered interactive storytelling for siblings. Models children as a relationship system to create dual-perspective narratives that strengthen sibling bonds.

Built for Ale & Sofi.

## Architecture

![System Architecture](architecture.png)

```
backend/           FastAPI + Gemini 2.0 agents (storyteller, voice, memory, visual, avatar)
frontend/          React app (Vite) — dual-screen story display, character setup, i18n
```

### AI Agent Architecture

![AI Agent Architecture](ai_architecture.png)

The Orchestrator coordinates 7 specialized agents per story beat:
- **Storyteller** — Gemini 2.0 Flash dual-perspective narrative generation with content filtering
- **Visual** — Imagen 3 scene illustration in Pixar/Disney style
- **Voice** — Google Cloud TTS with 7 character voice profiles + emotion adjustments
- **Memory** — ChromaDB vector embeddings for cross-beat continuity
- **Style Transfer** — Family photo face crops → art-style portraits composited into scenes
- **Scene Compositor** — Overlays style-transferred portraits into generated scenes
- **Avatar** — Photo-to-avatar pipeline (awaiting Imagen 3 integration)

Supporting services: personality engine, relationship mapper, narrative directives, skills discoverer, world state persistence, session time enforcer, content safety filter.

## User Flow

### Setup → Story Experience

![User Flow — Setup and Story](flow01.png)

1. **Privacy Modal** — Data usage consent (required for children's app)
2. **Language Selector** — English or Spanish
3. **Continue Screen** — Resume a saved adventure, or start fresh
4. **Character Setup** — Configure both siblings: name, gender, spirit animal, toy companion, family photos
5. **Story Experience** — Dual-perspective narrative with scene images, audio, choices, and collaborative drawing

### In-Session Features

![User Flow — In-Session](flow02.png)

- **Dual Story Display** — Split-screen showing each child's perspective of the story
- **Drawing Canvas** — AI-triggered collaborative drawing with dark glassmorphism theme, sound/haptic feedback, celebration overlay
- **Session Timer** — Countdown with pause-during-generation, time extensions, urgent pulse under 10s
- **Emergency Stop** — Press-and-hold 2s confirmation gate → Wind Down Screen with star-trail goodbye
- **Parent Controls** — Content filters, time extensions (+10/+15/+30 min), photo review
- **World Map** — Persistent locations, NPCs, and items discovered across sessions
- **Story Gallery** — Archived completed stories readable as storybooks
- **Sibling Dashboard** — Real-time relationship dynamics, skill discoveries, turn tracking

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

**Backend** (19 specs implemented, 500+ tests):

- 7 AI agents (orchestrator, storyteller, visual, voice, memory, style transfer, avatar)
- Sibling dynamics engine (personality, relationship mapping, narrative directives, skills discovery)
- Family photo pipeline (upload, content scanning, face extraction, style transfer, scene compositing)
- Voice recording system (record, normalize, playback integration with story beats)
- Session time enforcement (backend + frontend sync, generation pause, extensions)
- Collaborative drawing (real-time sync, persistence, orchestrator integration)
- Story archival (auto-archive on session end, storybook gallery)
- Persistent world state (locations, NPCs, items across sessions)
- Content safety (text filtering, image scanning, blocklist)
- Session persistence (snapshot save/restore, beacon API on tab close)
- SQLite database with 7 migration files

**Frontend** (React 18 + Vite + Zustand):
- Character setup wizard with photo upload
- Dual-perspective story display with animated transitions
- Scene audio system (ambient sounds per story setting)
- Drawing canvas with dark glassmorphism theme, sound/haptic feedback
- Session timer with pause, extension, and urgent state
- Emergency stop with press-and-hold confirmation gate
- Wind down screen with star-trail goodbye animation
- Parent controls, parent dashboard, sibling dashboard
- World map view, story gallery with storybook reader
- Voice library and recorder
- i18n (English/Spanish)
- Celebration overlays (confetti, star-shower)
- Session resumption (continue screen)
- Accessibility: skip links, ARIA live regions, focus management, reduced motion support

## What's Not Built Yet

- Imagen 3 scene generation (requires GCP project with Vertex AI access)
- Avatar pipeline (awaiting Imagen 3 for photo-to-avatar conversion)
- Speech-to-text input (STT service stubbed)
- Emotion detection from camera (service stubbed)
- Production deployment (Dockerfile exists, needs GCP credentials)

## Docs

- `docs/PHASE3_PLAN.md` — Phase 3 roadmap
- `docs/PHASE4_PLAN.md` — Phase 4 roadmap
- `docs/GCP_DEPLOYMENT.md` — Deployment guide
- `CHANGELOG.md` — Change history
