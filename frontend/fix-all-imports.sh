#!/bin/bash
# filepath: frontend/fix-all-imports.sh

echo "🔧 Fixing ALL imports in features..."
echo ""

cd src/features

# ==========================================
# SETUP FEATURE
# ==========================================

echo "📦 Fixing setup/ imports..."

if [ -f "setup/components/CharacterSetup.jsx" ]; then
  sed -i.bak "s|from ['\"]./LoadingAnimation['\"]|from '../../../shared/components'|g" setup/components/CharacterSetup.jsx
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/CharacterSetup.jsx
  echo "  ✅ CharacterSetup.jsx"
fi

if [ -f "setup/components/PrivacyModal.jsx" ]; then
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/PrivacyModal.jsx
  echo "  ✅ PrivacyModal.jsx"
fi

if [ -f "setup/components/LanguageSelector.jsx" ]; then
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" setup/components/LanguageSelector.jsx
  echo "  ✅ LanguageSelector.jsx"
fi

# ==========================================
# AUDIO FEATURE
# ==========================================

echo "📦 Fixing audio/ imports..."

if [ -f "audio/components/VoiceOnlyMode.jsx" ]; then
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/VoiceOnlyMode.jsx
  sed -i.bak "s|from ['\"]../../components/ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/VoiceOnlyMode.jsx
  echo "  ✅ VoiceOnlyMode.jsx"
fi

if [ -f "audio/components/MultimodalControls.jsx" ]; then
  sed -i.bak "s|from ['\"]./ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/MultimodalControls.jsx
  sed -i.bak "s|from ['\"]../../components/ChildFriendlyButton['\"]|from '../../../shared/components'|g" audio/components/MultimodalControls.jsx
  echo "  ✅ MultimodalControls.jsx"
fi

# ==========================================
# STORY FEATURE
# ==========================================

echo "📦 Fixing story/ imports..."

if [ -f "story/components/DualStoryDisplay.jsx" ]; then
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
echo "🔍 Verifying imports..."
echo ""

# Show all import statements to verify
grep -h "import.*from.*shared/components" */components/*.jsx 2>/dev/null | sort -u

echo ""
echo "🚀 Ready to run: npm run dev"