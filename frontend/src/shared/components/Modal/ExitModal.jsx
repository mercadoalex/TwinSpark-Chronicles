import React, { useRef } from 'react';
import { useFocusTrap } from '../../hooks';
import './ExitModal.css';

export default function ExitModal({ onSave, onExit, onClose, isSaving }) {
    const dialogRef = useRef(null);
    useFocusTrap(dialogRef, true, onClose);

    return (
        <div className="exit-modal-backdrop">
            <div
                ref={dialogRef}
                role="dialog"
                aria-modal="true"
                aria-labelledby="exit-modal-heading"
                className="exit-modal-dialog"
            >
                <div className="exit-modal-emoji" aria-hidden="true">🚪</div>

                <h2 id="exit-modal-heading" className="exit-modal-title">
                    Leaving the Magic?
                </h2>

                <p className="exit-modal-description">
                    Do you want to save your adventure so you can continue it later?
                </p>

                <div className="exit-modal-actions">
                    <button
                        className="exit-modal-btn-save"
                        onClick={onSave}
                        disabled={isSaving}
                    >
                        {isSaving ? 'Saving...' : '💾 Save & Exit'}
                    </button>

                    <button
                        className="exit-modal-btn-exit"
                        onClick={onExit}
                        disabled={isSaving}
                    >
                        🏃 Exit without Saving
                    </button>

                    <button
                        className="exit-modal-btn-cancel"
                        onClick={onClose}
                        disabled={isSaving}
                    >
                        Cancel
                    </button>
                </div>
            </div>
        </div>
    );
}
