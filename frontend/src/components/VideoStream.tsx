import { Maximize, Pause, Play, Volume2, VolumeX, X } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { useAlert } from "../context/AlertContext";
import WebSocketClient from "../utils/WebSocketClient";

interface VideoStreamProps {
  streamId?: string;
}

interface Stats {
  framesReceived: number;
  bytesReceived: number;
  lastFrameTime: string | null;
}

interface FrameMessage {
  type: string;
  data: string;
  contentType: string;
  streamId: string;
}

const VideoStream: React.FC<VideoStreamProps> = ({ streamId = "default" }) => {
  const { addAlert } = useAlert();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const clientRef = useRef<WebSocketClient | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isMuted, setIsMuted] = useState(false);
  const [frameRate, setFrameRate] = useState(0);
  const [stats, setStats] = useState<Stats>({
    framesReceived: 0,
    bytesReceived: 0,
    lastFrameTime: null,
  });
  const frameCountRef = useRef(0);
  const frameTimestampRef = useRef(Date.now());

  useEffect(() => {
    // Connect to WebSocket - use relative URL for nginx proxy
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsHost = window.location.host; // Use current host (nginx will proxy)
    const wsUrl = `${wsProtocol}//${wsHost}/ws/stream`; // nginx proxies /ws/ to backend /api/ws/

    console.log("VideoStream connecting to:", wsUrl);

    const client = new WebSocketClient(wsUrl);

    client.on("connected", () => {
      console.log("✅ Connected to video stream WebSocket");
      console.log("📡 Subscribing to stream:", streamId);
      setIsConnected(true);
      addAlert("Connected to video stream", "success");

      // Subscribe to the stream
      client.send({
        type: "subscribe",
        streamId: streamId,
      });
      console.log("✉️ Subscription message sent");
    });

    client.on("frame", (message: FrameMessage) => {
      console.log("📹 Frame received:", message.streamId);
      if (!isPlaying) return;

      try {
        const { data, contentType } = message;
        console.log("🎬 Decoding frame, size:", data ? data.length : 0);
        const frameData = Uint8Array.from(atob(data), (c) => c.charCodeAt(0));
        const blob = new Blob([frameData], { type: contentType });
        const url = URL.createObjectURL(blob);

        const img = new Image();
        img.onload = () => {
          const canvas = canvasRef.current;
          if (canvas) {
            const ctx = canvas.getContext("2d");
            if (ctx) {
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
          }
        };
        img.src = url;
      } catch (error) {
        console.error("Error rendering frame:", error);
      }
    });

    client.on("error", (error: any) => {
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
      const canvasElement = canvas as any;
      canvasElement.requestFullscreen?.() ||
        canvasElement.webkitRequestFullscreen?.() ||
        canvasElement.msRequestFullscreen?.();
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
            className={`w-3 h-3 rounded-full ${
              isConnected ? "bg-green-500" : "bg-red-500"
            } animate-pulse`}
          />
          <span className="text-white text-sm font-medium">
            {isConnected ? "Connected" : "Disconnected"}
          </span>
        </div>

        {/* Stats Overlay */}
        <div className="absolute bottom-4 right-4 bg-black bg-opacity-75 text-white text-xs p-3 rounded font-mono space-y-1">
          <div>FPS: {frameRate}</div>
          <div>Frames: {stats.framesReceived}</div>
          <div>Last: {stats.lastFrameTime || "N/A"}</div>
        </div>
      </div>

      {/* Controls */}
      <div className="bg-gray-800 text-white px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlayPause}
            className="p-2 hover:bg-gray-700 rounded-lg transition">
            {isPlaying ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="h-5 w-5" />
            )}
          </button>

          <button
            onClick={toggleMute}
            className="p-2 hover:bg-gray-700 rounded-lg transition">
            {isMuted ? (
              <VolumeX className="h-5 w-5" />
            ) : (
              <Volume2 className="h-5 w-5" />
            )}
          </button>

          <span className="text-sm text-gray-400">Stream: {streamId}</span>
        </div>

        <button
          onClick={fullscreen}
          className="p-2 hover:bg-gray-700 rounded-lg transition">
          <Maximize className="h-5 w-5" />
        </button>
      </div>
    </div>
  );
};

export default VideoStream;
