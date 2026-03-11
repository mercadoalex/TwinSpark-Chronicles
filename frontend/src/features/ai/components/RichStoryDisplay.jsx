import React, { useEffect, useRef, useState } from 'react';

/**
 * Rich Story Display - Shows text, images, and plays audio
 */
export default function RichStoryDisplay({ storyMoment, onNext }) {
  const audioRef = useRef(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showImage, setShowImage] = useState(false);

  useEffect(() => {
    if (storyMoment?.image) {
      // Fade in image after text appears
      setTimeout(() => setShowImage(true), 500);
    }

    // Auto-play narration if available
    if (storyMoment?.audio?.narration && audioRef.current) {
      audioRef.current.play();
      setIsPlaying(true);
    }
  }, [storyMoment]);

  const handleAudioEnd = () => {
    setIsPlaying(false);
  };

  const toggleAudio = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  if (!storyMoment) {
    return (
      <div className="loading-story">
        <div className="spinner"></div>
        <p>Creating your magical moment...</p>
      </div>
    );
  }

  return (
    <div className="rich-story-container">
      {/* Scene Image */}
      {storyMoment.image && (
        <div className={`story-scene ${showImage ? 'visible' : ''}`}>
          <img 
            src={storyMoment.image} 
            alt="Story scene"
            className="scene-illustration"
          />
          
          {/* Agent badges */}
          <div className="agent-badges">
            {storyMoment.agents_used?.visual && (
              <span className="badge">🎨 AI Illustrated</span>
            )}
            {storyMoment.agents_used?.voice && (
              <span className="badge">🎤 AI Voiced</span>
            )}
            {storyMoment.memories_used > 0 && (
              <span className="badge">🧠 {storyMoment.memories_used} Memories</span>
            )}
          </div>
        </div>
      )}

      {/* Story Text */}
      <div className="story-text-container">
        <p className="story-text">{storyMoment.text}</p>
      </div>

      {/* Audio Controls */}
      {storyMoment.audio?.narration && (
        <div className="audio-controls">
          <button 
            onClick={toggleAudio}
            className="audio-button"
          >
            {isPlaying ? '⏸️ Pause Story' : '▶️ Play Story'}
          </button>
          
          <audio
            ref={audioRef}
            src={storyMoment.audio.narration}
            onEnded={handleAudioEnd}
            onPlay={() => setIsPlaying(true)}
            onPause={() => setIsPlaying(false)}
          />
        </div>
      )}

      {/* Character Voices */}
      {storyMoment.audio?.character_voices?.map((voice, idx) => (
        <div key={idx} className="character-voice">
          <span className="character-name">{voice.character}:</span>
          <span className="dialogue-text">"{voice.text}"</span>
          <audio src={voice.audio} controls />
        </div>
      ))}

      {/* Interactive Prompt */}
      {storyMoment.interactive && (
        <div className="interactive-prompt">
          <p className="prompt-text">{storyMoment.interactive.text}</p>
          {storyMoment.interactive.expects_response && (
            <button 
              onClick={onNext}
              className="continue-button"
            >
              Continue Adventure →
            </button>
          )}
        </div>
      )}

      <style jsx>{`
        .rich-story-container {
          max-width: 900px;
          margin: 0 auto;
          padding: 20px;
        }

        .story-scene {
          opacity: 0;
          transform: scale(0.95);
          transition: all 0.8s ease-out;
          margin-bottom: 30px;
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 10px 40px rgba(0,0,0,0.2);
          position: relative;
        }

        .story-scene.visible {
          opacity: 1;
          transform: scale(1);
        }

        .scene-illustration {
          width: 100%;
          height: auto;
          display: block;
        }

        .agent-badges {
          position: absolute;
          top: 15px;
          right: 15px;
          display: flex;
          gap: 8px;
        }

        .badge {
          background: rgba(0,0,0,0.7);
          color: white;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 0.85rem;
          backdrop-filter: blur(10px);
        }

        .story-text-container {
          background: rgba(255,255,255,0.95);
          padding: 30px;
          border-radius: 15px;
          margin-bottom: 20px;
          box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }

        .story-text {
          font-size: 1.3rem;
          line-height: 1.8;
          color: #333;
          margin: 0;
        }

        .audio-controls {
          text-align: center;
          margin: 20px 0;
        }

        .audio-button {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border: none;
          padding: 15px 40px;
          border-radius: 30px;
          font-size: 1.1rem;
          cursor: pointer;
          box-shadow: 0 4px 15px rgba(118, 75, 162, 0.4);
          transition: all 0.3s;
        }

        .audio-button:hover {
          transform: translateY(-2px);
          box-shadow: 0 6px 20px rgba(118, 75, 162, 0.5);
        }

        .character-voice {
          background: #f8f9fa;
          padding: 15px;
          border-radius: 10px;
          margin: 10px 0;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .character-name {
          font-weight: bold;
          color: #667eea;
        }

        .dialogue-text {
          flex: 1;
          font-style: italic;
        }

        .interactive-prompt {
          background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
          padding: 25px;
          border-radius: 15px;
          margin-top: 20px;
          text-align: center;
        }

        .prompt-text {
          font-size: 1.2rem;
          font-weight: 600;
          color: #333;
          margin-bottom: 15px;
        }

        .continue-button {
          background: white;
          color: #667eea;
          border: 2px solid #667eea;
          padding: 12px 30px;
          border-radius: 25px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
        }

        .continue-button:hover {
          background: #667eea;
          color: white;
          transform: scale(1.05);
        }

        .loading-story {
          text-align: center;
          padding: 60px 20px;
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 20px;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}