import React, { useRef, useEffect, useState } from 'react';

const MagicMirror = ({ embedded = false }) => {
  const videoRef = useRef(null);
  const [cameraActive, setCameraActive] = useState(false);

  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then(stream => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraActive(true);
        }
      })
      .catch(err => {
        console.error("Camera mirroring failed:", err);
        setCameraActive(false);
      });

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  if (!cameraActive) return null;

  // Embedded mode - shown in main UI
  if (embedded) {
    return (
      <div style={{
        width: '100%',
        maxWidth: '400px',
        margin: '20px auto',
        borderRadius: '20px',
        overflow: 'hidden',
        border: '4px solid #a855f7',
        boxShadow: '0 0 30px rgba(168, 85, 247, 0.8)',
        position: 'relative',
        background: '#000'
      }}>
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          aria-label="Live camera preview showing your face"
          style={{
            width: '100%',
            height: 'auto',
            display: 'block',
            transform: 'scaleX(-1)' // Mirror effect
          }}
        />
        <div
          role="status"
          aria-label="Do your gesture here"
          style={{
            position: 'absolute',
            bottom: '15px',
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(0,0,0,0.8)',
            padding: '8px 20px',
            borderRadius: '20px',
            fontSize: '1rem',
            color: '#a855f7',
            fontWeight: 'bold',
            border: '2px solid #a855f7',
            boxShadow: '0 0 15px rgba(168, 85, 247, 0.6)'
          }}
        >
          <span aria-hidden="true">👋 </span>Do your gesture here!
        </div>
      </div>
    );
  }

  // Floating mode - small bubble (original)
  return (
    <div style={{
      position: 'fixed',
      bottom: '120px',
      right: '30px',
      width: '180px',
      height: '180px',
      borderRadius: '50%',
      border: '4px solid #a855f7',
      overflow: 'hidden',
      boxShadow: '0 0 30px rgba(168, 85, 247, 0.8)',
      zIndex: 1000,
      background: '#000'
    }}>
      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        aria-label="Live camera preview showing your face"
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          transform: 'scaleX(-1)'
        }}
      />
      <div
        role="status"
        aria-label="Wave here"
        style={{
          position: 'absolute',
          bottom: '5px',
          left: '50%',
          transform: 'translateX(-50%)',
          background: 'rgba(0,0,0,0.7)',
          padding: '3px 8px',
          borderRadius: '10px',
          fontSize: '0.7rem',
          color: '#a855f7',
          fontWeight: 'bold'
        }}
      >
        <span aria-hidden="true">👋 </span>Wave Here!
      </div>
    </div>
  );
};

export default MagicMirror;