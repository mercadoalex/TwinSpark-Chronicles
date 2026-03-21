# TwinSpark Chronicles — Developer Guide

Technical documentation for developers working on the codebase.

## Prerequisites

- Python 3.11+ with `venv`
- Node.js 18+ with npm
- Google API key (Gemini 2.0 Flash) — required for story generation
- Google Cloud TTS credentials — optional, for voice narration
- Google Cloud Project with Vertex AI — optional, for Imagen 3 scene generation

## Project Structure

```
backend/
  app/
    agents/           # AI agents (orchestrator, storyteller, visual, voice, memory, style_transfer, avatar)
    api/              # REST API routes
    config/           # Blocklist and configuration files
    db/               # Database connection, migration runner, migrations (001-007)
    models/           # Data models (character, session, photo, drawing, storybook, sibling, voice_recording, audio_theme)
    services/         # Business logic (30+ service modules)
    utils/            # Utilities (title_generator, beat_transformer)
    main.py           # FastAPI app, WebSocket handler, startup wiring
  tests/              # 39 test files, 500+ tests (pytest + Hypothesis)
  venv/               # Python virtual environment

frontend/
  src/
    components/       # Top-level components (SessionTimer, EmergencyStop, ParentControls, DualPrompt, SiblingDashboard)
    features/         # Feature modules (setup, story, audio, avatar, camera, drawing, gallery, session, world)
    shared/           # Shared components (CelebrationOverlay, WindDownScreen, LoadingAnimation, ExitModal, Modal)
    stores/           # Zustand stores (15 stores: session, story, audio, photo, drawing, gallery, sibling, etc.)
    App.jsx           # Root component with full routing and WebSocket wiring
    index.css         # Design system tokens (colors, fonts, shadows, radii, animations)
    locales.js        # i18n translations (English/Spanish)
```

## Local Development

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

The backend runs on port 8000. API docs at http://localhost:8000/docs.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on port 5173 via Vite. Proxies API calls to localhost:8000.

### Both at once

```bash
./dev.sh
```

## Environment Variables

Create `backend/.env` from `.env.development.example`:

| Variable | Required | Description |
|---|---|---|
| `GOOGLE_API_KEY` | Yes | Gemini 2.0 Flash API key for story generation |
| `GOOGLE_PROJECT_ID` | No | GCP project for Imagen 3 scene generation |
| `HUGGINGFACE_API_KEY` | No | HuggingFace API key (future use) |
| `DATABASE_URL` | No | SQLite path (defaults to `./data/twinspark.db`) |
| `SECRET_KEY` | No | App secret key |
| `SESSION_TIMEOUT_MINUTES` | No | Default session time limit (default: 30) |

Frontend env (`.env.development`):

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend URL (default: `http://localhost:8000`) |
| `VITE_WS_URL` | WebSocket URL (default: `ws://localhost:8000/ws`) |

## Running Tests

### Backend (pytest + Hypothesis)

```bash
cd backend
source venv/bin/activate
python3 -m pytest tests/ -x -q --tb=short
```

After running tests, clean up the CacheManager background loop:
```bash
pkill -f "python.*pytest"
```

There are 39 test files with 500+ tests covering all services, agents, and integrations. Property-based tests use Hypothesis with `max_examples=20`.

### Frontend

No test runner configured yet. Verify builds with:
```bash
cd frontend
npm run build
```

## Database

SQLite via a custom `DatabaseConnection` class (`backend/app/db/connection.py`). Migrations run automatically on startup via `MigrationRunner`.

### Migrations

| File | Description |
|---|---|
| `001_baseline.sql` | Core tables: sessions, story_beats, characters |
| `002_family_photos.sql` | Photos, face_portraits, character_mappings, style_transferred_portraits |
| `003_session_snapshots.sql` | Session persistence snapshots |
| `004_content_hash.sql` | Content hashing for cache deduplication |
| `005_voice_recordings.sql` | Voice recording metadata and storage |
| `006_storybook_gallery.sql` | Archived storybooks and pages |
| `007_collaborative_drawing.sql` | Drawing sessions and strokes |

To reset the database, delete `backend/data/twinspark.db` and restart the backend.

## Architecture

### WebSocket Protocol

The frontend connects via WebSocket at `/ws` with query parameters for character profiles and session config. The backend sends events:

| Event | Direction | Description |
|---|---|---|
| `CREATIVE_ASSET` | Server → Client | Story text, images, audio, choices |
| `STORY_COMPLETE` | Server → Client | All assets for a beat are ready |
| `STATUS` | Server → Client | Generation progress updates |
| `DRAWING_PROMPT` | Server → Client | AI requests collaborative drawing |
| `DRAWING_END` | Server → Client | Drawing session ended |
| `GENERATION_STARTED` | Server → Client | AI generation in progress (timer pauses) |
| `GENERATION_COMPLETED` | Server → Client | AI generation done (timer resumes) |
| `TIME_EXTENSION_CONFIRMED` | Server → Client | Parent extended session time |
| `SESSION_TIME_EXPIRED` | Server → Client | Backend time limit reached |
| `MECHANIC_WARNING` | Server → Client | Story mechanic prompt |
| `VOICE_COMMAND_MATCH` | Server → Client | Voice command recognized |
| `MAKE_CHOICE` | Client → Server | Child selected a story choice |
| `DRAWING_COMPLETE` | Client → Server | Drawing strokes submitted |
| `DRAWING_STROKE` | Client → Server | Real-time drawing sync |
| `TIME_EXTENSION` | Client → Server | Parent requests more time |
| `WRAP_UP` | Client → Server | Request story conclusion |

### Agent Pipeline

The Orchestrator runs a 10-step pipeline per story beat:

1. Memory recall (ChromaDB)
2. World state injection (persistent locations, NPCs, items)
3. Story generation (Gemini 2.0 Flash via Storyteller agent)
4. Drawing prompt injection (if storyteller decides)
5. Voice recording playback check (family recordings)
6. Photo portrait generation (Style Transfer agent)
7. Scene illustration (Visual agent → Imagen 3)
8. Scene compositing (overlay portraits into scene)
9. Narration + character voice audio (Voice agent → Google Cloud TTS)
10. Memory storage (ChromaDB)

Each agent gracefully degrades if its API isn't configured (`enabled = False`).

### Sibling Dynamics Engine

Four services model the sibling relationship:

- `PersonalityEngine` — tracks each child's personality traits and preferences
- `RelationshipMapper` — models the sibling relationship (cooperation, conflict, support)
- `NarrativeDirectives` — decides whose turn it is, story pacing, protagonist alternation
- `ComplementarySkillsDiscoverer` — identifies complementary skills between siblings

### State Management (Frontend)

15 Zustand stores, each focused on a single concern:

| Store | Purpose |
|---|---|
| `sessionStore` | WebSocket connection state, profiles, session ID |
| `storyStore` | Current beat, history, generation status, assets |
| `audioStore` | TTS toggle, audio feedback settings |
| `setupStore` | Language, privacy consent, character profiles, setup step |
| `siblingStore` | Sibling dynamics, roles, scores, suggestions |
| `parentControlsStore` | Time limits, content filters, time extensions |
| `sessionPersistenceStore` | Snapshot save/restore, beacon API |
| `photoStore` | Photo uploads, face portraits, character mappings |
| `drawingStore` | Drawing session state, strokes, sync queue |
| `galleryStore` | Archived storybooks |
| `sceneAudioStore` | Ambient scene audio, SFX preloading |
| `voiceRecordingStore` | Voice recording state |
| `worldStore` | World map data |
| `multimodalStore` | Camera/multimodal input state |

### Design System

CSS custom properties defined in `frontend/src/index.css`:

- Colors: `--color-bg-deep`, `--color-violet`, `--color-coral`, `--color-gold`, `--color-glass`, etc.
- Fonts: `--font-display` (Fredoka One), `--font-body` (Nunito)
- Shadows: `--shadow-glow-violet`, `--shadow-glow-gold`, `--shadow-glow-coral`
- Radii: `--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`
- Animations: `--ease-bounce`, `--ease-smooth`
- Dark glassmorphism theme throughout with `backdrop-filter: blur()` effects

### Content Safety

- `ContentFilter` — text-level filtering with blocklist, theme restrictions, custom blocked words
- `ContentScanner` — image-level safety scanning (BLOCKED / REVIEW / SAFE)
- Photos flagged as REVIEW require parent approval before face extraction
- All story text passes through the content filter before reaching children

## Adding a New Feature

1. Create a spec in `.kiro/specs/{feature-name}/` with `requirements.md`, `design.md`, `tasks.md`
2. Backend services go in `backend/app/services/`, agents in `backend/app/agents/`
3. Frontend features go in `frontend/src/features/{feature}/`, stores in `frontend/src/stores/`
4. Add tests in `backend/tests/test_{service}.py`
5. If new DB tables are needed, add a migration in `backend/app/db/migrations/`
6. Wire into the Orchestrator if the feature participates in story beat generation
7. Wire into `App.jsx` if the feature has UI components

## File Storage

| Directory | Contents |
|---|---|
| `backend/data/` | SQLite database |
| `backend/photo_storage/` | Uploaded photos, face crops, style-transferred portraits |
| `backend/voice_storage/` | Voice recordings (WAV/MP3) |
| `assets/` | Generated scene images, avatar images |
