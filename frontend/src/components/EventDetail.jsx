import { X } from "lucide-react";
import React from "react";

export default function EventDetail({ event, onClose }) {
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
                  {new Date(event.timestamp).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {new Date(event.timestamp).toISOString()}
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

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 font-medium">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
