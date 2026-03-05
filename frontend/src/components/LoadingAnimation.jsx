import React from 'react';
import { Sparkles, Wand2, Stars } from 'lucide-react';

/**
 * Loading Animation Component
 * Fun, child-friendly loading states for various actions
 */
export default function LoadingAnimation({ 
  type = 'default', // default, avatar, story, saving
  message 
}) {
  
  const getLoadingContent = () => {
    switch (type) {
      case 'avatar':
        return {
          icon: <Wand2 size={60} color="var(--color-accent-purple)" />,
          title: "Creating Your Magical Avatar",
          subtitle: message || "Drawing your character with AI magic...",
          emoji: "🎨"
        };
      
      case 'story':
        return {
          icon: <Stars size={60} color="var(--color-accent-pink)" />,
          title: "Weaving Your Story",
          subtitle: message || "The AI is crafting something amazing...",
          emoji: "📖"
        };
      
      case 'saving':
        return {
          icon: <Sparkles size={60} color="var(--color-accent-blue)" />,
          title: "Saving Your Adventure",
          subtitle: message || "Storing your story in the magic vault...",
          emoji: "💾"
        };
      
      default:
        return {
          icon: <Sparkles size={60} color="var(--color-accent-purple)" />,
          title: "Loading Magic",
          subtitle: message || "Please wait a moment...",
          emoji: "✨"
        };
    }
  };

  const content = getLoadingContent();

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '60px 40px',
      textAlign: 'center',
      animation: 'slideUp 0.5s ease-out'
    }}>
      
      {/* Animated Icon */}
      <div style={{
        marginBottom: '30px',
        animation: 'sparkle 2s ease-in-out infinite'
      }}>
        {content.icon}
      </div>

      {/* Title */}
      <h2 style={{
        fontSize: '2.5rem',
        fontFamily: 'var(--font-heading)',
        marginBottom: '15px',
        color: 'white',
        animation: 'float 3s ease-in-out infinite'
      }}>
        {content.emoji} {content.title}
      </h2>

      {/* Subtitle */}
      <p style={{
        fontSize: '1.3rem',
        color: 'rgba(255, 255, 255, 0.8)',
        marginBottom: '30px',
        maxWidth: '500px'
      }}>
        {content.subtitle}
      </p>

      {/* Animated Loading Dots */}
      <div style={{
        display: 'flex',
        gap: '15px',
        marginBottom: '20px'
      }}>
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: '16px',
              height: '16px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, var(--color-accent-pink), var(--color-accent-purple))',
              animation: `bounce-dot 1.4s ease-in-out ${i * 0.2}s infinite`
            }}
          />
        ))}
      </div>

      {/* Spinner */}
      <div className="loading-spinner" style={{ marginTop: '20px' }} />

      <style>
        {`
          @keyframes bounce-dot {
            0%, 80%, 100% {
              transform: scale(0.8);
              opacity: 0.5;
            }
            40% {
              transform: scale(1.2);
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
}
