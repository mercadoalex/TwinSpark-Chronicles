/**
 * Audio Store
 * Manages audio settings, TTS state, and voice recording playback
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

/** @type {HTMLAudioElement | null} */
let _voiceRecordingAudioEl = null;

export const useAudioStore = create(
  devtools(
    persist(
      (set, get) => ({
        // TTS State
        ttsEnabled: true,
        ttsLanguage: 'en',
        ttsRate: 1.0,
        ttsPitch: 1.0,
        ttsVolume: 1.0,
        isSpeaking: false,
        isPaused: false,
        audioFeedbackEnabled: true,
        currentUtterance: null,

        // Voice Recording Playback State
        isPlayingVoiceRecording: false,
        currentVoiceRecording: null,   // { audio_base64, recorder_name, recording_id, source }
        voiceRecordingQueue: [],       // Array of PlaybackResult objects to play in sequence
        ttsPausedForRecording: false,  // Whether TTS was paused to let a recording play

        // TTS Actions
        setTTSEnabled: (enabled) => 
          set({ ttsEnabled: enabled }, false, 'audio/setTTSEnabled'),

        setTTSLanguage: (language) => 
          set({ ttsLanguage: language }, false, 'audio/setTTSLanguage'),

        setTTSRate: (rate) => 
          set({ ttsRate: rate }, false, 'audio/setTTSRate'),

        setTTSPitch: (pitch) => 
          set({ ttsPitch: pitch }, false, 'audio/setTTSPitch'),

        setTTSVolume: (volume) => 
          set({ ttsVolume: volume }, false, 'audio/setTTSVolume'),

        setIsSpeaking: (speaking) => 
          set({ isSpeaking: speaking }, false, 'audio/setIsSpeaking'),

        setIsPaused: (paused) => 
          set({ isPaused: paused }, false, 'audio/setIsPaused'),

        setAudioFeedbackEnabled: (enabled) => 
          set({ audioFeedbackEnabled: enabled }, false, 'audio/setAudioFeedbackEnabled'),

        setCurrentUtterance: (utterance) => 
          set({ currentUtterance: utterance }, false, 'audio/setCurrentUtterance'),

        toggleTTS: () => 
          set((state) => ({ 
            ttsEnabled: !state.ttsEnabled 
          }), false, 'audio/toggleTTS'),

        toggleAudioFeedback: () => 
          set((state) => ({ 
            audioFeedbackEnabled: !state.audioFeedbackEnabled 
          }), false, 'audio/toggleAudioFeedback'),

        // Voice Recording Playback Actions

        /**
         * Play a single voice recording from base64 MP3 data.
         * Pauses TTS while the recording plays, resumes when done.
         * @param {string} base64Mp3 - Base64-encoded MP3 audio
         * @param {{ recorder_name?: string, recording_id?: string, source?: string }} metadata
         */
        playVoiceRecording: (base64Mp3, metadata = {}) => {
          const state = get();

          // Pause TTS if currently speaking
          if (state.isSpeaking && window.speechSynthesis) {
            window.speechSynthesis.pause();
            set({ ttsPausedForRecording: true }, false, 'audio/ttsPausedForRecording');
          }

          // Stop any currently playing voice recording
          if (_voiceRecordingAudioEl) {
            _voiceRecordingAudioEl.pause();
            _voiceRecordingAudioEl = null;
          }

          const audio = new Audio(`data:audio/mp3;base64,${base64Mp3}`);
          _voiceRecordingAudioEl = audio;

          set({
            isPlayingVoiceRecording: true,
            currentVoiceRecording: {
              audio_base64: base64Mp3,
              recorder_name: metadata.recorder_name || null,
              recording_id: metadata.recording_id || null,
              source: metadata.source || 'recording',
            },
          }, false, 'audio/playVoiceRecording');

          audio.onended = () => {
            _voiceRecordingAudioEl = null;
            set({
              isPlayingVoiceRecording: false,
              currentVoiceRecording: null,
            }, false, 'audio/voiceRecordingEnded');

            // Play next in queue or resume TTS
            const { voiceRecordingQueue, ttsPausedForRecording } = get();
            if (voiceRecordingQueue.length > 0) {
              const [next, ...rest] = voiceRecordingQueue;
              set({ voiceRecordingQueue: rest }, false, 'audio/dequeueVoiceRecording');
              get().playVoiceRecording(next.audio_base64, next);
            } else if (ttsPausedForRecording && window.speechSynthesis) {
              window.speechSynthesis.resume();
              set({ ttsPausedForRecording: false }, false, 'audio/ttsResumed');
            }
          };

          audio.onerror = () => {
            console.warn('⚠️ Voice recording playback failed, falling back');
            _voiceRecordingAudioEl = null;
            set({
              isPlayingVoiceRecording: false,
              currentVoiceRecording: null,
            }, false, 'audio/voiceRecordingError');

            // Try next in queue or resume TTS
            const { voiceRecordingQueue, ttsPausedForRecording } = get();
            if (voiceRecordingQueue.length > 0) {
              const [next, ...rest] = voiceRecordingQueue;
              set({ voiceRecordingQueue: rest }, false, 'audio/dequeueVoiceRecording');
              get().playVoiceRecording(next.audio_base64, next);
            } else if (ttsPausedForRecording && window.speechSynthesis) {
              window.speechSynthesis.resume();
              set({ ttsPausedForRecording: false }, false, 'audio/ttsResumed');
            }
          };

          audio.play().catch((err) => {
            console.warn('⚠️ Voice recording play() rejected:', err);
            audio.onended = null;
            audio.onerror = null;
            _voiceRecordingAudioEl = null;
            set({
              isPlayingVoiceRecording: false,
              currentVoiceRecording: null,
            }, false, 'audio/voiceRecordingPlayRejected');
          });
        },

        /**
         * Stop the currently playing voice recording immediately.
         */
        stopVoiceRecording: () => {
          if (_voiceRecordingAudioEl) {
            _voiceRecordingAudioEl.onended = null;
            _voiceRecordingAudioEl.onerror = null;
            _voiceRecordingAudioEl.pause();
            _voiceRecordingAudioEl = null;
          }

          const { ttsPausedForRecording } = get();
          set({
            isPlayingVoiceRecording: false,
            currentVoiceRecording: null,
            voiceRecordingQueue: [],
          }, false, 'audio/stopVoiceRecording');

          // Resume TTS if it was paused
          if (ttsPausedForRecording && window.speechSynthesis) {
            window.speechSynthesis.resume();
            set({ ttsPausedForRecording: false }, false, 'audio/ttsResumed');
          }
        },

        /**
         * Add a voice recording to the playback queue.
         * If nothing is currently playing, starts playback immediately.
         * @param {{ audio_base64: string, recorder_name?: string, recording_id?: string, source?: string }} playbackResult
         */
        queueVoiceRecording: (playbackResult) => {
          const { isPlayingVoiceRecording } = get();
          if (!isPlayingVoiceRecording) {
            get().playVoiceRecording(playbackResult.audio_base64, playbackResult);
          } else {
            set((state) => ({
              voiceRecordingQueue: [...state.voiceRecordingQueue, playbackResult],
            }), false, 'audio/queueVoiceRecording');
          }
        },

        reset: () => {
          // Stop any playing voice recording on reset
          if (_voiceRecordingAudioEl) {
            _voiceRecordingAudioEl.onended = null;
            _voiceRecordingAudioEl.onerror = null;
            _voiceRecordingAudioEl.pause();
            _voiceRecordingAudioEl = null;
          }
          set({
            ttsEnabled: true,
            ttsLanguage: 'en',
            ttsRate: 1.0,
            ttsPitch: 1.0,
            ttsVolume: 1.0,
            isSpeaking: false,
            isPaused: false,
            currentUtterance: null,
            isPlayingVoiceRecording: false,
            currentVoiceRecording: null,
            voiceRecordingQueue: [],
            ttsPausedForRecording: false,
          }, false, 'audio/reset');
        },

        // Selectors
        getTTSSettings: () => {
          const state = get();
          return {
            language: state.ttsLanguage,
            rate: state.ttsRate,
            pitch: state.ttsPitch,
            volume: state.ttsVolume
          };
        },

        isAudioEnabled: () => {
          return get().ttsEnabled || get().audioFeedbackEnabled;
        }
      }),
      {
        name: 'audio-storage',
        partialize: (state) => ({
          ttsEnabled: state.ttsEnabled,
          ttsLanguage: state.ttsLanguage,
          ttsRate: state.ttsRate,
          ttsPitch: state.ttsPitch,
          ttsVolume: state.ttsVolume,
          audioFeedbackEnabled: state.audioFeedbackEnabled
        })
      }
    ),
    { name: 'AudioStore' }
  )
);