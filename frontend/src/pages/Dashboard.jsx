import {
    Activity,
    AlertTriangle,
    BarChart3,
    RefreshCw,
    Users,
} from "lucide-react";
import React, { useEffect, useState } from "react";
import { getDetectionEvents, getFrames } from "../api/client";
import { useAlert } from "../context/AlertContext";

export default function Dashboard() {
  const { addAlert } = useAlert();
  const [stats, setStats] = useState({
    totalEvents: 0,
    totalFrames: 0,
    detectedPeople: 0,
    detectedDogs: 0,
  });
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

      const people = events.filter((e) => e.entityType === "Person").length;
      const dogs = events.filter((e) => e.entityType === "Dog").length;

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

  const StatCard = ({ icon: Icon, label, value, bgColor }) => (
    <div className={`${bgColor} rounded-lg p-6 text-white`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm opacity-90 mb-1">{label}</p>
          <p className="text-3xl font-bold">{loading ? "-" : value}</p>
        </div>
        <Icon className="h-12 w-12 opacity-30" />
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Real-time face recognition monitoring
          </p>
        </div>
        <button
          onClick={fetchStats}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Activity}
          label="Total Events"
          value={stats.totalEvents}
          bgColor="bg-gradient-to-br from-blue-500 to-blue-600"
        />
        <StatCard
          icon={BarChart3}
          label="Frames Processed"
          value={stats.totalFrames}
          bgColor="bg-gradient-to-br from-purple-500 to-purple-600"
        />
        <StatCard
          icon={Users}
          label="People Detected"
          value={stats.detectedPeople}
          bgColor="bg-gradient-to-br from-green-500 to-green-600"
        />
        <StatCard
          icon={AlertTriangle}
          label="Dogs Detected"
          value={stats.detectedDogs}
          bgColor="bg-gradient-to-br from-orange-500 to-orange-600"
        />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Quick Stats</h2>
        </div>
        <div className="p-6">
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-gray-600">Detection Rate</span>
              <span className="text-lg font-semibold text-gray-900">
                {stats.totalFrames > 0
                  ? Math.round((stats.totalEvents / stats.totalFrames) * 100)
                  : 0}
                %
              </span>
            </div>
            <div className="flex items-center justify-between pb-3 border-b border-gray-100">
              <span className="text-gray-600">Entity Types Detected</span>
              <span className="text-lg font-semibold text-gray-900">
                {(stats.detectedPeople > 0 ? 1 : 0) +
                  (stats.detectedDogs > 0 ? 1 : 0)}
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Last Updated</span>
              <span className="text-sm text-gray-500">
                {new Date().toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
