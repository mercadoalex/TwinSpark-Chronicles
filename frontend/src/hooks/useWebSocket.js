import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (url, onMessage) => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const ws = useRef(null);

  useEffect(() => {
    console.log('🔌 useWebSocket: Attempting to connect to:', url);
    
    try {
      ws.current = new WebSocket(url);
      
      ws.current.onopen = () => {
        console.log('✅ WebSocket connected successfully!');
        setIsConnected(true);
        setConnectionError(null);
      };
      
      ws.current.onmessage = (event) => {
        console.log('📨 WebSocket message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          console.log('📦 Parsed message:', data);
          if (onMessage) {
            onMessage(data);
          }
        } catch (error) {
          console.error('❌ Failed to parse WebSocket message:', error);
        }
      };
      
      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        setConnectionError(error);
      };
      
      ws.current.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
      };
      
    } catch (error) {
      console.error('❌ Failed to create WebSocket:', error);
      setConnectionError(error);
    }

    return () => {
      console.log('🔌 useWebSocket: Cleaning up connection');
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url, onMessage]);

  const sendMessage = (message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      console.log('📤 Sending WebSocket message:', message);
      ws.current.send(JSON.stringify(message));
    } else {
      console.error('❌ WebSocket not connected, cannot send:', message);
    }
  };

  return { isConnected, connectionError, sendMessage };
};