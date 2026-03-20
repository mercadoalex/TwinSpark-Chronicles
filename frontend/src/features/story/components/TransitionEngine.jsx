import { useState, useEffect, useRef, useCallback } from 'react';
import DualStoryDisplay from './DualStoryDisplay';
import CelebrationOverlay from '../../../shared/components/CelebrationOverlay';
import { useReducedMotion } from '../../../shared/hooks/useReducedMotion';
import { useImagePreloader } from '../../../shared/hooks/useImagePreloader';
import { getNextTransition } from '../transitions/transitionTypes';
import { useSceneAudioStore } from '../../../stores/sceneAudioStore';
import './TransitionEngine.css';

/**
 * TransitionEngine — wraps DualStoryDisplay with animated scene transitions.
 *
 * State machine: idle → preparing → animating → cleanup → idle
 *
 * On the very first render (no previous beat), it renders DualStoryDisplay
 * directly without any transition.
 */
export default function TransitionEngine({ storyBeat, t, profiles, onChoice }) {
  const prefersReducedMotion = useReducedMotion();

  // ── State machine ──────────────────────────────────
  const [transitionState, setTransitionState] = useState('idle');
  const [transitionIndex, setTransitionIndex] = useState(0);
  const [showSparkle, setShowSparkle] = useState(false);
  const [currentBeat, setCurrentBeat] = useState(storyBeat);
  const [incomingBeat, setIncomingBeat] = useState(null);
  const [activeTransition, setActiveTransition] = useState(null);

  // Refs for timeout / listener cleanup
  const sparkleTimerRef = useRef(null);
  const safetyTimerRef = useRef(null);
  const cleanupTimerRef = useRef(null);
  const reducedMotionTimerRef = useRef(null);
  const outgoingRef = useRef(null);
  const incomingRef = useRef(null);
  const stateRef = useRef(transitionState);

  // Keep stateRef in sync so callbacks see latest value
  stateRef.current = transitionState;

  // ── Image preloader for incoming scene ─────────────
  const incomingImageSrc = incomingBeat?.scene_image_url
    ? (incomingBeat.scene_image_url.startsWith('http')
        ? incomingBeat.scene_image_url
        : `http://localhost:8000${incomingBeat.scene_image_url}`)
    : null;

  const { loaded: imageLoaded, error: imageError } = useImagePreloader(
    transitionState === 'preparing' ? incomingImageSrc : null
  );

  // ── Cleanup helper ─────────────────────────────────
  const clearAllTimers = useCallback(() => {
    [sparkleTimerRef, safetyTimerRef, cleanupTimerRef, reducedMotionTimerRef].forEach((ref) => {
      if (ref.current) {
        clearTimeout(ref.current);
        ref.current = null;
      }
    });
  }, []);

  // ── Promote incoming → current (finish transition) ─
  const finishTransition = useCallback(() => {
    setShowSparkle(false);
    setTransitionState('cleanup');

    // Audio: restore ambient volume after transition completes
    useSceneAudioStore.getState().restoreAmbient(500);

    cleanupTimerRef.current = setTimeout(() => {
      cleanupTimerRef.current = null;
      setCurrentBeat(incomingBeat);
      setIncomingBeat(null);
      setActiveTransition(null);
      setTransitionState('idle');
    }, 100);
  }, [incomingBeat]);

  // ── Detect new storyBeat while idle ────────────────
  useEffect(() => {
    // Skip if no beat, same beat, or not idle
    if (!storyBeat) return;
    if (storyBeat === currentBeat) return;
    if (stateRef.current !== 'idle') return;

    // First render — no previous beat, just set directly
    if (!currentBeat) {
      setCurrentBeat(storyBeat);
      return;
    }

    // Start transition
    setIncomingBeat(storyBeat);
    setTransitionState('preparing');
  }, [storyBeat]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── preparing → animating (when image ready) ───────
  useEffect(() => {
    if (transitionState !== 'preparing') return;
    if (!imageLoaded && !imageError) return;

    // Audio: duck ambient during transition preparation
    const sceneAudio = useSceneAudioStore.getState();
    if (incomingBeat?.narration) {
      // Fetch scene theme from API and preload the track
      fetch('http://localhost:8000/api/audio/scene-theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scene_description: incomingBeat.narration }),
      })
        .then((r) => r.ok ? r.json() : null)
        .then((data) => {
          if (data?.ambient_track) {
            sceneAudio.preloadTrack(data.theme, data.ambient_track);
          }
        })
        .catch(() => { /* silent */ });
    }
    sceneAudio.duckAmbient(0.6);

    // Reduced motion: instant swap, no animation
    if (prefersReducedMotion) {
      // Audio: instant swap for reduced motion — crossfade + restore immediately
      if (incomingBeat?.narration) {
        fetch('http://localhost:8000/api/audio/scene-theme', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scene_description: incomingBeat.narration }),
        })
          .then((r) => r.ok ? r.json() : null)
          .then((data) => {
            if (data?.ambient_track) {
              sceneAudio.crossfadeTo(data.theme, data.ambient_track);
            }
            sceneAudio.restoreAmbient(500);
          })
          .catch(() => sceneAudio.restoreAmbient(500));
      } else {
        sceneAudio.restoreAmbient(500);
      }

      setTransitionState('cleanup');
      reducedMotionTimerRef.current = setTimeout(() => {
        reducedMotionTimerRef.current = null;
        setCurrentBeat(incomingBeat);
        setIncomingBeat(null);
        setActiveTransition(null);
        setTransitionState('idle');
      }, 100); // well within 200ms budget
      return;
    }

    // Select transition type using viewport width
    const viewportWidth = window.innerWidth;
    const { type, nextIndex } = getNextTransition(transitionIndex, viewportWidth);
    setTransitionIndex(nextIndex);
    setActiveTransition(type);
    setTransitionState('animating');
  }, [transitionState, imageLoaded, imageError, prefersReducedMotion, transitionIndex, incomingBeat]);

  // ── animating: schedule sparkle + safety timeout ───
  useEffect(() => {
    if (transitionState !== 'animating' || !activeTransition) return;

    const duration = activeTransition.duration || 800;

    // Audio: crossfade to new theme + play page_turn SFX
    const sceneAudio = useSceneAudioStore.getState();
    sceneAudio.playSfx('page_turn');
    if (incomingBeat?.narration) {
      fetch('http://localhost:8000/api/audio/scene-theme', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scene_description: incomingBeat.narration }),
      })
        .then((r) => r.ok ? r.json() : null)
        .then((data) => {
          if (data?.ambient_track) {
            sceneAudio.crossfadeTo(data.theme, data.ambient_track);
          }
        })
        .catch(() => { /* silent */ });
    }

    // Sparkle burst at 50% of transition duration
    sparkleTimerRef.current = setTimeout(() => {
      sparkleTimerRef.current = null;
      if (stateRef.current === 'animating') {
        setShowSparkle(true);
      }
    }, duration / 2);

    // Safety timeout: force-complete after 2s
    safetyTimerRef.current = setTimeout(() => {
      safetyTimerRef.current = null;
      if (stateRef.current === 'animating') {
        finishTransition();
      }
    }, 2000);

    return () => {
      if (sparkleTimerRef.current) {
        clearTimeout(sparkleTimerRef.current);
        sparkleTimerRef.current = null;
      }
      if (safetyTimerRef.current) {
        clearTimeout(safetyTimerRef.current);
        safetyTimerRef.current = null;
      }
    };
  }, [transitionState, activeTransition, finishTransition]);

  // ── animationend handler ───────────────────────────
  const handleAnimationEnd = useCallback((e) => {
    // Only respond to our transition animations on the outgoing scene
    if (stateRef.current !== 'animating') return;
    // Check that the event target is the outgoing scene element
    if (outgoingRef.current && outgoingRef.current.contains(e.target)) {
      finishTransition();
    }
  }, [finishTransition]);

  // ── Unmount cleanup ────────────────────────────────
  useEffect(() => {
    return () => clearAllTimers();
  }, [clearAllTimers]);

  // ── Choice handler: block during non-idle states ───
  const safeOnChoice = useCallback((choice) => {
    if (stateRef.current !== 'idle') return;
    onChoice?.(choice);
  }, [onChoice]);

  // ── Render ─────────────────────────────────────────

  const isTransitioning = transitionState !== 'idle';

  // No beat at all — let DualStoryDisplay handle empty state
  if (!currentBeat && !incomingBeat) {
    return <DualStoryDisplay storyBeat={storyBeat} t={t} profiles={profiles} onChoice={onChoice} />;
  }

  // Idle with no incoming — simple render, no wrapper overhead
  if (!isTransitioning && !incomingBeat) {
    return <DualStoryDisplay storyBeat={currentBeat} t={t} profiles={profiles} onChoice={onChoice} />;
  }

  // Build CSS classes for outgoing scene
  const outgoingClasses = ['transition-scene', 'transition-scene--outgoing'];
  if (transitionState === 'animating' && activeTransition?.outClass) {
    outgoingClasses.push(activeTransition.outClass);
    outgoingClasses.push('transition-scene--will-change');
    outgoingClasses.push('transition-scene--no-interaction');
  }

  // Build CSS classes for incoming scene
  const incomingClasses = ['transition-scene', 'transition-scene--incoming'];
  if (transitionState === 'animating' && activeTransition?.inClass) {
    incomingClasses.push(activeTransition.inClass);
    incomingClasses.push('transition-scene--will-change');
    incomingClasses.push('transition-scene--no-interaction');
  }

  // During preparing, incoming is at opacity 0
  const incomingStyle = transitionState === 'preparing' ? { opacity: 0 } : {};

  return (
    <div className="transition-container" onAnimationEnd={handleAnimationEnd}>
      {/* Outgoing scene */}
      <div ref={outgoingRef} className={outgoingClasses.join(' ')}>
        <DualStoryDisplay
          storyBeat={currentBeat}
          t={t}
          profiles={profiles}
          onChoice={isTransitioning ? undefined : safeOnChoice}
        />
      </div>

      {/* Incoming scene */}
      {incomingBeat && (
        <div ref={incomingRef} className={incomingClasses.join(' ')} style={incomingStyle}>
          <DualStoryDisplay
            storyBeat={incomingBeat}
            t={t}
            profiles={profiles}
            onChoice={undefined}
          />
        </div>
      )}

      {/* Sparkle burst at transition midpoint */}
      {showSparkle && (
        <CelebrationOverlay
          type="sparkle"
          duration={activeTransition ? activeTransition.duration / 2 : 400}
          particleCount={20}
          colors={['#fbbf24', '#fb7185', '#a78bfa']}
        />
      )}
    </div>
  );
}
