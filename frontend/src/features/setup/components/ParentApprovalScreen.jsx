import { useState, useRef, useCallback, useEffect } from 'react';
import { usePhotoStore } from '../../../stores/photoStore';
import { useAnnounce } from '../../../shared/hooks';
import { useFocusTrap } from '../../../shared/hooks/useFocusTrap';

const API_BASE = 'http://localhost:8000';
const GATE_HOLD_MS = 3000;

/**
 * Format an ISO date string to a human-readable date.
 */
function formatDate(isoString) {
  if (!isoString) return '';
  try {
    return new Date(isoString).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return '';
  }
}

/**
 * ParentApprovalScreen — parent gate + review/approve/reject flow for photos
 * with status === 'review'. Requires a 3-second long-press to enter.
 *
 * Props:
 *   siblingPairId: string
 *   onComplete: () => void
 */
export default function ParentApprovalScreen({ siblingPairId, onComplete }) {
  const [gateUnlocked, setGateUnlocked] = useState(false);
  const [holding, setHolding] = useState(false);
  const timerRef = useRef(null);
  const progressRef = useRef(null);
  const progressCountRef = useRef(0);
  const reviewAreaRef = useRef(null);
  const headingRef = useRef(null);
  const { announce } = useAnnounce();

  const photos = usePhotoStore((s) => s.photos);
  const loadPhotos = usePhotoStore((s) => s.loadPhotos);
  const approvePhoto = usePhotoStore((s) => s.approvePhoto);
  const deletePhoto = usePhotoStore((s) => s.deletePhoto);
  const storeError = usePhotoStore((s) => s.error);

  // ── Task 2.2: Image load error tracking ────────────
  const [imageLoadErrors, setImageLoadErrors] = useState(new Set());

  // ── Task 2.3: Per-photo loading states ─────────────
  const [actionInProgress, setActionInProgress] = useState({});

  // ── Task 2.4: Per-photo error messages ─────────────
  const [photoErrors, setPhotoErrors] = useState({});

  // ── Task 2.5: Rejection confirmation ───────────────
  const [rejectConfirmId, setRejectConfirmId] = useState(null);

  // ── Task 2.6: Load error state ─────────────────────
  const [loadError, setLoadError] = useState(false);

  // ── Task 4.1: Focus trap on review area ────────────
  useFocusTrap(reviewAreaRef, gateUnlocked, onComplete);

  // ── Task 2.1: Sort pending photos by upload date ascending ──
  const pendingPhotos = photos
    .filter((p) => p.status === 'review')
    .sort((a, b) => new Date(a.uploaded_at) - new Date(b.uploaded_at));

  // ── Focus management after gate unlock ─────────────
  useEffect(() => {
    if (gateUnlocked) {
      announce('Parent review unlocked', 'assertive');
      const focusTimer = setTimeout(() => {
        if (headingRef.current) {
          headingRef.current.focus();
        } else if (reviewAreaRef.current) {
          reviewAreaRef.current.focus();
        }
      }, 100);
      return () => clearTimeout(focusTimer);
    }
  }, [gateUnlocked, announce]);

  // ── Task 2.6: Track store error for load failures ──
  useEffect(() => {
    if (storeError) {
      setLoadError(true);
    }
  }, [storeError]);

  // ── Task 4.2: Announce when all photos reviewed ───
  const prevPendingCountRef = useRef(pendingPhotos.length);
  useEffect(() => {
    if (gateUnlocked && prevPendingCountRef.current > 0 && pendingPhotos.length === 0) {
      announce('All photos reviewed', 'assertive');
    }
    prevPendingCountRef.current = pendingPhotos.length;
  }, [pendingPhotos.length, gateUnlocked, announce]);

  // ── Shared unlock logic ────────────────────────────
  const startHold = useCallback(() => {
    setHolding(true);
    progressCountRef.current = 0;

    progressRef.current = setInterval(() => {
      progressCountRef.current += 1;
      const count = progressCountRef.current;
      if (count < 3) {
        announce(`${count} of 3 seconds`, 'assertive');
      }
    }, 1000);

    timerRef.current = setTimeout(() => {
      clearInterval(progressRef.current);
      progressRef.current = null;
      setGateUnlocked(true);
      setHolding(false);
    }, GATE_HOLD_MS);
  }, [announce]);

  const cancelHold = useCallback(() => {
    setHolding(false);
    progressCountRef.current = 0;
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    if (progressRef.current) {
      clearInterval(progressRef.current);
      progressRef.current = null;
    }
  }, []);

  // ── Parent gate handlers ───────────────────────────
  const handlePointerDown = useCallback(() => {
    startHold();
  }, [startHold]);

  const handlePointerUp = useCallback(() => {
    cancelHold();
  }, [cancelHold]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      if (e.repeat) return;
      startHold();
    }
  }, [startHold]);

  const handleKeyUp = useCallback((e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      cancelHold();
    }
  }, [cancelHold]);

  // ── Task 2.3 + 2.4: Approve handler with loading & error ──
  const handleApprove = useCallback(async (photoId) => {
    // Task 2.4: Clear error on retry
    setPhotoErrors((prev) => {
      const next = { ...prev };
      delete next[photoId];
      return next;
    });
    // Task 2.3: Set loading state
    setActionInProgress((prev) => ({ ...prev, [photoId]: 'approving' }));
    try {
      const result = await approvePhoto(photoId);
      if (result.success) {
        announce('Photo approved', 'assertive');
      } else {
        // Task 2.4: Set error message
        const msg = result.error === 'network' ? 'Connection issue' : 'Something went wrong';
        setPhotoErrors((prev) => ({ ...prev, [photoId]: msg }));
        announce('Failed to approve photo', 'assertive');
      }
    } finally {
      setActionInProgress((prev) => {
        const next = { ...prev };
        delete next[photoId];
        return next;
      });
    }
  }, [approvePhoto, announce]);

  // ── Task 2.5: Reject button opens confirmation ────
  const handleRejectTap = useCallback((photoId) => {
    setRejectConfirmId(photoId);
  }, []);

  // ── Task 2.5 + 2.3 + 2.4: Confirm rejection handler ──
  const handleConfirmReject = useCallback(async (photoId) => {
    setRejectConfirmId(null);
    // Task 2.4: Clear error on retry
    setPhotoErrors((prev) => {
      const next = { ...prev };
      delete next[photoId];
      return next;
    });
    // Task 2.3: Set loading state
    setActionInProgress((prev) => ({ ...prev, [photoId]: 'rejecting' }));
    try {
      const result = await deletePhoto(photoId);
      if (result.success) {
        announce('Photo removed', 'assertive');
      } else {
        const msg = result.error === 'network' ? 'Connection issue' : 'Something went wrong';
        setPhotoErrors((prev) => ({ ...prev, [photoId]: msg }));
        announce('Failed to remove photo', 'assertive');
      }
    } finally {
      setActionInProgress((prev) => {
        const next = { ...prev };
        delete next[photoId];
        return next;
      });
    }
  }, [deletePhoto, announce]);

  // ── Task 2.5: Cancel rejection ─────────────────────
  const handleCancelReject = useCallback(() => {
    setRejectConfirmId(null);
  }, []);

  // ── Task 2.2: Image error handler ──────────────────
  const handleImageError = useCallback((photoId) => {
    setImageLoadErrors((prev) => new Set(prev).add(photoId));
  }, []);

  // ── Task 2.6: Retry loading photos ─────────────────
  const handleRetryLoad = useCallback(async () => {
    setLoadError(false);
    await loadPhotos(siblingPairId);
  }, [loadPhotos, siblingPairId]);

  // ── Styles ─────────────────────────────────────────
  const styles = {
    container: {
      padding: '16px',
      maxWidth: '480px',
      margin: '0 auto',
    },
    gateWrapper: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      textAlign: 'center',
    },
    gateTitle: {
      fontSize: '18px',
      fontWeight: 600,
      marginBottom: '8px',
      color: '#1e293b',
    },
    gateHint: {
      fontSize: '14px',
      color: '#64748b',
      marginBottom: '32px',
    },
    ringContainer: {
      position: 'relative',
      width: '96px',
      height: '96px',
      cursor: 'pointer',
      userSelect: 'none',
      touchAction: 'none',
    },
    ringSvg: {
      width: '96px',
      height: '96px',
      transform: 'rotate(-90deg)',
    },
    ringBg: {
      fill: 'none',
      stroke: '#e2e8f0',
      strokeWidth: 6,
    },
    ringProgress: {
      fill: 'none',
      stroke: '#6366f1',
      strokeWidth: 6,
      strokeLinecap: 'round',
      strokeDasharray: '251.2',
      strokeDashoffset: '251.2',
    },
    ringProgressActive: {
      fill: 'none',
      stroke: '#6366f1',
      strokeWidth: 6,
      strokeLinecap: 'round',
      strokeDasharray: '251.2',
      strokeDashoffset: '251.2',
      animation: `parentGateFill ${GATE_HOLD_MS}ms linear forwards`,
    },
    ringIcon: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
      fontSize: '32px',
      pointerEvents: 'none',
    },
    heading: {
      fontSize: '20px',
      fontWeight: 700,
      textAlign: 'center',
      marginBottom: '16px',
      color: '#1e293b',
    },
    photoCard: {
      marginBottom: '20px',
      borderRadius: '16px',
      overflow: 'hidden',
      background: '#fff',
      boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
    },
    photoImg: {
      width: '100%',
      display: 'block',
      objectFit: 'cover',
      maxHeight: '320px',
    },
    photoMeta: {
      padding: '8px 12px 4px',
      fontSize: '13px',
      color: '#64748b',
    },
    photoFilename: {
      fontWeight: 600,
      color: '#334155',
    },
    photoDate: {
      marginLeft: '8px',
    },
    imagePlaceholder: {
      width: '100%',
      height: '200px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: '#f1f5f9',
      color: '#94a3b8',
      fontSize: '48px',
    },
    actions: {
      display: 'flex',
      justifyContent: 'center',
      gap: '16px',
      padding: '12px',
    },
    approveBtn: {
      minWidth: '48px',
      minHeight: '48px',
      fontSize: '24px',
      border: '2px solid #22c55e',
      borderRadius: '12px',
      background: '#f0fdf4',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '8px 20px',
      transition: 'background 150ms',
    },
    rejectBtn: {
      minWidth: '48px',
      minHeight: '48px',
      fontSize: '24px',
      border: '2px solid #ef4444',
      borderRadius: '12px',
      background: '#fef2f2',
      cursor: 'pointer',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '8px 20px',
      transition: 'background 150ms',
    },
    disabledBtn: {
      opacity: 0.5,
      cursor: 'not-allowed',
    },
    errorMsg: {
      padding: '4px 12px 8px',
      fontSize: '13px',
      color: '#dc2626',
    },
    confirmDialog: {
      padding: '12px',
      background: '#fef2f2',
      borderTop: '1px solid #fecaca',
    },
    confirmText: {
      fontSize: '14px',
      fontWeight: 500,
      color: '#991b1b',
      marginBottom: '8px',
    },
    confirmActions: {
      display: 'flex',
      gap: '12px',
    },
    confirmRemoveBtn: {
      minWidth: '48px',
      minHeight: '48px',
      padding: '8px 16px',
      fontSize: '14px',
      fontWeight: 600,
      border: 'none',
      borderRadius: '8px',
      background: '#ef4444',
      color: '#fff',
      cursor: 'pointer',
    },
    confirmCancelBtn: {
      minWidth: '48px',
      minHeight: '48px',
      padding: '8px 16px',
      fontSize: '14px',
      fontWeight: 600,
      border: '1px solid #d1d5db',
      borderRadius: '8px',
      background: '#fff',
      color: '#374151',
      cursor: 'pointer',
    },
    completionWrapper: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      textAlign: 'center',
    },
    completionEmoji: {
      fontSize: '56px',
      marginBottom: '16px',
    },
    completionText: {
      fontSize: '18px',
      fontWeight: 600,
      color: '#1e293b',
      marginBottom: '24px',
    },
    doneBtn: {
      padding: '12px 32px',
      fontSize: '16px',
      fontWeight: 600,
      border: 'none',
      borderRadius: '12px',
      background: '#6366f1',
      color: '#fff',
      cursor: 'pointer',
      minWidth: '48px',
      minHeight: '48px',
    },
    loadErrorWrapper: {
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '48px 24px',
      textAlign: 'center',
    },
    loadErrorText: {
      fontSize: '16px',
      color: '#dc2626',
      marginBottom: '16px',
    },
    retryBtn: {
      padding: '10px 24px',
      fontSize: '15px',
      fontWeight: 600,
      border: '2px solid #6366f1',
      borderRadius: '10px',
      background: '#eef2ff',
      color: '#4338ca',
      cursor: 'pointer',
      minWidth: '48px',
      minHeight: '48px',
    },
  };

  // ── CSS keyframe injection (once) ──────────────────
  const styleTagId = 'parent-gate-keyframes';
  if (typeof document !== 'undefined' && !document.getElementById(styleTagId)) {
    const styleEl = document.createElement('style');
    styleEl.id = styleTagId;
    styleEl.textContent = `
      @keyframes parentGateFill {
        from { stroke-dashoffset: 251.2; }
        to   { stroke-dashoffset: 0; }
      }
    `;
    document.head.appendChild(styleEl);
  }

  // ── GATE VIEW ──────────────────────────────────────
  if (!gateUnlocked) {
    return (
      <div style={styles.container}>
        <div style={styles.gateWrapper}>
          <div style={styles.gateTitle}>Parent Review</div>
          <div style={styles.gateHint}>Hold the button for 3 seconds to unlock</div>

          <div
            style={styles.ringContainer}
            onPointerDown={handlePointerDown}
            onPointerUp={handlePointerUp}
            onPointerLeave={handlePointerUp}
            onPointerCancel={handlePointerUp}
            onKeyDown={handleKeyDown}
            onKeyUp={handleKeyUp}
            onFocus={() => announce('Hold for 3 seconds to unlock parent review', 'polite')}
            role="button"
            aria-label="Hold for 3 seconds to unlock parent review"
            tabIndex={0}
          >
            <svg style={styles.ringSvg} viewBox="0 0 96 96">
              <circle cx="48" cy="48" r="40" style={styles.ringBg} />
              <circle
                cx="48"
                cy="48"
                r="40"
                style={holding ? styles.ringProgressActive : styles.ringProgress}
              />
            </svg>
            <span style={styles.ringIcon}>🔒</span>
          </div>
        </div>
      </div>
    );
  }

  // ── Task 2.6: LOAD ERROR VIEW ─────────────────────
  if (loadError) {
    return (
      <div style={styles.container} ref={reviewAreaRef}>
        <div style={styles.loadErrorWrapper} tabIndex={-1} ref={headingRef}>
          <div style={styles.loadErrorText}>Failed to load photos. Please try again.</div>
          <button style={styles.retryBtn} onClick={handleRetryLoad}>
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ── COMPLETION VIEW ────────────────────────────────
  if (pendingPhotos.length === 0) {
    return (
      <div style={styles.container} ref={reviewAreaRef}>
        <div style={styles.completionWrapper} tabIndex={-1} ref={headingRef}>
          <div style={styles.completionEmoji} aria-hidden="true">🎉</div>
          <div style={styles.completionText}>All photos reviewed!</div>
          <button style={styles.doneBtn} onClick={onComplete} aria-label="Done reviewing photos">
            Done
          </button>
        </div>
      </div>
    );
  }

  // ── REVIEW LIST VIEW ───────────────────────────────
  return (
    <div style={styles.container} ref={reviewAreaRef}>
      <div style={styles.heading} ref={headingRef} tabIndex={-1}>
        Review Photos ({pendingPhotos.length})
      </div>

      {pendingPhotos.map((photo) => {
        const inProgress = actionInProgress[photo.photo_id];
        const error = photoErrors[photo.photo_id];
        const hasImageError = imageLoadErrors.has(photo.photo_id);
        const isConfirming = rejectConfirmId === photo.photo_id;

        return (
          <div
            key={photo.photo_id}
            style={styles.photoCard}
            aria-busy={inProgress ? 'true' : undefined}
          >
            {/* Task 2.2: Image or placeholder */}
            {hasImageError ? (
              <div style={styles.imagePlaceholder} aria-label="Image unavailable">
                🖼️
              </div>
            ) : (
              <img
                src={`${API_BASE}/photo_storage/${photo.file_path}`}
                alt={`Photo pending review: ${photo.filename || ''}`}
                style={styles.photoImg}
                onError={() => handleImageError(photo.photo_id)}
              />
            )}

            {/* Task 2.1: Metadata display */}
            <div style={styles.photoMeta}>
              <span style={styles.photoFilename}>{photo.filename}</span>
              <span style={styles.photoDate}>{formatDate(photo.uploaded_at)}</span>
            </div>

            {/* Task 2.5: Rejection confirmation dialog */}
            {isConfirming ? (
              <div
                style={styles.confirmDialog}
                role="alertdialog"
                aria-label="Confirm photo rejection"
              >
                <div style={styles.confirmText}>Remove this photo permanently?</div>
                <div style={styles.confirmActions}>
                  <button
                    style={styles.confirmRemoveBtn}
                    onClick={() => handleConfirmReject(photo.photo_id)}
                    aria-label="Confirm removal"
                  >
                    Remove
                  </button>
                  <button
                    style={styles.confirmCancelBtn}
                    onClick={handleCancelReject}
                    aria-label="Cancel removal"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              /* Actions row */
              <div style={styles.actions}>
                <button
                  style={{
                    ...styles.approveBtn,
                    ...(inProgress ? styles.disabledBtn : {}),
                  }}
                  onClick={() => handleApprove(photo.photo_id)}
                  disabled={!!inProgress}
                  aria-label={`Approve photo ${photo.filename || ''}`}
                >
                  ✅
                </button>
                <button
                  style={{
                    ...styles.rejectBtn,
                    ...(inProgress ? styles.disabledBtn : {}),
                  }}
                  onClick={() => handleRejectTap(photo.photo_id)}
                  disabled={!!inProgress}
                  aria-label={`Reject photo ${photo.filename || ''}`}
                >
                  🗑️
                </button>
              </div>
            )}

            {/* Task 2.4: Inline error message */}
            {error && (
              <div style={styles.errorMsg} role="alert">
                {error}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
