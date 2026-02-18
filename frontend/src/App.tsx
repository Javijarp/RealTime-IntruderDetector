import React from "react";
import {
    Route,
    BrowserRouter as Router,
    Routes,
    useLocation,
    useNavigate,
} from "react-router-dom";
import Alert from "./components/Alert";
import EventNotificationPanel from "./components/EventNotificationPanel";
import Layout from "./components/Layout";
import { AlertProvider } from "./context/AlertContext";
import useAlertWebSocket from "./hooks/useAlertWebSocket";
import { useNewEventNotifications } from "./hooks/useNewEventNotifications";
import Dashboard from "./pages/Dashboard";
import Diagnostics from "./pages/Diagnostics";
import EventsList from "./pages/EventsList";
import FramesList from "./pages/FramesList";
import Home from "./pages/Home";
import LiveStream from "./pages/LiveStream";
import Settings from "./pages/Settings";

const AppContent: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { alerts, dismissAlert, markEventAsViewed } =
    useNewEventNotifications();

  // Map routes to page IDs for sidebar highlighting
  const getPageIdFromRoute = (pathname: string) => {
    switch (pathname) {
      case "/":
        return "dashboard";
      case "/dashboard":
        return "dashboard";
      case "/live-stream":
        return "stream";
      case "/events":
        return "events";
      case "/frames":
        return "frames";
      case "/settings":
        return "settings";
      default:
        return "dashboard";
    }
  };

  const currentPage = getPageIdFromRoute(location.pathname);

  // WebSocket URL - connect to backend for alerts
  // nginx proxies /ws/ to backend:8080/api/ws/
  const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsHost = window.location.host;
  const wsUrl = `${wsProtocol}//${wsHost}/ws/alerts`;

  console.log("WebSocket connecting to:", wsUrl);

  const { alert, clearAlert, connected } = useAlertWebSocket(wsUrl);

  const handleNavigate = (pageId: string) => {
    switch (pageId) {
      case "dashboard":
        navigate("/");
        break;
      case "stream":
        navigate("/live-stream");
        break;
      case "events":
        navigate("/events");
        break;
      case "frames":
        navigate("/frames");
        break;
      case "settings":
        navigate("/settings");
        break;
      default:
        navigate("/");
    }
  };

  // Handle notification click - navigate to events and mark as viewed
  const handleNotificationClick = (eventId: number) => {
    markEventAsViewed(eventId);
    navigate("/events");
  };

  return (
    <div className="App">
      {/* New Event Notifications Panel (Top Left) */}
      <EventNotificationPanel
        alerts={alerts}
        onDismiss={dismissAlert}
        onEventClick={handleNotificationClick}
      />

      {/* Global alert system */}
      {alert && (
        <Alert
          message={alert.message}
          entityType={alert.entityType}
          confidence={alert.confidence}
          timestamp={alert.timestamp}
          imageData={alert.imageData}
          imageType={alert.imageType}
          onClose={clearAlert}
        />
      )}

      {/* WebSocket connection status indicator */}
      {!connected && (
        <div className="fixed bottom-5 right-5 bg-orange-500 text-white px-4 py-2 rounded text-sm z-40">
          ⚠ Alert system disconnected
        </div>
      )}

      <Routes>
        <Route path="/diagnostics" element={<Diagnostics />} />
        <Route
          path="*"
          element={
            <Layout currentPage={currentPage} onNavigate={handleNavigate}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/live-stream" element={<LiveStream />} />
                <Route path="/events" element={<EventsList />} />
                <Route path="/frames" element={<FramesList />} />
                <Route path="/settings" element={<Settings />} />
              </Routes>
            </Layout>
          }
        />
      </Routes>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AlertProvider>
        <AppContent />
      </AlertProvider>
    </Router>
  );
};

export default App;
