import { X } from "lucide-react";
import React from "react";
import { getFrameImageSrc } from "../utils/imageUtils";

interface Frame {
  id: number;
  frameNumber: number;
  imageData?: string;
  imageType: string;
  imagePath?: string;
  timestamp: string;
}

interface Event {
  id?: number;
  eventId?: number;
  entityType: string;
  confidence: number;
  frameId?: number;
  timestamp?: string;
  frameData?: Frame;
}

interface EventDetailProps {
  event: Event;
  onClose: () => void;
}

const EventDetail: React.FC<EventDetailProps> = ({ event, onClose }) => {
  const imageSrc = event.frameData ? getFrameImageSrc(event.frameData) : null;
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-96 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Event Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Frame Preview */}
          {imageSrc && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame Preview
              </label>
              <div className="relative bg-gray-100 rounded-lg overflow-hidden max-h-96">
                <img
                  src={imageSrc}
                  alt="Event frame"
                  className="w-full h-auto"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
                  }}
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Event ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Event ID
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900 font-mono">#{event.eventId}</p>
              </div>
            </div>

            {/* Entity Type */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Entity Type
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <span
                  className={`inline-flex px-3 py-1 rounded-full text-sm font-semibold ${
                    event.entityType === "Person"
                      ? "bg-blue-100 text-blue-800"
                      : "bg-orange-100 text-orange-800"
                  }`}>
                  {event.entityType}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Confidence Score
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <div className="space-y-2">
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div
                      className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-3 rounded-full"
                      style={{ width: `${(event.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <p className="text-gray-900 font-semibold">
                    {Math.round((event.confidence || 0) * 100)}%
                  </p>
                </div>
              </div>
            </div>

            {/* Frame ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame ID
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900 font-mono">
                  Frame #{event.frameId}
                </p>
              </div>
            </div>

            {/* Timestamp */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Detection Timestamp
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900">
                  {event.timestamp
                    ? new Date(event.timestamp).toLocaleString()
                    : "N/A"}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {event.timestamp
                    ? new Date(event.timestamp).toISOString()
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> This detection event was processed by the
              edge module and stored in the backend database.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetail;
