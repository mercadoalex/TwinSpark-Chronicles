import { useState, useEffect, useRef } from 'react';
import '../components/DualStoryDisplay.css';

/**
 * VoiceCommandToast
 * Shows a brief visual indicator when a voice command is recognized,
 * and plays the confirmation audio if provided.
 */
export default function VoiceCommandToast({ match, t }) {
  const [visible, setVisible] = useState(false);
  const audioRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!match || !match.matched) {
      setVisible(false);
      return;
    }

    setVisible(true);

    // Play confirmation audio if provided
    if (match.confirmation_audio_url) {
      try {
        const url = match.confirmation_audio_url.startsWith('http')
          ? match.confirmation_audio_url
          : `http://localhost:8000${match.confirmation_audio_url}`;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.play().catch(() => {});
      } catch (_) { /* best effort */ }
    }

    // Auto-dismiss after 3 seconds
    timerRef.current = setTimeout(() => setVisible(false), 3000);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, [match]);

  if (!visible || !match?.matched) return null;

  const label = t?.voiceCommandRecognized || 'Voice command recognized!';
  const actionLabel = t?.voiceCommandAction || 'Action';

  return (
    <div className="story-voice-command-toast" role="status" aria-live="polite">
      <span className="story-voice-command-toast__icon" aria-hidden="true">✨</span>
      <div>
        <div className="story-voice-command-toast__text">{label}</div>
        {match.command_action && (
          <div className="story-voice-command-toast__action">
            {actionLabel}: {match.command_action}
          </div>
        )}
      </div>
    </div>
  );
}
