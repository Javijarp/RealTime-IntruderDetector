import { Camera, Settings } from "lucide-react";
import React, { useState } from "react";
import VideoStream from "../components/VideoStream";

export default function LiveStream() {
  const [streamId, setStreamId] = useState("default");
  const [showSettings, setShowSettings] = useState(false);
  const [customStreamId, setCustomStreamId] = useState("default");

  const handleApplySettings = () => {
    setStreamId(customStreamId);
    setShowSettings(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Camera className="w-8 h-8 text-blue-600" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Live Stream</h1>
            <p className="text-gray-600 mt-1">
              Real-time video feed from edge module
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
          <Settings className="h-4 w-4" />
          Settings
        </button>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Stream Settings
          </h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Stream ID
              </label>
              <input
                type="text"
                value={customStreamId}
                onChange={(e) => setCustomStreamId(e.target.value)}
                placeholder="e.g., camera-1, front-door"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <p className="text-xs text-gray-500 mt-1">
                The stream ID to subscribe to from the backend
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleApplySettings}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
                Apply
              </button>
              <button
                onClick={() => setShowSettings(false)}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Stream */}
      <VideoStream key={streamId} streamId={streamId} />

      {/* Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 className="font-semibold text-blue-900 mb-2">
            How to Stream Frames
          </h3>
          <p className="text-sm text-blue-800 mb-3">
            Push frames to the stream from your edge module or backend service
            using:
          </p>
          <code className="block bg-white p-2 rounded text-xs font-mono text-gray-800 overflow-auto border border-blue-200">
            POST /api/stream/&#123;streamId&#125;/frame
          </code>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h3 className="font-semibold text-green-900 mb-2">
            Current Stream ID
          </h3>
          <div className="bg-white p-2 rounded border border-green-200 font-mono text-sm text-gray-800">
            {streamId}
          </div>
          <p className="text-xs text-green-800 mt-2">
            Send frames with this ID to display them on this page
          </p>
        </div>
      </div>

      {/* Usage Guide */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Usage Guide
        </h2>
        <div className="space-y-4 text-sm text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              1. WebSocket Connection
            </h3>
            <p className="mb-2">
              The frontend automatically connects to{" "}
              <code className="bg-gray-100 px-2 py-1 rounded text-xs font-mono">
                ws://localhost:8080/ws/stream
              </code>
            </p>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              2. Subscribe to Stream
            </h3>
            <p className="mb-2">Client sends:</p>
            <code className="block bg-gray-100 p-3 rounded text-xs font-mono overflow-auto mb-2">
              &#123;"type": "subscribe", "streamId": "default"&#125;
            </code>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              3. Push Frames from Backend
            </h3>
            <p className="mb-2">Edge module or backend sends frames via:</p>
            <code className="block bg-gray-100 p-3 rounded text-xs font-mono overflow-auto mb-2">
              curl -X POST http://localhost:8080/api/stream/default/frame \ -F
              "frame=@frame.jpg" \ -F "contentType=image/jpeg"
            </code>
          </div>

          <div>
            <h3 className="font-semibold text-gray-900 mb-2">
              4. Receive and Display
            </h3>
            <p>
              Frames are broadcast via WebSocket as base64-encoded data and
              rendered on the canvas in real-time
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
