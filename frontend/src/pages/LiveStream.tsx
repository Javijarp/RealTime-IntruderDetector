import { Camera, Settings } from "lucide-react";
import React, { useState } from "react";
import VideoStream from "../components/VideoStream";

const LiveStream: React.FC = () => {
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
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="Enter stream ID"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleApplySettings}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                Apply
              </button>
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Video Stream */}
      <VideoStream streamId={streamId} />

      {/* Information */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Stream Information
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>
            • Current Stream ID: <strong>{streamId}</strong>
          </li>
          <li>• Connection: WebSocket-based real-time stream</li>
          <li>• Compression: Frame-by-frame compression</li>
          <li>• Protocol: Secure WebSocket (WSS) in production</li>
        </ul>
      </div>
    </div>
  );
};

export default LiveStream;
