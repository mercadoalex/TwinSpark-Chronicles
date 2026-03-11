#!/bin/bash
# filepath: frontend/create-avatar-feature.sh

echo "📸 Creating Avatar Feature..."
echo ""

cd src/features

# Create structure
mkdir -p avatar/components
mkdir -p avatar/hooks
mkdir -p avatar/services

echo "📁 Folders created"
echo ""

# ===========================================
# HOOKS
# ===========================================

# Create useCamera.js
cat > avatar/hooks/useCamera.js << 'EOF'
import { useState, useRef, useEffect } from 'react';

export function useCamera() {
  const [isActive, setIsActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
      });
      setStream(mediaStream);
      if (videoRef.current) videoRef.current.srcObject = mediaStream;
      setIsActive(true);
      setError(null);
    } catch (err) {
      console.error('Camera error:', err);
      setError('No se pudo acceder a la cámara');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
      setIsActive(false);
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current) return null;
    const canvas = document.createElement('canvas');
    const video = videoRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg', 0.8);
  };

  useEffect(() => () => stopCamera(), []);

  return { videoRef, isActive, error, startCamera, stopCamera, capturePhoto };
}
EOF

echo "✅ Created useCamera.js"

# Create useAvatarGeneration.js
cat > avatar/hooks/useAvatarGeneration.js << 'EOF'
import { useState } from 'react';
import { avatarService } from '../services/avatarService';

export function useAvatarGeneration() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedAvatar, setGeneratedAvatar] = useState(null);
  const [error, setError] = useState(null);

  const generateAvatar = async (photoBase64, metadata) => {
    setIsGenerating(true);
    setError(null);
    try {
      const avatar = await avatarService.generateAvatar({
        photo: photoBase64,
        name: metadata.name,
        gender: metadata.gender,
        spiritAnimal: metadata.spiritAnimal,
        toyName: metadata.toyName,
        style: 'child-friendly'
      });
      setGeneratedAvatar(avatar);
      return avatar;
    } catch (err) {
      console.error('Avatar generation error:', err);
      setError('No se pudo generar el avatar');
      throw err;
    } finally {
      setIsGenerating(false);
    }
  };

  const resetAvatar = () => {
    setGeneratedAvatar(null);
    setError(null);
  };

  return { isGenerating, generatedAvatar, error, generateAvatar, resetAvatar };
}
EOF

echo "✅ Created useAvatarGeneration.js"

# ===========================================
# SERVICES
# ===========================================

cat > avatar/services/avatarService.js << 'EOF'
import { ENV, API_ENDPOINTS } from '../../../shared/config';

class AvatarService {
  async generateAvatar({ photo, name, gender, spiritAnimal, toyName, style }) {
    try {
      const response = await fetch(`${ENV.API_URL}${API_ENDPOINTS.AVATAR_GENERATE}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          photo_base64: photo,
          metadata: { name, gender, spirit_animal: spiritAnimal, toy_name: toyName, style: style || 'child-friendly' }
        })
      });

      if (!response.ok) throw new Error(`Avatar generation failed: ${response.statusText}`);
      
      const data = await response.json();
      return { avatarUrl: data.avatar_url, avatarBase64: data.avatar_base64, metadata: data.metadata };
    } catch (error) {
      console.error('avatarService error:', error);
      throw error;
    }
  }

  async getAvatar(avatarId) {
    const response = await fetch(`${ENV.API_URL}${API_ENDPOINTS.AVATAR_GET}/${avatarId}`);
    if (!response.ok) throw new Error('Avatar not found');
    return await response.json();
  }
}

export const avatarService = new AvatarService();
EOF

echo "✅ Created avatarService.js"

# ===========================================
# COMPONENTS
# ===========================================

cat > avatar/components/AvatarCapture.jsx << 'EOF'
import React, { useEffect } from 'react';
import { Camera, X } from 'lucide-react';
import { useCamera } from '../hooks/useCamera';
import { ChildFriendlyButton } from '../../../shared/components';

export default function AvatarCapture({ onCapture, onCancel }) {
  const { videoRef, isActive, error, startCamera, stopCamera, capturePhoto } = useCamera();

  useEffect(() => {
    startCamera();
    return () => stopCamera();
  }, []);

  const handleCapture = () => {
    const photo = capturePhoto();
    if (photo) {
      onCapture(photo);
      stopCamera();
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '40px', maxWidth: '800px', position: 'relative' }}>
      <button onClick={() => { stopCamera(); onCancel(); }} style={{
        position: 'absolute', top: '20px', right: '20px', background: 'rgba(239, 68, 68, 0.8)',
        border: 'none', borderRadius: '50%', width: '40px', height: '40px',
        display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#fff'
      }}>
        <X size={24} />
      </button>

      <h2 style={{ fontSize: '2.5rem', marginBottom: '20px', textAlign: 'center', color: '#fff' }}>
        📸 Toma tu Foto
      </h2>

      <p style={{ textAlign: 'center', fontSize: '1.2rem', color: 'rgba(255,255,255,0.7)', marginBottom: '30px' }}>
        ¡Sonríe! Vamos a crear tu avatar mágico
      </p>

      <div style={{ position: 'relative', borderRadius: '20px', overflow: 'hidden', marginBottom: '30px', background: '#000' }}>
        {error ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#ef4444' }}>{error}</div>
        ) : (
          <video ref={videoRef} autoPlay playsInline muted style={{
            width: '100%', height: 'auto', display: 'block', transform: 'scaleX(-1)'
          }} />
        )}
        {isActive && (
          <div style={{
            position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
            width: '60%', height: '80%', border: '3px dashed rgba(255,255,255,0.5)',
            borderRadius: '50%', pointerEvents: 'none'
          }} />
        )}
      </div>

      {isActive && (
        <ChildFriendlyButton onClick={handleCapture} variant="primary" icon={<Camera size={32} />}
          style={{ width: '100%', fontSize: '1.8rem', padding: '20px' }}>
          📸 Capturar Foto
        </ChildFriendlyButton>
      )}
    </div>
  );
}
EOF

echo "✅ Created AvatarCapture.jsx"

cat > avatar/components/AvatarPreview.jsx << 'EOF'
import React from 'react';
import { Sparkles, RotateCcw } from 'lucide-react';
import { LoadingAnimation, ChildFriendlyButton } from '../../../shared/components';

export default function AvatarPreview({ isGenerating, avatarUrl, avatarBase64, childName, onRetake, onConfirm }) {
  if (isGenerating) {
    return (
      <div className="glass-panel" style={{ padding: '60px', textAlign: 'center' }}>
        <LoadingAnimation type="avatar" message="🎨 Creando tu avatar mágico..." />
      </div>
    );
  }

  const displayImage = avatarUrl || avatarBase64;

  return (
    <div className="glass-panel" style={{ padding: '40px', maxWidth: '800px', textAlign: 'center' }}>
      <h2 style={{ fontSize: '2.5rem', marginBottom: '10px', color: '#fff' }}>
        <Sparkles size={32} style={{ verticalAlign: 'middle', marginRight: '10px' }} />
        ¡Tu Avatar Está Listo!
      </h2>
      <p style={{ fontSize: '1.3rem', color: 'rgba(255,255,255,0.8)', marginBottom: '30px' }}>
        Así te verás en la aventura, {childName}
      </p>
      <div style={{ marginBottom: '30px', borderRadius: '20px', overflow: 'hidden', boxShadow: '0 10px 40px rgba(0,0,0,0.3)' }}>
        <img src={displayImage} alt={`Avatar de ${childName}`} style={{
          width: '100%', maxWidth: '500px', height: 'auto', display: 'block', margin: '0 auto'
        }} />
      </div>
      <div style={{ display: 'flex', gap: '20px', justifyContent: 'center', flexWrap: 'wrap' }}>
        <ChildFriendlyButton onClick={onRetake} variant="outline" icon={<RotateCcw size={24} />}>
          Tomar Otra Foto
        </ChildFriendlyButton>
        <ChildFriendlyButton onClick={onConfirm} variant="primary" icon={<Sparkles size={24} />}
          style={{ fontSize: '1.5rem', padding: '15px 40px' }}>
          ¡Me Encanta! Continuar
        </ChildFriendlyButton>
      </div>
    </div>
  );
}
EOF

echo "✅ Created AvatarPreview.jsx"

cat > avatar/components/AvatarCreator.jsx << 'EOF'
import React, { useState } from 'react';
import AvatarCapture from './AvatarCapture';
import AvatarPreview from './AvatarPreview';
import { useAvatarGeneration } from '../hooks/useAvatarGeneration';

export default function AvatarCreator({ childMetadata, onComplete, onSkip }) {
  const [step, setStep] = useState('capture');
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const { isGenerating, generatedAvatar, error, generateAvatar, resetAvatar } = useAvatarGeneration();

  const handleCapture = async (photoBase64) => {
    setCapturedPhoto(photoBase64);
    setStep('preview');
    try {
      await generateAvatar(photoBase64, childMetadata);
    } catch (err) {
      console.error('Error generating avatar:', err);
    }
  };

  const handleRetake = () => {
    setCapturedPhoto(null);
    resetAvatar();
    setStep('capture');
  };

  const handleConfirm = () => {
    onComplete({ photo: capturedPhoto, avatar: generatedAvatar });
  };

  if (step === 'capture') {
    return <AvatarCapture onCapture={handleCapture} onCancel={onSkip} />;
  }

  return (
    <AvatarPreview
      isGenerating={isGenerating}
      avatarUrl={generatedAvatar?.avatarUrl}
      avatarBase64={generatedAvatar?.avatarBase64 || capturedPhoto}
      childName={childMetadata.name}
      onRetake={handleRetake}
      onConfirm={handleConfirm}
    />
  );
}
EOF

echo "✅ Created AvatarCreator.jsx"

# ===========================================
# BARREL EXPORT
# ===========================================

cat > avatar/index.js << 'EOF'
export { default as AvatarCapture } from './components/AvatarCapture';
export { default as AvatarPreview } from './components/AvatarPreview';
export { default as AvatarCreator } from './components/AvatarCreator';
export { useCamera } from './hooks/useCamera';
export { useAvatarGeneration } from './hooks/useAvatarGeneration';
export { avatarService } from './services/avatarService';
EOF

echo "✅ Created index.js (barrel export)"

echo ""
echo "🎉 Avatar Feature Created Successfully!"
echo ""
echo "📂 Structure:"
tree avatar/ -L 2 2>/dev/null || find avatar/ -type f

echo ""
echo "🔧 Next: Update constants.js with avatar endpoints"