import React, { useState, useEffect, useCallback } from 'react';
import { usePhotoUxEffects, useAnnounce } from '../../../shared/hooks';

const API_BASE = 'http://localhost:8000';

/**
 * CharacterMapping — drag-to-assign family faces to story character roles.
 * Enforces min 2 sibling protagonists mapped before photo integration starts.
 * Unmapped roles show default AI avatar.
 */
export default function CharacterMapping({ siblingPairId, characterRoles, onMappingSaved }) {
  const [faces, setFaces] = useState([]); // all labeled faces from photos
  const [mappings, setMappings] = useState({}); // { role: faceId | null }
  const [saving, setSaving] = useState(false);
  const [draggedFace, setDraggedFace] = useState(null);
  const [dragOverRole, setDragOverRole] = useState(null);
  const [droppedRole, setDroppedRole] = useState(null);
  const [returningFace, setReturningFace] = useState(null);

  const { haptic, playWhoosh, playSnap } = usePhotoUxEffects();
  const { announce } = useAnnounce();

  // Default character roles if none provided
  const roles = characterRoles || [
    { role: 'protagonist_1', label: '🌟', isSibling: true },
    { role: 'protagonist_2', label: '⭐', isSibling: true },
    { role: 'companion', label: '🐾', isSibling: false },
    { role: 'guide', label: '🧙', isSibling: false },
  ];

  const loadData = useCallback(async () => {
    if (!siblingPairId) return;
    try {
      // Load photos to get labeled faces
      const photosResp = await fetch(`${API_BASE}/api/photos/${siblingPairId}`);
      if (photosResp.ok) {
        const photos = await photosResp.json();
        const allFaces = photos.flatMap(p =>
          (p.faces || []).filter(f => f.family_member_name).map(f => ({
            faceId: f.face_id,
            name: f.family_member_name,
            photoId: f.photo_id,
            cropPath: f.crop_path,
          }))
        );
        setFaces(allFaces);
      }

      // Load existing mappings
      const mapResp = await fetch(`${API_BASE}/api/photos/mappings/${siblingPairId}`);
      if (mapResp.ok) {
        const existing = await mapResp.json();
        const map = {};
        existing.forEach(m => { map[m.character_role] = m.face_id; });
        setMappings(map);
      }
    } catch (err) {
      console.error('Failed to load mapping data:', err);
    }
  }, [siblingPairId]);

  useEffect(() => { loadData(); }, [loadData]);

  // Count sibling protagonist mappings
  const siblingMapped = roles
    .filter(r => r.isSibling && mappings[r.role])
    .length;
  const canSave = siblingMapped >= 2;

  const handleDragStart = (faceId) => {
    setDraggedFace(faceId);
    playWhoosh();
  };

  const handleDragEnd = () => {
    if (draggedFace && !dragOverRole) {
      // Dropped outside any slot — animate return to pool
      setReturningFace(draggedFace);
      setTimeout(() => setReturningFace(null), 300);
    }
    setDraggedFace(null);
    setDragOverRole(null);
  };

  const handleDragOverRole = (e, role) => {
    e.preventDefault();
    setDragOverRole(role);
  };

  const handleDragLeaveRole = () => {
    setDragOverRole(null);
  };

  const handleDropOnRole = (role) => {
    if (draggedFace) {
      setMappings(prev => ({ ...prev, [role]: draggedFace }));
      setDroppedRole(role);
      haptic(80);
      playSnap();
      const face = getFace(draggedFace);
      const roleObj = roles.find(r => r.role === role);
      const faceName = face?.name || 'Face';
      const roleLabel = roleObj?.role?.replace(/_/g, ' ') || role;
      announce(`${faceName} assigned to ${roleLabel}`, 'assertive');
      setTimeout(() => setDroppedRole(null), 250);
      setDraggedFace(null);
      setDragOverRole(null);
    }
  };

  const handleTapAssign = (role, faceId) => {
    setMappings(prev => ({ ...prev, [role]: faceId }));
    haptic(80);
    playSnap();
    const face = getFace(faceId);
    const roleObj = roles.find(r => r.role === role);
    const faceName = face?.name || 'Face';
    const roleLabel = roleObj?.role?.replace(/_/g, ' ') || role;
    announce(`${faceName} assigned to ${roleLabel}`, 'assertive');
  };

  const handleClearRole = (role) => {
    const faceId = mappings[role];
    const face = faceId ? getFace(faceId) : null;
    const roleObj = roles.find(r => r.role === role);
    const faceName = face?.name || 'Face';
    const roleLabel = roleObj?.role?.replace(/_/g, ' ') || role;
    setMappings(prev => ({ ...prev, [role]: null }));
    announce(`${faceName} removed from ${roleLabel}`, 'assertive');
  };

  const handleSave = async () => {
    if (!canSave) return;
    haptic(40);
    setSaving(true);
    try {
      const body = roles.map(r => ({
        character_role: r.role,
        face_id: mappings[r.role] || null,
      }));
      const resp = await fetch(`${API_BASE}/api/photos/mappings/${siblingPairId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (resp.ok && onMappingSaved) {
        onMappingSaved(await resp.json());
      }
    } catch (err) {
      console.error('Save mappings failed:', err);
    } finally {
      setSaving(false);
    }
  };

  const getFace = (faceId) => faces.find(f => f.faceId === faceId);

  /** Renders a circular face crop image with emoji fallback */
  const FaceCropImg = ({ face, size = 40 }) => {
    const [imgError, setImgError] = useState(false);
    if (!face || !face.cropPath || imgError) {
      return <span style={{ fontSize: size * 0.6 }}>👤</span>;
    }
    return (
      <img
        src={`${API_BASE}/photo_storage/${face.cropPath}`}
        alt={face.name || 'Face'}
        onError={() => setImgError(true)}
        style={{
          width: `${size}px`,
          height: `${size}px`,
          minWidth: `${size}px`,
          minHeight: `${size}px`,
          borderRadius: '50%',
          objectFit: 'cover',
        }}
      />
    );
  };

  // --- Empty state (Task 5.4) ---
  if (faces.length === 0) {
    return (
      <div style={styles.container}>
        <svg width="140" height="140" viewBox="0 0 140 140" fill="none" xmlns="http://www.w3.org/2000/svg" style={{ minWidth: 120, minHeight: 120 }}>
          {/* Background circle */}
          <circle cx="70" cy="70" r="66" fill="rgba(168,85,247,0.12)" stroke="rgba(168,85,247,0.3)" strokeWidth="2" />
          {/* Left face */}
          <circle cx="42" cy="52" r="18" fill="rgba(56,189,248,0.25)" stroke="rgba(56,189,248,0.6)" strokeWidth="2" />
          <circle cx="36" cy="48" r="2.5" fill="rgba(56,189,248,0.8)" />
          <circle cx="48" cy="48" r="2.5" fill="rgba(56,189,248,0.8)" />
          <path d="M36 56 Q42 62 48 56" stroke="rgba(56,189,248,0.8)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          {/* Right face */}
          <circle cx="98" cy="52" r="18" fill="rgba(251,191,36,0.25)" stroke="rgba(251,191,36,0.6)" strokeWidth="2" />
          <circle cx="92" cy="48" r="2.5" fill="rgba(251,191,36,0.8)" />
          <circle cx="104" cy="48" r="2.5" fill="rgba(251,191,36,0.8)" />
          <path d="M92 56 Q98 62 104 56" stroke="rgba(251,191,36,0.8)" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          {/* Arrows pointing down to slots */}
          <path d="M42 76 L42 96" stroke="rgba(74,222,128,0.6)" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M36 90 L42 98 L48 90" stroke="rgba(74,222,128,0.6)" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M98 76 L98 96" stroke="rgba(74,222,128,0.6)" strokeWidth="2.5" strokeLinecap="round" />
          <path d="M92 90 L98 98 L104 90" stroke="rgba(74,222,128,0.6)" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          {/* Slot rectangles */}
          <rect x="26" y="100" width="32" height="22" rx="6" fill="rgba(74,222,128,0.12)" stroke="rgba(74,222,128,0.4)" strokeWidth="1.5" strokeDasharray="4 2" />
          <rect x="82" y="100" width="32" height="22" rx="6" fill="rgba(74,222,128,0.12)" stroke="rgba(74,222,128,0.4)" strokeWidth="1.5" strokeDasharray="4 2" />
          {/* Sparkles */}
          <circle cx="68" cy="30" r="3" fill="rgba(251,191,36,0.7)" />
          <circle cx="22" cy="85" r="2" fill="rgba(56,189,248,0.5)" />
          <circle cx="118" cy="85" r="2" fill="rgba(168,85,247,0.5)" />
        </svg>
        <div style={styles.emptyPrompt}>Upload photos and label faces to assign your characters! 📸</div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* Character role slots */}
      <div style={styles.roleList}>
        {roles.map((r) => {
          const assignedFaceId = mappings[r.role];
          const assignedFace = assignedFaceId ? getFace(assignedFaceId) : null;
          const isHovered = dragOverRole === r.role;
          const isJustDropped = droppedRole === r.role;

          return (
            <div
              key={r.role}
              tabIndex={0}
              role="button"
              aria-label={
                assignedFace
                  ? `${r.role.replace(/_/g, ' ')}: assigned to ${assignedFace.name}`
                  : `${r.role.replace(/_/g, ' ')}: empty slot`
              }
              style={{
                ...styles.roleSlot,
                ...(draggedFace ? styles.roleSlotDropTarget : {}),
                ...(isHovered ? styles.roleSlotGlow : {}),
                ...(isJustDropped ? styles.roleSlotSnap : {}),
                ...(r.isSibling && !assignedFaceId ? styles.requiredSlot : {}),
              }}
              onDragOver={(e) => handleDragOverRole(e, r.role)}
              onDragLeave={handleDragLeaveRole}
              onDrop={() => handleDropOnRole(r.role)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  if (!assignedFaceId) {
                    const unassignedFace = faces.find(f =>
                      !Object.values(mappings).includes(f.faceId)
                    );
                    if (unassignedFace) handleTapAssign(r.role, unassignedFace.faceId);
                  }
                }
              }}
            >
              <span style={styles.roleEmoji}>{r.label}</span>
              {assignedFace ? (
                <div style={styles.assignedFace}>
                  <FaceCropImg face={assignedFace} size={40} />
                  <button
                    onClick={() => handleClearRole(r.role)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.stopPropagation();
                        handleClearRole(r.role);
                      }
                    }}
                    style={styles.clearBtn}
                    aria-label={`Remove ${assignedFace.name} from ${r.role.replace(/_/g, ' ')}`}
                  >✕</button>
                </div>
              ) : (
                <span style={styles.defaultLabel}>🤖</span>
              )}
            </div>
          );
        })}
      </div>

      {/* Available faces to drag */}
      <div style={styles.facePool}>
        {faces.map((face) => {
          const isDragging = draggedFace === face.faceId;
          const isReturning = returningFace === face.faceId;

          return (
            <div
              key={face.faceId}
              draggable
              tabIndex={0}
              role="button"
              aria-label={`${face.name}, tap or press Enter to assign`}
              onDragStart={() => handleDragStart(face.faceId)}
              onDragEnd={handleDragEnd}
              onClick={() => {
                // Tap-to-assign: find first empty sibling slot, then any empty slot
                const emptyRole = roles.find(r => r.isSibling && !mappings[r.role])
                  || roles.find(r => !mappings[r.role]);
                if (emptyRole) handleTapAssign(emptyRole.role, face.faceId);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  const emptyRole = roles.find(r => r.isSibling && !mappings[r.role])
                    || roles.find(r => !mappings[r.role]);
                  if (emptyRole) handleTapAssign(emptyRole.role, face.faceId);
                }
              }}
              style={{
                ...styles.faceChip,
                ...(isDragging ? styles.faceChipDragging : {}),
                ...(isReturning ? styles.faceChipReturning : {}),
              }}
            >
              <FaceCropImg face={face} size={40} />
              <span style={styles.chipName}>{face.name}</span>
            </div>
          );
        })}
      </div>

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={!canSave || saving}
        style={{
          ...styles.saveBtn,
          opacity: canSave ? 1 : 0.4,
        }}
        aria-label="Save character mappings"
      >
        {saving ? '⏳' : '✅'}
      </button>

      {!canSave && faces.length > 0 && (
        <div style={styles.hint}>Assign both heroes first ⬆️</div>
      )}
    </div>
  );
}


const styles = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '16px',
    padding: '16px',
  },
  roleList: {
    display: 'flex',
    gap: '12px',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  roleSlot: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '6px',
    padding: '12px',
    borderRadius: '16px',
    background: 'rgba(255,255,255,0.08)',
    border: '2px solid rgba(255,255,255,0.15)',
    minWidth: '72px',
    minHeight: '72px',
    transition: 'border-color 0.2s, transform 0.2s, box-shadow 0.2s',
  },
  roleSlotDropTarget: {
    borderColor: 'rgba(74,222,128,0.5)',
    borderStyle: 'dashed',
  },
  roleSlotGlow: {
    borderColor: 'rgba(74,222,128,0.9)',
    borderStyle: 'solid',
    boxShadow: '0 0 16px rgba(74,222,128,0.5), 0 0 32px rgba(74,222,128,0.2)',
    transform: 'scale(1.08)',
  },
  roleSlotSnap: {
    transform: 'scale(1)',
    transition: 'transform 250ms cubic-bezier(0.34, 1.56, 0.64, 1)',
  },
  requiredSlot: {
    borderColor: 'rgba(251,191,36,0.4)',
  },
  roleEmoji: { fontSize: '28px' },
  assignedFace: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
  },
  assignedName: {
    fontSize: '12px',
    color: '#fff',
    maxWidth: '60px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  clearBtn: {
    background: 'rgba(248,113,113,0.3)',
    border: 'none',
    borderRadius: '50%',
    width: '44px',
    height: '44px',
    color: '#fff',
    fontSize: '14px',
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  defaultLabel: {
    fontSize: '20px',
    opacity: 0.4,
  },
  facePool: {
    display: 'flex',
    gap: '8px',
    flexWrap: 'wrap',
    justifyContent: 'center',
    padding: '8px',
    borderRadius: '12px',
    background: 'rgba(255,255,255,0.05)',
  },
  faceChip: {
    display: 'flex',
    alignItems: 'center',
    gap: '4px',
    padding: '6px 12px',
    borderRadius: '20px',
    background: 'linear-gradient(135deg, rgba(56,189,248,0.3), rgba(168,85,247,0.3))',
    cursor: 'grab',
    userSelect: 'none',
    minHeight: '44px',
    minWidth: '44px',
    transition: 'transform 0.15s ease, box-shadow 0.15s ease',
  },
  faceChipDragging: {
    transform: 'scale(1.1)',
    boxShadow: '0 8px 24px rgba(0,0,0,0.35)',
    opacity: 0.9,
  },
  faceChipReturning: {
    transition: 'transform 300ms cubic-bezier(0.34, 1.56, 0.64, 1), opacity 300ms ease',
    transform: 'scale(1)',
    opacity: 1,
  },
  chipName: {
    fontSize: '12px',
    color: '#fff',
  },
  saveBtn: {
    width: '64px',
    height: '64px',
    borderRadius: '50%',
    border: 'none',
    background: 'linear-gradient(135deg, #4ade80, #22d3ee)',
    cursor: 'pointer',
    fontSize: '28px',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    transition: 'opacity 0.2s, transform 0.15s',
  },
  hint: {
    fontSize: '13px',
    color: 'rgba(255,255,255,0.75)',
    textAlign: 'center',
  },
  emptyPrompt: {
    fontSize: '15px',
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    marginTop: '8px',
    fontWeight: 500,
  },
};
