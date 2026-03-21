# TwinSpark Chronicles — Stakeholder Overview

A high-level summary of the product, its current state, and roadmap for non-technical stakeholders.

## Product Summary

TwinSpark Chronicles is an AI-powered interactive storytelling app designed for siblings (ages 6-12) to co-create personalized adventures together. Each child sees the story from their own perspective, making every session a shared but personal experience. The AI adapts to each child's personality, tracks their relationship dynamics, and builds a persistent story world that grows across sessions.

Built for Ale & Sofi.

## How It Works

1. Children set up their characters (name, spirit animal, toy companion)
2. The AI generates a story beat with text, illustrations, audio, and interactive choices
3. Children take turns making choices that steer the narrative
4. The AI remembers past events and weaves them into future stories
5. Sessions are time-limited with parent controls for safety

## Key Differentiators

- **Dual-perspective storytelling** — each child gets their own version of the same story
- **Sibling dynamics modeling** — the AI tracks personality, relationship quality, and complementary skills
- **Persistent world** — locations, characters, and items carry across sessions
- **Family integration** — family photos become art-style characters in scenes; family voice recordings play at story-relevant moments
- **Child safety first** — content filtering, image scanning, parent approval flows, session time limits, emergency stop

## Current State (March 2026)

### What's Built

| Area | Status | Details |
|---|---|---|
| Story generation | ✅ Complete | Gemini 2.0 Flash, dual-perspective, content-filtered |
| Scene illustrations | ⚙️ API ready | Imagen 3 integration built, needs GCP Vertex AI access |
| Voice narration | ⚙️ API ready | Google Cloud TTS with 7 character voice profiles |
| Memory system | ✅ Complete | ChromaDB vector embeddings for cross-beat continuity |
| Sibling dynamics | ✅ Complete | Personality engine, relationship mapper, skills discoverer, narrative directives |
| Family photos | ✅ Complete | Upload, safety scan, face extraction, style transfer, scene compositing |
| Voice recordings | ✅ Complete | Record, normalize, playback integration with story beats |
| Collaborative drawing | ✅ Complete | Real-time sync, persistence, AI integration |
| Session management | ✅ Complete | Time enforcement, pause during generation, extensions, emergency stop |
| Story gallery | ✅ Complete | Auto-archive on session end, storybook reader |
| World persistence | ✅ Complete | Locations, NPCs, items across sessions |
| UI/UX polish | ✅ Complete | Dark glassmorphism theme, animations, sound/haptic feedback, celebrations |
| Content safety | ✅ Complete | Text filtering, image scanning, parent approval |
| Session persistence | ✅ Complete | Auto-save, restore, beacon API on tab close |
| i18n | ✅ Complete | English and Spanish |
| Accessibility | ✅ Complete | Skip links, ARIA live regions, focus management, reduced motion |
| Backend tests | ✅ Complete | 500+ tests across 39 test files (pytest + Hypothesis) |

### What's Not Built Yet

| Area | Status | Blocker |
|---|---|---|
| Scene image generation | Stubbed | Requires GCP project with Vertex AI and Imagen 3 access |
| Avatar pipeline | Stubbed | Depends on Imagen 3 for photo-to-avatar conversion |
| Speech-to-text input | Stubbed | STT service exists but not wired to a provider |
| Emotion detection | Stubbed | Camera service exists but no ML model integrated |
| Production deployment | Ready | Dockerfile exists, needs GCP credentials and Cloud Run setup |

### Spec Coverage

19 feature specs completed, each with requirements, design, and implementation tasks:

1. Database migration
2. Family photo integration
3. Photo UX polish
4. Content safety system
5. Parent approval flow
6. Multimodal input pipeline
7. Performance tuning
8. Sibling dynamics engine
9. Persistent story world
10. Scene audio system
11. Animated story transitions
12. Storybook gallery
13. Child-friendly UI redesign
14. Voice recording system
15. Session resumption
16. Story archival trigger
17. Emergency stop & session limits
18. Drawing UX polish
19. Collaborative drawing
20. Character costume customization (requirements only)
21. Accessibility audit

## Architecture Overview

![System Architecture](../architecture.png)

![AI Agent Architecture](../ai_architecture.png)

The system is a React frontend communicating with a FastAPI backend over WebSocket. The backend coordinates 7 AI agents per story beat:

- **Orchestrator** — the conductor, runs a 10-step pipeline per beat
- **Storyteller** — Gemini 2.0 Flash narrative generation
- **Visual** — Imagen 3 scene illustration
- **Voice** — Google Cloud TTS with emotion-adjusted character voices
- **Memory** — ChromaDB vector embeddings
- **Style Transfer** — family photo → art-style portrait conversion
- **Avatar** — photo-to-avatar pipeline (future)

## User Flow

![User Flow — Setup](../flow01.png)

![User Flow — In-Session](../flow02.png)

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Zustand, CSS custom properties |
| Backend | Python 3.11, FastAPI, WebSocket |
| AI — Story | Google Gemini 2.0 Flash |
| AI — Images | Google Imagen 3 (Vertex AI) |
| AI — Voice | Google Cloud Text-to-Speech |
| AI — Memory | ChromaDB (vector embeddings) |
| Database | SQLite (7 migration files) |
| Storage | Local filesystem (photos, voice recordings, generated images) |
| Testing | pytest, Hypothesis (property-based), 500+ tests |

## Safety and Privacy

- All story text passes through a content filter before reaching children
- Uploaded photos are scanned for safety (BLOCKED / REVIEW / SAFE)
- Photos flagged as REVIEW require explicit parent approval
- Session time limits are enforced both frontend and backend
- Emergency stop with accidental-press protection (2-second hold)
- No data leaves the local machine unless external APIs are configured (Gemini, TTS, Imagen)
- Privacy consent required before any interaction

## Metrics and Quality

- 500+ automated tests with property-based testing (Hypothesis)
- Frontend builds clean with zero diagnostics
- 19 feature specs with full requirements → design → implementation traceability
- Accessibility: skip navigation, ARIA live regions, focus management, reduced motion support
- i18n: English and Spanish

## Roadmap / Next Steps

1. **Imagen 3 access** — Enable scene illustration generation (requires GCP Vertex AI approval)
2. **Production deployment** — Deploy to GCP Cloud Run with Cloud SQL and Cloud Storage
3. **Speech-to-text** — Wire STT service to enable voice commands during story
4. **Emotion detection** — Integrate camera-based emotion detection to adapt story tone
5. **Avatar generation** — Complete photo-to-avatar pipeline once Imagen 3 is available
6. **Analytics dashboard** — Deeper parent insights into learning outcomes and engagement patterns
