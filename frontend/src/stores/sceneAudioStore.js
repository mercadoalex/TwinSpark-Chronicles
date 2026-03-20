/**
 * Scene Audio Store
 * Manages ambient audio loops, SFX playback, crossfade engine,
 * volume/mute controls, and coordination with audioStore.
 *
 * Uses Web Audio API for precise gain control and mixing,
 * independent of the HTML <audio> elements used by audioStore.
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { useAudioStore } from './audioStore';

// ── Reduced-motion detection (module-level) ──────────
let _prefersReducedMotion = false;
try {
  const mql = window.matchMedia('(prefers-reduced-motion: reduce)');
  _prefersReducedMotion = mql.matches;
  mql.addEventListener('change', (e) => {
    _prefersReducedMotion = e.matches;
  });
} catch {
  // SSR or unsupported — default to false
}

// ── Module-level refs for Web Audio nodes ────────────
let _currentSource = null;
let _outgoingSource = null;
let _outgoingGain = null;
let _crossfadeTimer = null;

// SFX category → file path mapping
const SFX_PATHS = {
  choice_select: '/audio/sfx/choice_select.mp3',
  page_turn: '/audio/sfx/page_turn.mp3',
  celebration: '/audio/sfx/celebration.mp3',
};

// Max cache entries (LRU)
const MAX_CACHE_SIZE = 10;

/**
 * LRU cache helper — moves key to "most recent" by re-inserting.
 * Evicts oldest entry when size exceeds max.
 */
function lruSet(cache, key, value) {
  const updated = { ...cache };
  // Remove existing entry so re-insert puts it at end
  delete updated[key];
  updated[key] = value;

  const keys = Object.keys(updated);
  if (keys.length > MAX_CACHE_SIZE) {
    delete updated[keys[0]]; // evict oldest
  }
  return updated;
}

/**
 * LRU cache access — moves key to most-recent position.
 */
function lruGet(cache, key) {
  if (!(key in cache)) return { value: undefined, cache };
  const value = cache[key];
  const updated = { ...cache };
  delete updated[key];
  updated[key] = value;
  return { value, cache: updated };
}

export const useSceneAudioStore = create(
  devtools(
    persist(
      (set, get) => ({
        // ── State (Task 3.1) ───────────────────────────
        audioContext: null,
        ambientGainNode: null,
        sfxGainNode: null,
        currentTheme: null,
        currentSource: null,
        isAmbientPlaying: false,
        ambientVolume: 70,
        sfxVolume: 70,
        isMuted: false,
        audioUnlocked: false,
        isDucking: false,
        preloadCache: {},

        // ── initAudio / unlockAudio (Task 3.2) ────────
        initAudio: () => {
          try {
            const state = get();
            if (state.audioContext) return;

            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            const ambientGain = ctx.createGain();
            const sfxGain = ctx.createGain();

            ambientGain.gain.value = state.isMuted ? 0 : state.ambientVolume / 100;
            sfxGain.gain.value = state.isMuted ? 0 : state.sfxVolume / 100;

            ambientGain.connect(ctx.destination);
            sfxGain.connect(ctx.destination);

            set({
              audioContext: ctx,
              ambientGainNode: ambientGain,
              sfxGainNode: sfxGain,
            }, false, 'sceneAudio/initAudio');
          } catch (err) {
            console.warn('⚠️ Failed to create AudioContext:', err);
          }
        },

        unlockAudio: async () => {
          try {
            const { audioContext } = get();
            if (!audioContext) return;
            if (audioContext.state === 'suspended') {
              await audioContext.resume();
            }
            set({ audioUnlocked: true }, false, 'sceneAudio/unlockAudio');
          } catch (err) {
            console.warn('⚠️ Failed to unlock audio:', err);
          }
        },

        // ── playAmbient / stopAmbient (Task 3.3) ──────
        playAmbient: async (theme, trackUrl) => {
          try {
            const state = get();
            const { audioContext, ambientGainNode } = state;
            if (!audioContext || !ambientGainNode) return;

            // Check cache (LRU access)
            let buffer;
            const { value: cached, cache: updatedCache } = lruGet(state.preloadCache, trackUrl);
            if (cached) {
              buffer = cached;
              set({ preloadCache: updatedCache }, false, 'sceneAudio/cacheHit');
            } else {
              const response = await fetch(trackUrl);
              if (!response.ok) {
                console.warn(`⚠️ Ambient track failed to load: ${trackUrl}`);
                return;
              }
              const arrayBuffer = await response.arrayBuffer();
              buffer = await audioContext.decodeAudioData(arrayBuffer);
              set((s) => ({
                preloadCache: lruSet(s.preloadCache, trackUrl, buffer),
              }), false, 'sceneAudio/cacheSet');
            }

            // Stop current source if any
            if (_currentSource) {
              try { _currentSource.stop(); } catch { /* already stopped */ }
              _currentSource = null;
            }

            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.loop = true;
            source.connect(ambientGainNode);
            source.start(0);
            _currentSource = source;

            set({
              currentTheme: theme,
              currentSource: source,
              isAmbientPlaying: true,
            }, false, 'sceneAudio/playAmbient');
          } catch (err) {
            console.warn('⚠️ playAmbient failed:', err);
          }
        },

        stopAmbient: () => {
          try {
            if (_currentSource) {
              _currentSource.stop();
              _currentSource = null;
            }
            set({
              isAmbientPlaying: false,
              currentTheme: null,
              currentSource: null,
            }, false, 'sceneAudio/stopAmbient');
          } catch (err) {
            console.warn('⚠️ stopAmbient failed:', err);
          }
        },

        // ── crossfadeTo (Task 3.4) ─────────────────────
        crossfadeTo: async (theme, trackUrl, durationMs = 2000) => {
          try {
            const state = get();
            const { audioContext, ambientGainNode } = state;
            if (!audioContext || !ambientGainNode) return;

            // Skip if same theme already active
            if (state.currentTheme === theme && state.isAmbientPlaying) return;

            // Cancel any in-progress crossfade
            if (_crossfadeTimer) {
              clearTimeout(_crossfadeTimer);
              _crossfadeTimer = null;
            }
            if (_outgoingSource) {
              try { _outgoingSource.stop(); } catch { /* already stopped */ }
              _outgoingSource = null;
            }
            if (_outgoingGain) {
              try { _outgoingGain.disconnect(); } catch { /* ok */ }
              _outgoingGain = null;
            }

            // Fetch/decode incoming buffer
            let buffer;
            const { value: cached, cache: updatedCache } = lruGet(state.preloadCache, trackUrl);
            if (cached) {
              buffer = cached;
              set({ preloadCache: updatedCache }, false, 'sceneAudio/crossfadeCacheHit');
            } else {
              const response = await fetch(trackUrl);
              if (!response.ok) {
                console.warn(`⚠️ Crossfade track failed to load: ${trackUrl}`);
                return;
              }
              const arrayBuffer = await response.arrayBuffer();
              buffer = await audioContext.decodeAudioData(arrayBuffer);
              set((s) => ({
                preloadCache: lruSet(s.preloadCache, trackUrl, buffer),
              }), false, 'sceneAudio/crossfadeCacheSet');
            }

            const now = audioContext.currentTime;
            const targetGain = state.isMuted ? 0 : (state.isDucking
              ? (state.ambientVolume / 100) * 0.3
              : state.ambientVolume / 100);

            // Reduced motion: instant swap
            if (_prefersReducedMotion) {
              if (_currentSource) {
                try { _currentSource.stop(); } catch { /* ok */ }
              }
              const source = audioContext.createBufferSource();
              source.buffer = buffer;
              source.loop = true;
              source.connect(ambientGainNode);
              ambientGainNode.gain.setValueAtTime(targetGain, now);
              source.start(0);
              _currentSource = source;

              set({
                currentTheme: theme,
                currentSource: source,
                isAmbientPlaying: true,
              }, false, 'sceneAudio/crossfadeInstant');
              return;
            }

            // Move current source to outgoing with its own gain node
            const outGain = audioContext.createGain();
            outGain.connect(audioContext.destination);
            outGain.gain.setValueAtTime(targetGain, now);
            outGain.gain.linearRampToValueAtTime(0, now + durationMs / 1000);

            if (_currentSource) {
              try {
                _currentSource.disconnect();
                _currentSource.connect(outGain);
              } catch {
                // Source may have ended
              }
              _outgoingSource = _currentSource;
              _outgoingGain = outGain;
            }

            // Create incoming source
            const incomingSource = audioContext.createBufferSource();
            incomingSource.buffer = buffer;
            incomingSource.loop = true;
            incomingSource.connect(ambientGainNode);

            // Ramp ambient gain: 0 → target
            ambientGainNode.gain.setValueAtTime(0, now);
            ambientGainNode.gain.linearRampToValueAtTime(targetGain, now + durationMs / 1000);

            incomingSource.start(0);
            _currentSource = incomingSource;

            set({
              currentTheme: theme,
              currentSource: incomingSource,
              isAmbientPlaying: true,
            }, false, 'sceneAudio/crossfadeTo');

            // Cleanup outgoing after crossfade completes
            _crossfadeTimer = setTimeout(() => {
              _crossfadeTimer = null;
              if (_outgoingSource) {
                try { _outgoingSource.stop(); } catch { /* ok */ }
                _outgoingSource = null;
              }
              if (_outgoingGain) {
                try { _outgoingGain.disconnect(); } catch { /* ok */ }
                _outgoingGain = null;
              }
            }, durationMs + 100);
          } catch (err) {
            console.warn('⚠️ crossfadeTo failed:', err);
          }
        },

        // ── SFX playback (Task 3.5) ─────────────────────
        playSfx: (category) => {
          try {
            // Reduced motion: skip page_turn SFX
            if (_prefersReducedMotion && category === 'page_turn') return;

            const { audioContext, sfxGainNode, preloadCache } = get();
            if (!audioContext || !sfxGainNode) return;

            const path = SFX_PATHS[category];
            if (!path) return;

            const buffer = preloadCache[path];
            if (!buffer) return;

            const source = audioContext.createBufferSource();
            source.buffer = buffer;
            source.connect(sfxGainNode);
            source.start(0);
            // Fire-and-forget — source auto-disconnects when done
          } catch (err) {
            // SFX failure is silent (Req 3.6)
          }
        },

        preloadAllSfx: async () => {
          const { audioContext } = get();
          if (!audioContext) return;

          const entries = Object.entries(SFX_PATHS);
          for (const [, url] of entries) {
            try {
              const { preloadCache } = get();
              if (preloadCache[url]) continue;

              const response = await fetch(url);
              if (!response.ok) continue;
              const arrayBuffer = await response.arrayBuffer();
              const buffer = await audioContext.decodeAudioData(arrayBuffer);
              set((s) => ({
                preloadCache: lruSet(s.preloadCache, url, buffer),
              }), false, 'sceneAudio/preloadSfx');
            } catch {
              // Skip silently
            }
          }
        },

        // ── Volume / Mute (Task 3.6) ──────────────────
        setAmbientVolume: (v) => {
          const { ambientGainNode, isMuted, isDucking, audioContext } = get();
          set({ ambientVolume: v }, false, 'sceneAudio/setAmbientVolume');
          if (ambientGainNode && audioContext && !isMuted) {
            const now = audioContext.currentTime;
            const target = isDucking ? (v / 100) * 0.3 : v / 100;
            ambientGainNode.gain.setValueAtTime(ambientGainNode.gain.value, now);
            ambientGainNode.gain.linearRampToValueAtTime(target, now + 0.1);
          }
        },

        setSfxVolume: (v) => {
          const { sfxGainNode, isMuted, audioContext } = get();
          set({ sfxVolume: v }, false, 'sceneAudio/setSfxVolume');
          if (sfxGainNode && audioContext && !isMuted) {
            const now = audioContext.currentTime;
            sfxGainNode.gain.setValueAtTime(sfxGainNode.gain.value, now);
            sfxGainNode.gain.linearRampToValueAtTime(v / 100, now + 0.1);
          }
        },

        toggleMute: () => {
          const { isMuted, ambientGainNode, sfxGainNode, ambientVolume, sfxVolume, isDucking, audioContext } = get();
          const newMuted = !isMuted;
          set({ isMuted: newMuted }, false, 'sceneAudio/toggleMute');

          if (ambientGainNode && audioContext) {
            const now = audioContext.currentTime;
            if (newMuted) {
              ambientGainNode.gain.setValueAtTime(ambientGainNode.gain.value, now);
              ambientGainNode.gain.linearRampToValueAtTime(0, now + 0.1);
            } else {
              const target = isDucking ? (ambientVolume / 100) * 0.3 : ambientVolume / 100;
              ambientGainNode.gain.setValueAtTime(0, now);
              ambientGainNode.gain.linearRampToValueAtTime(target, now + 0.1);
            }
          }
          if (sfxGainNode && audioContext) {
            const now = audioContext.currentTime;
            if (newMuted) {
              sfxGainNode.gain.setValueAtTime(sfxGainNode.gain.value, now);
              sfxGainNode.gain.linearRampToValueAtTime(0, now + 0.1);
            } else {
              sfxGainNode.gain.setValueAtTime(0, now);
              sfxGainNode.gain.linearRampToValueAtTime(sfxVolume / 100, now + 0.1);
            }
          }
        },

        // ── Ducking (Task 3.7) ──────────────────────────
        duckAmbient: (level) => {
          try {
            const { ambientGainNode, ambientVolume, isMuted, audioContext } = get();
            if (!ambientGainNode || !audioContext || isMuted) {
              set({ isDucking: true }, false, 'sceneAudio/duckAmbient');
              return;
            }
            const now = audioContext.currentTime;
            const target = (ambientVolume / 100) * level;
            ambientGainNode.gain.setValueAtTime(ambientGainNode.gain.value, now);
            ambientGainNode.gain.linearRampToValueAtTime(target, now + 0.1);
            set({ isDucking: true }, false, 'sceneAudio/duckAmbient');
          } catch (err) {
            console.warn('⚠️ duckAmbient failed:', err);
          }
        },

        restoreAmbient: (durationMs = 500) => {
          try {
            const { ambientGainNode, ambientVolume, isMuted, audioContext } = get();
            if (!ambientGainNode || !audioContext) {
              set({ isDucking: false }, false, 'sceneAudio/restoreAmbient');
              return;
            }
            const now = audioContext.currentTime;
            const target = isMuted ? 0 : ambientVolume / 100;
            ambientGainNode.gain.setValueAtTime(ambientGainNode.gain.value, now);
            ambientGainNode.gain.linearRampToValueAtTime(target, now + durationMs / 1000);
            set({ isDucking: false }, false, 'sceneAudio/restoreAmbient');
          } catch (err) {
            console.warn('⚠️ restoreAmbient failed:', err);
          }
        },

        // ── Preload / Reset (Task 3.8) ─────────────────
        preloadTrack: async (theme, url) => {
          try {
            const { audioContext, preloadCache } = get();
            if (!audioContext) return;
            if (preloadCache[url]) return; // already cached

            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000);

            const response = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);

            if (!response.ok) {
              console.warn(`⚠️ Preload failed for ${url}: ${response.status}`);
              return;
            }
            const arrayBuffer = await response.arrayBuffer();
            const buffer = await audioContext.decodeAudioData(arrayBuffer);
            set((s) => ({
              preloadCache: lruSet(s.preloadCache, url, buffer),
            }), false, 'sceneAudio/preloadTrack');
          } catch (err) {
            if (err.name === 'AbortError') {
              console.warn(`⚠️ Preload timed out for ${url}`);
            } else {
              console.warn('⚠️ preloadTrack failed:', err);
            }
          }
        },

        reset: () => {
          try {
            // Stop current source
            if (_currentSource) {
              try { _currentSource.stop(); } catch { /* ok */ }
              _currentSource = null;
            }
            // Stop outgoing crossfade source
            if (_outgoingSource) {
              try { _outgoingSource.stop(); } catch { /* ok */ }
              _outgoingSource = null;
            }
            if (_outgoingGain) {
              try { _outgoingGain.disconnect(); } catch { /* ok */ }
              _outgoingGain = null;
            }
            if (_crossfadeTimer) {
              clearTimeout(_crossfadeTimer);
              _crossfadeTimer = null;
            }

            const { ambientGainNode, sfxGainNode, audioContext } = get();
            if (ambientGainNode) {
              try { ambientGainNode.disconnect(); } catch { /* ok */ }
            }
            if (sfxGainNode) {
              try { sfxGainNode.disconnect(); } catch { /* ok */ }
            }
            if (audioContext) {
              try { audioContext.close(); } catch { /* ok */ }
            }

            set({
              audioContext: null,
              ambientGainNode: null,
              sfxGainNode: null,
              currentTheme: null,
              currentSource: null,
              isAmbientPlaying: false,
              audioUnlocked: false,
              isDucking: false,
              preloadCache: {},
            }, false, 'sceneAudio/reset');
          } catch (err) {
            console.warn('⚠️ reset failed:', err);
          }
        },
      }),
      {
        name: 'scene-audio-storage',
        partialize: (state) => ({
          ambientVolume: state.ambientVolume,
          sfxVolume: state.sfxVolume,
          isMuted: state.isMuted,
        }),
      }
    ),
    { name: 'SceneAudioStore' }
  )
);

// ── audioStore subscription (Task 3.9) ─────────────
// Subscribe to isSpeaking and isPlayingVoiceRecording from audioStore.
// Duck to 30% when either is true, restore over 500ms when both false.
// Also subscribe to audioStore reset to trigger sceneAudioStore reset.
let _prevSpeakingOrPlaying = false;

useAudioStore.subscribe((state, prevState) => {
  const sceneStore = useSceneAudioStore.getState();
  const isSpeakingOrPlaying = state.isSpeaking || state.isPlayingVoiceRecording;

  if (isSpeakingOrPlaying && !_prevSpeakingOrPlaying) {
    sceneStore.duckAmbient(0.3);
  } else if (!isSpeakingOrPlaying && _prevSpeakingOrPlaying) {
    sceneStore.restoreAmbient(500);
  }
  _prevSpeakingOrPlaying = isSpeakingOrPlaying;
});

// Detect audioStore reset by subscribing to state changes that indicate a reset
// (isSpeaking goes false, isPlayingVoiceRecording goes false, ttsEnabled goes true — all at once)
let _prevAudioStoreState = useAudioStore.getState();
useAudioStore.subscribe((state) => {
  // Detect reset: ttsEnabled resets to true, isSpeaking to false, ttsRate to 1.0
  // all simultaneously from a non-default state
  const wasNonDefault = _prevAudioStoreState.isSpeaking ||
    _prevAudioStoreState.isPlayingVoiceRecording ||
    _prevAudioStoreState.currentUtterance !== null ||
    _prevAudioStoreState.voiceRecordingQueue.length > 0;

  const isDefault = !state.isSpeaking &&
    !state.isPlayingVoiceRecording &&
    state.currentUtterance === null &&
    state.voiceRecordingQueue.length === 0 &&
    state.ttsEnabled === true &&
    state.ttsRate === 1.0;

  if (wasNonDefault && isDefault) {
    useSceneAudioStore.getState().reset();
  }

  _prevAudioStoreState = state;
});
