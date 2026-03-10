import React, { useState } from 'react';

/**
 * ImageMagnifier
 * A component that displays an image and allows the user to hover over it 
 * to see a magnified version in a "lens", helpful for viewing detailed images or text.
 */
export default function ImageMagnifier({
    src,
    alt,
    width = "100%",
    maxWidth = "400px",
    magnifierHeight = 150,
    magnifierWidth = 150,
    zoomLevel = 4.5,
    style = {}
}) {
    const [showMagnifier, setShowMagnifier] = useState(false);
    const [position, setPosition] = useState({ x: 0, y: 0 });
    const [cursorPosition, setCursorPosition] = useState({ x: 0, y: 0 });

    const handleMouseEnter = () => {
        setShowMagnifier(true);
    };

    const handleMouseLeave = () => {
        setShowMagnifier(false);
    };

    const handleMouseMove = (e) => {
        const elem = e.currentTarget;
        const { top, left, width, height } = elem.getBoundingClientRect();

        // Calculate cursor position on the image
        const x = e.clientX - left;
        const y = e.clientY - top;

        setCursorPosition({ x, y });

        // Calculate background position percentages
        // Limit to 0-100% to avoid background repeating issues at edges
        const bgX = Math.max(0, Math.min(100, (x / width) * 100));
        const bgY = Math.max(0, Math.min(100, (y / height) * 100));

        setPosition({ x: bgX, y: bgY });
    };

    return (
        <div
            style={{
                position: 'relative',
                display: 'inline-block',
                width: width,
                maxWidth: maxWidth,
                cursor: showMagnifier ? 'none' : 'default',
                margin: '0 auto',
                ...style
            }}
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
            onMouseMove={handleMouseMove}
            onTouchStart={handleMouseEnter}
            onTouchEnd={handleMouseLeave}
            onTouchMove={(e) => {
                if (e.touches.length > 0) {
                    const touch = e.touches[0];
                    const elem = e.currentTarget;
                    const { top, left, width, height } = elem.getBoundingClientRect();
                    const x = touch.clientX - left;
                    const y = touch.clientY - top;
                    if (x >= 0 && x <= width && y >= 0 && y <= height) {
                        setCursorPosition({ x, y });
                        setPosition({
                            x: (x / width) * 100,
                            y: (y / height) * 100
                        });
                    }
                }
            }}
        >
            <img
                src={src}
                alt={alt}
                style={{ width: '100%', height: 'auto', display: 'block', borderRadius: '10px' }}
            />
            {showMagnifier && (
                <div
                    style={{
                        position: 'absolute',
                        pointerEvents: 'none',
                        height: `${magnifierHeight}px`,
                        width: `${magnifierWidth}px`,
                        // Center the magnifier on the cursor
                        top: cursorPosition.y - magnifierHeight / 2,
                        left: cursorPosition.x - magnifierWidth / 2,
                        opacity: 1,
                        border: '3px solid var(--color-accent-pink)',
                        borderRadius: '50%',
                        backgroundColor: 'white',
                        backgroundImage: `url('${src}')`,
                        backgroundRepeat: 'no-repeat',
                        // Zoom the image
                        backgroundSize: `${zoomLevel * 100}%`,
                        // Align the magnified part with the cursor
                        backgroundPosition: `${position.x}% ${position.y}%`,
                        boxShadow: '0 5px 15px rgba(0,0,0,0.5), inset 0 0 10px rgba(0,0,0,0.3)',
                        zIndex: 100
                    }}
                />
            )}
        </div>
    );
}
