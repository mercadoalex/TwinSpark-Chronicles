#!/bin/bash

echo "🔍 Finding all deprecated imports..."
echo ""

echo "1️⃣ Searching for old hook imports..."
grep -rn "from ['\"]\.\.\/hooks\/" src/components/ --include="*.js" --include="*.jsx" 2>/dev/null

echo ""
echo "2️⃣ Searching for old utils imports..."
grep -rn "from ['\"]\.\.\/utils\/" src/components/ --include="*.js" --include="*.jsx" 2>/dev/null

echo ""
echo "3️⃣ Searching for old config imports..."
grep -rn "from ['\"]\.\.\/config\/" src/components/ --include="*.js" --include="*.jsx" 2>/dev/null

echo ""
echo "4️⃣ Searching for old service imports..."
grep -rn "from ['\"]\.\.\/services\/" src/components/ --include="*.js" --include="*.jsx" 2>/dev/null

echo ""
echo "✅ Search complete!"