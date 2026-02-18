import {
    ChevronDown,
    ChevronLeft,
    ChevronRight,
    Eye,
    Filter,
    RefreshCw,
    Search,
    Trash2,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { getDetectionEvents } from "../api/client";
import EventDetail from "../components/EventDetail";
import { useAlert } from "../context/AlertContext";
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

const EventsList: React.FC = () => {
  const { addAlert } = useAlert();
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("all");
  const [sortBy, setSortBy] = useState("newest");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [showDetail, setShowDetail] = useState(false);

  const itemsPerPage = 10;

  const fetchEvents = async () => {
    try {
      setLoading(true);
      const response = await getDetectionEvents();
      setEvents(response.data || []);
    } catch (error) {
      addAlert("Failed to load detection events", "error");
      console.error("Error fetching events:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEvents();
  }, []);

  // Filter and sort events
  let filteredEvents = events.filter((event) => {
    const matchesSearch =
      event.entityType.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (event.frameId && event.frameId.toString().includes(searchTerm)) ||
      (event.eventId && event.eventId.toString().includes(searchTerm));

    const matchesFilter =
      filterType === "all" || event.entityType === filterType;

    return matchesSearch && matchesFilter;
  });

  if (sortBy === "newest") {
    filteredEvents.sort((a, b) => {
      const dateA = new Date(a.timestamp || 0).getTime();
      const dateB = new Date(b.timestamp || 0).getTime();
      return dateB - dateA;
    });
  } else if (sortBy === "confidence") {
    filteredEvents.sort((a, b) => b.confidence - a.confidence);
  }

  const totalPages = Math.ceil(filteredEvents.length / itemsPerPage);
  const paginatedEvents = filteredEvents.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage,
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Detection Events</h1>
          <p className="text-gray-600 mt-1">
            Showing{" "}
            {paginatedEvents.length === 0
              ? 0
              : (currentPage - 1) * itemsPerPage + 1}
            -{Math.min(currentPage * itemsPerPage, filteredEvents.length)} of{" "}
            {filteredEvents.length} events
          </p>
        </div>
        <button
          onClick={fetchEvents}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search events..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filter by Type */}
          <div className="relative">
            <Filter className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
            <select
              value={filterType}
              onChange={(e) => {
                setFilterType(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none">
              <option value="all">All Types</option>
              <option value="Person">Person</option>
              <option value="Dog">Dog</option>
            </select>
            <ChevronDown className="absolute right-3 top-3 h-5 w-5 text-gray-400 pointer-events-none" />
          </div>

          {/* Sort */}
          <div className="relative">
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent appearance-none">
              <option value="newest">Newest First</option>
              <option value="confidence">Highest Confidence</option>
            </select>
            <ChevronDown className="absolute right-3 top-3 h-5 w-5 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Events Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="p-6 text-center text-gray-500">Loading events...</div>
        ) : paginatedEvents.length === 0 ? (
          <div className="p-6 text-center text-gray-500">No events found</div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Event ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Preview
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Frame ID
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedEvents.map((event, index) => {
                    const imageSrc = event.frameData
                      ? getFrameImageSrc(event.frameData)
                      : null;
                    return (
                      <tr
                        key={index}
                        className="border-b border-gray-200 hover:bg-gray-50">
                        <td className="px-6 py-4 text-sm text-gray-900">
                          #{event.eventId}
                        </td>
                        <td className="px-6 py-4">
                          <div className="w-16 h-16 bg-gray-100 rounded overflow-hidden flex items-center justify-center">
                            {imageSrc ? (
                              <img
                                src={imageSrc}
                                alt="Event preview"
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  (e.target as HTMLImageElement).style.display =
                                    "none";
                                }}
                              />
                            ) : (
                              <span className="text-xs text-gray-400">
                                No image
                              </span>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-semibold ${
                              event.entityType === "Person"
                                ? "bg-blue-100 text-blue-800"
                                : "bg-orange-100 text-orange-800"
                            }`}>
                            {event.entityType}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          {Math.round(event.confidence * 100)}%
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900">
                          #{event.frameId}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-600">
                          {event.timestamp
                            ? new Date(event.timestamp).toLocaleString()
                            : "N/A"}
                        </td>
                        <td className="px-6 py-4 text-sm flex gap-2">
                          <button
                            onClick={() => {
                              setSelectedEvent(event);
                              setShowDetail(true);
                            }}
                            className="p-2 hover:bg-blue-100 rounded-lg text-blue-600">
                            <Eye className="h-4 w-4" />
                          </button>
                          <button className="p-2 hover:bg-red-100 rounded-lg text-red-600">
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-6 py-4 border-t border-gray-200 flex items-center justify-between">
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
      </div>

      {/* Detail Modal */}
      {showDetail && selectedEvent && (
        <EventDetail
          event={selectedEvent}
          onClose={() => setShowDetail(false)}
        />
      )}
    </div>
  );
};

export default EventsList;
