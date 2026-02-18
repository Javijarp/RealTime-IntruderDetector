import {
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Download,
    Eye,
    Filter,
    RefreshCw,
    Search,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { getFrames } from "../api/client";
import FrameDetail from "../components/FrameDetail";
import { useAlert } from "../context/AlertContext";
import { getFrameImageSrc } from "../utils/imageUtils";

interface Frame {
  id: number;
  frameNumber: number;
  imageData?: string;
  imageType: string;
  imagePath?: string;
  timestamp: string;
  detectionEventId?: number;
}

const FramesList: React.FC = () => {
  const { addAlert } = useAlert();
  const [frames, setFrames] = useState<Frame[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedFrame, setSelectedFrame] = useState<Frame | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  const itemsPerPage = 10;

  const fetchFrames = async () => {
    try {
      setLoading(true);
      const response = await getFrames();
      setFrames(response.data || []);
    } catch (error) {
      addAlert("Failed to load frames", "error");
      console.error("Error fetching frames:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFrames();
  }, []);

  // Filter and sort frames
  let filteredFrames = frames.filter((frame) => {
    const matchesSearch =
      (frame.id && frame.id.toString().includes(searchTerm)) ||
      (frame.frameNumber && frame.frameNumber.toString().includes(searchTerm));

    return matchesSearch;
  });

  if (sortBy === "newest") {
    filteredFrames.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
    );
  } else if (sortBy === "oldest") {
    filteredFrames.sort(
      (a, b) =>
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    );
  }

  const totalPages = Math.ceil(filteredFrames.length / itemsPerPage);
  const paginatedFrames = filteredFrames.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Frames</h1>
          <p className="text-gray-600 mt-1">
            Showing{" "}
            {paginatedFrames.length === 0
              ? 0
              : (currentPage - 1) * itemsPerPage + 1}
            -{Math.min(currentPage * itemsPerPage, filteredFrames.length)} of{" "}
            {filteredFrames.length} frames
          </p>
        </div>
        <button
          onClick={fetchFrames}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search frames..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Sort */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none">
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
            </select>
            <ChevronDown className="absolute right-3 top-3 h-5 w-5 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Frames Grid */}
      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading frames...</div>
      ) : paginatedFrames.length === 0 ? (
        <div className="text-center py-12 text-gray-500">No frames found</div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {paginatedFrames.map((frame, index) => (
              <div
                key={index}
                className="bg-white rounded-lg shadow overflow-hidden hover:shadow-lg transition">
                {/* Frame Thumbnail */}
                <div className="bg-gray-100 aspect-video flex items-center justify-center overflow-hidden">
                  {(() => {
                    const imageSrc = getFrameImageSrc(frame);
                    return imageSrc ? (
                      <img
                        src={imageSrc}
                        alt={`Frame ${frame.frameNumber}`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    ) : (
                      <div className="text-gray-400">No preview</div>
                    );
                  })()}
                </div>

                {/* Frame Info */}
                <div className="p-4">
                  <div className="space-y-2 mb-4">
                    <p className="text-sm text-gray-600">
                      <strong>ID:</strong> #{frame.id}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Frame #:</strong> {frame.frameNumber}
                    </p>
                    <p className="text-sm text-gray-600">
                      <strong>Type:</strong> {frame.imageType}
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(frame.timestamp).toLocaleString()}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        setSelectedFrame(frame);
                        setShowDetail(true);
                      }}
                      className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">
                      <Eye className="h-4 w-4" />
                      View
                    </button>
                    {getFrameImageSrc(frame) && (
                      <a
                        href={getFrameImageSrc(frame)!}
                        download={`frame_${frame.frameNumber}.${frame.imageType || "jpg"}`}
                        className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm">
                        <Download className="h-4 w-4" />
                        Download
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 bg-white rounded-lg shadow">
              <span className="text-sm text-gray-600">
                Page {currentPage} of {totalPages}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                  disabled={currentPage === 1}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50">
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() =>
                    setCurrentPage(Math.min(totalPages, currentPage + 1))
                  }
                  disabled={currentPage === totalPages}
                  className="p-2 hover:bg-gray-100 rounded-lg disabled:opacity-50">
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Detail Modal */}
      {showDetail && selectedFrame && (
        <FrameDetail
          frame={selectedFrame}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  );
};

export default FramesList;
