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
