import React, { useState, useEffect, useCallback } from 'react';
import LazyImage from '../../../shared/components/LazyImage';

const API_BASE = 'http://localhost:8000';

/**
 * PhotoGallery — grid of uploaded photos with face cards, labeling, delete, storage stats.
 * Touch-friendly for 6yo: swipe support, big targets, colorful face cards.
 */
export default function PhotoGallery({ siblingPairId, refreshKey }) {
  const [photos, setPhotos] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedPhoto, setSelectedPhoto] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null);
  const [editingFace, setEditingFace] = useState(null);
  const [faceName, setFaceName] = useState('');
  const [imageDims, setImageDims] = useState(null);
  const [viewTransition, setViewTransition] = useState(null);

  const loadPhotos = useCallback(async () => {
    if (!siblingPairId) return;
    try {
      const [photosResp, statsResp] = await Promise.all([
        fetch(`${API_BASE}/api/photos/${siblingPairId}`),
        fetch(`${API_BASE}/api/photos/stats/${siblingPairId}`),
      ]);
      if (photosResp.ok) setPhotos(await photosResp.json());
      if (statsResp.ok) setStats(await statsResp.json());
    } catch (err) {
      console.error('Failed to load photos:', err);
    }
  }, [siblingPairId]);

  useEffect(() => { loadPhotos(); }, [loadPhotos, refreshKey]);

  const handleDelete = async (photoId) => {
    try {
      const resp = await fetch(`${API_BASE}/api/photos/${photoId}`, { method: 'DELETE' });
      if (resp.ok) {
        setDeleteConfirm(null);
        setSelectedPhoto(null);
        loadPhotos();
      }
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const handleLabelFace = async (faceId) => {
    if (!faceName.trim()) return;
    try {
      const resp = await fetch(`${API_BASE}/api/photos/faces/${faceId}/label`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: faceName.trim() }),
      });
      if (resp.ok) {
        setEditingFace(null);
        setFaceName('');
        loadPhotos();
      }
    } catch (err) {
      console.error('Label failed:', err);
    }
  };

  if (photos.length === 0) {
    return (
      <div style={styles.emptyState}>
        <svg width="140" height="140" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ minWidth: '120px', minHeight: '120px' }}>
          {/* Camera body */}
          <rect x="25" y="45" width="90" height="65" rx="14" fill="#7c3aed" opacity="0.85" />
          <rect x="50" y="30" width="30" height="18" rx="6" fill="#a78bfa" />
          {/* Lens */}
          <circle cx="70" cy="75" r="22" fill="#1e1b4b" />
          <circle cx="70" cy="75" r="16" fill="#312e81" />
          <circle cx="70" cy="75" r="8" fill="#6366f1" />
          <circle cx="64" cy="69" r="3" fill="rgba(255,255,255,0.5)" />
          {/* Flash */}
          <rect x="92" y="50" width="10" height="6" rx="2" fill="#fbbf24" />
          {/* Sparkles */}
          <circle cx="22" cy="38" r="4" fill="#fbbf24" opacity="0.9" />
          <circle cx="118" cy="32" r="3" fill="#f472b6" opacity="0.9" />
          <circle cx="12" cy="80" r="3" fill="#4ade80" opacity="0.8" />
          <circle cx="128" cy="90" r="4" fill="#60a5fa" opacity="0.8" />
          <path d="M30 25l2-6 2 6-6-2 6-2z" fill="#fbbf24" opacity="0.7" />
          <path d="M112 20l2-5 2 5-5-2 5-2z" fill="#f472b6" opacity="0.7" />
          <path d="M125 65l1.5-4 1.5 4-4-1.5 4-1.5z" fill="#4ade80" opacity="0.7" />
        </svg>
        <p style={styles.emptyPrompt}>Your faces will appear in the story! Add a photo to begin 📸</p>
      </div>
    );
  }

  // ── Full photo detail view ──
  if (selectedPhoto) {
    const photo = photos.find(p => p.photo_id === selectedPhoto);
    if (!photo) { setSelectedPhoto(null); return null; }

    return (
      <>
        <style>{`
          @keyframes pgScaleIn {
            from { opacity: 0; transform: scale(0.85); }
            to { opacity: 1; transform: scale(1); }
          }
          @keyframes pgFadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }
        `}</style>
        <div style={{
          ...styles.detailView,
          animation: viewTransition === 'grid-to-detail' ? 'pgScaleIn 300ms ease-out both' : undefined,
        }}>
        <button onClick={() => { setViewTransition('detail-to-grid'); setSelectedPhoto(null); setImageDims(null); }} style={styles.backBtn} aria-label="Back">
          <span style={{ fontSize: '28px' }}>←</span>
        </button>

        <div style={styles.detailImageContainer}>
          <img
            src={`${API_BASE}/photo_storage/${photo.file_path}`}
            alt={(() => {
              const faces = photo.faces || [];
              const count = faces.length;
              const named = faces.filter(f => f.family_member_name).map(f => f.family_member_name);
              if (count === 0) return 'Family photo with no detected faces';
              const base = `Family photo with ${count} detected face${count > 1 ? 's' : ''}`;
              return named.length > 0 ? `${base}: ${named.join(', ')}` : base;
            })()}
            style={styles.detailImage}
            onLoad={(e) => setImageDims({ w: e.target.naturalWidth, h: e.target.naturalHeight })}
            onError={(e) => { e.target.style.display = 'none'; }}
          />
          {imageDims && (photo.faces || []).map((face, i) => (
            <div
              key={face.face_id}
              onClick={() => { setEditingFace(face.face_id); setFaceName(face.family_member_name || ''); }}
              style={{
                position: 'absolute',
                left: `${(face.bbox_x / imageDims.w) * 100}%`,
                top: `${(face.bbox_y / imageDims.h) * 100}%`,
                width: `${(face.bbox_width / imageDims.w) * 100}%`,
                height: `${(face.bbox_height / imageDims.h) * 100}%`,
                minWidth: '44px',
                minHeight: '44px',
                border: `2px ${i % 2 === 0 ? 'solid' : 'dashed'} ${BBOX_BORDERS[i % BBOX_BORDERS.length]}`,
                background: BBOX_COLORS[i % BBOX_COLORS.length],
                borderRadius: '6px',
                cursor: 'pointer',
                boxSizing: 'border-box',
              }}
              aria-label={`Face: ${face.family_member_name || 'unlabeled'}`}
            />
          ))}
        </div>

        {/* Face cards */}
        <div style={styles.faceCardRow}>
          {(photo.faces || []).map((face) => (
            <div key={face.face_id} style={styles.faceCard}>
              <div style={styles.faceThumb}>
                <img
                  src={`${API_BASE}/photo_storage/${face.crop_path}`}
                  alt={face.family_member_name || 'Detected face'}
                  style={styles.faceThumbImg}
                  onError={(e) => {
                    e.target.style.display = 'none';
                    e.target.nextSibling.style.display = 'block';
                  }}
                />
                <span style={{ display: 'none', fontSize: '28px' }}>👤</span>
              </div>
              {editingFace === face.face_id ? (
                <div style={styles.labelForm}>
                  <label htmlFor={`face-name-${face.face_id}`} className="sr-only">
                    Name for detected face
                  </label>
                  <input
                    id={`face-name-${face.face_id}`}
                    type="text"
                    value={faceName}
                    onChange={(e) => setFaceName(e.target.value)}
                    placeholder="Name"
                    style={styles.labelInput}
                    maxLength={20}
                    autoFocus
                    aria-describedby={!faceName.trim() ? `face-name-error-${face.face_id}` : undefined}
                  />
                  {!faceName.trim() && (
                    <span id={`face-name-error-${face.face_id}`} className="sr-only">
                      Name cannot be empty
                    </span>
                  )}
                  <button
                    onClick={() => handleLabelFace(face.face_id)}
                    style={styles.labelSaveBtn}
                    aria-label="Save name"
                  >✓</button>
                </div>
              ) : (
                <button
                  onClick={() => { setEditingFace(face.face_id); setFaceName(face.family_member_name || ''); }}
                  style={styles.faceNameBtn}
                >
                  {face.family_member_name || '✏️ Name?'}
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Delete */}
        {deleteConfirm === photo.photo_id ? (
          <div style={styles.deleteConfirmRow}>
            <button onClick={() => handleDelete(photo.photo_id)} style={styles.deleteYes} aria-label="Confirm delete">🗑️</button>
            <button onClick={() => setDeleteConfirm(null)} style={styles.deleteNo} aria-label="Cancel delete">✖️</button>
          </div>
        ) : (
          <button onClick={() => setDeleteConfirm(photo.photo_id)} style={styles.deleteBtn} aria-label="Delete photo">
            🗑️
          </button>
        )}
      </div>
      </>
    );
  }

  // ── Grid view ──
  return (
    <div style={{
      ...styles.container,
      animation: viewTransition === 'detail-to-grid' ? 'pgFadeIn 300ms ease-out both' : undefined,
    }}>
      {/* Storage indicator */}
      {stats && (
        <div style={styles.statsBar}>
          📷 {stats.photo_count} · 👤 {stats.face_count} · {(stats.total_size_bytes / 1024 / 1024).toFixed(1)} MB
        </div>
      )}

      <div style={styles.grid}>
        {photos.map((photo) => (
          <button
            key={photo.photo_id}
            onClick={() => {
              setViewTransition('grid-to-detail');
              setSelectedPhoto(photo.photo_id);
            }}
            style={{
              ...styles.gridItem,
              ...(photo.status === 'review' ? styles.reviewBorder : {}),
            }}
            aria-label={`Photo with ${photo.faces?.length || 0} faces`}
          >
            <LazyImage
              src={`${API_BASE}/photo_storage/${photo.file_path}`}
              alt={(() => {
                const faces = photo.faces || [];
                const count = faces.length;
                const named = faces.filter(f => f.family_member_name).map(f => f.family_member_name);
                if (count === 0) return 'Photo with no detected faces';
                const base = `Photo with ${count} detected face${count > 1 ? 's' : ''}`;
                return named.length > 0 ? `${base}: ${named.join(', ')}` : base;
              })()}
              style={styles.gridThumbImg}
              onError={(e) => {
                e.target.style.display = 'none';
                e.target.parentElement.nextSibling.style.display = 'flex';
              }}
            />
            <div style={{ ...styles.gridThumbFallback, display: 'none' }}>🖼️</div>
            {photo.status === 'review' && (
              <div style={styles.reviewOverlay} />
            )}
            {photo.faces?.length > 0 && (
              <span style={styles.faceCount}>👤 {photo.faces.length}</span>
            )}
            {photo.status === 'review' && (
              <span style={styles.reviewBadge}>⏳</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}


const BBOX_COLORS = [
  'rgba(251,113,133,0.35)', // pink
  'rgba(96,165,250,0.35)',  // blue
  'rgba(74,222,128,0.35)',  // green
  'rgba(251,191,36,0.35)',  // amber
  'rgba(167,139,250,0.35)', // purple
  'rgba(45,212,191,0.35)',  // teal
];
const BBOX_BORDERS = [
  '#fb7185', '#60a5fa', '#4ade80', '#fbbf24', '#a78bfa', '#2dd4bf',
];

const styles = {
  container: { display: 'flex', flexDirection: 'column', gap: '12px' },
  emptyState: {
    textAlign: 'center',
    padding: '32px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
  },
  emptyPrompt: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: '16px',
    margin: 0,
    fontWeight: 500,
  },
  statsBar: {
    textAlign: 'center',
    fontSize: '13px',
    color: 'rgba(255,255,255,0.75)',
    padding: '4px 0',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(90px, 1fr))',
    gap: '10px',
  },
  gridItem: {
    position: 'relative',
    width: '100%',
    aspectRatio: '1',
    borderRadius: '16px',
    border: '2px solid rgba(255,255,255,0.15)',
    background: 'rgba(255,255,255,0.08)',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'transform 0.15s',
    overflow: 'hidden',
  },
  reviewBorder: { borderColor: '#fbbf24' },
  gridThumbImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    borderRadius: '12px',
  },
  gridThumbFallback: {
    position: 'absolute',
    inset: 0,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontSize: '32px',
  },
  reviewOverlay: {
    position: 'absolute',
    inset: 0,
    borderRadius: '12px',
    background: 'rgba(251,191,36,0.25)',
    pointerEvents: 'none',
  },
  faceCount: {
    position: 'absolute',
    bottom: '4px',
    right: '6px',
    fontSize: '11px',
    background: 'rgba(0,0,0,0.5)',
    borderRadius: '8px',
    padding: '2px 6px',
    color: '#fff',
  },
  reviewBadge: {
    position: 'absolute',
    top: '4px',
    right: '6px',
    fontSize: '16px',
  },
  detailView: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '12px',
    padding: '12px',
  },
  backBtn: {
    alignSelf: 'flex-start',
    background: 'none',
    border: 'none',
    color: '#fff',
    cursor: 'pointer',
    minWidth: '48px',
    minHeight: '48px',
  },
  detailImage: {
    maxWidth: '100%',
    maxHeight: '250px',
    borderRadius: '16px',
    objectFit: 'contain',
  },
  detailImageContainer: {
    position: 'relative',
    display: 'inline-block',
    maxWidth: '100%',
  },
  faceCardRow: {
    display: 'flex',
    gap: '10px',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  faceCard: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '6px',
    padding: '8px',
    borderRadius: '14px',
    background: 'rgba(255,255,255,0.1)',
    minWidth: '70px',
  },
  faceThumb: {
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    overflow: 'hidden',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'rgba(255,255,255,0.1)',
  },
  faceThumbImg: {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
    borderRadius: '50%',
  },
  faceNameBtn: {
    background: 'rgba(255,255,255,0.15)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    padding: '4px 10px',
    fontSize: '12px',
    cursor: 'pointer',
    minHeight: '44px',
    minWidth: '44px',
  },
  labelForm: { display: 'flex', gap: '4px', alignItems: 'center' },
  labelInput: {
    width: '70px',
    padding: '4px 8px',
    borderRadius: '8px',
    border: '1px solid rgba(255,255,255,0.3)',
    background: 'rgba(0,0,0,0.3)',
    color: '#fff',
    fontSize: '12px',
  },
  labelSaveBtn: {
    background: '#4ade80',
    border: 'none',
    borderRadius: '8px',
    width: '44px',
    height: '44px',
    cursor: 'pointer',
    fontSize: '16px',
  },
  deleteBtn: {
    background: 'rgba(248,113,113,0.2)',
    border: 'none',
    borderRadius: '12px',
    padding: '8px 16px',
    cursor: 'pointer',
    fontSize: '20px',
    minWidth: '48px',
    minHeight: '48px',
  },
  deleteConfirmRow: { display: 'flex', gap: '12px' },
  deleteYes: {
    background: '#ef4444',
    border: 'none',
    borderRadius: '12px',
    width: '56px',
    height: '56px',
    cursor: 'pointer',
    fontSize: '24px',
  },
  deleteNo: {
    background: 'rgba(255,255,255,0.15)',
    border: 'none',
    borderRadius: '12px',
    width: '56px',
    height: '56px',
    cursor: 'pointer',
    fontSize: '24px',
  },
};
