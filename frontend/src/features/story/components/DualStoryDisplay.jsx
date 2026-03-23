import React, { useState, useEffect, useRef } from 'react';
import './DualStoryDisplay.css';
import SceneImageLoader from './SceneImageLoader';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import { useAudioStore } from '../../../stores/audioStore';
import { useSceneAudioStore } from '../../../stores/sceneAudioStore';

const choiceIcons = ['🌙', '⚡', '🌿', '🔮', '🌊', '🦋'];

const presetToyEmojis = {
  teddy: '🧸',
  robot: '🤖',
  bunny: '🐰',
  dino: '🦕',
  kitty: '🐱',
  puppy: '🐶',
};

/** Companion avatar with graceful degradation — broken photo URLs fall back to 🧸 (Req 5.6) */
function CompanionAvatar({ toyType, toyImage, childClass, small }) {
  const [broken, setBroken] = React.useState(false);
  const sizeClass = small ? 'companion-avatar--sm' : '';

  if (!toyType || !toyImage) return null;

  if (toyType === 'photo' && !broken) {
    return (
      <img
        className={`companion-avatar ${sizeClass} ${childClass}`}
        src={toyImage}
        alt="toy companion"
        onError={() => setBroken(true)}
      />
    );
  }

  // Preset emoji or broken-photo fallback to generic 🧸
  const emoji = toyType === 'photo' ? '🧸' : (presetToyEmojis[toyImage] || '🧸');
  return (
    <span className={`companion-avatar ${sizeClass} ${childClass}`} aria-hidden="true">
      {emoji}
    </span>
  );
}

function DualStoryDisplay({ storyBeat, t, profiles, onChoice }) {
  const [selectedIdx, setSelectedIdx] = useState(null);
  const [showPerspectives, setShowPerspectives] = useState(false);
  const [showSceneShimmer, setShowSceneShimmer] = useState(false);
  const narrationRef = useRef(null);
  const prevBeatRef = useRef(null);
  const prevSceneUrlRef = useRef(null);

  const { queueVoiceRecording, isPlayingVoiceRecording, currentVoiceRecording } = useAudioStore();

  // Play voice recordings when a new story beat arrives with voice_recordings
  useEffect(() => {
    if (
      storyBeat?.voice_recordings &&
      Array.isArray(storyBeat.voice_recordings) &&
      storyBeat.voice_recordings.length > 0 &&
      storyBeat !== prevBeatRef.current
    ) {
      for (const rec of storyBeat.voice_recordings) {
        if (rec.audio_base64 && rec.source === 'recording') {
          queueVoiceRecording(rec);
        }
      }
    }
  }, [storyBeat, queueVoiceRecording]);

  // Move focus to narration text when a new story beat loads (Req 9.3)
  useEffect(() => {
    if (storyBeat?.narration && storyBeat !== prevBeatRef.current) {
      prevBeatRef.current = storyBeat;
      // Delay to ensure DOM has rendered after loading animation is replaced
      requestAnimationFrame(() => {
        narrationRef.current?.focus();
      });
    }
  }, [storyBeat]);

  // Trigger shimmer sweep when a new scene image appears (Req 4.3)
  useEffect(() => {
    const currentUrl = storyBeat?.scene_image_url;
    if (currentUrl && currentUrl !== prevSceneUrlRef.current) {
      prevSceneUrlRef.current = currentUrl;
      setShowSceneShimmer(true);
      const timer = setTimeout(() => setShowSceneShimmer(false), 900);
      return () => clearTimeout(timer);
    }
  }, [storyBeat?.scene_image_url]);

  if (!storyBeat) {
    return (
      <div className="story-empty">
        <div className="story-empty__sparkle" aria-hidden="true">✨</div>
        <p className="story-empty__text">Preparing your magical adventure…</p>
      </div>
    );
  }

  const handleChoiceTap = (choice, idx) => {
    setSelectedIdx(idx);
    useSceneAudioStore.getState().playSfx('choice_select');
    // Satisfying bounce then send
    setTimeout(() => {
      onChoice(choice);
      setSelectedIdx(null);
      setShowPerspectives(false);
    }, 400);
  };

  const togglePerspectives = () => setShowPerspectives(p => !p);

  // Descriptive alt text from scene_description or fallback (Req 5.1)
  const sceneAlt = storyBeat?.scene_description || 'Illustration for the current story scene';

  return (
    <section className="story-stage-main" aria-label="Story content">
      {/* ── Cinematic scene image ──────────────────── */}
      {storyBeat?.scene_image_url && (
        <div className="story-scene">
          <SceneImageLoader
            src={storyBeat.scene_image_url.startsWith('http')
              ? storyBeat.scene_image_url
              : `http://localhost:8000${storyBeat.scene_image_url}`}
            alt={sceneAlt}
          />
          <div className="story-scene__fade" />

          {/* Shimmer sweep on new scene image load (Req 4.3) */}
          {showSceneShimmer && (
            <CelebrationOverlay type="shimmer" duration={800} particleCount={1} />
          )}

          {/* Floating child avatars on the scene */}
          <div className="story-scene__avatars">
            <div className="story-scene__avatar story-scene__avatar--c1">
              <span aria-hidden="true">🌟</span>
              <span className="story-scene__avatar-name">{profiles?.c1_name}</span>
              <CompanionAvatar toyType={profiles?.c1_toy_type} toyImage={profiles?.c1_toy_image} childClass="companion-avatar--c1" />
            </div>
            <div className="story-scene__avatar story-scene__avatar--c2">
              <span aria-hidden="true">⭐</span>
              <span className="story-scene__avatar-name">{profiles?.c2_name}</span>
              <CompanionAvatar toyType={profiles?.c2_toy_type} toyImage={profiles?.c2_toy_image} childClass="companion-avatar--c2" />
            </div>
          </div>
        </div>
      )}

      {/* ── Narration — short, voice-first (Req 4.1) ── */}
      {storyBeat?.narration && (
        <div
          className="story-narration"
          onClick={togglePerspectives}
          ref={narrationRef}
          tabIndex={-1}
          aria-live="polite"
        >
          <p className="story-narration__text">{storyBeat.narration}</p>
          <span className="story-narration__tap-hint">
            {showPerspectives ? '▲ hide details' : '▼ tap for details'}
          </span>
        </div>
      )}

      {/* ── Voice recording playing indicator ──────── */}
      {isPlayingVoiceRecording && currentVoiceRecording?.recorder_name && (
        <div className="story-voice-badge" aria-live="polite">
          <span className="story-voice-badge__icon" aria-hidden="true">🎙️</span>
          <span className="story-voice-badge__name">
            {currentVoiceRecording.recorder_name}
          </span>
          <span className="story-voice-badge__pulse" aria-hidden="true" />
        </div>
      )}

      {/* ── Expandable perspectives ────────────────── */}
      {showPerspectives && (
        <div className="story-perspectives">
          <div className="story-card story-card--child1">
            <span className="story-card__emoji" aria-hidden="true">🌟</span>
            <span className="story-card__name story-card__name--child1">
              {profiles?.c1_name}
            </span>
            <CompanionAvatar toyType={profiles?.c1_toy_type} toyImage={profiles?.c1_toy_image} childClass="companion-avatar--c1" small />
            <p className="story-card__text">
              {storyBeat?.child1_perspective}
            </p>
          </div>
          <div className="story-card story-card--child2">
            <span className="story-card__emoji" aria-hidden="true">⭐</span>
            <span className="story-card__name story-card__name--child2">
              {profiles?.c2_name}
            </span>
            <CompanionAvatar toyType={profiles?.c2_toy_type} toyImage={profiles?.c2_toy_image} childClass="companion-avatar--c2" small />
            <p className="story-card__text">
              {storyBeat?.child2_perspective}
            </p>
          </div>
        </div>
      )}

      {/* ── Choice cards — BIG tappable ────────────── */}
      {storyBeat?.choices && storyBeat.choices.length > 0 && (
        <div className="story-choices">
          <h3 className="story-choices__title">What happens next?</h3>
          <div className="story-choices__grid">
            {storyBeat.choices.map((choice, idx) => (
              <button
                key={idx}
                className={`story-choice-card ${selectedIdx === idx ? 'story-choice-card--selected' : ''} ${selectedIdx !== null && selectedIdx !== idx ? 'story-choice-card--dimmed' : ''}`}
                onClick={() => handleChoiceTap(choice, idx)}
                disabled={selectedIdx !== null}
              >
                <span className="story-choice-card__icon" aria-hidden="true">
                  {choiceIcons[idx % choiceIcons.length]}
                </span>
                <span className="story-choice-card__text">{choice}</span>
                <div className="story-choice-card__glow" />
              </button>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}

export default DualStoryDisplay;
