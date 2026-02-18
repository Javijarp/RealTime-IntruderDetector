import {
  Activity,
  AlertTriangle,
  BarChart3,
  Eye,
  RefreshCw,
  TrendingUp,
  Users,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { getDetectionEvents, getFrames } from "../api/client";
import { useAlert } from "../context/AlertContext";
import { getFrameImageSrc } from "../utils/imageUtils";

interface DashboardStats {
  totalEvents: number;
  totalFrames: number;
  detectedPeople: number;
  detectedDogs: number;
}

interface StatCard {
  icon: React.ComponentType<any>;
  label: string;
  value: number;
  color: string;
}

interface Event {
  id?: number;
  eventId?: number;
  entityType: string;
  confidence: number;
  frameId?: number;
  timestamp?: string;
}

interface Frame {
  id: number;
  frameNumber: number;
  imageData?: string;
  imageType: string;
  imagePath?: string;
  timestamp: string;
}

const Dashboard: React.FC = () => {
  const { addAlert } = useAlert();
  const [stats, setStats] = useState<DashboardStats>({
    totalEvents: 0,
    totalFrames: 0,
    detectedPeople: 0,
    detectedDogs: 0,
  });
  const [recentEvents, setRecentEvents] = useState<Event[]>([]);
  const [latestFrame, setLatestFrame] = useState<Frame | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const [eventsRes, framesRes] = await Promise.all([
        getDetectionEvents(),
        getFrames(),
      ]);

      const events = eventsRes.data || [];
      const frames = framesRes.data || [];

      console.log(
        `Dashboard: Fetched ${events.length} events and ${frames.length} frames`,
      );

      // Count events by type (case-insensitive for robustness)
      const people = events.filter(
        (e: any) => e.entityType && e.entityType.toLowerCase() === "person",
      ).length;
      const dogs = events.filter(
        (e: any) => e.entityType && e.entityType.toLowerCase() === "dog",
      ).length;

      console.log(`Dashboard: People=${people}, Dogs=${dogs}`);

      // Get last 5 events for recent activity
      const sortedEvents = [...events]
        .filter((e: any) => e.timestamp) // Only include events with timestamps
        .sort((a: any, b: any) => {
          const dateA = new Date(a.timestamp).getTime();
          const dateB = new Date(b.timestamp).getTime();
          return dateB - dateA;
        });
      setRecentEvents(sortedEvents.slice(0, 5));

      // Get latest frame
      if (frames.length > 0) {
        const sortedFrames = [...frames]
          .filter((f: any) => f.timestamp) // Only include frames with timestamps
          .sort((a: any, b: any) => {
            const dateA = new Date(a.timestamp).getTime();
            const dateB = new Date(b.timestamp).getTime();
            return dateB - dateA;
          });
        if (sortedFrames.length > 0) {
          setLatestFrame(sortedFrames[0]);
        }
      }

      setStats({
        totalEvents: events.length,
        totalFrames: frames.length,
        detectedPeople: people,
        detectedDogs: dogs,
      });
    } catch (error) {
      addAlert("Failed to load dashboard stats", "error");
      console.error("Error fetching stats:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    const interval = setInterval(fetchStats, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const statCards: StatCard[] = [
    {
      icon: AlertTriangle,
      label: "Total Events",
      value: stats.totalEvents,
      color: "bg-red-100 text-red-600",
    },
    {
      icon: Eye,
      label: "Total Frames",
      value: stats.totalFrames,
      color: "bg-blue-100 text-blue-600",
    },
    {
      icon: Users,
      label: "People Detected",
      value: stats.detectedPeople,
      color: "bg-green-100 text-green-600",
    },
    {
      icon: Activity,
      label: "Dogs Detected",
      value: stats.detectedDogs,
      color: "bg-yellow-100 text-yellow-600",
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="animate-spin mb-4">
            <RefreshCw className="h-8 w-8 text-blue-600" />
          </div>
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">System statistics and overview</p>
        </div>
        <button
          onClick={fetchStats}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((card, index) => {
          const Icon = card.icon;
          return (
            <div key={index} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className={`${card.color} p-3 rounded-lg`}>
                  <Icon className="h-6 w-6" />
                </div>
                <div className="ml-4">
                  <p className="text-gray-600 text-sm">{card.label}</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {card.value}
                  </p>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity - Events Table */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Recent Events</h2>
        {recentEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <AlertTriangle className="h-12 w-12 mx-auto mb-2 text-gray-400" />
            <p>No recent events</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">
                    Event ID
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">
                    Type
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">
                    Confidence
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">
                    Frame ID
                  </th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-700">
                    Timestamp
                  </th>
                </tr>
              </thead>
              <tbody>
                {recentEvents.map((event, idx) => (
                  <tr
                    key={idx}
                    className="border-b border-gray-100 hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-900">
                      #{event.eventId}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`px-3 py-1 rounded-full text-xs font-semibold ${
                          event.entityType === "Person"
                            ? "bg-blue-100 text-blue-800"
                            : "bg-orange-100 text-orange-800"
                        }`}>
                        {event.entityType}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-900">
                      {Math.round((event.confidence || 0) * 100)}%
                    </td>
                    <td className="px-4 py-3 text-gray-900">
                      #{event.frameId}
                    </td>
                    <td className="px-4 py-3 text-gray-600 text-xs">
                      {event.timestamp
                        ? new Date(event.timestamp).toLocaleString()
                        : "N/A"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Latest Frame Preview */}
      {latestFrame && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Latest Frame</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="bg-gray-100 rounded-lg overflow-hidden aspect-video flex items-center justify-center">
                {(() => {
                  const imageSrc = getFrameImageSrc(latestFrame);
                  return imageSrc ? (
                    <img
                      src={imageSrc}
                      alt="Latest frame"
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).style.display = "none";
                      }}
                    />
                  ) : (
                    <div className="text-gray-400">No preview available</div>
                  );
                })()}
              </div>
            </div>
            <div className="flex flex-col justify-between">
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-600">Frame ID</p>
                  <p className="text-2xl font-bold text-gray-900">
                    #{latestFrame.id}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Frame Number</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {latestFrame.frameNumber}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Type</p>
                  <p className="text-lg font-semibold text-gray-900">
                    {latestFrame.imageType}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Captured</p>
                  <p className="text-sm text-gray-900">
                    {new Date(latestFrame.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
