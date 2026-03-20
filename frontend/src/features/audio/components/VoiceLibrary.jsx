import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Trash2, Play, Pause, Filter, X } from 'lucide-react';
import { ChildFriendlyButton } from '../../../shared/components';
import { useVoiceRecordingStore } from '../../../stores/voiceRecordingStore';

const API_BASE = 'http://localhost:8000';

const MESSAGE_TYPES = ['story_intro', 'encouragement', 'sound_effect', 'voice_command', 'custom'];

const LANGUAGE_BADGES = { en: '🇺🇸', es: '🇪🇸' };

/**
 * VoiceLibrary Component
 * Browse, preview, filter, and manage voice recordings grouped by recorder name.
 * Requires parent PIN for delete actions.
 */
export default function VoiceLibrary({ siblingPairId, language = 'en', onClose, t }) {
  const {
    recordings,
    recordingCount,
    maxRecordings,
    filters,
    loading,
    error,
    fetchRecordings,
    deleteRecording,
    deleteAllRecordings,
    setFilter,
  } = useVoiceRecordingStore();

  const [playingId, setPlayingId] = useState(null);
  const [audioEl, setAudioEl] = useState(null);
  const [showFilters, setShowFilters] = useState(false);

  // Delete single confirmation
  const [deleteTarget, setDeleteTarget] = useState(null);

  // Delete all confirmation
  const [showDeleteAll, setShowDeleteAll] = useState(false);

  // PIN dialog
  const [pinAction, setPinAction] = useState(null); // { type: 'single' | 'all', recordingId? }
  const [pinValue, setPinValue] = useState('');
  const [pinError, setPinError] = useState('');

  // Delete result warning
  const [triggerWarning, setTriggerWarning] = useState(null);

  const tr = useCallback((key, fallback) => (t && t[key]) || fallback || key, [t]);

  // Fetch recordings on mount and when filters change
  useEffect(() => {
    if (siblingPairId) {
      fetchRecordings(siblingPairId);
    }
  }, [siblingPairId, filters.messageType, filters.recorderName, fetchRecordings]);

  // Close on Escape
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (pinAction) { setPinAction(null); setPinValue(''); setPinError(''); }
        else if (deleteTarget) setDeleteTarget(null);
        else if (showDeleteAll) setShowDeleteAll(false);
        else if (triggerWarning) setTriggerWarning(null);
        else if (onClose) onClose();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, pinAction, deleteTarget, showDeleteAll, triggerWarning]);

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (audioEl) { audioEl.pause(); }
    };
  }, [audioEl]);

  // Group recordings by recorder_name
  const grouped = useMemo(() => {
    const groups = {};
    for (const rec of recordings) {
      const name = rec.recorder_name || tr('unknownRecorder', 'Unknown');
      if (!groups[name]) groups[name] = [];
      groups[name].push(rec);
    }
    // Sort each group by created_at
    for (const name of Object.keys(groups)) {
      groups[name].sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    }
    return groups;
  }, [recordings, tr]);

  // Unique recorder names for filter dropdown
  const recorderNames = useMemo(() => {
    const names = new Set(recordings.map((r) => r.recorder_name).filter(Boolean));
    return Array.from(names).sort();
  }, [recordings]);

  // --- Playback ---
  function handlePlay(rec) {
    if (playingId === rec.recording_id) {
      // Toggle pause
      if (audioEl) { audioEl.pause(); }
      setPlayingId(null);
      setAudioEl(null);
      return;
    }
    // Stop any current playback
    if (audioEl) { audioEl.pause(); }

    const mp3Url = rec.mp3_url
      ? (rec.mp3_url.startsWith('http') ? rec.mp3_url : `${API_BASE}${rec.mp3_url}`)
      : `${API_BASE}/voice_recordings/${rec.sibling_pair_id}/${rec.recording_id}.mp3`;

    const audio = new Audio(mp3Url);
    audio.onended = () => { setPlayingId(null); setAudioEl(null); };
    audio.onerror = () => { setPlayingId(null); setAudioEl(null); };
    audio.play().catch(() => { setPlayingId(null); setAudioEl(null); });
    setPlayingId(rec.recording_id);
    setAudioEl(audio);
  }

  // --- Filter handlers ---
  function handleMessageTypeFilter(value) {
    setFilter('messageType', value || null);
  }

  function handleRecorderFilter(value) {
    setFilter('recorderName', value || null);
  }

  // --- Delete single flow ---
  function handleDeleteClick(rec) {
    setDeleteTarget(rec);
  }

  function confirmDeleteSingle() {
    // Move to PIN entry
    setPinAction({ type: 'single', recordingId: deleteTarget.recording_id });
    setDeleteTarget(null);
    setPinValue('');
    setPinError('');
  }

  // --- Delete all flow ---
  function handleDeleteAllClick() {
    setShowDeleteAll(true);
  }

  function confirmDeleteAll() {
    setPinAction({ type: 'all' });
    setShowDeleteAll(false);
    setPinValue('');
    setPinError('');
  }

  // --- PIN submission ---
  async function handlePinSubmit() {
    if (pinValue.length !== 4) {
      setPinError(tr('pinLengthError', 'PIN must be 4 digits'));
      return;
    }

    if (pinAction.type === 'single') {
      const result = await deleteRecording(pinAction.recordingId, pinValue, siblingPairId);
      if (result.success) {
        if (result.data?.had_trigger_assignments) {
          setTriggerWarning(tr('triggerAssignmentWarning', 'This recording had active story trigger assignments that have been removed.'));
        }
        setPinAction(null);
        setPinValue('');
        setPinError('');
      } else {
        setPinError(result.error || tr('deleteFailed', 'Delete failed'));
      }
    } else if (pinAction.type === 'all') {
      const result = await deleteAllRecordings(siblingPairId, pinValue);
      if (result.success) {
        setPinAction(null);
        setPinValue('');
        setPinError('');
      } else {
        setPinError(result.error || tr('deleteFailed', 'Delete failed'));
      }
    }
  }

  // --- Format helpers ---
  function formatDuration(seconds) {
    if (!seconds && seconds !== 0) return '--';
    const m = String(Math.floor(seconds / 60)).padStart(2, '0');
    const s = String(Math.round(seconds) % 60).padStart(2, '0');
    return `${m}:${s}`;
  }

  function formatDate(dateStr) {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString(language === 'es' ? 'es' : 'en', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  }

  function messageTypeLabel(mt) {
    const labels = {
      story_intro: tr('messageTypeStoryIntro', 'Story Intro'),
      encouragement: tr('messageTypeEncouragement', 'Encouragement'),
      sound_effect: tr('messageTypeSoundEffect', 'Sound Effect'),
      voice_command: tr('messageTypeVoiceCommand', 'Voice Command'),
      custom: tr('messageTypeCustom', 'Custom'),
    };
    return labels[mt] || mt;
  }

  // ===================== RENDER =====================

  // --- PIN Dialog ---
  if (pinAction) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>{tr('enterParentPin', 'Enter Parent PIN')}</h2>
          <p style={styles.subtitle}>
            {pinAction.type === 'all'
              ? tr('pinRequiredDeleteAll', 'PIN required to delete all recordings')
              : tr('pinRequiredDelete', 'PIN required to delete this recording')}
          </p>
          <input
            style={{ ...styles.input, textAlign: 'center', letterSpacing: 8, fontSize: '1.5rem', maxWidth: 180 }}
            type="password"
            inputMode="numeric"
            maxLength={4}
            value={pinValue}
            onChange={(e) => { setPinValue(e.target.value.replace(/\D/g, '').slice(0, 4)); setPinError(''); }}
            placeholder="••••"
            autoFocus
          />
          {pinError && <p style={styles.errorText}>{pinError}</p>}
          <div style={styles.actions}>
            <ChildFriendlyButton variant="danger" onClick={handlePinSubmit} disabled={pinValue.length !== 4}>
              {tr('confirmDelete', 'Confirm Delete')}
            </ChildFriendlyButton>
            <ChildFriendlyButton variant="secondary" onClick={() => { setPinAction(null); setPinValue(''); setPinError(''); }} icon={<X size={18} />}>
              {tr('cancel', 'Cancel')}
            </ChildFriendlyButton>
          </div>
        </div>
      </div>
    );
  }

  // --- Delete single confirmation ---
  if (deleteTarget) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>{tr('deleteConfirm', 'Delete Recording?')}</h2>
          <p style={styles.subtitle}>
            {tr('deleteConfirmMessage', 'Are you sure you want to delete this recording by')} <strong>{deleteTarget.recorder_name}</strong>?
          </p>
          <p style={styles.subtitleSmall}>
            {messageTypeLabel(deleteTarget.message_type)} · {formatDuration(deleteTarget.duration_seconds)}
          </p>
          <div style={styles.actions}>
            <ChildFriendlyButton variant="danger" onClick={confirmDeleteSingle} icon={<Trash2 size={18} />}>
              {tr('deleteRecording', 'Delete')}
            </ChildFriendlyButton>
            <ChildFriendlyButton variant="secondary" onClick={() => setDeleteTarget(null)} icon={<X size={18} />}>
              {tr('cancel', 'Cancel')}
            </ChildFriendlyButton>
          </div>
        </div>
      </div>
    );
  }

  // --- Delete all confirmation ---
  if (showDeleteAll) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <h2 style={styles.title}>{tr('deleteAllConfirm', 'Delete All Recordings?')}</h2>
          <p style={styles.subtitle}>
            {tr('deleteAllConfirmMessage', `This will permanently delete all ${recordingCount} recording(s). This cannot be undone.`)}
          </p>
          <div style={styles.actions}>
            <ChildFriendlyButton variant="danger" onClick={confirmDeleteAll} icon={<Trash2 size={18} />}>
              {tr('deleteAll', 'Delete All')}
            </ChildFriendlyButton>
            <ChildFriendlyButton variant="secondary" onClick={() => setShowDeleteAll(false)} icon={<X size={18} />}>
              {tr('cancel', 'Cancel')}
            </ChildFriendlyButton>
          </div>
        </div>
      </div>
    );
  }

  // --- Trigger warning toast ---
  const triggerWarningBanner = triggerWarning ? (
    <div style={styles.warningBanner}>
      <span>{triggerWarning}</span>
      <button style={styles.warningClose} onClick={() => setTriggerWarning(null)} aria-label="Dismiss">
        <X size={16} />
      </button>
    </div>
  ) : null;

  // --- Main library view ---
  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <h2 style={styles.title}>{tr('voiceLibraryTitle', 'Voice Library 🎙️')}</h2>
          {onClose && (
            <button style={styles.closeBtn} onClick={onClose} aria-label={tr('close', 'Close')}>
              <X size={22} />
            </button>
          )}
        </div>

        {/* Count / capacity */}
        <p style={styles.capacityText}>
          {recordingCount} / {maxRecordings} {tr('recordingsLabel', 'recordings')}
        </p>

        {triggerWarningBanner}

        {/* Filter controls */}
        <div style={styles.filterRow}>
          <ChildFriendlyButton
            variant={showFilters ? 'primary' : 'secondary'}
            onClick={() => setShowFilters(!showFilters)}
            icon={<Filter size={18} />}
            style={{ minHeight: 40 }}
          >
            {tr('filters', 'Filters')}
          </ChildFriendlyButton>

          {recordings.length > 0 && (
            <ChildFriendlyButton
              variant="danger"
              onClick={handleDeleteAllClick}
              icon={<Trash2 size={18} />}
              style={{ minHeight: 40 }}
            >
              {tr('deleteAll', 'Delete All')}
            </ChildFriendlyButton>
          )}
        </div>

        {showFilters && (
          <div style={styles.filtersPanel}>
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>{tr('filterMessageType', 'Message Type')}</label>
              <select
                style={styles.select}
                value={filters.messageType || ''}
                onChange={(e) => handleMessageTypeFilter(e.target.value)}
              >
                <option value="">{tr('allTypes', 'All Types')}</option>
                {MESSAGE_TYPES.map((mt) => (
                  <option key={mt} value={mt}>{messageTypeLabel(mt)}</option>
                ))}
              </select>
            </div>
            <div style={styles.filterGroup}>
              <label style={styles.filterLabel}>{tr('filterRecorder', 'Recorder')}</label>
              <select
                style={styles.select}
                value={filters.recorderName || ''}
                onChange={(e) => handleRecorderFilter(e.target.value)}
              >
                <option value="">{tr('allRecorders', 'All Recorders')}</option>
                {recorderNames.map((name) => (
                  <option key={name} value={name}>{name}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Error */}
        {error && <p style={styles.errorText}>{error}</p>}

        {/* Loading */}
        {loading && <p style={styles.subtitle}>{tr('loadingRecordings', 'Loading recordings...')}</p>}

        {/* Empty state */}
        {!loading && recordings.length === 0 && (
          <div style={styles.emptyState}>
            <span style={{ fontSize: 48 }}>🎤</span>
            <p style={styles.subtitle}>{tr('noRecordings', 'No recordings yet. Record your first voice message!')}</p>
          </div>
        )}

        {/* Grouped recordings */}
        {!loading && Object.keys(grouped).length > 0 && (
          <div style={styles.recordingsList}>
            {Object.entries(grouped).map(([recorderName, recs]) => (
              <div key={recorderName} style={styles.recorderGroup}>
                <h3 style={styles.recorderHeader}>{recorderName}</h3>
                {recs.map((rec) => (
                  <div key={rec.recording_id} style={styles.recordingRow}>
                    {/* Play/Pause */}
                    <button
                      style={styles.playBtn}
                      onClick={() => handlePlay(rec)}
                      aria-label={playingId === rec.recording_id ? tr('pausePreview', 'Pause') : tr('playPreview', 'Play')}
                    >
                      {playingId === rec.recording_id ? <Pause size={20} /> : <Play size={20} />}
                    </button>

                    {/* Info */}
                    <div style={styles.recordingInfo}>
                      <div style={styles.recordingMeta}>
                        <span style={styles.messageTypeBadge}>{messageTypeLabel(rec.message_type)}</span>
                        <span style={styles.langBadge}>{LANGUAGE_BADGES[rec.language] || rec.language}</span>
                        <span style={styles.durationText}>{formatDuration(rec.duration_seconds)}</span>
                      </div>
                      <span style={styles.dateText}>{formatDate(rec.created_at)}</span>
                    </div>

                    {/* Delete */}
                    <button
                      style={styles.deleteBtn}
                      onClick={() => handleDeleteClick(rec)}
                      aria-label={tr('deleteRecording', 'Delete recording')}
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ===================== Inline Styles =====================
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'flex-start',
    padding: 24,
    minHeight: 300,
    position: 'relative',
  },
  card: {
    background: 'rgba(255,255,255,0.08)',
    borderRadius: 24,
    padding: 28,
    maxWidth: 560,
    width: '100%',
    display: 'flex',
    flexDirection: 'column',
    gap: 12,
    boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 800,
    margin: 0,
    fontFamily: 'var(--font-heading, inherit)',
  },
  subtitle: {
    fontSize: '1rem',
    opacity: 0.8,
    textAlign: 'center',
    margin: 0,
  },
  subtitleSmall: {
    fontSize: '0.9rem',
    opacity: 0.7,
    textAlign: 'center',
    margin: 0,
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    color: 'inherit',
    cursor: 'pointer',
    padding: 6,
    borderRadius: 8,
    display: 'flex',
    alignItems: 'center',
    opacity: 0.7,
  },
  capacityText: {
    fontSize: '0.95rem',
    fontWeight: 600,
    opacity: 0.7,
    margin: 0,
  },
  filterRow: {
    display: 'flex',
    gap: 8,
    flexWrap: 'wrap',
    alignItems: 'center',
  },
  filtersPanel: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
    padding: '12px 0',
  },
  filterGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 4,
    flex: '1 1 180px',
  },
  filterLabel: {
    fontSize: '0.85rem',
    fontWeight: 600,
    opacity: 0.8,
  },
  select: {
    padding: '8px 12px',
    borderRadius: 12,
    border: '2px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.06)',
    color: 'inherit',
    fontSize: '0.95rem',
    outline: 'none',
    minHeight: 40,
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
  actions: {
    display: 'flex',
    gap: 12,
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 8,
  },
  errorText: {
    color: '#ef4444',
    fontSize: '0.9rem',
    fontWeight: 600,
    textAlign: 'center',
    margin: 0,
  },
  emptyState: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: 12,
    padding: '24px 0',
  },
  recordingsList: {
    display: 'flex',
    flexDirection: 'column',
    gap: 16,
    maxHeight: 420,
    overflowY: 'auto',
    paddingRight: 4,
  },
  recorderGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
  },
  recorderHeader: {
    fontSize: '1.1rem',
    fontWeight: 700,
    margin: 0,
    paddingBottom: 4,
    borderBottom: '1px solid rgba(255,255,255,0.1)',
  },
  recordingRow: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '8px 4px',
    borderRadius: 12,
    transition: 'background 0.15s',
  },
  playBtn: {
    background: 'rgba(139,92,246,0.2)',
    border: 'none',
    color: '#a78bfa',
    cursor: 'pointer',
    borderRadius: '50%',
    width: 40,
    height: 40,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  recordingInfo: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
    gap: 2,
    minWidth: 0,
  },
  recordingMeta: {
    display: 'flex',
    gap: 6,
    alignItems: 'center',
    flexWrap: 'wrap',
  },
  messageTypeBadge: {
    fontSize: '0.8rem',
    fontWeight: 600,
    background: 'rgba(139,92,246,0.15)',
    padding: '2px 8px',
    borderRadius: 8,
    whiteSpace: 'nowrap',
  },
  langBadge: {
    fontSize: '1rem',
  },
  durationText: {
    fontSize: '0.85rem',
    opacity: 0.7,
    fontVariantNumeric: 'tabular-nums',
  },
  dateText: {
    fontSize: '0.78rem',
    opacity: 0.5,
  },
  deleteBtn: {
    background: 'rgba(239,68,68,0.15)',
    border: 'none',
    color: '#f87171',
    cursor: 'pointer',
    borderRadius: '50%',
    width: 36,
    height: 36,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexShrink: 0,
  },
  warningBanner: {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
    background: 'rgba(245,158,11,0.15)',
    color: '#f59e0b',
    padding: '8px 12px',
    borderRadius: 12,
    fontSize: '0.85rem',
    fontWeight: 600,
  },
  warningClose: {
    background: 'none',
    border: 'none',
    color: 'inherit',
    cursor: 'pointer',
    padding: 2,
    display: 'flex',
  },
};
