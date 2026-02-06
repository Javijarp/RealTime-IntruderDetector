import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { DetectionEvent, fetchEvents } from '../services/api';
import Layout from './Layout';

const EventLog: React.FC = () => {
    const [events, setEvents] = useState<DetectionEvent[]>([]);
    const navigate = useNavigate();

    useEffect(() => {
        const getEvents = async () => {
            const fetchedEvents = await fetchEvents();
            setEvents(fetchedEvents as DetectionEvent[]);
        };

        getEvents();
        const interval = setInterval(getEvents, 5000); // Refresh every 5 seconds

        return () => clearInterval(interval); // Cleanup on unmount
    }, []);

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
        <Layout currentPage="events" onNavigate={handleNavigate}>
            <div className="event-log">
                <h2 className="text-2xl font-bold mb-4 text-gray-800">Event Log</h2>
                <div className="bg-white rounded-lg shadow overflow-hidden">
                    <ul className="divide-y divide-gray-200">
                        {events.length === 0 ? (
                            <li className="px-6 py-4 text-gray-500">No events yet</li>
                        ) : (
                            events.map((event) => (
                                <li key={event.id} className="px-6 py-4 hover:bg-gray-50">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <span className="font-semibold text-gray-900">{event.entity_type}</span>
                                            <span className="text-gray-600"> detected with confidence </span>
                                            <span className="font-medium text-blue-600">{(event.confidence * 100).toFixed(1)}%</span>
                                        </div>
                                        <span className="text-sm text-gray-500">
                                            {event.timestamp ? new Date(event.timestamp).toLocaleString() : 'N/A'}
                                        </span>
                                    </div>
                                </li>
                            ))
                        )}
                    </ul>
                </div>
            </div>
        </Layout>
    );
};

export default EventLog;