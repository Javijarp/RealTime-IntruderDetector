import React, { useEffect, useState } from 'react';
import { DetectionEvent, fetchEvents, fetchFrames, Frame } from '../services/api';
import '../styles/Dashboard.css';

interface EventWithFrame extends DetectionEvent {
    frameName?: string;
}

const Dashboard: React.FC = () => {
    const [events, setEvents] = useState<EventWithFrame[]>([]);
    const [frames, setFrames] = useState<Frame[]>([]);
    const [selectedFrame, setSelectedFrame] = useState<Frame | null>(null);
    const [loadingFrames, setLoadingFrames] = useState(false);
    const [loadingEvents, setLoadingEvents] = useState(false);
    const [initialLoading, setInitialLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
        const interval = setInterval(() => loadData(true), 5000); // Refresh every 5 seconds (silent)
        return () => clearInterval(interval);
    }, []);

    const loadData = async (silent = false) => {
        try {
            if (!silent) {
                setInitialLoading(true);
            }
            setError(null);

            const [eventsData, framesData] = await Promise.all([
                fetchEvents(),
                fetchFrames()
            ]);

            setEvents(eventsData || []);
            setFrames(framesData || []);

            // Auto-select the latest frame if none is selected
            if (!selectedFrame && framesData && framesData.length > 0) {
                setSelectedFrame(framesData[framesData.length - 1]);
            }
        } catch (err) {
            console.error('Error loading data:', err);
            setError('Failed to load data from server. Check console for details.');
        } finally {
            if (!silent) {
                setInitialLoading(false);
            }
        }
    };

    const refreshFrames = async () => {
        try {
            setLoadingFrames(true);
            setError(null);
            const framesData = await fetchFrames();
            setFrames(framesData || []);
        } catch (err) {
            console.error('Error refreshing frames:', err);
            setError('Failed to refresh frames from server.');
        } finally {
            setLoadingFrames(false);
        }
    };

    const refreshEvents = async () => {
        try {
            setLoadingEvents(true);
            setError(null);
            const eventsData = await fetchEvents();
            setEvents(eventsData || []);
        } catch (err) {
            console.error('Error refreshing events:', err);
            setError('Failed to refresh events from server.');
        } finally {
            setLoadingEvents(false);
        }
    };

    const handleFrameClick = (frame: Frame) => {
        setSelectedFrame(frame);
    };

    const formatDate = (timestamp: string | undefined) => {
        if (!timestamp) return 'N/A';
        try {
            return new Date(timestamp).toLocaleString();
        } catch {
            return timestamp;
        }
    };

    return (
        <div className="dashboard-container">
            <h1>Face Recognition Dashboard</h1>

            {error && <div className="error-banner">{error}</div>}

            {initialLoading && frames.length === 0 ? (
                <div className="loading">Loading dashboard data...</div>
            ) : (
                <>
                    {/* Live Preview Section */}
                    <section className="preview-section">
                        <div className="preview-header">
                            <h2>Live Preview</h2>
                            <span className="preview-info">
                                {selectedFrame && `Frame #${selectedFrame.frameNumber}`}
                            </span>
                        </div>
                        <div className="preview-container">
                            {selectedFrame && selectedFrame.imageData ? (
                                <img
                                    src={`data:image/jpeg;base64,${selectedFrame.imageData}`}
                                    alt="Selected Frame"
                                    className="preview-image"
                                />
                            ) : (
                                <div className="no-preview">No frame selected</div>
                            )}
                        </div>
                    </section>

                    {/* Frames Table Section */}
                    <section className="frames-section">
                        <div className="section-header">
                            <h2>Frames ({frames.length})</h2>
                            <button className="refresh-btn" onClick={refreshFrames} disabled={loadingFrames}>
                                {loadingFrames ? 'Refreshing...' : 'Refresh'}
                            </button>
                        </div>
                        <div className="table-wrapper">
                            <table className="frames-table">
                                <thead>
                                    <tr>
                                        <th>Frame #</th>
                                        <th>Timestamp</th>
                                        <th>Type</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {frames.length > 0 ? (
                                        frames.map((frame) => (
                                            <tr key={frame.id}>
                                                <td>{frame.frameNumber}</td>
                                                <td>{formatDate(frame.timestamp)}</td>
                                                <td>{frame.imageType}</td>
                                                <td>
                                                    <button
                                                        className={`action-btn ${selectedFrame?.id === frame.id ? 'active' : ''
                                                            }`}
                                                        onClick={() => handleFrameClick(frame)}
                                                    >
                                                        View
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={4} className="text-center">
                                                No frames available
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* Events Table Section */}
                    <section className="events-section">
                        <div className="section-header">
                            <h2>Detection Events ({events.length})</h2>
                            <button className="refresh-btn" onClick={refreshEvents} disabled={loadingEvents}>
                                {loadingEvents ? 'Refreshing...' : 'Refresh'}
                            </button>
                        </div>
                        <div className="table-wrapper">
                            <table className="events-table">
                                <thead>
                                    <tr>
                                        <th>Event ID</th>
                                        <th>Entity Type</th>
                                        <th>Confidence</th>
                                        <th>Frame #</th>
                                        <th>Timestamp</th>
                                        <th>Status</th>
                                        <th>Action</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {events.length > 0 ? (
                                        events.map((event) => (
                                            <tr key={event.id}>
                                                <td>{event.id}</td>
                                                <td>{event.entity_type}</td>
                                                <td>
                                                    <span className="confidence-badge">
                                                        {(event.confidence * 100).toFixed(1)}%
                                                    </span>
                                                </td>
                                                <td>
                                                    {event.frameId ? (
                                                        <span className="frame-ref">{event.frameId}</span>
                                                    ) : (
                                                        <span className="no-ref">—</span>
                                                    )}
                                                </td>
                                                <td>{formatDate(event.timestamp)}</td>
                                                <td>
                                                    <span className={`status-badge ${event.processed ? 'processed' : 'pending'}`}>
                                                        {event.processed ? 'Processed' : 'Pending'}
                                                    </span>
                                                </td>
                                                <td>
                                                    <button
                                                        className="link-btn"
                                                        onClick={() => {
                                                            const frame = frames.find((f) => f.frameNumber === event.frameId);
                                                            if (frame) {
                                                                handleFrameClick(frame);
                                                            }
                                                        }}
                                                        disabled={!event.frameId}
                                                    >
                                                        View Frame
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan={7} className="text-center">
                                                No events recorded
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </section>
                </>
            )}
        </div>
    );
};

export default Dashboard;