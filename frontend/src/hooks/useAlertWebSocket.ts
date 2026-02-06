import { useEffect, useState } from 'react';

interface AlertData {
    type: string;
    eventId: number;
    entityType: string;
    confidence: number;
    timestamp: string;
    message: string;
    imageData?: string;
    imageType?: string;
}

export const useAlertWebSocket = (url: string) => {
    const [alert, setAlert] = useState<AlertData | null>(null);
    const [connected, setConnected] = useState(false);
    const [socket, setSocket] = useState<WebSocket | null>(null);

    useEffect(() => {
        let ws: WebSocket;
        let reconnectTimeout: NodeJS.Timeout;
        let reconnectAttempts = 0;
        const maxReconnectAttempts = 5;

        const connect = () => {
            try {
                ws = new WebSocket(url);

                ws.onopen = () => {
                    console.log('Alert WebSocket connected');
                    setConnected(true);
                    setSocket(ws);
                    reconnectAttempts = 0;
                };

                ws.onmessage = (event) => {
                    try {
                        const data = JSON.parse(event.data);
                        console.log('WebSocket message received:', data);

                        // Handle alert messages
                        if (data.type === 'alert') {
                            setAlert(data);
                        }
                    } catch (e) {
                        console.error('Error parsing WebSocket message:', e);
                    }
                };

                ws.onerror = (error) => {
                    console.error('WebSocket error:', error);
                };

                ws.onclose = () => {
                    console.log('Alert WebSocket disconnected');
                    setConnected(false);
                    setSocket(null);

                    // Attempt reconnection
                    if (reconnectAttempts < maxReconnectAttempts) {
                        reconnectAttempts++;
                        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
                        reconnectTimeout = setTimeout(connect, delay);
                    }
                };
            } catch (error) {
                console.error('Error creating WebSocket:', error);
            }
        };

        connect();

        return () => {
            if (reconnectTimeout) {
                clearTimeout(reconnectTimeout);
            }
            if (ws) {
                ws.close();
            }
        };
    }, [url]);

    const clearAlert = () => {
        setAlert(null);
    };

    return { alert, clearAlert, connected, socket };
};

export default useAlertWebSocket;
