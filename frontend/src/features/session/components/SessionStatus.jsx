import React from 'react';
import { useSessionStore } from '../../../stores/sessionStore';
import './SessionStatus.css';

export default function SessionStatus({ t }) {
  const { isConnected, connectionState, error } = useSessionStore();

  const getStatusIcon = () => {
    if (error) return { emoji: '⚠️', className: 'session-status__icon--error' };
    if (isConnected) return { emoji: '✨', className: 'session-status__icon--connected' };
    if (connectionState === 'CONNECTING') return { emoji: '💫', className: 'session-status__icon--connecting' };
    return { emoji: '💤', className: 'session-status__icon--disconnected' };
  };

  const getStatusText = () => {
    if (error) return error;
    if (isConnected) return t?.connected || 'Connected';
    if (connectionState === 'CONNECTING') return t?.connecting || 'Connecting...';
    return 'Disconnected';
  };

  const getStatusColor = () => {
    if (error) return '#ef4444';
    if (isConnected) return '#8b5cf6';
    if (connectionState === 'CONNECTING') return '#f59e0b';
    return 'rgba(255,255,255,0.7)';
  };

  const { emoji, className } = getStatusIcon();

  return (
    <div
      className="session-status"
      role="status"
      aria-live="assertive"
      style={{ color: getStatusColor() }}
    >
      <span className={`session-status__icon ${className}`} aria-hidden="true">
        {emoji}
      </span>
      <span className="session-status__sr-only">{getStatusText()}</span>
    </div>
  );
}
