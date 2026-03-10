#!/bin/bash
# filepath: frontend/verify-architecture.sh

echo "🔍 ========================================"
echo "   TwinSpark Architecture Verification"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check if file exists
check_file() {
  if [ -f "$1" ]; then
    echo -e "${GREEN}✓${NC} $1"
    return 0
  else
    echo -e "${RED}✗${NC} MISSING: $1"
    ((ERRORS++))
    return 1
  fi
}

# Function to check if directory exists
check_dir() {
  if [ -d "$1" ]; then
    echo -e "${GREEN}✓${NC} $1/"
    return 0
  else
    echo -e "${RED}✗${NC} MISSING DIR: $1/"
    ((ERRORS++))
    return 1
  fi
}

# Function to check for old/deprecated files
check_deprecated() {
  if [ -e "$1" ]; then
    echo -e "${YELLOW}⚠${NC}  DEPRECATED (should remove): $1"
    ((WARNINGS++))
    return 1
  else
    echo -e "${GREEN}✓${NC} (cleaned) $1"
    return 0
  fi
}

echo "📂 PHASE 1: Configuration Layer"
echo "================================"
check_dir "src/shared/config"
check_file "src/shared/config/env.config.js"
check_file "src/shared/config/theme.config.js"
check_file "src/shared/config/constants.js"
check_file "src/shared/config/audio.config.js"
check_file "src/shared/config/index.js"
echo ""

echo "🛠️  PHASE 1: Utilities"
echo "================================"
check_dir "src/shared/utils"
check_file "src/shared/utils/validation.js"
check_file "src/shared/utils/formatting.js"
check_file "src/shared/utils/index.js"
echo ""

echo "📦 PHASE 1: Environment Files"
echo "================================"
check_file ".env.development"
check_file ".env.production"
check_file ".env.example"
echo ""

echo "🔌 PHASE 2: Services - Session"
echo "================================"
check_dir "src/features/session/services"
check_file "src/features/session/services/websocketService.js"
echo ""

echo "🔊 PHASE 2: Services - Audio"
echo "================================"
check_dir "src/features/audio/services"
check_file "src/features/audio/services/ttsService.js"
check_file "src/features/audio/services/audioFeedbackService.js"
echo ""

echo "📖 PHASE 2: Services - Story"
echo "================================"
check_dir "src/features/story/services"
check_file "src/features/story/services/storyService.js"
echo ""

echo "🪝 PHASE 3: Hooks - Session"
echo "================================"
check_dir "src/features/session/hooks"
check_file "src/features/session/hooks/useWebSocket.js"
echo ""

echo "🪝 PHASE 3: Hooks - Audio"
echo "================================"
check_dir "src/features/audio/hooks"
check_file "src/features/audio/hooks/useAudio.js"
check_file "src/features/audio/hooks/useAudioFeedback.js"
echo ""

echo "🪝 PHASE 3: Hooks - Story"
echo "================================"
check_dir "src/features/story/hooks"
check_file "src/features/story/hooks/useStory.js"
check_file "src/features/story/hooks/useStoryAssets.js"
echo ""

echo "🪝 PHASE 3: Shared Hooks"
echo "================================"
check_dir "src/shared/hooks"
check_file "src/shared/hooks/useLocalStorage.js"
check_file "src/shared/hooks/useDebounce.js"
check_file "src/shared/hooks/index.js"
echo ""

echo "🧹 CLEANUP: Deprecated Files/Folders"
echo "================================"
check_deprecated "src/hooks"
check_deprecated "src/utils"
check_deprecated "src/config"
check_deprecated "src/services"
echo ""

echo "📦 CLEANUP: Old Component Structure"
echo "================================"
# Check if components are still in src/components (should eventually move to features)
if [ -d "src/components" ]; then
  echo -e "${YELLOW}⚠${NC}  src/components/ still exists (will refactor later)"
  ((WARNINGS++))
else
  echo -e "${GREEN}✓${NC} Components properly organized"
fi
echo ""

echo "🔍 IMPORT VALIDATION"
echo "================================"

# Check for imports from old structure
echo "Checking for deprecated import paths..."

OLD_IMPORTS=$(grep -r "from ['\"].*\/hooks\/" src/ --include="*.js" --include="*.jsx" 2>/dev/null | grep -v "features\|shared" | wc -l | xargs)
if [ "$OLD_IMPORTS" -gt 0 ]; then
  echo -e "${RED}✗${NC} Found $OLD_IMPORTS deprecated import(s) in:"
  grep -r "from ['\"].*\/hooks\/" src/ --include="*.js" --include="*.jsx" 2>/dev/null | grep -v "features\|shared" | head -5
  ((ERRORS++))
else
  echo -e "${GREEN}✓${NC} No deprecated hook imports found"
fi

OLD_CONFIG_IMPORTS=$(grep -r "from ['\"].*\/config\/" src/ --include="*.js" --include="*.jsx" 2>/dev/null | grep -v "shared/config" | wc -l | xargs)
if [ "$OLD_CONFIG_IMPORTS" -gt 0 ]; then
  echo -e "${RED}✗${NC} Found $OLD_CONFIG_IMPORTS deprecated config import(s)"
  ((ERRORS++))
else
  echo -e "${GREEN}✓${NC} No deprecated config imports found"
fi
echo ""

echo "📊 SUMMARY"
echo "================================"
echo -e "Errors:   ${RED}$ERRORS${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
  echo -e "${GREEN}✅ Architecture verification PASSED!${NC}"
  echo "🎉 Everything is in order!"
  exit 0
elif [ $ERRORS -eq 0 ]; then
  echo -e "${YELLOW}⚠️  Architecture verification passed with warnings${NC}"
  echo "💡 Review warnings above"
  exit 0
else
  echo -e "${RED}❌ Architecture verification FAILED${NC}"
  echo "🔧 Fix errors above before continuing"
  exit 1
fi