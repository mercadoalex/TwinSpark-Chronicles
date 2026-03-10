#!/bin/bash
# filepath: frontend/create-services.sh

echo "🏗️ Creating service layer structure..."

# Create directories
mkdir -p src/features/session/services
mkdir -p src/features/audio/services
mkdir -p src/features/story/services

# Create placeholder files
touch src/features/session/services/websocketService.js
touch src/features/audio/services/ttsService.js
touch src/features/audio/services/audioFeedbackService.js
touch src/features/story/services/storyService.js

echo "✅ Service structure created!"
echo ""
echo "📁 Created:"
echo "  - src/features/session/services/websocketService.js"
echo "  - src/features/audio/services/ttsService.js"
echo "  - src/features/audio/services/audioFeedbackService.js"
echo "  - src/features/story/services/storyService.js"
echo ""
echo "📝 Now copy the code into each file!"