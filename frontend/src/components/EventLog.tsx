import React, { useEffect, useState } from 'react';
import { fetchEvents } from '../services/api';

const EventLog: React.FC = () => {
    const [events, setEvents] = useState([]);

    useEffect(() => {
        const getEvents = async () => {
            const fetchedEvents = await fetchEvents();
            setEvents(fetchedEvents);
        };

        getEvents();
        const interval = setInterval(getEvents, 5000); // Refresh every 5 seconds

        return () => clearInterval(interval); // Cleanup on unmount
    }, []);

    return (
        <div className="event-log">
            <h2>Event Log</h2>
            <ul>
                {events.map((event) => (
                    <li key={event.event_id}>
                        <strong>{event.entity_type}</strong> detected with confidence {event.confidence} at {event.timestamp}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default EventLog;