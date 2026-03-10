/**
 * Audio Feedback Service
 * Handles UI sound effects (beeps, clicks, etc.)
 */

import { BEEP_FREQUENCIES, BEEP_DURATIONS } from '../../../shared/config';

class AudioFeedbackService {
  constructor() {
    /** @type {AudioContext | null} */
    this.audioContext = null;
    
    /** @type {boolean} */
    this.isEnabled = true;
  }

  /**
   * Initialize audio context (must be called after user interaction)
   */
  init() {
    if (!this.audioContext) {
      try {
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        console.log('🎵 Audio context initialized');
      } catch (error) {
        console.error('❌ Failed to initialize audio context:', error);
        this.isEnabled = false;
      }
    }
  }

  /**
   * Play a beep sound
   * @param {number} [frequency=800] - Frequency in Hz
   * @param {number} [duration=0.2] - Duration in seconds
   * @param {number} [volume=0.3] - Volume (0 to 1)
   */
  playBeep(frequency = 800, duration = 0.2, volume = 0.3) {
    if (!this.isEnabled) return;
    
    this.init();
    
    if (!this.audioContext) return;

    try {
      const oscillator = this.audioContext.createOscillator();
      const gainNode = this.audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(this.audioContext.destination);
      
      oscillator.frequency.value = frequency;
      oscillator.type = 'sine';
      
      gainNode.gain.setValueAtTime(volume, this.audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(
        0.01, 
        this.audioContext.currentTime + duration
      );
      
      oscillator.start(this.audioContext.currentTime);
      oscillator.stop(this.audioContext.currentTime + duration);
      
    } catch (error) {
      console.error('❌ Error playing beep:', error);
    }
  }

  /**
   * Play success sound (high pitch, medium duration)
   */
  playSuccess() {
    this.playBeep(
      BEEP_FREQUENCIES.success, 
      BEEP_DURATIONS.medium
    );
  }

  /**
   * Play error sound (low pitch, long duration)
   */
  playError() {
    this.playBeep(
      BEEP_FREQUENCIES.error, 
      BEEP_DURATIONS.long
    );
  }

  /**
   * Play notification sound (very high pitch, short duration)
   */
  playNotification() {
    this.playBeep(
      BEEP_FREQUENCIES.notification, 
      BEEP_DURATIONS.short
    );
  }

  /**
   * Play choice selection sound (medium pitch, medium duration)
   */
  playChoice() {
    this.playBeep(
      BEEP_FREQUENCIES.choice, 
      BEEP_DURATIONS.medium
    );
  }

  /**
   * Play custom sound sequence
   * @param {Array<{frequency: number, duration: number, delay?: number}>} sequence
   */
  playSequence(sequence) {
    let totalDelay = 0;
    
    sequence.forEach(({ frequency, duration, delay = 0 }) => {
      setTimeout(() => {
        this.playBeep(frequency, duration);
      }, totalDelay + delay);
      
      totalDelay += (duration * 1000) + delay;
    });
  }

  /**
   * Enable/disable audio feedback
   * @param {boolean} enabled
   */
  setEnabled(enabled) {
    this.isEnabled = enabled;
    console.log(`🔊 Audio feedback ${enabled ? 'enabled' : 'disabled'}`);
  }

  /**
   * Check if audio is enabled
   * @returns {boolean}
   */
  getEnabled() {
    return this.isEnabled;
  }
}

export const audioFeedbackService = new AudioFeedbackService();