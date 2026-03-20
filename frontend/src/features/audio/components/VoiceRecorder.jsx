import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, Square, Play, Pause, RotateCcw, Check, X, AlertTriangle } from 'lucide-react';
import { ChildFriendlyButton } from '../../../shared/components';
import { useVoiceRecordingStore } from '../../../stores/voiceRecordingStore';

const RELATIONSHIPS = ['grandparent', 'parent', 'sibling', 'other'];
const MESSAGE_TYPES = ['story_intro', 'encouragement', 'sound_effect', 'voice_command', 'custom'];
const MAX_DURATION = 60;

/**
 * VoiceRecorder Component
 * Child-friendly voice recording with waveform visualization,
 * playback preview, metadata form, and confetti celebration.
 */
export default function VoiceRecorder({ siblingPairId, language = 'en', onClose, t }) {
  // --- Phase: 'idle' | 'recording' | 'preview' | 'metadata' | 'uploading' | 'success' | 'permissionError'
  const [phase, setPhase] = useState('idle');
  const [elapsed, setElapsed] = useState(0);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [waveformBars, setWaveformBars] = useState(new Array(12).fill(5));
  const [uploadError, setUploadError] = useState(null);
  const [showConfetti, setShowConfetti] = useState(false);

  // Metadata state
  const [recorderName, setRecorderName] = useState('');
  const [relationship, setRelationship] = useState('grandparent');
  const [messageType, setMessageType] = useState('story_intro');
  const [commandPhrase, setCommandPhrase] = useState('');
  const [commandAction, setCommandAction] = useState('');

  // Refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const streamRef = useRef(null);
  const audioElRef = useRef(null);

  const { uploadRecording, isUploading } = useVoiceRecordingStore();

  const tr = useCallback((key, fallback) => (t && t[key]) || fallback || key, [t]);

  // --- Cleanup on unmount ---
  useEffect(() => {
    return () => {
      stopEverything();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function stopEverything() {
    if (timerRef.current) clearInterval(timerRef.current);
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current = null;
    }
    if (audioUrl) URL.revokeObjectURL(audioUrl);
  }

  // --- Waveform analysis loop ---
  function startWaveformLoop() {
    const analyser = analyserRef.current;
    if (!analyser) return;
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    function loop() {
      analyser.getByteFrequencyData(dataArray);
      // Compute average level 0-1
      const avg = dataArray.reduce((s, v) => s + v, 0) / dataArray.length / 255;
      setAudioLevel(avg);

      // Build bar heights from frequency bins
      const barCount = 12;
      const binSize = Math.floor(dataArray.length / barCount);
      const bars = [];
      for (let i = 0; i < barCount; i++) {
        let sum = 0;
        for (let j = 0; j < binSize; j++) {
          sum += dataArray[i * binSize + j];
        }
        bars.push(Math.max(5, (sum / binSize / 255) * 60));
      }
      setWaveformBars(bars);
      animFrameRef.current = requestAnimationFrame(loop);
    }
    loop();
  }

  // --- Start recording ---
  async function handleStartRecording() {
    setUploadError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Web Audio API for visualization
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      audioContextRef.current = audioCtx;
      const source = audioCtx.createMediaStreamSource(stream);
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyserRef.current = analyser;

      // MediaRecorder
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const url = URL.createObjectURL(blob);
        setAudioBlob(blob);
        setAudioUrl(url);
        setPhase('preview');
        // Stop stream tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
        }
        if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      };

      recorder.start(250);
      setPhase('recording');
      setElapsed(0);

      // Elapsed timer
      const startTime = Date.now();
      timerRef.current = setInterval(() => {
        const secs = Math.floor((Date.now() - startTime) / 1000);
        setElapsed(secs);
        if (secs >= MAX_DURATION) {
          handleStopRecording();
        }
      }, 250);

      startWaveformLoop();
    } catch (err) {
      console.error('Microphone access error:', err);
      setPhase('permissionError');
    }
  }

  // --- Stop recording ---
  function handleStopRecording() {
    if (timerRef.current) clearInterval(timerRef.current);
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
    }
    if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      audioContextRef.current.close();
    }
  }

  // --- Playback preview ---
  function handlePlayPreview() {
    if (!audioUrl) return;
    if (isPlaying && audioElRef.current) {
      audioElRef.current.pause();
      setIsPlaying(false);
      return;
    }
    const audio = new Audio(audioUrl);
    audioElRef.current = audio;
    audio.onended = () => setIsPlaying(false);
    audio.play();
    setIsPlaying(true);
  }

  // --- Re-record ---
  function handleReRecord() {
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current = null;
    }
    if (audioUrl) URL.revokeObjectURL(audioUrl);
    setAudioBlob(null);
    setAudioUrl(null);
    setIsPlaying(false);
    setElapsed(0);
    setWaveformBars(new Array(12).fill(5));
    setAudioLevel(0);
    setPhase('idle');
  }

  // --- Confirm → go to metadata ---
  function handleConfirm() {
    if (audioElRef.current) {
      audioElRef.current.pause();
      audioElRef.current = null;
    }
    setIsPlaying(false);
    setPhase('metadata');
  }

  // --- Upload ---
  async function handleUpload() {
    if (!audioBlob || !recorderName.trim()) return;
    setUploadError(null);
    setPhase('uploading');

    const metadata = {
      recorderName: recorderName.trim(),
      relationship,
      messageType,
      language,
    };
    if (messageType === 'voice_command') {
      metadata.commandPhrase = commandPhrase.trim();
      metadata.commandAction = commandAction.trim();
    }

    const file = new File([audioBlob], 'recording.webm', { type: 'audio/webm' });
    const result = await uploadRecording(siblingPairId, file, metadata);

    if (result.success) {
      setShowConfetti(true);
      setPhase('success');
      setTimeout(() => setShowConfetti(false), 3000);
    } else {
      setUploadError(result.error || tr('uploadError', 'Upload failed'));
      setPhase('metadata');
    }
  }

  // --- Format MM:SS ---
  function formatTime(secs) {
    const m = String(Math.floor(secs / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    return `${m}:${s}`;
  }

  // --- Relationship / message type display labels ---
  const relationshipLabels = {
    grandparent: tr('relationshipGrandparent', 'Grandparent'),
    parent: tr('relationshipParent', 'Parent'),
    sibling: tr('relationshipSibling', 'Sibling'),
    other: tr('relationshipOther', 'Other'),
  };
  const messageTypeLabels = {
    story_intro: tr('messageTypeStoryIntro', 'Story Intro'),
    encouragement: tr('messageTypeEncouragement', 'Encouragement'),
    sound_effect: tr('messageTypeSoundEffect', 'Sound Effect'),
    voice_command: tr('messageTypeVoiceCommand', 'Voice Command'),
    custom: tr('messageTypeCustom', 'Custom'),
  };

  // ===================== RENDER =====================

  // --- Permission Error ---
  if (phase === 'permissionError') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <AlertTriangle size={48} color="#f59e0b" style={{ marginBottom: 16 }} />
          <h2 style={styles.title}>{tr('micPermissionDenied', 'We need your microphone!')}</h2>
          <p style={styles.subtitle}>{tr('micPermissionHelp', 'Please allow microphone access in your browser settings.')}</p>
          <div style={styles.actions}>
            <ChildFriendlyButton variant="primary" onClick={() => setPhase('idle')}>
              {tr('reRecord', 'Try Again')}
            </ChildFriendlyButton>
            {onClose && (
              <ChildFriendlyButton variant="secondary" onClick={onClose} icon={<X size={20} />}>
                {tr('cancel', 'Cancel')}
              </ChildFriendlyButton>
            )}
          </div>
        </div>
      </div>
    );
  }

  // --- Success with confetti ---
  if (phase === 'success') {
    return (
      <div style={styles.container}>
        {showConfetti && <ConfettiBurst />}
        <div style={styles.card}>
          <div style={{ fontSize: 64, marginBottom: 12 }}>🎉</div>
          <h2 style={styles.title}>{tr('uploadSuccess', 'Recording saved!')}</h2>
          <div style={styles.actions}>
            <ChildFriendlyButton variant="primary" onClick={handleReRecord}>
              {tr('tapToRecord', 'Record Another')}
            </ChildFriendlyButton>
            {onClose && (
              <ChildFriendlyButton variant="secondary" onClick={onClose} icon={<Check size={20} />}>
                {tr('done', 'Done')}
              </ChildFriendlyButton>
            )}
          </div>
        </div>
      </div>
    );
  }

  // --- Metadata form ---
  if (phase === 'metadata' || phase === 'uploading') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>{tr('metadataTitle', 'Tell Us About This Recording')}</h2>

          <div style={styles.formGroup}>
            <label style={styles.label}>{tr('recorderNameLabel', 'Who is recording?')}</label>
            <input
              style={styles.input}
              type="text"
              value={recorderName}
              onChange={(e) => setRecorderName(e.target.value)}
              placeholder={tr('recorderNamePlaceholder', 'e.g. Abuela María')}
              maxLength={50}
            />
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>{tr('relationshipLabel', 'Relationship')}</label>
            <select style={styles.select} value={relationship} onChange={(e) => setRelationship(e.target.value)}>
              {RELATIONSHIPS.map((r) => (
                <option key={r} value={r}>{relationshipLabels[r]}</option>
              ))}
            </select>
          </div>

          <div style={styles.formGroup}>
            <label style={styles.label}>{tr('messageTypeLabel', 'Message Type')}</label>
            <select style={styles.select} value={messageType} onChange={(e) => setMessageType(e.target.value)}>
              {MESSAGE_TYPES.map((mt) => (
                <option key={mt} value={mt}>{messageTypeLabels[mt]}</option>
              ))}
            </select>
          </div>

          {messageType === 'voice_command' && (
            <>
              <div style={styles.formGroup}>
                <label style={styles.label}>{tr('commandPhraseLabel', 'Command Phrase')}</label>
                <input
                  style={styles.input}
                  type="text"
                  value={commandPhrase}
                  onChange={(e) => setCommandPhrase(e.target.value)}
                  placeholder={tr('commandPhrasePlaceholder', 'e.g. ¡Aventura mágica!')}
                  maxLength={100}
                />
              </div>
              <div style={styles.formGroup}>
                <label style={styles.label}>{tr('commandActionLabel', 'Action')}</label>
                <input
                  style={styles.input}
                  type="text"
                  value={commandAction}
                  onChange={(e) => setCommandAction(e.target.value)}
                  placeholder={tr('commandActionPlaceholder', 'e.g. start adventure')}
                  maxLength={100}
                />
              </div>
            </>
          )}

          {uploadError && <p style={styles.errorText}>{uploadError}</p>}

          <div style={styles.actions}>
            <ChildFriendlyButton
              variant="success"
              onClick={handleUpload}
              disabled={phase === 'uploading' || !recorderName.trim()}
              icon={<Check size={24} />}
            >
              {phase === 'uploading' ? tr('uploadingRecording', 'Saving...') : tr('saveRecording', 'Save Recording ✨')}
            </ChildFriendlyButton>
            <ChildFriendlyButton variant="secondary" onClick={() => setPhase('preview')} icon={<RotateCcw size={20} />}>
              {tr('cancel', 'Back')}
            </ChildFriendlyButton>
          </div>
        </div>
      </div>
    );
  }

  // --- Preview phase ---
  if (phase === 'preview') {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>{tr('previewTitle', 'Listen to Your Recording')}</h2>
          <p style={styles.subtitle}>{formatTime(elapsed)}</p>

          <div style={styles.actions}>
            <ChildFriendlyButton
              variant="primary"
              onClick={handlePlayPreview}
              icon={isPlaying ? <Pause size={28} /> : <Play size={28} />}
              style={{ minWidth: 48, minHeight: 48 }}
            >
              {isPlaying ? tr('pausePreview', 'Pause') : tr('playPreview', 'Play')}
            </ChildFriendlyButton>
            <ChildFriendlyButton
              variant="secondary"
              onClick={handleReRecord}
              icon={<RotateCcw size={28} />}
              style={{ minWidth: 48, minHeight: 48 }}
            >
              {tr('reRecord', 'Re-record')}
            </ChildFriendlyButton>
            <ChildFriendlyButton
              variant="success"
              onClick={handleConfirm}
              icon={<Check size={28} />}
              style={{ minWidth: 48, minHeight: 48 }}
            >
              {tr('confirmRecording', 'Sounds Great!')}
            </ChildFriendlyButton>
          </div>
        </div>
      </div>
    );
  }

  // --- Idle / Recording phase ---
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <h2 style={styles.title}>{tr('voiceRecorderTitle', 'Record a Voice Message 🎤')}</h2>

        {/* Animated avatar reacting to audio level */}
        <div style={{
          ...styles.avatar,
          transform: phase === 'recording' ? `scale(${1 + audioLevel * 0.4})` : 'scale(1)',
        }}>
          {phase === 'recording' ? '🗣️' : '😊'}
        </div>

        {/* Waveform visualization */}
        {phase === 'recording' && (
          <div style={styles.waveformContainer}>
            {waveformBars.map((h, i) => (
              <div
                key={i}
                style={{
                  width: 8,
                  height: h,
                  borderRadius: 4,
                  background: `linear-gradient(to top, #ec4899, #8b5cf6)`,
                  transition: 'height 0.1s ease',
                }}
              />
            ))}
          </div>
        )}

        {/* Elapsed time */}
        {phase === 'recording' && (
          <div style={styles.timer}>
            <span>{formatTime(elapsed)}</span>
            <span style={styles.timerMax}> / {formatTime(MAX_DURATION)}</span>
            {elapsed >= MAX_DURATION && (
              <span style={styles.maxReached}>{tr('maxDurationReached', 'Max reached!')}</span>
            )}
          </div>
        )}

        {/* Main action buttons — max 3 visible */}
        <div style={styles.actions}>
          {phase === 'idle' && (
            <ChildFriendlyButton
              variant="success"
              onClick={handleStartRecording}
              icon={<Mic size={32} />}
              style={{ minWidth: 48, minHeight: 48 }}
            >
              {tr('tapToRecord', 'Tap to Record')}
            </ChildFriendlyButton>
          )}
          {phase === 'recording' && (
            <ChildFriendlyButton
              variant="danger"
              onClick={handleStopRecording}
              icon={<Square size={32} />}
              style={{ minWidth: 48, minHeight: 48, animation: 'pulse-voice 1.5s infinite' }}
            >
              {tr('stopRecording', 'Stop')}
            </ChildFriendlyButton>
          )}
          {onClose && phase === 'idle' && (
            <ChildFriendlyButton variant="secondary" onClick={onClose} icon={<X size={20} />}>
              {tr('cancel', 'Cancel')}
            </ChildFriendlyButton>
          )}
        </div>
      </div>

      {/* Pulsing mic + waveform keyframes */}
      <style>{`
        @keyframes pulse-voice {
          0%, 100% { transform: scale(1); }
          50% { transform: scale(1.06); }
        }
        @keyframes bounce-bar {
          0%, 100% { transform: scaleY(0.4); }
          50% { transform: scaleY(1); }
        }
      `}</style>
    </div>
  );
}

// ===================== Confetti Burst (CSS only) =====================
function ConfettiBurst() {
  const pieces = Array.from({ length: 30 }, (_, i) => {
    const colors = ['#ec4899', '#8b5cf6', '#f59e0b', '#10b981', '#3b82f6', '#ef4444'];
    const color = colors[i % colors.length];
    const left = Math.random() * 100;
    const delay = Math.random() * 0.5;
    const duration = 1.5 + Math.random();
    const rotation = Math.random() * 360;
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: `${left}%`,
          top: '-10px',
          width: 8,
          height: 8,
          borderRadius: i % 3 === 0 ? '50%' : '2px',
          background: color,
          animation: `confetti-fall ${duration}s ease-out ${delay}s forwards`,
          transform: `rotate(${rotation}deg)`,
        }}
      />
    );
  });

  return (
    <div style={{ position: 'fixed', inset: 0, pointerEvents: 'none', zIndex: 9999, overflow: 'hidden' }}>
      {pieces}
      <style>{`
        @keyframes confetti-fall {
          0% { opacity: 1; transform: translateY(0) rotate(0deg); }
          100% { opacity: 0; transform: translateY(100vh) rotate(720deg); }
        }
      `}</style>
    </div>
  );
}

// ===================== Inline Styles =====================
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    minHeight: 300,
    position: 'relative',
  },
  card: {
    background: 'rgba(255,255,255,0.08)',
    borderRadius: 24,
    padding: 32,
    maxWidth: 480,
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 16,
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 800,
    textAlign: 'center',
    margin: 0,
    fontFamily: 'var(--font-heading, inherit)',
  },
  subtitle: {
    fontSize: '1.1rem',
    opacity: 0.8,
    textAlign: 'center',
    margin: 0,
  },
  avatar: {
    fontSize: 64,
    transition: 'transform 0.15s ease',
    userSelect: 'none',
  },
  waveformContainer: {
    display: 'flex',
    gap: 4,
    alignItems: 'flex-end',
    justifyContent: 'center',
    height: 64,
  },
  timer: {
    fontSize: '1.8rem',
    fontWeight: 700,
    fontVariantNumeric: 'tabular-nums',
    textAlign: 'center',
  },
  timerMax: {
    fontSize: '1rem',
    opacity: 0.5,
    fontWeight: 400,
  },
  maxReached: {
    display: 'block',
    fontSize: '0.9rem',
    color: '#f59e0b',
    fontWeight: 600,
    marginTop: 4,
  },
  actions: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 8,
  },
  formGroup: {
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
  },
  label: {
    fontSize: '0.95rem',
    fontWeight: 600,
    opacity: 0.9,
  },
  input: {
    padding: '10px 14px',
    borderRadius: 12,
    border: '2px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.06)',
    color: 'inherit',
    fontSize: '1rem',
    outline: 'none',
    minHeight: 48,
  },
  select: {
    padding: '10px 14px',
    borderRadius: 12,
    border: '2px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.06)',
    color: 'inherit',
    fontSize: '1rem',
    outline: 'none',
    minHeight: 48,
  },
  errorText: {
    color: '#ef4444',
    fontSize: '0.9rem',
    fontWeight: 600,
    textAlign: 'center',
    margin: 0,
  },
};
