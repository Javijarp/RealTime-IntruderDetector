import React, { useEffect, useRef } from 'react';

const LiveFeed: React.FC = () => {
    const videoRef = useRef<HTMLVideoElement | null>(null);

    useEffect(() => {
        const startVideo = async () => {
            try {
                if (videoRef.current) {
                    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    videoRef.current.srcObject = stream;
                }
            } catch (error) {
                console.error('Failed to access camera:', error);
            }
        };

        startVideo();

        return () => {
            if (videoRef.current && videoRef.current.srcObject) {
                const stream: any = videoRef.current.srcObject;
                stream.getTracks().forEach((track: any) => track.stop());
            }
        };
    }, []);

    return (
        <div>
            <h2>Live Feed</h2>
            <video ref={videoRef} autoPlay playsInline style={{ width: '100%', height: 'auto' }} />
        </div>
    );
};

export default LiveFeed;