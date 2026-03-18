import React, { useRef, useState, useEffect } from 'react';
import './LazyImage.css';

/**
 * LazyImage — defers image loading until the element is near the viewport.
 * Uses IntersectionObserver with a configurable rootMargin for early loading.
 * Shows a shimmer skeleton placeholder until the image is fully loaded,
 * then fades it in. Falls back to loading="lazy" if IntersectionObserver
 * is not supported.
 */
export default function LazyImage({
  src,
  alt,
  width,
  height,
  className,
  style,
  rootMargin = '200px',
  fadeDuration = 200,
  onError,
}) {
  const containerRef = useRef(null);
  const [isInView, setIsInView] = useState(
    typeof IntersectionObserver === 'undefined'
  );
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    if (typeof IntersectionObserver === 'undefined') return;

    const el = containerRef.current;
    if (!el) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      { rootMargin }
    );

    observer.observe(el);

    return () => observer.disconnect();
  }, [rootMargin]);

  const showSkeleton = !isInView || !isLoaded;

  return (
    <div
      ref={containerRef}
      className={`lazy-image${className ? ` ${className}` : ''}`}
      style={{ width, height, ...style }}
    >
      {showSkeleton && (
        <div
          className="lazy-image__skeleton"
          style={{ width, height }}
          aria-hidden="true"
        />
      )}

      {isInView && (
        <img
          className="lazy-image__img"
          src={src}
          alt={alt}
          width={width}
          height={height}
          loading="lazy"
          onLoad={() => setIsLoaded(true)}
          onError={onError}
          style={{
            opacity: isLoaded ? 1 : 0,
            transition: `opacity ${fadeDuration}ms ease-in`,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      )}
    </div>
  );
}
