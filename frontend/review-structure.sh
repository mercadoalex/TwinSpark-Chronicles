#!/bin/bash
# filepath: frontend/review-structure.sh

echo "🔍 ========================================"
echo "   TwinSpark Project Structure Review"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

# ==========================================
# 1. ROOT STRUCTURE
# ==========================================

echo "📁 ROOT LEVEL FILES"
echo "================================"
ls -la | grep -E "^-" | awk '{print $9}' | grep -E "\.(json|js|sh|md)$"
echo ""

# ==========================================
# 2. SRC STRUCTURE
# ==========================================

echo "📁 SRC/ STRUCTURE"
echo "================================"
if [ -d "src" ]; then
  echo "✅ src/ exists"
  ls -la src/ | grep "^d" | awk '{print "   " $9}' | grep -v "^\.$" | grep -v "^\.\.$"
else
  echo "❌ src/ NOT FOUND"
fi
echo ""

# ==========================================
# 3. FEATURES STRUCTURE
# ==========================================

echo "📦 FEATURES/ STRUCTURE"
echo "================================"

if [ -d "src/features" ]; then
  echo "✅ features/ exists"
  
  # Setup
  if [ -d "src/features/setup" ]; then
    echo "   ✅ setup/"
    [ -d "src/features/setup/components" ] && echo "      ✅ components/" || echo "      ❌ components/ MISSING"
    [ -f "src/features/setup/index.js" ] && echo "      ✅ index.js" || echo "      ❌ index.js MISSING"
    
    if [ -d "src/features/setup/components" ]; then
      echo "         Components:"
      ls src/features/setup/components/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    fi
  else
    echo "   ❌ setup/ MISSING"
  fi
  
  # Story
  if [ -d "src/features/story" ]; then
    echo "   ✅ story/"
    [ -d "src/features/story/components" ] && echo "      ✅ components/" || echo "      ❌ components/ MISSING"
    [ -d "src/features/story/hooks" ] && echo "      ✅ hooks/" || echo "      ⚠️  hooks/ missing"
    [ -d "src/features/story/services" ] && echo "      ✅ services/" || echo "      ⚠️  services/ missing"
    [ -f "src/features/story/index.js" ] && echo "      ✅ index.js" || echo "      ❌ index.js MISSING"
    
    if [ -d "src/features/story/components" ]; then
      echo "         Components:"
      ls src/features/story/components/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    fi
  else
    echo "   ❌ story/ MISSING"
  fi
  
  # Audio
  if [ -d "src/features/audio" ]; then
    echo "   ✅ audio/"
    [ -d "src/features/audio/components" ] && echo "      ✅ components/" || echo "      ❌ components/ MISSING"
    [ -d "src/features/audio/hooks" ] && echo "      ✅ hooks/" || echo "      ❌ hooks/ MISSING"
    [ -d "src/features/audio/services" ] && echo "      ✅ services/" || echo "      ❌ services/ MISSING"
    [ -f "src/features/audio/index.js" ] && echo "      ✅ index.js" || echo "      ❌ index.js MISSING"
    
    if [ -d "src/features/audio/components" ]; then
      echo "         Components:"
      ls src/features/audio/components/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    fi
  else
    echo "   ❌ audio/ MISSING"
  fi
  
  # Session
  if [ -d "src/features/session" ]; then
    echo "   ✅ session/"
    [ -d "src/features/session/components" ] && echo "      ✅ components/" || echo "      ❌ components/ MISSING"
    [ -d "src/features/session/hooks" ] && echo "      ✅ hooks/" || echo "      ❌ hooks/ MISSING"
    [ -d "src/features/session/services" ] && echo "      ✅ services/" || echo "      ❌ services/ MISSING"
    [ -f "src/features/session/index.js" ] && echo "      ✅ index.js" || echo "      ❌ index.js MISSING"
    
    if [ -d "src/features/session/components" ]; then
      echo "         Components:"
      ls src/features/session/components/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    fi
  else
    echo "   ❌ session/ MISSING"
  fi
  
else
  echo "❌ features/ NOT FOUND"
fi
echo ""

# ==========================================
# 4. SHARED STRUCTURE
# ==========================================

echo "🔧 SHARED/ STRUCTURE"
echo "================================"

if [ -d "src/shared" ]; then
  echo "✅ shared/ exists"
  
  # Config
  if [ -d "src/shared/config" ]; then
    echo "   ✅ config/"
    ls src/shared/config/*.js 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/      - /'
  else
    echo "   ❌ config/ MISSING"
  fi
  
  # Utils
  if [ -d "src/shared/utils" ]; then
    echo "   ✅ utils/"
    ls src/shared/utils/*.js 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/      - /'
  else
    echo "   ❌ utils/ MISSING"
  fi
  
  # Hooks
  if [ -d "src/shared/hooks" ]; then
    echo "   ✅ hooks/"
    ls src/shared/hooks/*.js 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/      - /'
  else
    echo "   ❌ hooks/ MISSING"
  fi
  
  # Components
  if [ -d "src/shared/components" ]; then
    echo "   ✅ components/"
    [ -f "src/shared/components/index.js" ] && echo "      ✅ index.js (master barrel)" || echo "      ❌ index.js MISSING"
    
    # Button
    if [ -d "src/shared/components/Button" ]; then
      echo "      ✅ Button/"
      [ -f "src/shared/components/Button/index.js" ] && echo "         ✅ index.js" || echo "         ❌ index.js MISSING"
      ls src/shared/components/Button/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    else
      echo "      ❌ Button/ MISSING"
    fi
    
    # Modal
    if [ -d "src/shared/components/Modal" ]; then
      echo "      ✅ Modal/"
      [ -f "src/shared/components/Modal/index.js" ] && echo "         ✅ index.js" || echo "         ❌ index.js MISSING"
      ls src/shared/components/Modal/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    else
      echo "      ❌ Modal/ MISSING"
    fi
    
    # Loading
    if [ -d "src/shared/components/Loading" ]; then
      echo "      ✅ Loading/"
      [ -f "src/shared/components/Loading/index.js" ] && echo "         ✅ index.js" || echo "         ❌ index.js MISSING"
      ls src/shared/components/Loading/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    else
      echo "      ❌ Loading/ MISSING"
    fi
    
    # Feedback
    if [ -d "src/shared/components/Feedback" ]; then
      echo "      ✅ Feedback/"
      [ -f "src/shared/components/Feedback/index.js" ] && echo "         ✅ index.js" || echo "         ❌ index.js MISSING"
      ls src/shared/components/Feedback/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    else
      echo "      ❌ Feedback/ MISSING"
    fi
    
    # Layout
    if [ -d "src/shared/components/Layout" ]; then
      echo "      ✅ Layout/"
      [ -f "src/shared/components/Layout/index.js" ] && echo "         ✅ index.js" || echo "         ❌ index.js MISSING"
      ls src/shared/components/Layout/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/         - /'
    else
      echo "      ❌ Layout/ MISSING"
    fi
    
  else
    echo "   ❌ components/ MISSING"
  fi
  
else
  echo "❌ shared/ NOT FOUND"
fi
echo ""

# ==========================================
# 5. STORES STRUCTURE
# ==========================================

echo "🗄️  STORES/ STRUCTURE"
echo "================================"

if [ -d "src/stores" ]; then
  echo "✅ stores/ exists"
  [ -f "src/stores/index.js" ] && echo "   ✅ index.js (barrel)" || echo "   ❌ index.js MISSING"
  [ -f "src/stores/sessionStore.js" ] && echo "   ✅ sessionStore.js" || echo "   ❌ sessionStore.js MISSING"
  [ -f "src/stores/storyStore.js" ] && echo "   ✅ storyStore.js" || echo "   ❌ storyStore.js MISSING"
  [ -f "src/stores/audioStore.js" ] && echo "   ✅ audioStore.js" || echo "   ❌ audioStore.js MISSING"
  [ -f "src/stores/setupStore.js" ] && echo "   ✅ setupStore.js" || echo "   ❌ setupStore.js MISSING"
else
  echo "❌ stores/ NOT FOUND"
fi
echo ""

# ==========================================
# 6. LEGACY COMPONENTS
# ==========================================

echo "🗂️  LEGACY COMPONENTS/"
echo "================================"

if [ -d "src/components" ]; then
  echo "⚠️  components/ still exists (legacy)"
  echo "   Remaining files:"
  ls src/components/*.jsx 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^/   - /'
  
  COMPONENT_COUNT=$(ls src/components/*.jsx 2>/dev/null | wc -l)
  if [ "$COMPONENT_COUNT" -eq 0 ]; then
    echo "   ✅ Empty - Safe to delete"
  else
    echo "   ⚠️  $COMPONENT_COUNT files remaining - Review before deleting"
  fi
else
  echo "✅ components/ removed (clean)"
fi
echo ""

# ==========================================
# 7. ENVIRONMENT FILES
# ==========================================

echo "🌍 ENVIRONMENT FILES"
echo "================================"
[ -f ".env.development" ] && echo "✅ .env.development" || echo "❌ .env.development MISSING"
[ -f ".env.production" ] && echo "✅ .env.production" || echo "❌ .env.production MISSING"
[ -f ".env.example" ] && echo "✅ .env.example" || echo "❌ .env.example MISSING"
echo ""

# ==========================================
# 8. KEY APP FILES
# ==========================================

echo "📄 KEY APPLICATION FILES"
echo "================================"
[ -f "src/App.jsx" ] && echo "✅ App.jsx" || echo "❌ App.jsx MISSING"
[ -f "src/App.css" ] && echo "✅ App.css" || echo "❌ App.css MISSING"
[ -f "src/main.jsx" ] && echo "✅ main.jsx" || echo "❌ main.jsx MISSING"
[ -f "src/index.css" ] && echo "✅ index.css" || echo "❌ index.css MISSING"
echo ""

# ==========================================
# 9. PACKAGE DEPENDENCIES
# ==========================================

echo "📦 CRITICAL DEPENDENCIES"
echo "================================"
if [ -f "package.json" ]; then
  echo "Checking package.json..."
  
  grep -q "zustand" package.json && echo "✅ zustand installed" || echo "❌ zustand NOT INSTALLED"
  grep -q "lucide-react" package.json && echo "✅ lucide-react installed" || echo "⚠️  lucide-react missing"
  grep -q "react" package.json && echo "✅ react installed" || echo "❌ react NOT INSTALLED"
  grep -q "vite" package.json && echo "✅ vite installed" || echo "❌ vite NOT INSTALLED"
else
  echo "❌ package.json NOT FOUND"
fi
echo ""

# ==========================================
# 10. SUMMARY & RECOMMENDATIONS
# ==========================================

echo "📊 ========================================"
echo "   SUMMARY & RECOMMENDATIONS"
echo "=========================================="
echo ""

# Count files
FEATURE_COUNT=$(find src/features -name "*.jsx" 2>/dev/null | wc -l | tr -d ' ')
SHARED_COUNT=$(find src/shared/components -name "*.jsx" 2>/dev/null | wc -l | tr -d ' ')
STORE_COUNT=$(find src/stores -name "*.js" 2>/dev/null | wc -l | tr -d ' ')
LEGACY_COUNT=$(find src/components -name "*.jsx" 2>/dev/null | wc -l | tr -d ' ')

echo "📈 Component Counts:"
echo "   Features:     $FEATURE_COUNT components"
echo "   Shared:       $SHARED_COUNT components"
echo "   Stores:       $STORE_COUNT stores"
echo "   Legacy:       $LEGACY_COUNT components (should be 0)"
echo ""

echo "🎯 Next Actions:"
if [ ! -d "src/features/setup/components" ]; then
  echo "   ❗ RUN: ./migrate-componets.sh"
fi

if [ ! -f "src/features/setup/index.js" ]; then
  echo "   ❗ RUN: ./create-barrel-exports.sh"
fi

if [ "$LEGACY_COUNT" -gt 0 ]; then
  echo "   ⚠️  Review remaining legacy components"
fi

if [ ! -f ".env.development" ]; then
  echo "   ❗ CREATE: .env files"
fi

if ! grep -q "zustand" package.json 2>/dev/null; then
  echo "   ❗ RUN: npm install zustand"
fi

echo ""
echo "✅ Review complete!"