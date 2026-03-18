import React from 'react';
import { useSessionStore } from '../../../stores/sessionStore';

export default function SessionStatus({ t }) {
  const { isConnected, connectionState, error } = useSessionStore();

  const getStatusColor = () => {
    if (error) return '#ef4444';
    if (isConnected) return '#8b5cf6';
    if (connectionState === 'CONNECTING') return '#f59e0b';
    return 'rgba(255,255,255,0.7)';
  };

  const getStatusText = () => {
    if (error) return error;
    if (isConnected) return t?.connected || 'Connected';
    if (connectionState === 'CONNECTING') return t?.connecting || 'Connecting...';
    return 'Disconnected';
  };

  return (
    <p
      role="status"
      aria-live="assertive"
      style={{
        fontSize: '1.2rem',
        color: getStatusColor(),
        marginBottom: '30px',
        textAlign: 'center',
        fontWeight: 500
      }}
    >
      {getStatusText()}
    </p>
  );
}
