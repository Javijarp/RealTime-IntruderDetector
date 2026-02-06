import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Alert from './components/Alert';
import Dashboard from './components/Dashboard';
import EventLog from './components/EventLog';
import LiveFeed from './components/LiveFeed';
import useAlertWebSocket from './hooks/useAlertWebSocket';
import Home from './pages/Home';
import Settings from './pages/Settings';
import './styles/App.css';

const App: React.FC = () => {
    // WebSocket URL - connect through nginx proxy (same host as frontend)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host; // includes hostname:port (e.g., "192.168.5.74:3000")
    const wsUrl = `${wsProtocol}//${wsHost}/ws/stream`;

    console.log('WebSocket connecting to:', wsUrl);

    const { alert, clearAlert, connected } = useAlertWebSocket(wsUrl);

    return (
        <Router>
            <div className="App">
                {/* Global alert system */}
                {alert && (
                    <Alert
                        message={alert.message}
                        entityType={alert.entityType}
                        confidence={alert.confidence}
                        timestamp={alert.timestamp}
                        imageData={alert.imageData}
                        imageType={alert.imageType}
                        onClose={clearAlert}
                    />
                )}

                {/* WebSocket connection status indicator (optional) */}
                {!connected && (
                    <div style={{
                        position: 'fixed',
                        bottom: '20px',
                        right: '20px',
                        background: '#ff9800',
                        color: 'white',
                        padding: '8px 16px',
                        borderRadius: '4px',
                        fontSize: '12px',
                        zIndex: 9998
                    }}>
                        ⚠ Alert system disconnected
                    </div>
                )}

                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/settings" element={<Settings />} />
                    <Route path="/dashboard" element={<Dashboard />} />
                    <Route path="/event-log" element={<EventLog />} />
                    <Route path="/live-feed" element={<LiveFeed />} />
                </Routes>
            </div>
        </Router>
    );
};

export default App;