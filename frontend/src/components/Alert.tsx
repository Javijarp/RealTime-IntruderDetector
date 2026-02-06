import React, { useEffect, useState } from 'react';
import '../styles/Alert.css';

interface AlertProps {
    message: string;
    entityType: string;
    confidence: number;
    timestamp: string;
    imageData?: string;
    imageType?: string;
    onClose: () => void;
}

export const Alert: React.FC<AlertProps> = ({
    message,
    entityType,
    confidence,
    timestamp,
    imageData,
    imageType,
    onClose,
}) => {
    const [show, setShow] = useState(false);

    useEffect(() => {
        // Trigger animation
        setShow(true);

        // Auto-close after 10 seconds
        const timer = setTimeout(() => {
            handleClose();
        }, 10000);

        return () => clearTimeout(timer);
    }, []);

    const handleClose = () => {
        setShow(false);
        setTimeout(onClose, 300); // Wait for animation
    };

    const formatTimestamp = (ts: string) => {
        try {
            return new Date(ts).toLocaleString();
        } catch {
            return ts;
        }
    };

    const getEntityEmoji = (type: string) => {
        return type.toLowerCase() === 'person' ? '👤' : '🐕';
    };

    return (
        <div className={`alert-overlay ${show ? 'show' : ''}`}>
            <div className={`alert-popup ${show ? 'show' : ''}`}>
                <div className="alert-header">
                    <span className="alert-icon">🚨</span>
                    <h2 className="alert-title">Security Alert</h2>
                    <button className="alert-close" onClick={handleClose}>
                        ×
                    </button>
                </div>

                <div className="alert-body">
                    <div className="alert-message">
                        <span className="entity-icon">{getEntityEmoji(entityType)}</span>
                        <span className="message-text">{message}</span>
                    </div>

                    {imageData && (
                        <div className="alert-image-container">
                            <img
                                src={`data:${imageType || 'image/jpeg'};base64,${imageData}`}
                                alt="Detection snapshot"
                                className="alert-image"
                            />
                        </div>
                    )}

                    <div className="alert-details">
                        <div className="detail-row">
                            <span className="detail-label">Entity:</span>
                            <span className="detail-value">{entityType}</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Confidence:</span>
                            <span className="detail-value">{(confidence * 100).toFixed(1)}%</span>
                        </div>
                        <div className="detail-row">
                            <span className="detail-label">Time:</span>
                            <span className="detail-value">{formatTimestamp(timestamp)}</span>
                        </div>
                    </div>
                </div>

                <div className="alert-footer">
                    <button className="alert-button" onClick={handleClose}>
                        Acknowledge
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Alert;
