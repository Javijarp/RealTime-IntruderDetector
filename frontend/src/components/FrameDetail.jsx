import { Download, X } from "lucide-react";
import React from "react";

export default function FrameDetail({ frame, onClose }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">Frame Details</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 p-1 rounded hover:bg-gray-100">
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Frame Preview */}
          {frame.imagePath && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame Preview
              </label>
              <div className="relative bg-gray-100 rounded-lg overflow-hidden max-h-96">
                <img
                  src={frame.imagePath}
                  alt="Frame preview"
                  className="w-full h-auto"
                  onError={(e) => {
                    e.target.style.display = "none";
                  }}
                />
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Frame ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame ID
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900 font-mono">#{frame.id}</p>
              </div>
            </div>

            {/* Frame Number */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame Number
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900 font-mono">{frame.frameNumber}</p>
              </div>
            </div>

            {/* Image Type */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Image Type
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <span className="inline-flex px-2 py-1 rounded text-sm font-semibold bg-gray-200 text-gray-800">
                  {frame.imageType || "N/A"}
                </span>
              </div>
            </div>

            {/* Detection Event ID */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Detection Event ID
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900 font-mono">
                  {frame.detectionEventId
                    ? `#${frame.detectionEventId}`
                    : "N/A"}
                </p>
              </div>
            </div>

            {/* Timestamp */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Timestamp
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900">
                  {new Date(frame.timestamp).toLocaleString()}
                </p>
                <p className="text-sm text-gray-600 mt-1">
                  {new Date(frame.timestamp).toISOString()}
                </p>
              </div>
            </div>

            {/* Created At */}
            <div className="md:col-span-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Created At
              </label>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-gray-900">
                  {frame.createdAt
                    ? new Date(frame.createdAt).toLocaleString()
                    : "N/A"}
                </p>
              </div>
            </div>
          </div>

          {/* Faces */}
          {frame.faces && frame.faces.length > 0 && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-3">
                Detected Faces ({frame.faces.length})
              </label>
              <div className="space-y-3">
                {frame.faces.map((face, idx) => (
                  <div
                    key={idx}
                    className="border border-gray-200 rounded-lg p-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-600 font-semibold">
                          Face ID
                        </p>
                        <p className="text-sm text-gray-900 font-mono">
                          {face.faceId || `Face ${idx + 1}`}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-600 font-semibold">
                          Confidence
                        </p>
                        <p className="text-sm text-gray-900 font-semibold">
                          {Math.round((face.confidence || 0) * 100)}%
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Additional Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> This frame was processed by the edge module
              and stored in the backend.
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
