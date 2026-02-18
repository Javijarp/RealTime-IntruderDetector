import axios from "axios";
import React, { useEffect, useState } from "react";

interface ApiTest {
  endpoint: string;
  status: "pending" | "success" | "error";
  message: string;
  data?: any;
}

const DiagnosticsPage: React.FC = () => {
  const [tests, setTests] = useState<ApiTest[]>([
    {
      endpoint: "/api/events",
      status: "pending",
      message: "Testing API connection...",
    },
    {
      endpoint: "/api/frames",
      status: "pending",
      message: "Testing frames endpoint...",
    },
    {
      endpoint: "Backend health",
      status: "pending",
      message: "Checking backend connectivity...",
    },
  ]);

  useEffect(() => {
    const runTests = async () => {
      const newTests = [...tests];

      // Test Events endpoint
      try {
        console.log("Testing /api/events...");
        const response = await axios.get("/api/events", { timeout: 5000 });
        newTests[0] = {
          endpoint: "/api/events",
          status: "success",
          message: `Got ${response.data?.length || 0} events`,
          data: response.data,
        };
      } catch (error: any) {
        console.error("Events error:", error);
        newTests[0] = {
          endpoint: "/api/events",
          status: "error",
          message: `Error: ${error.message} - ${error.response?.status || "Network error"}`,
        };
      }

      // Test Frames endpoint
      try {
        console.log("Testing /api/frames...");
        const response = await axios.get("/api/frames", { timeout: 5000 });
        newTests[1] = {
          endpoint: "/api/frames",
          status: "success",
          message: `Got ${response.data?.length || 0} frames`,
          data: response.data,
        };
      } catch (error: any) {
        console.error("Frames error:", error);
        newTests[1] = {
          endpoint: "/api/frames",
          status: "error",
          message: `Error: ${error.message} - ${error.response?.status || "Network error"}`,
        };
      }

      // Test backend health
      try {
        console.log("Testing backend connectivity...");
        // This tests if vite proxy is working
        const response = await axios
          .get("/api/health", { timeout: 5000 })
          .catch(() => {
            // If health endpoint doesn't exist, try with events
            return axios.get("/api/events", { timeout: 5000 });
          });
        newTests[2] = {
          endpoint: "Backend health",
          status: "success",
          message: "Backend is reachable",
        };
      } catch (error: any) {
        console.error("Backend error:", error);
        newTests[2] = {
          endpoint: "Backend health",
          status: "error",
          message: `Cannot reach backend - ensure it's running on http://localhost:8080`,
        };
      }

      setTests(newTests);
    };

    runTests();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-100 to-gray-200 p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-8">
          API Diagnostics
        </h1>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-semibold text-gray-800 mb-4">
            Configuration
          </h2>
          <div className="space-y-3 font-mono text-sm bg-gray-50 p-4 rounded">
            <p>
              <span className="font-bold">Frontend URL:</span>{" "}
              {window.location.origin}
            </p>
            <p>
              <span className="font-bold">Vite Proxy:</span> /api →
              http://localhost:8080/api
            </p>
            <p>
              <span className="font-bold">Backend URL:</span>{" "}
              http://localhost:8080
            </p>
            <p>
              <span className="font-bold">Mode:</span> Development (npm run dev)
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {tests.map((test, idx) => (
            <div
              key={idx}
              className={`p-4 rounded-lg border-l-4 ${
                test.status === "success"
                  ? "bg-green-50 border-green-500"
                  : test.status === "error"
                    ? "bg-red-50 border-red-500"
                    : "bg-yellow-50 border-yellow-500"
              }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {test.endpoint}
                  </h3>
                  <p className="text-sm text-gray-700 mt-1">{test.message}</p>
                </div>
                <div className="text-2xl">
                  {test.status === "success"
                    ? "✅"
                    : test.status === "error"
                      ? "❌"
                      : "⏳"}
                </div>
              </div>
              {test.data && (
                <pre className="mt-3 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-32">
                  {JSON.stringify(test.data, null, 2).slice(0, 500)}...
                </pre>
              )}
            </div>
          ))}
        </div>

        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">Troubleshooting</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>✓ Vite dev server running on port 5173</li>
            <li>✓ API proxy configured in vite.config.js</li>
            <li>? Backend must be running on port 8080</li>
            <li>
              ? Check that backend has /api/events and /api/frames endpoints
            </li>
            <li>
              ? If using Docker, ensure ports are exposed and containers can
              connect
            </li>
          </ul>
        </div>

        <div className="mt-6 text-center">
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
            Retry Tests
          </button>
        </div>
      </div>
    </div>
  );
};

export default DiagnosticsPage;
