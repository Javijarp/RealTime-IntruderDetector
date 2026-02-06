import axios from "axios";

const API_BASE_URL = "http://localhost:8080";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Detection Events
export const getDetectionEvents = () => api.get("/api/events");
export const getDetectionEventById = (id) => api.get(`/api/events/${id}`);
export const createDetectionEvent = (data) => api.post("/api/events", data);
export const updateDetectionEvent = (id, data) =>
  api.patch(`/api/events/${id}`, data);
export const markEventAsProcessed = (id) =>
  api.patch(`/api/events/${id}/process`);

// Frames
export const getFrames = () => api.get("/api/frames");
export const getFrameById = (id) => api.get(`/api/frames/${id}`);
export const createFrame = (formData) =>
  api.post("/api/frames", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

export default api;
