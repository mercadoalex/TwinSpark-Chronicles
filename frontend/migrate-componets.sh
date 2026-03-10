#!/bin/bash
# filepath: frontend/migrate-components.sh

echo "🚚 Migrating components to new structure..."
echo ""

cd src

# ==========================================
# PHASE 1: Create Directory Structure
# ==========================================

echo "📁 Creating directory structure..."

mkdir -p features/setup/components
mkdir -p features/story/components
mkdir -p features/audio/components
mkdir -p features/session/components

mkdir -p shared/components/Button
mkdir -p shared/components/Modal
mkdir -p shared/components/Loading
mkdir -p shared/components/Feedback
mkdir -p shared/components/Layout

echo "✅ Directories created"
echo ""

# ==========================================
# PHASE 2: Move Components
# ==========================================

echo "🔄 Moving components..."

# Setup
[ -f "components/PrivacyModal.jsx" ] && mv components/PrivacyModal.jsx features/setup/components/ && echo "✅ Moved PrivacyModal"
[ -f "components/LanguageSelector.jsx" ] && mv components/LanguageSelector.jsx features/setup/components/ && echo "✅ Moved LanguageSelector"
[ -f "components/CharacterSetup.jsx" ] && mv components/CharacterSetup.jsx features/setup/components/ && echo "✅ Moved CharacterSetup"

# Story
[ -f "components/DualStoryDisplay.jsx" ] && mv components/DualStoryDisplay.jsx features/story/components/ && echo "✅ Moved DualStoryDisplay"

# Audio
[ -f "components/VoiceOnlyMode.jsx" ] && mv components/VoiceOnlyMode.jsx features/audio/components/ && echo "✅ Moved VoiceOnlyMode"
[ -f "components/MultimodalControls.jsx" ] && mv components/MultimodalControls.jsx features/audio/components/ && echo "✅ Moved MultimodalControls"

# Shared - Button
[ -f "components/ChildFriendlyButton.jsx" ] && mv components/ChildFriendlyButton.jsx shared/components/Button/ && echo "✅ Moved ChildFriendlyButton"

# Shared - Modal
[ -f "components/AlertModal.jsx" ] && mv components/AlertModal.jsx shared/components/Modal/ && echo "✅ Moved AlertModal"
[ -f "components/ExitModal.jsx" ] && mv components/ExitModal.jsx shared/components/Modal/ && echo "✅ Moved ExitModal"

# Shared - Loading
[ -f "components/LoadingAnimation.jsx" ] && mv components/LoadingAnimation.jsx shared/components/Loading/ && echo "✅ Moved LoadingAnimation"

# Shared - Feedback
[ -f "components/VisualFeedback.jsx" ] && mv components/VisualFeedback.jsx shared/components/Feedback/ && echo "✅ Moved VisualFeedback"

echo ""

# ==========================================
# PHASE 3: Create New Components
# ==========================================

echo "📝 Creating new components..."

# SessionStatus
if [ ! -f "features/session/components/SessionStatus.jsx" ]; then
cat > features/session/components/SessionStatus.jsx << 'EOF'
import React from 'react';
import { useSessionStore } from '../../../stores/sessionStore';

export default function SessionStatus({ t }) {
  const { isConnected, connectionState, error } = useSessionStore();

  const getStatusColor = () => {
    if (error) return '#ef4444';
    if (isConnected) return '#8b5cf6';
    if (connectionState === 'CONNECTING') return '#f59e0b';
    return 'rgba(255,255,255,0.7)';
  };

  const getStatusText = () => {
    if (error) return error;
    if (isConnected) return t?.connected || 'Connected';
    if (connectionState === 'CONNECTING') return t?.connecting || 'Connecting...';
    return 'Disconnected';
  };

  return (
    <p style={{
      fontSize: '1.2rem',
      color: getStatusColor(),
      marginBottom: '30px',
      textAlign: 'center',
      fontWeight: 500
    }}>
      {getStatusText()}
    </p>
  );
}
EOF
echo "✅ Created SessionStatus.jsx"
fi

# AppContainer
if [ ! -f "shared/components/Layout/AppContainer.jsx" ]; then
cat > shared/components/Layout/AppContainer.jsx << 'EOF'
import React from 'react';

export default function AppContainer({ children }) {
  return (
    <div className="app-container" style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '20px'
    }}>
      {children}
    </div>
  );
}
EOF
echo "✅ Created AppContainer.jsx"
fi

echo ""
echo "🎉 Component migration complete!"
echo ""
echo "📊 Summary:"
echo "   ✅ Setup: 3 components"
echo "   ✅ Story: 1 component"
echo "   ✅ Audio: 2 components"
echo "   ✅ Session: 1 component"
echo "   ✅ Shared: 6 components"
echo ""
echo "Next step: Run ./create-barrel-exports.sh"