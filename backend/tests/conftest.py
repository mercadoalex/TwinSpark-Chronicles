"""Shared test fixtures — mock heavy third-party modules so app.main can import."""

import sys
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Pre-populate sys.modules with mocks for packages that may not be installed
# in the test environment.  This must happen BEFORE any app.* import that
# transitively pulls in these packages.
# ---------------------------------------------------------------------------

_MOCK_MODULES = {
    # Google AI / Cloud
    "google.generativeai": MagicMock(),
    "google.cloud.speech_v1": MagicMock(),
    "google.cloud.texttospeech_v1": MagicMock(),
    "google.cloud.texttospeech": MagicMock(),
    "google.cloud.aiplatform": MagicMock(),
    "google.cloud.storage": MagicMock(),
    # Vertex AI (visual_agent.py: from vertexai.preview.vision_models import ...)
    "vertexai": MagicMock(),
    "vertexai.preview": MagicMock(),
    "vertexai.preview.vision_models": MagicMock(),
    # ChromaDB (memory_agent.py)
    "chromadb": MagicMock(),
}

for mod_name, mock in _MOCK_MODULES.items():
    sys.modules.setdefault(mod_name, mock)
