/**
 * Audio Input Service
 * Captures microphone audio with client-side Voice Activity Detection (VAD).
 * Streams base64-encoded audio segments containing detected speech.
 * Never persists audio to disk or localStorage.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 11.2
 */

/** @type {number} Target sample rate for audio capture */
const TARGET_SAMPLE_RATE = 16000;

/** @type {number} Silence duration (ms) before ending a speech segment */
const SILENCE_TIMEOUT_MS = 800;

/** @type {number} Reconnection delay in ms */
const RECONNECT_DELAY_MS = 3000;

/** @type {number} RMS threshold for speech detection */
const SPEECH_THRESHOLD = 0.015;

/** @type {number} ScriptProcessorNode buffer size */
const BUFFER_SIZE = 4096;

class AudioInputService {
  constructor() {
    /** @type {boolean} */
    this.isActive = false;

    /** @type {boolean} */
    this.isSpeechDetected = false;

    /** @type {MediaStream | null} */
    this._stream = null;

    /** @type {AudioContext | null} */
    this._audioContext = null;

    /** @type {MediaStreamAudioSourceNode | null} */
    this._sourceNode = null;

    /** @type {ScriptProcessorNode | null} */
    this._processorNode = null;

    /** @type {Float32Array[]} Buffered audio chunks during speech */
    this._speechBuffer = [];

    /** @type {number | null} Silence timeout id */
    this._silenceTimeoutId = null;

    /** @type {boolean} Whether a reconnection attempt is in progress */
    this._reconnecting = false;

    /** @type {Map<string, Function[]>} Event listeners */
    this._listeners = new Map();
  }

  /**
   * Start microphone capture at 16kHz mono using Web Audio API.
   * @returns {Promise<MediaStream>}
   */
  async start() {
    if (this.isActive && this._stream) {
      return this._stream;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: { ideal: TARGET_SAMPLE_RATE },
          echoCancellation: true,
          noiseSuppression: true
        },
        video: false
      });

      this._stream = stream;
      this.isActive = true;

      this._setupAudioPipeline(stream);
      this._listenForStreamEnd(stream);

      console.log('🎤 Microphone started');
      return stream;
    } catch (error) {
      console.error('🎤 Microphone access denied or failed:', error.name);
      this.isActive = false;
      this._stream = null;
      this._emit('mic_unavailable');
      throw error;
    }
  }

  /**
   * Stop microphone and release all resources.
   */
  stop() {
    this._clearSilenceTimeout();

    // If speech was in progress, discard the buffer (never persist)
    this._speechBuffer = [];
    this.isSpeechDetected = false;

    if (this._processorNode) {
      this._processorNode.disconnect();
      this._processorNode.onaudioprocess = null;
      this._processorNode = null;
    }

    if (this._sourceNode) {
      this._sourceNode.disconnect();
      this._sourceNode = null;
    }

    if (this._audioContext) {
      this._audioContext.close().catch(() => {});
      this._audioContext = null;
    }

    if (this._stream) {
      this._stream.getTracks().forEach(track => track.stop());
      this._stream = null;
    }

    this.isActive = false;
    this._reconnecting = false;

    console.log('🎤 Microphone stopped');
  }

  /**
   * Register a callback for speech segment events.
   * Called with base64-encoded audio when speech ends (after 800ms silence).
   * @param {(base64Audio: string) => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onSpeechSegment(callback) {
    return this._on('speech_segment', callback);
  }

  /**
   * Register a callback for the mic_unavailable event.
   * @param {() => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onUnavailable(callback) {
    return this._on('mic_unavailable', callback);
  }

  /**
   * Register a callback for the mic_lost event.
   * @param {() => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onLost(callback) {
    return this._on('mic_lost', callback);
  }

  // ─── Private Methods ──────────────────────────────────────

  /**
   * Set up the Web Audio API pipeline for capture and VAD.
   * Uses ScriptProcessorNode to access raw PCM samples.
   * Resamples to 16kHz mono if the hardware sample rate differs.
   * @param {MediaStream} stream
   * @private
   */
  _setupAudioPipeline(stream) {
    this._audioContext = new (window.AudioContext || window.webkitAudioContext)({
      sampleRate: TARGET_SAMPLE_RATE
    });

    this._sourceNode = this._audioContext.createMediaStreamSource(stream);

    // ScriptProcessorNode gives us access to raw PCM for VAD + buffering
    this._processorNode = this._audioContext.createScriptProcessor(BUFFER_SIZE, 1, 1);

    this._processorNode.onaudioprocess = (event) => {
      if (!this.isActive) return;

      const inputData = event.inputBuffer.getChannelData(0);
      const samples = new Float32Array(inputData);

      const rms = this._calculateRMS(samples);
      const isSpeech = rms > SPEECH_THRESHOLD;

      if (isSpeech) {
        this._handleSpeechDetected(samples);
      } else {
        this._handleSilence(samples);
      }
    };

    this._sourceNode.connect(this._processorNode);
    // Connect to destination to keep the processor running
    this._processorNode.connect(this._audioContext.destination);
  }

  /**
   * Calculate Root Mean Square (RMS) of audio samples for VAD.
   * @param {Float32Array} samples
   * @returns {number}
   * @private
   */
  _calculateRMS(samples) {
    let sum = 0;
    for (let i = 0; i < samples.length; i++) {
      sum += samples[i] * samples[i];
    }
    return Math.sqrt(sum / samples.length);
  }

  /**
   * Handle a chunk where speech is detected.
   * Starts buffering if not already, resets silence timeout.
   * @param {Float32Array} samples
   * @private
   */
  _handleSpeechDetected(samples) {
    if (!this.isSpeechDetected) {
      this.isSpeechDetected = true;
      this._speechBuffer = [];
      console.log('🎤 Speech onset detected');
    }

    this._speechBuffer.push(new Float32Array(samples));
    this._clearSilenceTimeout();
  }

  /**
   * Handle a chunk where silence is detected.
   * If speech was in progress, starts the 800ms silence countdown.
   * @param {Float32Array} samples
   * @private
   */
  _handleSilence(samples) {
    if (!this.isSpeechDetected) return;

    // Keep buffering during silence countdown so we don't clip the tail
    this._speechBuffer.push(new Float32Array(samples));

    if (this._silenceTimeoutId === null) {
      this._silenceTimeoutId = setTimeout(() => {
        this._finalizeSpeechSegment();
      }, SILENCE_TIMEOUT_MS);
    }
  }

  /**
   * Finalize a speech segment: merge buffered chunks, encode as base64, emit.
   * Audio is never persisted to disk or localStorage.
   * @private
   */
  _finalizeSpeechSegment() {
    this._clearSilenceTimeout();

    if (this._speechBuffer.length === 0) {
      this.isSpeechDetected = false;
      return;
    }

    // Merge all buffered Float32Array chunks into one
    const totalLength = this._speechBuffer.reduce((sum, chunk) => sum + chunk.length, 0);
    const merged = new Float32Array(totalLength);
    let offset = 0;
    for (const chunk of this._speechBuffer) {
      merged.set(chunk, offset);
      offset += chunk.length;
    }

    // Convert Float32 [-1, 1] to Int16 PCM for transmission
    const pcm16 = this._float32ToInt16(merged);

    // Encode as base64
    const base64 = this._arrayBufferToBase64(pcm16.buffer);

    // Clear buffer immediately — never persist
    this._speechBuffer = [];
    this.isSpeechDetected = false;

    console.log(`🎤 Speech segment complete: ${pcm16.length} samples`);
    this._emit('speech_segment', base64);
  }

  /**
   * Convert Float32Array samples to Int16Array (PCM 16-bit).
   * @param {Float32Array} float32 - Audio samples in [-1, 1] range
   * @returns {Int16Array}
   * @private
   */
  _float32ToInt16(float32) {
    const int16 = new Int16Array(float32.length);
    for (let i = 0; i < float32.length; i++) {
      const clamped = Math.max(-1, Math.min(1, float32[i]));
      int16[i] = clamped < 0 ? clamped * 0x8000 : clamped * 0x7FFF;
    }
    return int16;
  }

  /**
   * Encode an ArrayBuffer as a base64 string.
   * @param {ArrayBuffer} buffer
   * @returns {string}
   * @private
   */
  _arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.length; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Listen for audio stream track ending (mic disconnect).
   * On disconnect, emits mic_lost and retries once after 3 seconds.
   * @param {MediaStream} stream
   * @private
   */
  _listenForStreamEnd(stream) {
    const audioTrack = stream.getAudioTracks()[0];
    if (!audioTrack) return;

    audioTrack.addEventListener('ended', () => {
      console.warn('🎤 Microphone stream ended unexpectedly');
      this.isActive = false;
      this._clearSilenceTimeout();
      this._speechBuffer = [];
      this.isSpeechDetected = false;
      this._emit('mic_lost');

      // Retry once after 3 seconds
      if (!this._reconnecting) {
        this._reconnecting = true;
        console.log('🎤 Attempting mic reconnection in 3 seconds...');

        setTimeout(async () => {
          try {
            await this.start();
            this._reconnecting = false;
            console.log('🎤 Microphone reconnected successfully');
          } catch {
            this._reconnecting = false;
            console.error('🎤 Microphone reconnection failed');
            this._emit('mic_unavailable');
          }
        }, RECONNECT_DELAY_MS);
      }
    });
  }

  /**
   * Clear the silence timeout if active.
   * @private
   */
  _clearSilenceTimeout() {
    if (this._silenceTimeoutId !== null) {
      clearTimeout(this._silenceTimeoutId);
      this._silenceTimeoutId = null;
    }
  }

  /**
   * Subscribe to an internal event.
   * @param {string} event
   * @param {Function} callback
   * @returns {() => void} Unsubscribe function
   * @private
   */
  _on(event, callback) {
    if (!this._listeners.has(event)) {
      this._listeners.set(event, []);
    }
    this._listeners.get(event).push(callback);

    return () => {
      const callbacks = this._listeners.get(event);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
        }
      }
    };
  }

  /**
   * Emit an internal event.
   * @param {string} event
   * @param {any} [data]
   * @private
   */
  _emit(event, data) {
    const callbacks = this._listeners.get(event) || [];
    callbacks.forEach(cb => {
      try {
        cb(data);
      } catch (error) {
        console.error(`🎤 Error in ${event} listener:`, error);
      }
    });
  }
}

// Singleton instance
export const audioInputService = new AudioInputService();
