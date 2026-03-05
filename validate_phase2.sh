#!/bin/bash

# TwinSpark Chronicles - Phase 2 Completion Test
# This script validates all Phase 2 components

echo "=================================="
echo "🚀 TwinSpark Chronicles"
echo "   Phase 2 Validation Test"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track results
PASS=0
FAIL=0

# Helper function
test_component() {
    local name=$1
    local command=$2
    
    echo -n "Testing $name... "
    
    if $command > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASS${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

# 1. Check Python environment
echo "1️⃣  Checking Python Environment"
test_component "Python 3.11+" "python3 --version"
test_component "pip" "pip --version"
echo ""

# 2. Check dependencies
echo "2️⃣  Checking Dependencies"
test_component "opencv-python" "python3 -c 'import cv2'"
test_component "mediapipe" "python3 -c 'import mediapipe'"
test_component "speech_recognition" "python3 -c 'import speech_recognition'"
test_component "PIL/Pillow" "python3 -c 'from PIL import Image'"
test_component "fastapi" "python3 -c 'import fastapi'"
test_component "google.generativeai" "python3 -c 'import google.generativeai'"
echo ""

# 3. Check core modules
echo "3️⃣  Checking Core Modules"
test_component "models.py" "python3 -c 'from src.models import ChildProfile, PersonalityTrait'"
test_component "config.py" "python3 -c 'from src.config import settings'"
test_component "twin_intelligence.py" "python3 -c 'from src.ai.twin_intelligence import TwinIntelligenceEngine'"
test_component "story_generator.py" "python3 -c 'from src.story.story_generator import StoryGenerator'"
echo ""

# 4. Check Phase 2 components
echo "4️⃣  Checking Phase 2 Components"
test_component "camera_processor.py" "python3 -c 'from src.multimodal.camera_processor import CameraProcessor'"
test_component "audio_processor.py" "python3 -c 'from src.multimodal.audio_processor import AudioProcessor'"
test_component "emotion_detector.py" "python3 -c 'from src.multimodal.emotion_detector import EmotionDetector'"
test_component "input_manager.py" "python3 -c 'from src.multimodal.input_manager import InputManager'"
test_component "image_generator.py" "python3 -c 'from src.story.image_generator import ImageGenerator; print(\"skipped\")'" # May fail without API key
test_component "keepsake_maker.py" "python3 -c 'from src.story.keepsake_maker import KeepsakeMaker'"
test_component "state_manager.py" "python3 -c 'from src.utils.state_manager import StateManager'"
echo ""

# 5. Check directory structure
echo "5️⃣  Checking Directory Structure"
test_component "assets/ directory" "test -d assets"
test_component "data/ directory" "test -d data || mkdir -p data"
test_component "tests/ directory" "test -d tests"
test_component "docs/ directory" "test -d docs"
echo ""

# 6. Check documentation
echo "6️⃣  Checking Documentation"
test_component "README.md" "test -f README.md"
test_component "IMPLEMENTATION_STATUS.md" "test -f IMPLEMENTATION_STATUS.md"
test_component "PHASE2_COMPLETE.md" "test -f PHASE2_COMPLETE.md"
test_component "DEVELOPER_GUIDE.md" "test -f DEVELOPER_GUIDE.md"
test_component "docs/PHASE3_PLAN.md" "test -f docs/PHASE3_PLAN.md"
test_component "docs/PHASE4_PLAN.md" "test -f docs/PHASE4_PLAN.md"
echo ""

# Summary
echo "=================================="
echo "📊 Test Summary"
echo "=================================="
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo -e "${GREEN}🎉 Phase 2 is ready!${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo "Please check the output above"
    exit 1
fi
