import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Alert from './components/Alert';
import Dashboard from './components/Dashboard';
import EventLog from './components/EventLog';
import LiveFeed from './components/LiveFeed';
import { AlertProvider } from './context/AlertContext';
import useAlertWebSocket from './hooks/useAlertWebSocket';
import Home from './pages/Home';
import Settings from './pages/Settings';
import './styles/App.css';

const AppContent: React.FC = () => {
    // WebSocket URL - connect to backend for alerts (via nginx proxy)
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = window.location.host; // Use current host (nginx will proxy)
    const wsUrl = `${wsProtocol}//${wsHost}/ws/stream`;  // nginx proxies /ws/ to backend /api/ws/

    console.log('WebSocket connecting to:', wsUrl);

    const { alert, clearAlert, connected } = useAlertWebSocket(wsUrl);

    return (
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
    );
};

const App: React.FC = () => {
    return (
        <Router>
            <AlertProvider>
                <AppContent />
            </AlertProvider>
        </Router>
    );
};

export default App;