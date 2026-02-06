import React from 'react';
import { useNavigate } from 'react-router-dom';
import Layout from './Layout';
import VideoStream from './VideoStream';

const LiveFeed: React.FC = () => {
    const navigate = useNavigate();

    const handleNavigate = (pageId: string) => {
        switch (pageId) {
            case 'stream':
                navigate('/live-feed');
                break;
            case 'events':
                navigate('/event-log');
                break;
            case 'dashboard':
                navigate('/');
                break;
            case 'frames':
                navigate('/frames');
                break;
            default:
                navigate('/');
        }
    };

    return (
        <Layout currentPage="stream" onNavigate={handleNavigate}>
            <div>
                <h2 className="text-2xl font-bold mb-4 text-gray-800">Live Camera Feed</h2>
                <p className="text-gray-600 mb-4">
                    Real-time video stream from edge module camera
                </p>
                <VideoStream streamId="default" />
            </div>
        </Layout>
    );
};

export default LiveFeed;