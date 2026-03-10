#!/bin/bash
# filepath: frontend/fix-all-imports-v2.sh

echo "🔧 Fixing ALL imports in features (v2)..."
echo ""

cd src/features

# ==========================================
# SETUP FEATURE
# ==========================================

echo "📦 Fixing setup/ imports..."

if [ -f "setup/components/CharacterSetup.jsx" ]; then
  # Fix default imports to named imports
  sed -i.bak "s|import LoadingAnimation from|import { LoadingAnimation } from|g" setup/components/CharacterSetup.jsx
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" setup/components/CharacterSetup.jsx
  
  # Fix paths
  sed -i.bak "s|from ['\"]./LoadingAnimation['\"]|from '../../../shared/components'|g" setup/components/CharacterSetup.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/CharacterSetup.jsx
  
  echo "  ✅ CharacterSetup.jsx"
fi

if [ -f "setup/components/PrivacyModal.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" setup/components/PrivacyModal.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/PrivacyModal.jsx
  echo "  ✅ PrivacyModal.jsx"
fi

if [ -f "setup/components/LanguageSelector.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" setup/components/LanguageSelector.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/LanguageSelector.jsx
  echo "  ✅ LanguageSelector.jsx"
fi

# ==========================================
# AUDIO FEATURE
# ==========================================

echo "📦 Fixing audio/ imports..."

if [ -f "audio/components/VoiceOnlyMode.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" audio/components/VoiceOnlyMode.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/VoiceOnlyMode.jsx
  sed -i.bak "s|from ['\"]../../components/ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/VoiceOnlyMode.jsx
  echo "  ✅ VoiceOnlyMode.jsx"
fi

if [ -f "audio/components/MultimodalControls.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" audio/components/MultimodalControls.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/MultimodalControls.jsx
  sed -i.bak "s|from ['\"]../../components/ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/MultimodalControls.jsx
  echo "  ✅ MultimodalControls.jsx"
fi

# ==========================================
# STORY FEATURE
# ==========================================

echo "📦 Fixing story/ imports..."

if [ -f "story/components/DualStoryDisplay.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" story/components/DualStoryDisplay.jsx
  sed -i.bak "s|import LoadingAnimation from|import { LoadingAnimation } from|g" story/components/DualStoryDisplay.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" story/components/DualStoryDisplay.jsx
  sed -i.bak "s|from ['\"]../../components/ChildFriendlyButton['\"]|from '../../../shared/components'|g" story/components/DualStoryDisplay.jsx
  sed -i.bak "s|from ['\"]./LoadingAnimation['\"]|from '../../../shared/components'|g" story/components/DualStoryDisplay.jsx
  echo "  ✅ DualStoryDisplay.jsx"
fi

# ==========================================
# SESSION FEATURE
# ==========================================

echo "📦 Fixing session/ imports..."

if [ -f "session/components/MagicMirror.jsx" ]; then
  sed -i.bak "s|import ChildFriendlyButton from|import { ChildFriendlyButton } from|g" session/components/MagicMirror.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" session/components/MagicMirror.jsx
  echo "  ✅ MagicMirror.jsx"
fi

# ==========================================
# CLEANUP
# ==========================================

echo ""
echo "🧹 Cleaning up backup files..."
find . -name "*.bak" -delete

echo ""
echo "✅ All imports fixed!"
echo ""
echo "🔍 Verifying fixed imports..."
echo ""

# Show fixed imports
echo "Named imports found:"
grep -h "import {.*} from.*shared/components" */components/*.jsx 2>/dev/null | sort -u

echo ""
echo "❌ Default imports (should be empty):"
grep -h "import [A-Z][a-zA-Z]* from.*shared/components" */components/*.jsx 2>/dev/null | grep -v "import {" | sort -u

echo ""
echo "🚀 Ready to run: npm run dev"