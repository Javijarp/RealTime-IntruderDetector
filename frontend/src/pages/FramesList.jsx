import {
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Download,
    Eye,
    Filter,
    Search,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { getFrames } from "../api/client";
import FrameDetail from "../components/FrameDetail";
import { useAlert } from "../context/AlertContext";

export default function FramesList() {
  const { addAlert } = useAlert();
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [sortBy, setSortBy] = useState("newest");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedFrame, setSelectedFrame] = useState(null);
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
      (a, b) => new Date(b.timestamp) - new Date(a.timestamp),
    );
  } else if (sortBy === "oldest") {
    filteredFrames.sort(
      (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
    );
  } else if (sortBy === "frameNumber") {
    filteredFrames.sort((a, b) => (b.frameNumber || 0) - (a.frameNumber || 0));
  }

  const totalPages = Math.ceil(filteredFrames.length / itemsPerPage);
  const paginatedFrames = filteredFrames.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  const handleViewDetail = (frame) => {
    setSelectedFrame(frame);
    setShowDetail(true);
  };

  const handleDownload = (frame) => {
    if (frame.imagePath) {
      const link = document.createElement("a");
      link.href = frame.imagePath;
      link.download = `frame-${frame.frameNumber}.jpg`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      addAlert("Frame download started", "success");
    } else {
      addAlert("No image available for download", "warning");
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Frames</h1>
          <p className="text-gray-600 mt-1">
            View processed frames from the edge module
          </p>
        </div>
        <button
          onClick={fetchFrames}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by frame ID or frame number..."
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
            <ChevronDown className="absolute right-3 top-3 h-5 w-5 text-gray-400 pointer-events-none" />
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none">
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="frameNumber">Frame Number (Descending)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Frame ID
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Frame Number
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Image Type
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Timestamp
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Created At
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {paginatedFrames.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="px-6 py-8 text-center text-gray-500">
                    {loading ? "Loading frames..." : "No frames found"}
                  </td>
                </tr>
              ) : (
                paginatedFrames.map((frame) => (
                  <tr key={frame.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      #{frame.id}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {frame.frameNumber}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <span className="inline-flex px-2 py-1 rounded text-xs font-semibold bg-gray-100 text-gray-800">
                        {frame.imageType || "N/A"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {new Date(frame.timestamp).toLocaleString()}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600">
                      {frame.createdAt
                        ? new Date(frame.createdAt).toLocaleString()
                        : "N/A"}
                    </td>
                    <td className="px-6 py-4 text-sm">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleViewDetail(frame)}
                          className="text-blue-600 hover:text-blue-800 p-1 rounded hover:bg-blue-50"
                          title="View frame details">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDownload(frame)}
                          className="text-green-600 hover:text-green-800 p-1 rounded hover:bg-green-50"
                          title="Download frame">
                          <Download className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Page {currentPage} of {totalPages} ({filteredFrames.length}{" "}
              frames)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                <ChevronLeft className="h-4 w-4" />
              </button>
              <button
                onClick={() =>
                  setCurrentPage(Math.min(totalPages, currentPage + 1))
                }
                disabled={currentPage === totalPages}
                className="p-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed">
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetail && selectedFrame && (
        <FrameDetail
          frame={selectedFrame}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  );
}
