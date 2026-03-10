import React from 'react';
import './ChildFriendlyButton.css';

/**
 * ChildFriendlyButton
 * A large, accessible button component designed for 6-year-olds and touch interfaces.
 * 
 * @param {string} children - The text content of the button.
 * @param {function} onClick - The callback function when clicked.
 * @param {ReactNode} icon - Optional icon to render alongside text.
 * @param {string} variant - 'primary', 'secondary', 'danger', 'success' (default: 'primary')
 * @param {boolean} disabled - Whether the button is disabled.
 * @param {boolean} fullWidth - If the button should take up 100% width.
 * @param {object} style - Optional extra style overrides.
 */
const ChildFriendlyButton = ({
    children,
    onClick,
    icon = null,
    variant = 'primary',
    disabled = false,
    fullWidth = false,
    style = {},
    className = ''
}) => {
    const baseClasses = `child-friendly-btn variant-${variant} ${fullWidth ? 'full-width' : ''} ${disabled ? 'disabled' : ''} ${className}`;

    return (
        <button
            className={baseClasses}
            onClick={disabled ? undefined : onClick}
            disabled={disabled}
            style={style}
            aria-label={typeof children === 'string' ? children : 'Button'}
        >
            {icon && <span className="btn-icon">{icon}</span>}
            <span className="btn-text">{children}</span>
        </button>
    );
};

export default ChildFriendlyButton;
