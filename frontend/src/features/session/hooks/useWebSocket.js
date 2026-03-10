/**
 * useWebSocket Hook
 * Manages WebSocket connection lifecycle in React components
 */

import { useEffect, useCallback, useRef } from 'react';
import { websocketService } from '../services/websocketService';

/**
 * @typedef {Object} UseWebSocketOptions
 * @property {boolean} [autoConnect=true] - Auto-connect on mount
 * @property {boolean} [reconnectOnUnmount=false] - Keep connection alive on unmount
 */

/**
 * Hook for managing WebSocket connection
 * @param {Object} params - Connection parameters
 * @param {UseWebSocketOptions} [options={}] - Hook options
 * @returns {Object} WebSocket utilities
 */
export function useWebSocket(params, options = {}) {
  const { autoConnect = true, reconnectOnUnmount = false } = options;
  const unsubscribersRef = useRef([]);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(async () => {
    if (!params) {
      console.warn('⚠️ Cannot connect: params not provided');
      return;
    }
    
    try {
      await websocketService.connect(params);
      console.log('✅ WebSocket connected via hook');
    } catch (error) {
      console.error('❌ WebSocket connection failed:', error);
      throw error;
    }
  }, [params]);

  /**
   * Send message through WebSocket
   */
  const sendMessage = useCallback((type, payload = {}) => {
    return websocketService.send({ type, ...payload });
  }, []);

  /**
   * Subscribe to WebSocket events
   */
  const subscribe = useCallback((eventType, callback) => {
    const unsubscribe = websocketService.on(eventType, callback);
    unsubscribersRef.current.push(unsubscribe);
    return unsubscribe;
  }, []);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  /**
   * Get connection state
   */
  const getState = useCallback(() => {
    return websocketService.getState();
  }, []);

  /**
   * Check if connected
   */
  const isConnected = useCallback(() => {
    return websocketService.isConnected();
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect && params) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      // Unsubscribe all listeners
      unsubscribersRef.current.forEach(unsubscribe => unsubscribe());
      unsubscribersRef.current = [];

      // Disconnect if configured
      if (!reconnectOnUnmount) {
        disconnect();
      }
    };
  }, [autoConnect, params, connect, disconnect, reconnectOnUnmount]);

  return {
    connect,
    disconnect,
    sendMessage,
    subscribe,
    getState,
    isConnected
  };
}