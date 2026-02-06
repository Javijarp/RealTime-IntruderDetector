import React, { useState } from "react";
import Layout from "./components/Layout";
import { AlertProvider } from "./context/AlertContext";
import "./index.css";
import Dashboard from "./pages/Dashboard";
import EventsList from "./pages/EventsList";
import FramesList from "./pages/FramesList";
import LiveStream from "./pages/LiveStream";

function App() {
  const [currentPage, setCurrentPage] = useState("dashboard");

  const renderPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />;
      case "stream":
        return <LiveStream />;
      case "events":
        return <EventsList />;
      case "frames":
        return <FramesList />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <AlertProvider>
      <Layout currentPage={currentPage} onNavigate={setCurrentPage}>
        {renderPage()}
      </Layout>
    </AlertProvider>
  );
}

export default App;
