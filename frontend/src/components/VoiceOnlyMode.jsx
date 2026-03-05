import React, { useState, useEffect } from 'react';
import { Mic, Volume2, Sparkles } from 'lucide-react';

/**
 * Voice-Only Mode Component
 * Simplified interface for younger children - just push and talk!
 */
export default function VoiceOnlyMode({ 
  onVoiceInput, 
  isListening, 
  currentStory,
  childName,
  t 
}) {
  const [visualFeedback, setVisualFeedback] = useState('idle'); // idle, listening, processing, speaking
  const [encouragementText, setEncouragementText] = useState('');

  const encouragements = [
    "🌟 Great idea!",
    "✨ Keep going!",
    "🎨 So creative!",
    "🚀 Amazing!",
    "💫 You're doing great!",
    "🌈 Wonderful!",
    "⭐ Brilliant!",
    "🎭 So fun!"
  ];

  useEffect(() => {
    if (isListening) {
      setVisualFeedback('listening');
    } else {
      setVisualFeedback('idle');
    }
  }, [isListening]);

  const handlePushToTalk = () => {
    if (onVoiceInput) {
      onVoiceInput();
      // Show encouragement
      const randomEncouragement = encouragements[Math.floor(Math.random() * encouragements.length)];
      setEncouragementText(randomEncouragement);
      setTimeout(() => setEncouragementText(''), 2000);
    }
  };

  return (
    <div className="voice-mode-container">
      
      {/* Main Title */}
      <div className="voice-mode-title">
        <span className="glow-text">
          {childName ? `${childName}'s Turn! 🎤` : t?.voiceModeTitle || "Your Turn to Talk! 🎤"}
        </span>
      </div>

      {/* Current Story Context (if available) */}
      {currentStory && (
        <div className="glass-panel" style={{
          padding: '30px',
          maxWidth: '700px',
          textAlign: 'center',
          animation: 'slideUp 0.5s ease-out'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px',
            marginBottom: '15px'
          }}>
            <Volume2 size={28} color="var(--color-accent-purple)" />
            <h3 style={{
              fontSize: '1.8rem',
              color: 'var(--color-accent-purple)',
              fontFamily: 'var(--font-heading)'
            }}>
              {t?.storyContext || "The Story So Far..."}
            </h3>
          </div>
          <p className="story-text" style={{ fontSize: '1.3rem' }}>
            {currentStory}
          </p>
        </div>
      )}

      {/* Giant Push-to-Talk Button */}
      <button
        className={`btn-voice-giant ${isListening ? 'listening' : ''}`}
        onClick={handlePushToTalk}
        onTouchStart={handlePushToTalk}
        aria-label={isListening ? "Stop recording" : "Start recording"}
      >
        <Mic size={80} color="white" strokeWidth={3} />
        <span style={{ fontSize: '1.8rem', fontWeight: 900 }}>
          {isListening ? (t?.releaseToStop || "Recording...") : (t?.pushToTalk || "Push to Talk")}
        </span>
      </button>

      {/* Visual Feedback */}
      {visualFeedback === 'listening' && (
        <div style={{
          fontSize: '2rem',
          animation: 'pulse-voice 1s infinite',
          color: 'var(--color-accent-green)',
          fontWeight: 700
        }}>
          🎤 {t?.listening || "Listening..."} 
        </div>
      )}

      {/* Encouragement Text */}
      {encouragementText && (
        <div style={{
          fontSize: '2.5rem',
          fontWeight: 900,
          animation: 'bounce-in 0.5s ease-out',
          color: 'var(--color-accent-pink)',
          textShadow: '0 4px 8px rgba(236, 72, 153, 0.5)'
        }}>
          {encouragementText}
        </div>
      )}

      {/* Instructions */}
      <div className="voice-mode-instruction">
        {isListening ? (
          <>
            <Sparkles size={24} style={{ display: 'inline', marginRight: '10px' }} />
            {t?.voiceInstruction || "Tell your part of the story! What happens next?"}
            <Sparkles size={24} style={{ display: 'inline', marginLeft: '10px' }} />
          </>
        ) : (
          <>
            {t?.voiceInstructionIdle || "Press the big button to add to the adventure!"}
          </>
        )}
      </div>

      {/* Audio Visualization */}
      {isListening && (
        <div style={{
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          justifyContent: 'center',
          height: '60px'
        }}>
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              style={{
                width: '12px',
                background: 'linear-gradient(to top, var(--color-accent-pink), var(--color-accent-purple))',
                borderRadius: '10px',
                animation: `audio-bar ${0.5 + i * 0.1}s ease-in-out infinite alternate`,
                animationDelay: `${i * 0.1}s`
              }}
            />
          ))}
        </div>
      )}

      <style>
        {`
          @keyframes audio-bar {
            from {
              height: 20px;
              opacity: 0.5;
            }
            to {
              height: 60px;
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
}
