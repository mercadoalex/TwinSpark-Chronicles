import React, { useState, useRef, useCallback, useEffect } from 'react';
import { usePhotoUxEffects, useAnnounce } from '../../../shared/hooks';

const API_BASE = 'http://localhost:8000';

/* ── CSS keyframe animations (injected once) ── */
const STYLE_ID = 'photo-uploader-keyframes';
function injectKeyframes() {
  if (document.getElementById(STYLE_ID)) return;
  const sheet = document.createElement('style');
  sheet.id = STYLE_ID;
  sheet.textContent = `
    @keyframes pu-spin {
      0%   { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes pu-check-pop {
      0%   { transform: scale(0); opacity: 0; }
      60%  { transform: scale(1.2); opacity: 1; }
      100% { transform: scale(1); opacity: 1; }
    }
    @keyframes pu-error-shake {
      0%, 100% { transform: translateX(0); }
      20%      { transform: translateX(-4px); }
      40%      { transform: translateX(4px); }
      60%      { transform: translateX(-4px); }
      80%      { transform: translateX(4px); }
    }
    @keyframes pu-confetti-fall {
      0%   { transform: translateY(-20px) rotate(0deg); opacity: 1; }
      100% { transform: translateY(120px) rotate(360deg); opacity: 0; }
    }
    @keyframes pu-celebration-fade {
      0%   { opacity: 1; }
      80%  { opacity: 1; }
      100% { opacity: 0; }
    }
    @keyframes pu-face-pop {
      0%   { transform: scale(0); opacity: 0; }
      60%  { transform: scale(1.15); opacity: 1; }
      100% { transform: scale(1); opacity: 1; }
    }
  `;
  document.head.appendChild(sheet);
}

/**
 * PhotoUploader — camera capture, gallery pick, drag-and-drop for family photos.
 * Designed for 6yo: big colorful icons, no text labels, max 3 actions visible,
 * celebratory animation on face detection.
 */
export default function PhotoUploader({ siblingPairId, onUploadComplete, onVoicePrompt }) {
  const [dragOver, setDragOver] = useState(false);
  const [preview, setPreview] = useState(null); // { file, url }
  const [uploading, setUploading] = useState(false);
  const [uploadDone, setUploadDone] = useState(null); // 'success' | 'error'
  const [celebration, setCelebration] = useState(false);
  const [celebrationFaces, setCelebrationFaces] = useState([]);
  const [error, setError] = useState(null);

  const cameraRef = useRef(null);
  const galleryRef = useRef(null);

  const { haptic, hapticPattern, playShutter, playChime } = usePhotoUxEffects();
  const { announce } = useAnnounce();

  // Inject CSS keyframes on mount
  useEffect(() => { injectKeyframes(); }, []);

  // Voice prompt helper
  const speak = useCallback((msg) => {
    if (onVoicePrompt) onVoicePrompt(msg);
  }, [onVoicePrompt]);

  // ── File selection handlers ──
  const handleFileSelected = (file) => {
    if (!file) return;
    const validTypes = ['image/jpeg', 'image/png'];
    if (!validTypes.includes(file.type)) {
      setError('photo');
      announce('Error: Please use a JPEG or PNG photo', 'polite');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('size');
      announce('Error: Photo is too large', 'polite');
      return;
    }
    setError(null);
    setPreview({ file, url: URL.createObjectURL(file) });
    speak('Great photo! Tap the green button to use it.');
  };

  const handleCameraCapture = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelected(file);
  };

  const handleGalleryPick = (e) => {
    const file = e.target.files?.[0];
    if (file) handleFileSelected(file);
  };

  // ── Drag and drop ──
  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);
  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileSelected(file);
  };

  // ── Upload ──
  const handleConfirm = async () => {
    if (!preview?.file || !siblingPairId) return;
    setUploading(true);
    setUploadDone(null);
    setError(null);
    speak('Uploading your photo...');

    try {
      const formData = new FormData();
      formData.append('file', preview.file);
      formData.append('sibling_pair_id', siblingPairId);

      const resp = await fetch(`${API_BASE}/api/photos/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!resp.ok) {
        const detail = await resp.json().catch(() => ({}));
        throw new Error(detail.detail || 'Upload failed');
      }

      const result = await resp.json();

      // Show success checkmark briefly
      setUploadDone('success');
      announce('Photo uploaded successfully', 'polite');

      // Celebrate if faces found
      if (result.faces?.length > 0) {
        setCelebrationFaces(result.faces);
        setTimeout(() => {
          setCelebration(true);
          hapticPattern([100, 50, 100]);
          playChime();
          speak('We found faces! Amazing!');
        }, 600); // let checkmark show first
        setTimeout(() => {
          setCelebration(false);
          setCelebrationFaces([]);
          setPreview(null);
          setUploadDone(null);
        }, 2600); // 600ms checkmark + 2000ms celebration
      } else {
        speak('Photo saved! Try a clearer one to find faces.');
        setTimeout(() => {
          setPreview(null);
          setUploadDone(null);
        }, 600);
      }

      if (onUploadComplete) onUploadComplete(result);
    } catch (err) {
      setUploadDone('error');
      announce('Upload failed, please try again', 'polite');
      setTimeout(() => {
        setError('upload');
        setUploadDone(null);
      }, 800);
      speak('Oops, try again!');
    } finally {
      setUploading(false);
    }
  };

  const handleRetake = () => {
    if (preview?.url) URL.revokeObjectURL(preview.url);
    setPreview(null);
    setError(null);
    setUploadDone(null);
  };

  // ── Camera capture with haptic + shutter sound ──
  const handleCameraTap = () => {
    haptic(50);
    playShutter();
    speak('Take a photo!');
    cameraRef.current?.click();
  };

  // ── Celebration overlay with confetti + face crops ──
  if (celebration) {
    return (
      <div style={celebrationStyles.overlay}>
        {/* Confetti particles */}
        {CONFETTI_COLORS.map((color, i) => (
          <div
            key={i}
            style={{
              ...celebrationStyles.confettiPiece,
              background: color,
              left: `${10 + (i * 17) % 80}%`,
              animationDelay: `${(i * 0.15) % 0.6}s`,
              width: `${8 + (i % 3) * 4}px`,
              height: `${8 + (i % 3) * 4}px`,
              borderRadius: i % 2 === 0 ? '50%' : '2px',
            }}
          />
        ))}
        {/* Face crop thumbnails */}
        <div style={celebrationStyles.facesRow}>
          {celebrationFaces.map((face, i) => (
            <img
              key={face.face_id || i}
              src={`${API_BASE}/photo_storage/${face.crop_path}`}
              alt="Detected face"
              style={{
                ...celebrationStyles.faceCrop,
                animationDelay: `${0.2 + i * 0.15}s`,
              }}
              onError={(e) => { e.target.style.display = 'none'; }}
            />
          ))}
        </div>
        <span style={celebrationStyles.text}>🎉 Faces found!</span>
      </div>
    );
  }

  // ── Preview + confirm/retake ──
  if (preview) {
    return (
      <div style={styles.container}>
        <img src={preview.url} alt="Preview" style={styles.previewImage} />
        <div style={styles.actionRow}>
          <button
            onClick={handleRetake}
            style={{ ...styles.actionBtn, ...styles.retakeBtn }}
            disabled={uploading}
            aria-label="Retake photo"
          >
            <span style={styles.btnEmoji}>🔄</span>
          </button>
          <button
            onClick={handleConfirm}
            style={{ ...styles.actionBtn, ...styles.confirmBtn }}
            disabled={uploading}
            aria-label="Use this photo"
            aria-describedby={error === 'upload' ? 'photo-upload-error' : undefined}
          >
            {uploading ? (
              <div style={spinnerStyles.ring} />
            ) : uploadDone === 'success' ? (
              <span style={spinnerStyles.checkmark}>✓</span>
            ) : uploadDone === 'error' ? (
              <span style={spinnerStyles.errorMark}>✕</span>
            ) : (
              <span style={styles.btnEmoji}>✅</span>
            )}
          </button>
        </div>
        {error && (
          <div id="photo-upload-error" style={styles.errorBubble} role="alert">
            {error === 'upload' && '😅 Upload failed, try again!'}
          </div>
        )}
      </div>
    );
  }

  // ── Main capture UI (max 3 actions) ──
  return (
    <div
      style={{ ...styles.container, ...(dragOver ? styles.dragOverBorder : {}) }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      {error && (
        <div id="photo-upload-error" style={styles.errorBubble} role="alert">
          {error === 'photo' && '📷 Use a JPEG or PNG photo'}
          {error === 'size' && '📏 Photo is too big!'}
          {error === 'upload' && '😅 Upload failed, try again!'}
        </div>
      )}

      <div style={styles.actionRow}>
        {/* Camera capture */}
        <button
          onClick={handleCameraTap}
          style={{ ...styles.actionBtn, ...styles.cameraBtn }}
          aria-label="Take a photo"
          aria-describedby={error ? 'photo-upload-error' : undefined}
        >
          <span style={styles.btnEmoji}>📸</span>
        </button>

        {/* Gallery pick */}
        <button
          onClick={() => { speak('Pick a photo!'); galleryRef.current?.click(); }}
          style={{ ...styles.actionBtn, ...styles.galleryBtn }}
          aria-label="Choose from gallery"
          aria-describedby={error ? 'photo-upload-error' : undefined}
        >
          <span style={styles.btnEmoji}>🖼️</span>
        </button>

        {/* Drag-drop hint (desktop) */}
        <div style={styles.dropHint}>
          <span style={styles.btnEmoji}>👆</span>
        </div>
      </div>

      {/* Hidden file inputs */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={handleCameraCapture}
        style={{ display: 'none' }}
      />
      <input
        ref={galleryRef}
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleGalleryPick}
        style={{ display: 'none' }}
      />
    </div>
  );
}

/* ── Confetti colors ── */
const CONFETTI_COLORS = [
  '#f472b6', '#fb923c', '#facc15', '#4ade80',
  '#38bdf8', '#818cf8', '#f472b6', '#22d3ee',
  '#a78bfa', '#fb7185', '#34d399', '#fbbf24',
];


/* ── Spinner / progress indicator styles ── */
const spinnerStyles = {
  ring: {
    width: '36px',
    height: '36px',
    border: '4px solid rgba(255,255,255,0.3)',
    borderTopColor: '#fff',
    borderRadius: '50%',
    animation: 'pu-spin 0.8s linear infinite',
  },
  checkmark: {
    fontSize: '32px',
    color: '#fff',
    fontWeight: 'bold',
    animation: 'pu-check-pop 0.4s ease-out forwards',
  },
  errorMark: {
    fontSize: '32px',
    color: '#fff',
    fontWeight: 'bold',
    animation: 'pu-error-shake 0.5s ease-out',
  },
};

/* ── Celebration overlay styles ── */
const celebrationStyles = {
  overlay: {
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '16px',
    padding: '48px 24px',
    overflow: 'hidden',
    animation: 'pu-celebration-fade 2s ease-in-out forwards',
  },
  confettiPiece: {
    position: 'absolute',
    top: '-10px',
    animation: 'pu-confetti-fall 2s ease-in forwards',
  },
  facesRow: {
    display: 'flex',
    gap: '12px',
    justifyContent: 'center',
    flexWrap: 'wrap',
    zIndex: 1,
  },
  faceCrop: {
    width: '64px',
    height: '64px',
    borderRadius: '50%',
    objectFit: 'cover',
    border: '3px solid #fff',
    boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
    animation: 'pu-face-pop 0.4s ease-out forwards',
    opacity: 0,
  },
  text: {
    fontSize: '24px',
    fontWeight: 'bold',
    color: '#fff',
    zIndex: 1,
    textShadow: '0 2px 8px rgba(0,0,0,0.3)',
  },
};

/* ── Base component styles ── */
const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
    padding: '24px',
    borderRadius: '24px',
    background: 'rgba(255,255,255,0.1)',
    backdropFilter: 'blur(12px)',
    border: '3px dashed rgba(255,255,255,0.3)',
    transition: 'border-color 0.2s',
  },
  dragOverBorder: {
    borderColor: '#4ade80',
    background: 'rgba(74,222,128,0.1)',
  },
  actionRow: {
    display: 'flex',
    gap: '16px',
    justifyContent: 'center',
    flexWrap: 'wrap',
  },
  actionBtn: {
    width: '80px',
    height: '80px',
    borderRadius: '20px',
    border: 'none',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 0.15s',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
  },
  cameraBtn: { background: 'linear-gradient(135deg, #38bdf8, #818cf8)' },
  galleryBtn: { background: 'linear-gradient(135deg, #fb923c, #f472b6)' },
  confirmBtn: { background: 'linear-gradient(135deg, #4ade80, #22d3ee)' },
  retakeBtn: { background: 'linear-gradient(135deg, #f87171, #fb923c)' },
  btnEmoji: { fontSize: '36px' },
  dropHint: {
    width: '80px',
    height: '80px',
    borderRadius: '20px',
    background: 'rgba(255,255,255,0.08)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    opacity: 0.5,
  },
  previewImage: {
    maxWidth: '100%',
    maxHeight: '300px',
    borderRadius: '16px',
    objectFit: 'contain',
  },
  errorBubble: {
    background: 'rgba(248,113,113,0.2)',
    color: '#fca5a5',
    padding: '8px 16px',
    borderRadius: '12px',
    fontSize: '14px',
    textAlign: 'center',
  },
};
