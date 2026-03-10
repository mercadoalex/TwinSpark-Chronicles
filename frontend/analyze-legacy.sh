#!/bin/bash
# filepath: frontend/analyze-legacy.sh

echo "🔍 Analyzing Legacy Component Usage"
echo "====================================="
echo ""

cd src

echo "📊 Checking imports in App.jsx..."
echo ""

# Check each legacy component
for component in ImageMagnifier MagicMirror ParentDashboard ProfileForm Story; do
  echo "🔎 $component:"
  
  # Check in App.jsx
  if grep -q "import.*$component" App.jsx 2>/dev/null; then
    echo "   ✅ USED in App.jsx"
    grep "import.*$component" App.jsx | sed 's/^/      /'
  else
    echo "   ❌ NOT USED in App.jsx"
  fi
  
  # Check in other files
  USAGE_COUNT=$(grep -r "import.*$component" --include="*.jsx" --include="*.js" . 2>/dev/null | grep -v "components/$component.jsx" | wc -l | tr -d ' ')
  
  if [ "$USAGE_COUNT" -gt 0 ]; then
    echo "   ℹ️  Found $USAGE_COUNT other references"
  fi
  
  echo ""
done

echo "📄 Checking component content..."
echo ""

# Check if components are functional or class components
for component in ImageMagnifier MagicMirror ParentDashboard ProfileForm Story; do
  if [ -f "components/$component.jsx" ]; then
    echo "📝 $component.jsx:"
    
    # Get first 10 lines
    head -n 10 "components/$component.jsx" | sed 's/^/   /'
    echo "   ..."
    echo ""
  fi
done

echo "✅ Analysis complete!"