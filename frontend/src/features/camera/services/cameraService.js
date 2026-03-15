/**
 * Camera Service
 * Manages webcam access, frame capture, and JPEG encoding.
 * Only activates after privacy consent from PrivacyModal.
 * Never persists frames to disk or localStorage.
 *
 * Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 11.1, 11.6
 */

/** @type {number} Default capture width */
const DEFAULT_WIDTH = 640;

/** @type {number} Default capture height */
const DEFAULT_HEIGHT = 480;

/** @type {number} Minimum capture rate in fps */
const MIN_FPS = 1;

/** @type {number} Maximum capture rate in fps */
const MAX_FPS = 5;

/** @type {number} Default capture rate in fps */
const DEFAULT_FPS = 2;

/** @type {number} JPEG quality (0-1 range, maps to 60-80%) */
const JPEG_QUALITY = 0.7;

/** @type {number} Reconnection delay in ms */
const RECONNECT_DELAY_MS = 3000;

class CameraService {
  constructor() {
    /** @type {MediaStream | null} */
    this.stream = null;

    /** @type {boolean} */
    this.isActive = false;

    /** @type {HTMLVideoElement | null} */
    this._video = null;

    /** @type {HTMLCanvasElement | null} */
    this._canvas = null;

    /** @type {CanvasRenderingContext2D | null} */
    this._ctx = null;

    /** @type {number} Capture interval id */
    this._captureIntervalId = null;

    /** @type {number} Frames per second (1-5) */
    this._fps = DEFAULT_FPS;

    /** @type {boolean} Whether privacy consent has been given */
    this._privacyConsented = false;

    /** @type {boolean} Whether a reconnection attempt is in progress */
    this._reconnecting = false;

    /** @type {Map<string, Function[]>} Event listeners */
    this._listeners = new Map();
  }

  /**
   * Start camera with 640x480 constraint and mirrored preview.
   * Will not activate unless privacy consent has been granted.
   * @returns {Promise<MediaStream>}
   */
  async start() {
    if (!this._privacyConsented) {
      console.warn('📷 Camera blocked: privacy consent not given');
      this._emit('camera_unavailable');
      throw new Error('Privacy consent required before activating camera');
    }

    if (this.isActive && this.stream) {
      return this.stream;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: DEFAULT_WIDTH },
          height: { ideal: DEFAULT_HEIGHT },
          facingMode: 'user'
        },
        audio: false
      });

      this.stream = stream;
      this.isActive = true;

      this._setupVideo(stream);
      this._listenForStreamEnd(stream);

      console.log('📷 Camera started');
      return stream;
    } catch (error) {
      console.error('📷 Camera access denied or failed:', error.name);
      this.isActive = false;
      this.stream = null;
      this._emit('camera_unavailable');
      throw error;
    }
  }

  /**
   * Stop camera and release all resources.
   */
  stop() {
    this._stopCaptureInterval();

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this._video) {
      this._video.srcObject = null;
      this._video = null;
    }

    this._canvas = null;
    this._ctx = null;
    this.isActive = false;
    this._reconnecting = false;

    console.log('📷 Camera stopped');
  }

  /**
   * Capture a single JPEG frame encoded as base64.
   * Returns null if camera is not active.
   * Frames are never persisted to disk or localStorage.
   * @returns {string | null} Base64-encoded JPEG string (without data URI prefix)
   */
  captureFrame() {
    if (!this.isActive || !this._video || !this._canvas || !this._ctx) {
      return null;
    }

    if (this._video.readyState < this._video.HAVE_CURRENT_DATA) {
      return null;
    }

    // Draw current video frame to canvas (mirrored)
    this._ctx.save();
    this._ctx.translate(this._canvas.width, 0);
    this._ctx.scale(-1, 1);
    this._ctx.drawImage(this._video, 0, 0, this._canvas.width, this._canvas.height);
    this._ctx.restore();

    // Encode as JPEG with quality 60-80% (0.7 = 70%)
    const dataUrl = this._canvas.toDataURL('image/jpeg', JPEG_QUALITY);

    // Strip the data URI prefix, return only base64 payload
    const base64 = dataUrl.split(',')[1] || null;
    return base64;
  }

  /**
   * Set capture rate between 1 and 5 fps.
   * @param {number} fps - Frames per second (clamped to 1-5)
   */
  setCaptureRate(fps) {
    this._fps = Math.max(MIN_FPS, Math.min(MAX_FPS, Math.round(fps)));
    console.log(`📷 Capture rate set to ${this._fps} fps`);

    // Restart interval if currently capturing
    if (this._captureIntervalId !== null) {
      this._stopCaptureInterval();
      this._startCaptureInterval();
    }
  }

  /**
   * Register a callback for the camera_unavailable event.
   * @param {() => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onUnavailable(callback) {
    return this._on('camera_unavailable', callback);
  }

  /**
   * Register a callback for the camera_lost event.
   * @param {() => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onLost(callback) {
    return this._on('camera_lost', callback);
  }

  /**
   * Register a callback for the camera_reconnected event.
   * @param {() => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onReconnected(callback) {
    return this._on('camera_reconnected', callback);
  }

  /**
   * Register a callback for captured frames.
   * Called at the configured fps rate with base64 JPEG data.
   * @param {(base64Frame: string) => void} callback
   * @returns {() => void} Unsubscribe function
   */
  onFrame(callback) {
    return this._on('frame', callback);
  }

  /**
   * Set privacy consent status. Camera will not start without consent.
   * @param {boolean} consented
   */
  setPrivacyConsent(consented) {
    this._privacyConsented = !!consented;
    console.log(`📷 Privacy consent: ${this._privacyConsented ? 'granted' : 'revoked'}`);
  }

  /**
   * Start the periodic frame capture interval.
   * Emits 'frame' events at the configured fps rate.
   */
  startCapturing() {
    if (this._captureIntervalId !== null) return;
    this._startCaptureInterval();
  }

  /**
   * Stop the periodic frame capture interval.
   */
  stopCapturing() {
    this._stopCaptureInterval();
  }

  /**
   * Get the CSS transform style for mirroring the video preview.
   * @returns {string}
   */
  getMirrorStyle() {
    return 'scaleX(-1)';
  }

  // ─── Private Methods ──────────────────────────────────────

  /**
   * Set up the hidden video element and canvas for frame capture.
   * @param {MediaStream} stream
   * @private
   */
  _setupVideo(stream) {
    this._video = document.createElement('video');
    this._video.srcObject = stream;
    this._video.setAttribute('playsinline', '');
    this._video.muted = true;
    this._video.play().catch(err => {
      console.error('📷 Video play failed:', err);
    });

    this._canvas = document.createElement('canvas');
    this._canvas.width = DEFAULT_WIDTH;
    this._canvas.height = DEFAULT_HEIGHT;
    this._ctx = this._canvas.getContext('2d');
  }

  /**
   * Listen for stream track ending (camera disconnect).
   * On disconnect, emits camera_lost and retries once after 3 seconds.
   * @param {MediaStream} stream
   * @private
   */
  _listenForStreamEnd(stream) {
    const videoTrack = stream.getVideoTracks()[0];
    if (!videoTrack) return;

    videoTrack.addEventListener('ended', () => {
      console.warn('📷 Camera stream ended unexpectedly');
      this.isActive = false;
      this._stopCaptureInterval();
      this._emit('camera_lost');

      // Retry once after 3 seconds
      if (!this._reconnecting) {
        this._reconnecting = true;
        console.log('📷 Attempting camera reconnection in 3 seconds...');

        setTimeout(async () => {
          try {
            await this.start();
            this._reconnecting = false;
            this._emit('camera_reconnected');
            console.log('📷 Camera reconnected successfully');
          } catch {
            this._reconnecting = false;
            console.error('📷 Camera reconnection failed');
            this._emit('camera_unavailable');
          }
        }, RECONNECT_DELAY_MS);
      }
    });
  }

  /**
   * Start the frame capture interval.
   * @private
   */
  _startCaptureInterval() {
    const intervalMs = 1000 / this._fps;
    this._captureIntervalId = setInterval(() => {
      const frame = this.captureFrame();
      if (frame) {
        this._emit('frame', frame);
      }
    }, intervalMs);
    console.log(`📷 Frame capture started at ${this._fps} fps`);
  }

  /**
   * Stop the frame capture interval.
   * @private
   */
  _stopCaptureInterval() {
    if (this._captureIntervalId !== null) {
      clearInterval(this._captureIntervalId);
      this._captureIntervalId = null;
      console.log('📷 Frame capture stopped');
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
        console.error(`📷 Error in ${event} listener:`, error);
      }
    });
  }
}

// Singleton instance
export const cameraService = new CameraService();
