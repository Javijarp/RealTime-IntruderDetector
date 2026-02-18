import { Save, Settings as SettingsIcon, Trash2 } from "lucide-react";
import React, { useState } from "react";
import { deleteAllEvents, deleteAllFrames } from "../services/api";

const Settings: React.FC = () => {
  const [settings, setSettings] = useState({
    apiEndpoint: "/api",
    refreshInterval: 5000,
    darkMode: false,
    notificationsEnabled: true,
  });

  const [isDeleting, setIsDeleting] = useState(false);

  const handleSave = () => {
    localStorage.setItem("appSettings", JSON.stringify(settings));
    alert("Settings saved successfully!");
  };

  const handleDeleteAllEvents = async () => {
    if (
      !confirm(
        "Are you sure you want to delete ALL events? This action cannot be undone.",
      )
    ) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteAllEvents();
      alert("All events deleted successfully!");
    } catch (error) {
      alert("Error deleting events. Check console for details.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteAllFrames = async () => {
    if (
      !confirm(
        "Are you sure you want to delete ALL frames? This action cannot be undone.",
      )
    ) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteAllFrames();
      alert("All frames deleted successfully!");
    } catch (error) {
      alert("Error deleting frames. Check console for details.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeleteAll = async () => {
    if (
      !confirm(
        "Are you sure you want to delete ALL events AND frames? This will completely clear the database. This action cannot be undone!",
      )
    ) {
      return;
    }

    setIsDeleting(true);
    try {
      await deleteAllEvents();
      await deleteAllFrames();
      alert("All events and frames deleted successfully!");
    } catch (error) {
      alert("Error deleting data. Check console for details.");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <SettingsIcon className="w-8 h-8 text-blue-600" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">
            Configure your application preferences
          </p>
        </div>
      </div>

      {/* Settings Form */}
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* API Endpoint */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            API Endpoint
          </label>
          <input
            type="text"
            value={settings.apiEndpoint}
            onChange={(e) =>
              setSettings({ ...settings, apiEndpoint: e.target.value })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-1">
            Base URL for API requests
          </p>
        </div>

        {/* Refresh Interval */}
        <div>
          <label className="block text-sm font-semibold text-gray-700 mb-2">
            Refresh Interval (ms)
          </label>
          <input
            type="number"
            value={settings.refreshInterval}
            onChange={(e) =>
              setSettings({
                ...settings,
                refreshInterval: parseInt(e.target.value),
              })
            }
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <p className="text-sm text-gray-500 mt-1">
            How often to refresh data
          </p>
        </div>

        {/* Toggles */}
        <div className="space-y-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.darkMode}
              onChange={(e) =>
                setSettings({ ...settings, darkMode: e.target.checked })
              }
              className="w-4 h-4 rounded border-gray-300"
            />
            <div>
              <span className="font-medium text-gray-700">Dark Mode</span>
              <p className="text-sm text-gray-500">
                Enable dark mode interface
              </p>
            </div>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.notificationsEnabled}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  notificationsEnabled: e.target.checked,
                })
              }
              className="w-4 h-4 rounded border-gray-300"
            />
            <div>
              <span className="font-medium text-gray-700">
                Enable Notifications
              </span>
              <p className="text-sm text-gray-500">
                Receive system notifications
              </p>
            </div>
          </label>
        </div>

        {/* Save Button */}
        <div className="pt-4 border-t border-gray-200">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            <Save className="h-4 w-4" />
            Save Settings
          </button>
        </div>
      </div>

      {/* Database Management */}
      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900 mb-1">
            Database Management
          </h2>
          <p className="text-gray-600 text-sm">
            Manage stored events and frames
          </p>
        </div>

        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-900 font-semibold mb-2">⚠️ Danger Zone</h3>
          <p className="text-red-700 text-sm mb-4">
            These actions are permanent and cannot be undone. All data will be
            lost.
          </p>

          <div className="space-y-3">
            <button
              onClick={handleDeleteAllEvents}
              disabled={isDeleting}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
              <Trash2 className="h-4 w-4" />
              {isDeleting ? "Deleting..." : "Delete All Events"}
            </button>

            <button
              onClick={handleDeleteAllFrames}
              disabled={isDeleting}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
              <Trash2 className="h-4 w-4" />
              {isDeleting ? "Deleting..." : "Delete All Frames"}
            </button>

            <button
              onClick={handleDeleteAll}
              disabled={isDeleting}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400 disabled:cursor-not-allowed">
              <Trash2 className="h-4 w-4" />
              {isDeleting ? "Deleting..." : "Delete All Events & Frames"}
            </button>
          </div>
        </div>
      </div>

      {/* Information */}
      <div className="bg-blue-50 rounded-lg border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-2">
          Application Info
        </h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Version: 1.0.0</li>
          <li>• Built with: React + Vite + TypeScript</li>
          <li>• Styling: Tailwind CSS</li>
          <li>• Communication: REST API + WebSocket</li>
        </ul>
      </div>
    </div>
  );
};

export default Settings;
