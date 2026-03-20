import React, { useRef } from 'react';
import { useFocusTrap } from '../../hooks';
import './AlertModal.css';

export default function AlertModal({ message, onClose }) {
    const dialogRef = useRef(null);
    const isOpen = Boolean(message);

    useFocusTrap(dialogRef, isOpen, onClose);

    if (!message) return null;

    return (
        <div className="alert-modal-backdrop">
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="alert-modal-heading"
                className="alert-modal-dialog"
            >
                <div className="alert-modal-emoji" aria-hidden="true">✨</div>

                <h2 id="alert-modal-heading" className="alert-modal-title">
                    TwinSpark Magic
                </h2>

                <p className="alert-modal-message">{message}</p>

                <button className="alert-modal-btn" onClick={onClose}>
                    OK!
                </button>
            </div>
        </div>
    );
}
