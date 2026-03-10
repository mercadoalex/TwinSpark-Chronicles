/**
 * Text-to-Speech Service
 * Handles speech synthesis for story narration
 */

import { TTS_SETTINGS, LANGUAGE_VOICES } from '../../../shared/config';

/**
 * @typedef {Object} TTSOptions
 * @property {number} [rate] - Speech rate (0.1 to 10)
 * @property {number} [pitch] - Speech pitch (0 to 2)
 * @property {number} [volume] - Speech volume (0 to 1)
 */

class TTSService {
  constructor() {
    /** @type {SpeechSynthesis | null} */
    this.synth = window.speechSynthesis;
    
    /** @type {SpeechSynthesisUtterance | null} */
    this.currentUtterance = null;
    
    /** @type {boolean} */
    this.isEnabled = 'speechSynthesis' in window;
    
    if (!this.isEnabled) {
      console.warn('⚠️ Speech synthesis not available in this browser');
    }
  }

  /**
   * Speak text with given language
   * @param {string} text - Text to speak
   * @param {string} [language='en'] - Language code
   * @param {TTSOptions} [options={}] - TTS options
   * @returns {Promise<void>}
   */
  speak(text, language = 'en', options = {}) {
    if (!this.isEnabled) {
      console.warn('⚠️ TTS not available');
      return Promise.resolve();
    }

    return new Promise((resolve) => {
      // Cancel any ongoing speech
      this.stop();

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Apply settings
      utterance.lang = LANGUAGE_VOICES[language] || LANGUAGE_VOICES.en;
      utterance.rate = options.rate || TTS_SETTINGS.rate;
      utterance.pitch = options.pitch || TTS_SETTINGS.pitch;
      utterance.volume = options.volume || TTS_SETTINGS.volume;

      // Event handlers
      utterance.onstart = () => {
        console.log('🔊 TTS started:', text.substring(0, 50) + '...');
      };

      utterance.onend = () => {
        console.log('✅ TTS completed');
        this.currentUtterance = null;
        resolve();
      };

      utterance.onerror = (error) => {
        console.error('❌ TTS error:', error);
        this.currentUtterance = null;
        resolve(); // Resolve anyway to not block
      };

      this.currentUtterance = utterance;
      this.synth.speak(utterance);
    });
  }

  /**
   * Stop current speech
   */
  stop() {
    if (this.synth && this.synth.speaking) {
      this.synth.cancel();
      this.currentUtterance = null;
      console.log('⏹️ TTS stopped');
    }
  }

  /**
   * Pause current speech
   */
  pause() {
    if (this.synth && this.synth.speaking) {
      this.synth.pause();
      console.log('⏸️ TTS paused');
    }
  }

  /**
   * Resume paused speech
   */
  resume() {
    if (this.synth && this.synth.paused) {
      this.synth.resume();
      console.log('▶️ TTS resumed');
    }
  }

  /**
   * Check if currently speaking
   * @returns {boolean}
   */
  isSpeaking() {
    return this.synth ? this.synth.speaking : false;
  }

  /**
   * Check if paused
   * @returns {boolean}
   */
  isPaused() {
    return this.synth ? this.synth.paused : false;
  }

  /**
   * Get available voices for a language
   * @param {string} language - Language code
   * @returns {SpeechSynthesisVoice[]}
   */
  getVoicesForLanguage(language) {
    if (!this.isEnabled) return [];
    
    const voices = this.synth.getVoices();
    const targetLang = LANGUAGE_VOICES[language] || 'en-US';
    
    return voices.filter(voice => 
      voice.lang.startsWith(targetLang.split('-')[0])
    );
  }

  /**
   * Get all available voices
   * @returns {SpeechSynthesisVoice[]}
   */
  getAllVoices() {
    if (!this.isEnabled) return [];
    return this.synth.getVoices();
  }
}

export const ttsService = new TTSService();