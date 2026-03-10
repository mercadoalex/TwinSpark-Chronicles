#!/bin/bash
# filepath: frontend/migrate-legacy-final.sh

echo "🚚 Final Legacy Component Migration & Cleanup"
echo "=============================================="
echo ""

cd src

# ==========================================
# PHASE 1: Migrate Used Components
# ==========================================

echo "📦 Phase 1: Migrating actively used components..."
echo ""

# MagicMirror → Session Feature
if [ -f "components/MagicMirror.jsx" ]; then
  mv components/MagicMirror.jsx features/session/components/
  echo "✅ Moved MagicMirror → features/session/components/"
  
  # Update session barrel export
  if ! grep -q "MagicMirror" features/session/index.js; then
    echo "" >> features/session/index.js
    echo "export { default as MagicMirror } from './components/MagicMirror';" >> features/session/index.js
    echo "✅ Updated features/session/index.js"
  fi
else
  echo "⚠️  MagicMirror.jsx already moved or not found"
fi

echo ""

# ParentDashboard → Setup Feature
if [ -f "components/ParentDashboard.jsx" ]; then
  mv components/ParentDashboard.jsx features/setup/components/
  echo "✅ Moved ParentDashboard → features/setup/components/"
  
  # Update setup barrel export
  if ! grep -q "ParentDashboard" features/setup/index.js; then
    echo "" >> features/setup/index.js
    echo "export { default as ParentDashboard } from './components/ParentDashboard';" >> features/setup/index.js
    echo "✅ Updated features/setup/index.js"
  fi
else
  echo "⚠️  ParentDashboard.jsx already moved or not found"
fi

echo ""

# Check for ParentDashboard.css
if [ -f "components/ParentDashboard.css" ]; then
  mv components/ParentDashboard.css features/setup/components/
  echo "✅ Moved ParentDashboard.css → features/setup/components/"
fi

echo ""

# ==========================================
# PHASE 2: Archive Deprecated Components
# ==========================================

echo "🗑️  Phase 2: Archiving deprecated components..."
echo ""

mkdir -p ../archived-components

# ImageMagnifier - Not used
if [ -f "components/ImageMagnifier.jsx" ]; then
  mv components/ImageMagnifier.jsx ../archived-components/
  echo "✅ Archived ImageMagnifier.jsx (not used)"
fi

# ProfileForm - Replaced by CharacterSetup
if [ -f "components/ProfileForm.jsx" ]; then
  mv components/ProfileForm.jsx ../archived-components/
  echo "✅ Archived ProfileForm.jsx (replaced by CharacterSetup)"
fi

# Story.jsx - Replaced by DualStoryDisplay
if [ -f "components/Story.jsx" ]; then
  mv components/Story.jsx ../archived-components/
  echo "✅ Archived Story.jsx (replaced by DualStoryDisplay)"
fi

echo ""

# ==========================================
# PHASE 3: Check for Dashboard Dependencies
# ==========================================

echo "🔍 Phase 3: Checking for dashboard dependencies..."
echo ""

# Check if dashboard has subdirectories
if [ -d "components/dashboard" ]; then
  echo "⚠️  Found components/dashboard/ directory"
  echo "   Moving to features/setup/components/dashboard/"
  
  mkdir -p features/setup/components/dashboard
  mv components/dashboard/* features/setup/components/dashboard/
  rmdir components/dashboard
  
  echo "✅ Moved dashboard components"
fi

echo ""

# ==========================================
# PHASE 4: Clean Up Empty Directories
# ==========================================

echo "🧹 Phase 4: Cleaning up..."
echo ""

# Check if components/ is empty or only has leftover files
REMAINING_FILES=$(find components -type f 2>/dev/null | wc -l | tr -d ' ')

if [ "$REMAINING_FILES" -eq 0 ]; then
  echo "✅ components/ directory is empty"
  echo "   Removing components/ directory..."
  rmdir components
  echo "✅ Removed empty components/ directory"
elif [ "$REMAINING_FILES" -le 2 ]; then
  echo "⚠️  Found $REMAINING_FILES remaining files in components/:"
  find components -type f
  echo ""
  echo "   Review these files manually"
else
  echo "⚠️  Found $REMAINING_FILES files in components/"
  echo "   Please review manually before deleting"
fi

echo ""

# ==========================================
# PHASE 5: Summary & Next Steps
# ==========================================

echo "📊 ============================================"
echo "   Migration Summary"
echo "=============================================="
echo ""

echo "✅ Migrated to features/:"
echo "   • MagicMirror → session/components/"
echo "   • ParentDashboard → setup/components/"
echo ""

echo "🗑️  Archived (not used):"
echo "   • ImageMagnifier.jsx → ../archived-components/"
echo "   • ProfileForm.jsx → ../archived-components/"
echo "   • Story.jsx → ../archived-components/"
echo ""

if [ -d "components" ]; then
  echo "⚠️  components/ directory still exists"
  echo "   Remaining files: $REMAINING_FILES"
else
  echo "✅ components/ directory removed"
fi

echo ""
echo "🔧 Next Steps:"
echo ""
echo "1. Update App.jsx imports:"
echo "   ❌ import MagicMirror from './components/MagicMirror';"
echo "   ✅ import { MagicMirror } from './features/session';"
echo ""
echo "   ❌ import ParentDashboard from './components/ParentDashboard';"
echo "   ✅ import { ParentDashboard } from './features/setup';"
echo ""
echo "2. Test the application:"
echo "   npm run dev"
echo ""
echo "3. If everything works, delete archived components:"
echo "   rm -rf ../archived-components/"
echo ""
echo "✅ Migration complete!"