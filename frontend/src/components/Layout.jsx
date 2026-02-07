import {
  AlertCircle,
  BarChart3,
  Camera,
  Layers,
  ListChecks,
  Menu,
  X,
} from "lucide-react";
import React, { useState } from "react";

export default function Layout({ children, currentPage, onNavigate }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const menuItems = [
    {
      id: "dashboard",
      label: "Dashboard",
      icon: BarChart3,
    },
    {
      id: "stream",
      label: "Live Stream",
      icon: Camera,
    },
    {
      id: "events",
      label: "Detection Events",
      icon: AlertCircle,
    },
    {
      id: "frames",
      label: "Frames",
      icon: Layers,
    },
  ];

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <div
        className={`bg-gray-900 text-white transition-all duration-300 ${sidebarOpen ? "w-64" : "w-20"
          } flex flex-col`}>
        {/* Logo */}
        <div className="px-6 py-4 border-b border-gray-800 flex items-center justify-between">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-lg">FaceGuard</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1 hover:bg-gray-800 rounded-lg">
            {sidebarOpen ? (
              <X className="w-5 h-5" />
            ) : (
              <Menu className="w-5 h-5" />
            )}
          </button>
        </div>

        {/* Menu */}
        <nav className="flex-1 px-3 py-4 space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentPage === item.id;

            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-300 hover:bg-gray-800 hover:text-white"
                  }`}>
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && (
                  <span className="text-sm font-medium">{item.label}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t border-gray-800">
          <div className="flex items-center gap-3 px-4 py-3">
            <div className="w-8 h-8 bg-gray-700 rounded-full flex-shrink-0" />
            {sidebarOpen && (
              <div className="text-sm">
                <p className="font-medium">User</p>
                <p className="text-gray-400 text-xs">Admin</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Content Area */}
        <div className="flex-1 overflow-auto p-6">{children}</div>
      </div>
    </div>
  );
}
