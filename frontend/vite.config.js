import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "0.0.0.0", // Allow access from Docker containers and external hosts
    strictPort: false, // Use next available port if 5173 is taken
    proxy: {
      "/api": {
        // Support environment variable, fallback to localhost:8080
        target: process.env.VITE_API_URL || "http://localhost:8080",
        changeOrigin: true,
        rewrite: (path) => {
          // Remove /api prefix since backend already has it
          return path;
        },
      },
      "/ws": {
        // WebSocket proxy for alerts and streams
        target: (process.env.VITE_API_URL || "http://localhost:8080").replace(
          /^http/,
          "ws",
        ),
        ws: true,
        changeOrigin: true,
        rewrite: (path) => {
          // Keep /ws in path as backend expects it
          return path.replace(/^\/ws/, "/api/ws");
        },
      },
    },
  },
  preview: {
    port: 5173,
    host: "0.0.0.0",
  },
});
