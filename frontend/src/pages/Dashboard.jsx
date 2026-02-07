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
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  const StatCard = ({ icon: Icon, label, value, bgColor, trend }) => (
    <div className="group relative overflow-hidden bg-white rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-300 border border-gray-100">
      <div className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-5 transition-opacity duration-300"
        style={{ background: bgColor }}></div>
      <div className="p-6 relative">
        <div className="flex items-start justify-between mb-4">
          <div className={`p-3 rounded-xl ${bgColor} bg-opacity-10`}>
            <Icon className={`h-6 w-6 ${bgColor.replace('bg-', 'text-')}`} strokeWidth={2} />
          </div>
          {trend && (
            <div className="flex items-center gap-1 px-2 py-1 bg-green-50 text-green-600 rounded-lg text-xs font-medium">
              <TrendingUp className="h-3 w-3" />
              {trend}%
            </div>
          )}
        </div>
        <div>
          <p className="text-sm font-medium text-gray-500 mb-1">{label}</p>
          <p className="text-3xl font-bold text-gray-900">
            {loading ? (
              <span className="inline-block animate-pulse bg-gray-200 rounded h-9 w-16"></span>
            ) : (
              value.toLocaleString()
            )}
          </p>
        </div>
      </div>
    </div>
  );

  const detectionRate = stats.totalFrames > 0
    ? Math.round((stats.totalEvents / stats.totalFrames) * 100)
    : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50 to-indigo-50 p-6">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            icon={Activity}
            label="Total Events"
            value={stats.totalEvents}
            bgColor="bg-blue-500"
            trend={12}
          />
          <StatCard
            icon={BarChart3}
            label="Frames Processed"
            value={stats.totalFrames}
            bgColor="bg-purple-500"
          />
          <StatCard
            icon={Users}
            label="People Detected"
            value={stats.detectedPeople}
            bgColor="bg-green-500"
            trend={8}
          />
          <StatCard
            icon={AlertTriangle}
            label="Dogs Detected"
            value={stats.detectedDogs}
            bgColor="bg-orange-500"
          />
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Detection Analytics */}
          <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
            <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-blue-50 to-indigo-50">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">Detection Analytics</h2>
                  <p className="text-sm text-gray-600 mt-1">Real-time monitoring overview</p>
                </div>
                <button
                  onClick={fetchStats}
                  disabled={loading}
                  className="flex items-center gap-2 px-4 py-2 bg-white text-gray-700 rounded-xl hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm border border-gray-200 transition-all duration-200 hover:shadow-md">
                  <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                  <span className="font-medium">Refresh</span>
                </button>
              </div>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {/* Detection Rate Progress */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-semibold text-gray-700">Detection Rate</span>
                    <span className="text-2xl font-bold text-blue-600">{detectionRate}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-blue-500 to-indigo-500 h-3 rounded-full transition-all duration-500 ease-out"
                      style={{ width: `${detectionRate}%` }}
                    ></div>
                  </div>
                </div>

                {/* Entity Distribution */}
                <div className="grid grid-cols-2 gap-4 pt-4">
                  <div className="bg-green-50 rounded-xl p-4 border border-green-100">
                    <div className="flex items-center gap-3">
                      <Users className="h-8 w-8 text-green-600" />
                      <div>
                        <p className="text-sm text-green-700 font-medium">People</p>
                        <p className="text-2xl font-bold text-green-900">{stats.detectedPeople}</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-orange-50 rounded-xl p-4 border border-orange-100">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="h-8 w-8 text-orange-600" />
                      <div>
                        <p className="text-sm text-orange-700 font-medium">Dogs</p>
                        <p className="text-2xl font-bold text-orange-900">{stats.detectedDogs}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Info */}
          <div className="space-y-6">
            {/* System Status */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
              <div className="p-6 border-b border-gray-100 bg-gradient-to-r from-purple-50 to-pink-50">
                <h3 className="text-lg font-bold text-gray-900">System Status</h3>
              </div>
              <div className="p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <Eye className="h-5 w-5 text-green-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Monitoring</span>
                  </div>
                  <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                    Active
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <Activity className="h-5 w-5 text-blue-600" />
                    </div>
                    <span className="text-sm font-medium text-gray-700">Processing</span>
                  </div>
                  <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">
                    Real-time
                  </span>
                </div>
              </div>
            </div>

            {/* Last Update */}
            <div className="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-2xl shadow-lg p-6 text-white">
              <div className="flex items-center gap-3 mb-3">
                <div className="p-2 bg-white bg-opacity-20 rounded-lg">
                  <RefreshCw className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-bold">Last Updated</h3>
              </div>
              <p className="text-2xl font-bold">{new Date().toLocaleTimeString()}</p>
              <p className="text-sm text-blue-100 mt-2">
                {new Date().toLocaleDateString('en-US', {
                  weekday: 'long',
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric'
                })}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
