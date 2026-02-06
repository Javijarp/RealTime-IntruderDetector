import { Maximize, Pause, Play, Volume2, VolumeX, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useAlert } from "../context/AlertContext";
import WebSocketClient from "../utils/WebSocketClient";

export default function VideoStream({ streamId = "default" }) {
  const { addAlert } = useAlert();
  const canvasRef = useRef(null);
  const clientRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [frameRate, setFrameRate] = useState(0);
  const [stats, setStats] = useState({
    framesReceived: 0,
    bytesReceived: 0,
    lastFrameTime: null,
  });
  const frameCountRef = useRef(0);
  const frameTimestampRef = useRef(Date.now());

  useEffect(() => {
    // Connect to WebSocket - use dynamic host
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Use the backend server IP directly - change this to match your backend
    const wsHost = "192.168.5.74:8080";  // Backend server address
    const wsUrl = `${wsProtocol}//${wsHost}/ws/stream`;

    console.log("VideoStream connecting to:", wsUrl);

    const client = new WebSocketClient(wsUrl);

    client.on("connected", () => {
      console.log("Connected to video stream");
      setIsConnected(true);
      addAlert("Connected to video stream", "success");

      // Subscribe to the stream
      client.send({
        type: "subscribe",
        streamId: streamId,
      });
    });

    client.on("frame", (message) => {
      if (!isPlaying) return;

      try {
        const { data, contentType } = message;
        const frameData = Uint8Array.from(atob(data), (c) => c.charCodeAt(0));
        const blob = new Blob([frameData], { type: contentType });
        const url = URL.createObjectURL(blob);

        const img = new Image();
        img.onload = () => {
          const canvas = canvasRef.current;
          if (canvas) {
            const ctx = canvas.getContext("2d");
            canvas.width = img.width;
            canvas.height = img.height;
            ctx.drawImage(img, 0, 0);
            URL.revokeObjectURL(url);

            // Update stats
            frameCountRef.current++;
            const now = Date.now();
            const timeDiff = now - frameTimestampRef.current;
            if (timeDiff >= 1000) {
              setFrameRate(frameCountRef.current);
              frameCountRef.current = 0;
              frameTimestampRef.current = now;
            }

            setStats((prev) => ({
              ...prev,
              framesReceived: prev.framesReceived + 1,
              bytesReceived: prev.bytesReceived + frameData.length,
              lastFrameTime: new Date().toLocaleTimeString(),
            }));
          }
        };
        img.src = url;
      } catch (error) {
        console.error("Error rendering frame:", error);
      }
    });

    client.on("error", (error) => {
      console.error("WebSocket error:", error);
      addAlert("Stream connection error", "error");
    });

    client.on("disconnected", () => {
      setIsConnected(false);
      addAlert("Disconnected from video stream", "warning");
    });

    clientRef.current = client;

    // Connect
    client.connect().catch((error) => {
      console.error("Failed to connect:", error);
      addAlert("Failed to connect to video stream", "error");
    });

    return () => {
      if (clientRef.current) {
        clientRef.current.send({
          type: "unsubscribe",
        });
        clientRef.current.disconnect();
      }
    };
  }, [streamId, isPlaying, addAlert]);

  const togglePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    setIsMuted(!isMuted);
  };

  const fullscreen = () => {
    const canvas = canvasRef.current;
    if (canvas) {
      canvas.requestFullscreen?.() ||
        canvas.webkitRequestFullscreen?.() ||
        canvas.msRequestFullscreen?.();
    }
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Video Display */}
      <div className="relative bg-black aspect-video flex items-center justify-center">
        <canvas
          ref={canvasRef}
          className="w-full h-full"
          style={{ maxWidth: "100%", maxHeight: "100%", objectFit: "contain" }}
        />

        {/* Connection Status Overlay */}
        <div className="absolute top-4 left-4 flex items-center gap-2">
          <div
            className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"
              } animate-pulse`}
          />
          <span className="text-white text-sm font-semibold">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>

        {/* FPS Counter */}
        <div className="absolute top-4 right-4 bg-black bg-opacity-70 text-white px-3 py-1 rounded text-sm font-mono">
          {frameRate} FPS
        </div>

        {/* No Signal Message */}
        {!isConnected && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-70">
            <div className="text-center">
              <p className="text-white text-lg font-semibold mb-2">No Signal</p>
              <p className="text-gray-400 text-sm">
                Waiting for stream connection...
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="px-4 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <button
              onClick={togglePlayPause}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title={isPlaying ? "Pause" : "Play"}>
              {isPlaying ? (
                <Pause className="h-5 w-5 text-gray-700" />
              ) : (
                <Play className="h-5 w-5 text-gray-700" />
              )}
            </button>

            <button
              onClick={toggleMute}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title={isMuted ? "Unmute" : "Mute"}>
              {isMuted ? (
                <VolumeX className="h-5 w-5 text-gray-700" />
              ) : (
                <Volume2 className="h-5 w-5 text-gray-700" />
              )}
            </button>

            <button
              onClick={fullscreen}
              className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
              title="Fullscreen">
              <Maximize className="h-5 w-5 text-gray-700" />
            </button>
          </div>

          <span className="text-sm text-gray-600 font-mono">
            {stats.lastFrameTime || "Waiting for frames..."}
          </span>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 text-sm">
          <div className="bg-white rounded px-3 py-2 border border-gray-200">
            <p className="text-gray-600 text-xs mb-1">Frames</p>
            <p className="font-semibold text-gray-900">
              {stats.framesReceived}
            </p>
          </div>

          <div className="bg-white rounded px-3 py-2 border border-gray-200">
            <p className="text-gray-600 text-xs mb-1">Data Received</p>
            <p className="font-semibold text-gray-900">
              {(stats.bytesReceived / 1024 / 1024).toFixed(2)} MB
            </p>
          </div>

          <div className="bg-white rounded px-3 py-2 border border-gray-200">
            <p className="text-gray-600 text-xs mb-1">Status</p>
            <p
              className={`font-semibold ${isConnected ? "text-green-600" : "text-red-600"}`}>
              {isConnected ? "Active" : "Offline"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
