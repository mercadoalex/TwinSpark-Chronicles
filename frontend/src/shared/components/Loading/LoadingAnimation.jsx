import React from 'react';
import './LoadingAnimation.css';

/**
 * Loading Animation Component
 * Magical bouncing star with orbiting sparkles — child-friendly loading states.
 */
export default function LoadingAnimation({ 
  type = 'default', // default, avatar, story, saving
  message 
}) {
  
  const getLoadingContent = () => {
    switch (type) {
      case 'avatar':
        return {
          title: "Creating Your Magical Avatar",
          subtitle: message || "Drawing your character with AI magic...",
          emoji: "🎨"
        };
      
      case 'story':
        return {
          title: "Weaving Your Story",
          subtitle: message || "The AI is crafting something amazing...",
          emoji: "📖"
        };
      
      case 'saving':
        return {
          title: "Saving Your Adventure",
          subtitle: message || "Storing your story in the magic vault...",
          emoji: "💾"
        };
      
      default:
        return {
          title: "Loading Magic",
          subtitle: message || "Please wait a moment...",
          emoji: "✨"
        };
    }
  };

  const content = getLoadingContent();

  return (
    <div className="loading-magic">
      {/* Bouncing star with orbiting sparkles */}
      <div className="loading-magic__star-container">
        <div className="loading-magic__star" aria-hidden="true">⭐</div>
        <span className="loading-magic__sparkle" aria-hidden="true" />
        <span className="loading-magic__sparkle" aria-hidden="true" />
        <span className="loading-magic__sparkle" aria-hidden="true" />
      </div>

      {/* Title */}
      <h2 className="loading-magic__title">
        <span aria-hidden="true">{content.emoji} </span>
        {content.title}
      </h2>

      {/* Subtitle */}
      <p className="loading-magic__subtitle">
        {content.subtitle}
      </p>

      {/* Animated Loading Dots */}
      <div className="loading-magic__dots">
        <div className="loading-magic__dot" />
        <div className="loading-magic__dot" />
        <div className="loading-magic__dot" />
      </div>
    </div>
  );
}
