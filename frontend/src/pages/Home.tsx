import React from 'react';
import Dashboard from '../components/Dashboard';
import EventLog from '../components/EventLog';
import LiveFeed from '../components/LiveFeed';

const Home: React.FC = () => {
    return (
        <div>
            <h1>Face Recognition System</h1>
            <Dashboard />
            <LiveFeed />
            <EventLog />
        </div>
    );
};

export default Home;