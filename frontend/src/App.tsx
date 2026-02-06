import React from 'react';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import EventLog from './components/EventLog';
import LiveFeed from './components/LiveFeed';
import Home from './pages/Home';
import Settings from './pages/Settings';
import './styles/App.css';

const App: React.FC = () => {
    return (
        <Router>
            <div className="App">
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