import React from 'react';
import { useNavigate } from 'react-router-dom';
import Dashboard from '../components/Dashboard';
import Layout from '../components/Layout';

const Home: React.FC = () => {
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
        <Layout currentPage="dashboard" onNavigate={handleNavigate}>
            <Dashboard />
        </Layout>
    );
};

export default Home;