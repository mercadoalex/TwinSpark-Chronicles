/**
 * WebSocket Service
 * Handles WebSocket connection, reconnection, and message routing
 */

import { ENV, API_ENDPOINTS, TIMEOUTS } from '../../../shared/config';

/**
 * @typedef {Object} ConnectionParams
 * @property {string} lang - Language code
 * @property {string} c1_name - Child 1 name
 * @property {string} c1_gender - Child 1 gender
 * @property {string} c1_personality - Child 1 personality
 * @property {string} c1_spirit - Child 1 spirit animal
 * @property {string} c1_toy - Child 1 toy name
 * @property {string} c2_name - Child 2 name
 * @property {string} c2_gender - Child 2 gender
 * @property {string} c2_personality - Child 2 personality
 * @property {string} c2_spirit - Child 2 spirit animal
 * @property {string} c2_toy - Child 2 toy name
 */

/**
 * @typedef {Object} WebSocketMessage
 * @property {string} type - Message type
 * @property {any} [content] - Message content
 * @property {Object} [metadata] - Additional metadata
 */

class WebSocketService {
  constructor() {
    /** @type {WebSocket | null} */
    this.ws = null;
    
    /** @type {Map<string, Function[]>} */
    this.listeners = new Map();
    
    /** @type {number} */
    this.reconnectAttempts = 0;
    
    /** @type {number} */
    this.maxReconnectAttempts = TIMEOUTS.WS_MAX_RECONNECT_ATTEMPTS;
    
    /** @type {number} */
    this.reconnectDelay = TIMEOUTS.WS_RECONNECT;
    
    /** @type {ConnectionParams | null} */
    this.connectionParams = null;
    
    /** @type {boolean} */
    this.isIntentionallyClosed = false;
  }

  /**
   * Connect to WebSocket with profile parameters
   * @param {ConnectionParams} params - Connection parameters
   * @returns {Promise<void>}
   */
  connect(params) {
    return new Promise((resolve, reject) => {
      this.connectionParams = params;
      this.isIntentionallyClosed = false;
      
      const queryString = new URLSearchParams(params).toString();
      const url = `${ENV.WS_BASE_URL}${API_ENDPOINTS.WS_SESSION}?${queryString}`;
      
      console.log('🔌 Connecting to WebSocket:', url);
      
      try {
        this.ws = new WebSocket(url);
        
        this.ws.onopen = () => {
          console.log('✅ WebSocket connected successfully');
          this.reconnectAttempts = 0;
          this.notifyListeners('connected', { status: 'connected' });
          resolve();
        };
        
        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('📩 WebSocket message:', data.type, data);
            this.notifyListeners(data.type, data);
            this.notifyListeners('message', data);
          } catch (error) {
            console.error('❌ Error parsing WebSocket message:', error);
          }
        };
        
        this.ws.onerror = (error) => {
          console.error('❌ WebSocket error:', error);
          this.notifyListeners('error', { error });
          reject(error);
        };
        
        this.ws.onclose = (event) => {
          console.log('🔌 WebSocket closed:', event.code, event.reason);
          this.notifyListeners('disconnected', { 
            code: event.code, 
            reason: event.reason 
          });
          
          if (!this.isIntentionallyClosed) {
            this.attemptReconnect();
          }
        };
        
      } catch (error) {
        console.error('❌ Failed to create WebSocket:', error);
        reject(error);
      }
    });
  }

  /**
   * Send message through WebSocket
   * @param {WebSocketMessage | string} message - Message to send
   * @returns {boolean} Success status
   */
  send(message) {
    if (!this.ws) {
      console.error('❌ WebSocket not initialized');
      return false;
    }
    
    if (this.ws.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket not connected. State:', this.ws.readyState);
      return false;
    }
    
    try {
      const payload = typeof message === 'string' 
        ? message 
        : JSON.stringify(message);
      
      this.ws.send(payload);
      console.log('📤 Sent message:', message);
      return true;
    } catch (error) {
      console.error('❌ Error sending message:', error);
      return false;
    }
  }

  /**
   * Subscribe to WebSocket events
   * @param {string} eventType - Event type to listen for
   * @param {(data: any) => void} callback - Callback function
   * @returns {() => void} Unsubscribe function
   */
  on(eventType, callback) {
    if (!this.listeners.has(eventType)) {
      this.listeners.set(eventType, []);
    }
    
    this.listeners.get(eventType).push(callback);
    console.log(`📝 Registered listener for: ${eventType}`);
    
    // Return unsubscribe function
    return () => {
      const callbacks = this.listeners.get(eventType);
      if (callbacks) {
        const index = callbacks.indexOf(callback);
        if (index > -1) {
          callbacks.splice(index, 1);
          console.log(`🗑️ Unregistered listener for: ${eventType}`);
        }
      }
    };
  }

  /**
   * Notify all listeners for a specific event type
   * @param {string} eventType - Event type
   * @param {any} data - Data to pass to listeners
   */
  notifyListeners(eventType, data) {
    const callbacks = this.listeners.get(eventType) || [];
    callbacks.forEach(callback => {
      try {
        callback(data);
      } catch (error) {
        console.error(`❌ Error in listener for ${eventType}:`, error);
      }
    });
  }

  /**
   * Attempt to reconnect with exponential backoff
   */
  attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('❌ Max reconnection attempts reached');
      this.notifyListeners('reconnect_failed', {
        attempts: this.reconnectAttempts
      });
      return;
    }
    
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * this.reconnectAttempts;
    
    console.log(
      `🔄 Reconnection attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts} in ${delay}ms`
    );
    
    this.notifyListeners('reconnecting', {
      attempt: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
      delay
    });
    
    setTimeout(() => {
      if (this.connectionParams) {
        this.connect(this.connectionParams).catch(() => {
          // Error handled by connect()
        });
      }
    }, delay);
  }

  /**
   * Manually disconnect WebSocket
   */
  disconnect() {
    this.isIntentionallyClosed = true;
    
    if (this.ws) {
      console.log('🔌 Disconnecting WebSocket...');
      this.ws.close();
      this.ws = null;
    }
    
    this.listeners.clear();
    this.reconnectAttempts = 0;
    this.connectionParams = null;
  }

  /**
   * Check if WebSocket is connected
   * @returns {boolean}
   */
  isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current connection state
   * @returns {string}
   */
  getState() {
    if (!this.ws) return 'CLOSED';
    
    const states = {
      [WebSocket.CONNECTING]: 'CONNECTING',
      [WebSocket.OPEN]: 'OPEN',
      [WebSocket.CLOSING]: 'CLOSING',
      [WebSocket.CLOSED]: 'CLOSED'
    };
    
    return states[this.ws.readyState] || 'UNKNOWN';
  }
}

// Singleton instance
export const websocketService = new WebSocketService();