#!/bin/bash
# filepath: frontend/create-barrel-exports.sh

echo "📦 Creating barrel export files..."

# Setup
cat > src/features/setup/index.js << 'EOF'
/**
 * Setup Feature Barrel Export
 */

export { default as PrivacyModal } from './components/PrivacyModal';
export { default as LanguageSelector } from './components/LanguageSelector';
export { default as CharacterSetup } from './components/CharacterSetup';
EOF
echo "✅ Created features/setup/index.js"

# Story
cat > src/features/story/index.js << 'EOF'
/**
 * Story Feature Barrel Export
 */

export { default as DualStoryDisplay } from './components/DualStoryDisplay';
EOF
echo "✅ Created features/story/index.js"

# Audio
cat > src/features/audio/index.js << 'EOF'
/**
 * Audio Feature Barrel Export
 */

export { default as VoiceOnlyMode } from './components/VoiceOnlyMode';
export { default as MultimodalControls } from './components/MultimodalControls';
EOF
echo "✅ Created features/audio/index.js"

# Session
cat > src/features/session/index.js << 'EOF'
/**
 * Session Feature Barrel Export
 */

export { default as SessionStatus } from './components/SessionStatus';
EOF
echo "✅ Created features/session/index.js"

# Shared - Button
cat > src/shared/components/Button/index.js << 'EOF'
export { default as ChildFriendlyButton } from './ChildFriendlyButton';
EOF
echo "✅ Created shared/components/Button/index.js"

# Shared - Modal
cat > src/shared/components/Modal/index.js << 'EOF'
export { default as AlertModal } from './AlertModal';
export { default as ExitModal } from './ExitModal';
EOF
echo "✅ Created shared/components/Modal/index.js"

# Shared - Loading
cat > src/shared/components/Loading/index.js << 'EOF'
export { default as LoadingAnimation } from './LoadingAnimation';
EOF
echo "✅ Created shared/components/Loading/index.js"

# Shared - Feedback
cat > src/shared/components/Feedback/index.js << 'EOF'
export { useFeedback } from './VisualFeedback';
EOF
echo "✅ Created shared/components/Feedback/index.js"

# Shared - Layout
cat > src/shared/components/Layout/index.js << 'EOF'
export { default as AppContainer } from './AppContainer';
EOF
echo "✅ Created shared/components/Layout/index.js"

# Shared - Master
cat > src/shared/components/index.js << 'EOF'
/**
 * Shared Components Barrel Export
 */

export * from './Button';
export * from './Modal';
export * from './Loading';
export * from './Feedback';
export * from './Layout';
EOF
echo "✅ Created shared/components/index.js"

echo ""
echo "🎉 All barrel export files created successfully!"