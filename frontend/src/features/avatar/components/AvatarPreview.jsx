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
