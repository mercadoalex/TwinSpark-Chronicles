import React from 'react';
import { Mic, MicOff, Camera, CameraOff, Sparkles } from 'lucide-react';

export default function MultimodalControls({ isListening, hasCamera, t }) {
  return (
    <div className="glass-panel" style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      gap: '20px',
      padding: '15px 30px',
      margin: '0 auto',
      width: 'fit-content'
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        background: isListening ? 'rgba(236, 72, 153, 0.2)' : 'rgba(255, 255, 255, 0.05)',
        padding: '12px 24px',
        borderRadius: '50px',
        border: `1px solid ${isListening ? 'var(--color-accent-pink)' : 'var(--color-glass-border)'}`,
        boxShadow: isListening ? '0 0 15px rgba(236, 72, 153, 0.4)' : 'none',
        transition: 'all 0.3s ease'
      }}>
        {isListening ? (
          <Mic size={24} color="var(--color-accent-pink)" />
        ) : (
          <MicOff size={24} color="#aaa" />
        )}
        <span style={{
          marginLeft: '12px',
          fontWeight: 600,
          color: isListening ? '#fff' : '#aaa'
        }}>
          {isListening ? t.listening : t.micOff}
        </span>
      </div>

      <div style={{
        display: 'flex',
        alignItems: 'center',
        background: hasCamera ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255, 255, 255, 0.05)',
        padding: '12px 24px',
        borderRadius: '50px',
        border: `1px solid ${hasCamera ? 'var(--color-accent-blue)' : 'var(--color-glass-border)'}`,
        boxShadow: hasCamera ? '0 0 15px rgba(59, 130, 246, 0.4)' : 'none',
        transition: 'all 0.3s ease'
      }}>
        {hasCamera ? (
          <Camera size={24} color="var(--color-accent-blue)" />
        ) : (
          <CameraOff size={24} color="#aaa" />
        )}
        <span style={{
          marginLeft: '12px',
          fontWeight: 600,
          color: hasCamera ? '#fff' : '#aaa'
        }}>
          {hasCamera ? t.cameraActive : t.cameraOff}
        </span>
      </div>

      {/* Sparkle badge to show AI connection */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, var(--color-accent-purple), var(--color-accent-pink))',
        width: '48px',
        height: '48px',
        borderRadius: '50%',
        boxShadow: 'var(--shadow-glow)',
        animation: 'pulse-glow 3s infinite'
      }}>
        <Sparkles size={24} color="#fff" />
      </div>
    </div>
  );
}
