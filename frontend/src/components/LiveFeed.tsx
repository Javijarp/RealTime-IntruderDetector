import React, { useEffect, useRef } from 'react';

const LiveFeed: React.FC = () => {
    const videoRef = useRef<HTMLVideoElement | null>(null);

    useEffect(() => {
        const startVideo = async () => {
            if (videoRef.current) {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                videoRef.current.srcObject = stream;
            }
        };

        startVideo();

        return () => {
            if (videoRef.current) {
                const stream = videoRef.current.srcObject as MediaStream;
                if (stream) {
                    const tracks = stream.getTracks();
                    tracks.forEach(track => track.stop());
                }
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