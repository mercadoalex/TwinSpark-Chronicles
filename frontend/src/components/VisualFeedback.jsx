import React, { useState, useEffect } from 'react';
import { Check, X, Star, Heart, Sparkles, Trophy, Gift } from 'lucide-react';

/**
 * Visual Feedback Component
 * Provides fun, animated feedback for user actions
 */
export default function VisualFeedback({ 
  type, // success, error, achievement, sparkle, love
  message,
  onComplete,
  duration = 2000 
}) {
  const [visible, setVisible] = useState(true);
  const [particles, setParticles] = useState([]);

  useEffect(() => {
    // Generate random particles for celebrations
    if (type === 'success' || type === 'achievement') {
      const newParticles = Array.from({ length: 12 }, (_, i) => ({
        id: i,
        x: Math.random() * 200 - 100,
        y: Math.random() * 200 - 100,
        delay: Math.random() * 0.5
      }));
      setParticles(newParticles);
    }

    // Auto-hide after duration
    const timer = setTimeout(() => {
      setVisible(false);
      if (onComplete) onComplete();
    }, duration);

    return () => clearTimeout(timer);
  }, [type, duration, onComplete]);

  if (!visible) return null;

  const getContent = () => {
    switch (type) {
      case 'success':
        return {
          icon: <Check size={50} color="white" strokeWidth={4} />,
          color: 'var(--color-accent-green)',
          animation: 'bounce-in',
          emoji: '✅',
          bgGradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
        };
      
      case 'error':
        return {
          icon: <X size={50} color="white" strokeWidth={4} />,
          color: 'var(--color-accent-orange)',
          animation: 'shake',
          emoji: '⚠️',
          bgGradient: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
        };
      
      case 'achievement':
        return {
          icon: <Trophy size={50} color="white" strokeWidth={3} />,
          color: 'var(--color-accent-pink)',
          animation: 'bounce-in',
          emoji: '🏆',
          bgGradient: 'linear-gradient(135deg, #f59e0b 0%, #ef4444 100%)'
        };
      
      case 'love':
        return {
          icon: <Heart size={50} color="white" strokeWidth={3} />,
          color: 'var(--color-accent-pink)',
          animation: 'sparkle',
          emoji: '💖',
          bgGradient: 'linear-gradient(135deg, #ec4899 0%, #db2777 100%)'
        };
      
      case 'sparkle':
        return {
          icon: <Sparkles size={50} color="white" strokeWidth={3} />,
          color: 'var(--color-accent-purple)',
          animation: 'sparkle',
          emoji: '✨',
          bgGradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
        };
      
      case 'gift':
        return {
          icon: <Gift size={50} color="white" strokeWidth={3} />,
          color: 'var(--color-accent-blue)',
          animation: 'bounce-in',
          emoji: '🎁',
          bgGradient: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)'
        };
      
      default:
        return {
          icon: <Star size={50} color="white" strokeWidth={3} />,
          color: 'var(--color-accent-purple)',
          animation: 'bounce-in',
          emoji: '⭐',
          bgGradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
        };
    }
  };

  const content = getContent();

  return (
    <div style={{
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      zIndex: 9999,
      pointerEvents: 'none'
    }}>
      
      {/* Main Feedback Container */}
      <div 
        className="glass-panel"
        style={{
          padding: '40px 60px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '20px',
          animation: `${content.animation} 0.6s ease-out`,
          boxShadow: `0 20px 60px ${content.color}80`,
          border: `3px solid ${content.color}`,
          background: `${content.bgGradient}, var(--color-glass)`,
          minWidth: '300px'
        }}
      >
        {/* Icon */}
        <div style={{
          width: '100px',
          height: '100px',
          borderRadius: '50%',
          background: content.bgGradient,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: `0 10px 30px ${content.color}60`
        }}>
          {content.icon}
        </div>

        {/* Message */}
        {message && (
          <p style={{
            fontSize: '1.8rem',
            fontWeight: 700,
            color: 'white',
            textAlign: 'center',
            fontFamily: 'var(--font-heading)',
            textShadow: '0 2px 8px rgba(0, 0, 0, 0.5)'
          }}>
            {content.emoji} {message}
          </p>
        )}
      </div>

      {/* Celebration Particles */}
      {(type === 'success' || type === 'achievement') && particles.map(particle => (
        <div
          key={particle.id}
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            width: '20px',
            height: '20px',
            borderRadius: '50%',
            background: content.bgGradient,
            animation: `particle-burst 1s ease-out ${particle.delay}s forwards`,
            '--particle-x': `${particle.x}px`,
            '--particle-y': `${particle.y}px`,
            opacity: 0
          }}
        />
      ))}

      <style>
        {`
          @keyframes particle-burst {
            0% {
              transform: translate(0, 0) scale(1);
              opacity: 1;
            }
            100% {
              transform: translate(var(--particle-x), var(--particle-y)) scale(0);
              opacity: 0;
            }
          }
        `}
      </style>
    </div>
  );
}

/**
 * Hook for easy feedback usage
 */
export function useFeedback() {
  const [feedback, setFeedback] = useState(null);

  const showFeedback = (type, message, duration) => {
    setFeedback({ type, message, duration });
  };

  const clearFeedback = () => {
    setFeedback(null);
  };

  const FeedbackComponent = feedback ? (
    <VisualFeedback
      type={feedback.type}
      message={feedback.message}
      duration={feedback.duration}
      onComplete={clearFeedback}
    />
  ) : null;

  return {
    showFeedback,
    clearFeedback,
    FeedbackComponent
  };
}
