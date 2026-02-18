import { Download, X } from "lucide-react";
import React from "react";
import { getFrameImageSrc, hasImageData } from "../utils/imageUtils";

interface Frame {
  id: number;
  frameNumber: number;
  imageData?: string;
  imageType: string;
  imagePath?: string;
  timestamp: string;
  detectionEventId?: number;
}

interface FrameDetailProps {
  frame: Frame;
  onClose: () => void;
}

const FrameDetail: React.FC<FrameDetailProps> = ({ frame, onClose }) => {
  const imageSrc = getFrameImageSrc(frame);
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
          {imageSrc && (
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Frame Preview
              </label>
              <div className="relative bg-gray-100 rounded-lg overflow-hidden max-h-96">
                <img
                  src={imageSrc}
                  alt="Frame preview"
                  className="w-full h-auto"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = "none";
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
          </div>

          {/* Download Button */}
          {imageSrc && (
            <div className="flex gap-2">
              <a
                href={imageSrc}
                download={`frame_${frame.frameNumber}.${frame.imageType || "jpg"}`}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                <Download className="h-4 w-4" />
                Download Frame
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FrameDetail;
