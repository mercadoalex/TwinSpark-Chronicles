#!/bin/bash
# filepath: frontend/fix-imports.sh

echo "🔧 Fixing imports in all components..."
echo ""

cd src/features

# Fix CharacterSetup.jsx
if [ -f "setup/components/CharacterSetup.jsx" ]; then
  sed -i.bak 's|import LoadingAnimation from "\.\/LoadingAnimation"|import { LoadingAnimation } from "../../../shared/components"|g' setup/components/CharacterSetup.jsx
  sed -i.bak 's|import ChildFriendlyButton from "\.\/ChildFriendlyButton"|import { ChildFriendlyButton } from "../../../shared/components"|g' setup/components/CharacterSetup.jsx
  echo "✅ Fixed setup/components/CharacterSetup.jsx"
fi

# Remove backup files
find . -name "*.bak" -delete

echo ""
echo "✅ Import fixes complete!"