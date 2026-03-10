#!/bin/bash
# filepath: frontend/create-config.sh

echo "🔧 Creating configuration files..."
echo ""

cd src

# Create config directory
mkdir -p shared/config

# Create constants.js
cat > shared/config/constants.js << 'EOF'
/**
 * Application Constants
 */

export const ENV = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  WS_URL: import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws',
  MODE: import.meta.env.MODE || 'development',
  IS_DEV: import.meta.env.DEV,
  IS_PROD: import.meta.env.PROD
};

export const API_ENDPOINTS = {
  WEBSOCKET: '/ws',
  SESSION_SAVE: '/api/session/save',
  SESSION_LOAD: '/api/session/load',
  ANALYTICS: '/api/analytics',
  HEALTH: '/api/health'
};

export const TIMEOUTS = {
  WEBSOCKET_CONNECT: 5000,
  WEBSOCKET_RECONNECT: 3000,
  API_REQUEST: 10000,
  TTS_MAX_LENGTH: 30000,
  FEEDBACK_DURATION: 2000
};

export const TTS_SETTINGS = {
  rate: 0.9,
  pitch: 1.1,
  volume: 0.8,
  maxLength: 500
};

export const LANGUAGE_VOICES = {
  en: { name: 'Google UK English Female', lang: 'en-GB', fallback: 'en-US' },
  es: { name: 'Google español', lang: 'es-ES', fallback: 'es-MX' },
  fr: { name: 'Google français', lang: 'fr-FR', fallback: 'fr-CA' },
  de: { name: 'Google Deutsch', lang: 'de-DE', fallback: 'de-AT' },
  it: { name: 'Google italiano', lang: 'it-IT', fallback: 'it-CH' },
  pt: { name: 'Google português do Brasil', lang: 'pt-BR', fallback: 'pt-PT' }
};

export const BEEP_FREQUENCIES = {
  success: 800,
  error: 400,
  choice: 600,
  notification: 700
};

export const BEEP_DURATIONS = {
  success: 150,
  error: 300,
  choice: 100,
  notification: 200
};

export const WS_EVENTS = {
  MAKE_CHOICE: 'MAKE_CHOICE',
  CONNECTED: 'connected',
  DISCONNECTED: 'disconnected',
  CREATIVE_ASSET: 'CREATIVE_ASSET',
  STORY_COMPLETE: 'STORY_COMPLETE',
  STATUS: 'STATUS',
  MECHANIC_WARNING: 'MECHANIC_WARNING',
  ERROR: 'error'
};

export const STORAGE_KEYS = {
  LANGUAGE: 'twinspark_language',
  PRIVACY_ACCEPTED: 'twinspark_privacy',
  PROFILES: 'twinspark_profiles',
  SESSION_ID: 'twinspark_session_id',
  AUDIO_ENABLED: 'twinspark_audio_enabled'
};
EOF

echo "✅ Created constants.js"

# Create barrel export
cat > shared/config/index.js << 'EOF'
export {
  ENV,
  API_ENDPOINTS,
  TIMEOUTS,
  TTS_SETTINGS,
  LANGUAGE_VOICES,
  BEEP_FREQUENCIES,
  BEEP_DURATIONS,
  WS_EVENTS,
  STORAGE_KEYS
} from './constants';
EOF

echo "✅ Created config/index.js"
echo ""

# Create .env files
cd ../..

cat > .env.development << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENV=development
EOF

echo "✅ Created .env.development"

cat > .env.example << 'EOF'
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENV=development
EOF

echo "✅ Created .env.example"

echo ""
echo "🎉 Configuration files created successfully!"
echo ""
echo "📂 Structure:"
echo "   src/shared/config/"
echo "   ├── constants.js"
echo "   └── index.js"
echo ""
echo "   .env.development"
echo "   .env.example"
echo ""
echo "🔧 Next: npm run dev"