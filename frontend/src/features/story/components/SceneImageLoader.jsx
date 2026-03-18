import React, { useState, useEffect, useRef } from 'react';
import './SceneImageLoader.css';

/**
 * SceneImageLoader — loads story scene images in the background with
 * a blurred skeleton placeholder, crossfade transition, and timeout fallback.
 *
 * Unlike LazyImage (which defers via IntersectionObserver), this component
 * starts loading immediately using a preload Image() object so the browser
 * begins downloading as soon as the story beat arrives.
 */
export default function SceneImageLoader({
  src,
  alt,
  timeout = 10000,
  fadeDuration = 300,
  className,
}) {
  const [status, setStatus] = useState('loading'); // 'loading' | 'loaded' | 'error'
  const timeoutRef = useRef(null);

  useEffect(() => {
    if (!src) {
      setStatus('error');
      return;
    }

    setStatus('loading');

    const img = new Image();

    const clearTimer = () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };

    img.onload = () => {
      clearTimer();
      setStatus('loaded');
    };

    img.onerror = () => {
      clearTimer();
      setStatus('error');
    };

    // Start the timeout timer
    timeoutRef.current = setTimeout(() => {
      console.warn(`[SceneImageLoader] Image load timed out after ${timeout}ms: ${src}`);
      setStatus('error');
    }, timeout);

    // Kick off the download
    img.src = src;

    return () => {
      clearTimer();
      img.onload = null;
      img.onerror = null;
    };
  }, [src, timeout]);

  return (
    <div className={`scene-loader${className ? ` ${className}` : ''}`}>
      {/* Blurred skeleton — visible while loading, fades out when done */}
      {(status === 'loading') && (
        <div className="scene-loader__skeleton" aria-hidden="true" />
      )}

      {/* Actual image — opacity transitions for crossfade */}
      {status === 'loaded' && (
        <img
          className="scene-loader__img"
          src={src}
          alt={alt}
          style={{
            opacity: 1,
            transition: `opacity ${fadeDuration}ms ease-in`,
          }}
        />
      )}

      {/* Fallback on error / timeout */}
      {status === 'error' && (
        <div className="scene-loader__fallback" role="img" aria-label={alt || 'Scene illustration unavailable'}>
          <span className="scene-loader__fallback-icon" aria-hidden="true">🎨</span>
          <p className="scene-loader__fallback-text">Oops, the picture got lost in the story!</p>
        </div>
      )}
    </div>
  );
}
