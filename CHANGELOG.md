# Changelog

All notable changes to TwinSpark Chronicles will be documented in this file.

## [0.1.0-phase1] - 2026-03-10

### Added
- **Storyteller Agent**: Gemini 2.0 Flash for personalized narratives
- **Voice Agent**: Google Cloud TTS with character-specific voices
- **Memory Agent**: ChromaDB vector store for session continuity
- **Visual Agent**: Imagen 3 for AI-generated scene illustrations
- **Agent Orchestrator**: Coordinates all agents for rich multimodal experiences
- Rich story API endpoint (`/api/story/generate-rich`)
- Session summary endpoint (`/api/session/{id}/summary`)
- Multi-language support (English, Spanish, Hindi)
- Graceful degradation when cloud features unavailable

### Changed
- Restructured backend to `/backend` directory
- Updated frontend geminiService.js to use new endpoints
- Fixed API_URL bug in geminiService

### Fixed
- ChromaDB deprecation warnings
- Voice agent credential handling
- API endpoint consistency

### Infrastructure
- Clean project structure (backend/ + frontend/)
- Moved old files to _old_backup/
- Added start scripts for quick launch
- Updated .gitignore and README.md

### Technical Details
- FastAPI with async/await
- Pydantic models for type safety
- Vector embeddings for memory
- Graceful error handling
- Comprehensive logging

## [0.0.1] - Initial Release

### Added
- Basic storytelling with Gemini
- Character setup flow
- Avatar capture
- Frontend React application
